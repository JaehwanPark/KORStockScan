"""One-process, read-only code compatibility inside real startup isolation.

The trusted parent authenticates native origin and source-delta proofs before
launch. This child rebinds those proofs to its actual request, kernel boundary,
Git identity and unchanged bytes. It issues no operational handoff or PID claim.
"""
from __future__ import annotations

from datetime import date
import hashlib
import json
import os
from pathlib import Path
import re

SCHEMA = 'main_startup_validation_code_context_v1'
PROOF_SCHEMA = 'main_startup_validation_consumer_code_handoff_v1'
REQUEST_SCHEMA = 'main_policy_load_exit_validation_v1'
ROOT = Path(__file__).resolve().parents[3]
_FAMILIES = {
    'pre_submit_delay': ('pre_submit_delay_handoff', 'policy_sha256'),
    'main_stop': ('main_stop_confirmation_receipt', 'policy_sha256'),
    'holding_vote': ('holding_path_vote_policy_receipt', 'bundle_sha256'),
}
_CONTEXT = None
_MAX_JSON = 8 * 1024 * 1024


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
        ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def _hex(value, length=64):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{' + str(length) + '}', value) is not None


def _read(path, *, maximum=_MAX_JSON):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > maximum:
        raise ValueError('startup_code_context_source_not_regular_bounded')
    with path.open('rb') as stream:
        raw = stream.read(maximum + 1)
    if len(raw) > maximum:
        raise ValueError('startup_code_context_source_unbounded')
    return raw


def _json(path):
    value = json.loads(_read(path))
    if not isinstance(value, dict):
        raise ValueError('startup_code_context_object_required')
    return value


def _sha(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError('startup_code_context_source_not_regular')
    def identity(value):
        return (value.st_dev, value.st_ino, value.st_mode, value.st_size,
                value.st_mtime_ns, value.st_ctime_ns)
    with path.open('rb') as stream:
        before = identity(os.fstat(stream.fileno()))
        digest = hashlib.sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
        if before != identity(os.fstat(stream.fileno())) or path.is_symlink() or before != identity(path.stat()):
            raise ValueError('startup_code_context_source_changed_during_read')
    return digest.hexdigest()


def _check_sources(sources, *, absent_allowed=False):
    if not isinstance(sources, dict) or not sources:
        raise ValueError('startup_code_context_sources_required')
    for name, expected in sources.items():
        if not isinstance(name, str) or not Path(name).is_absolute():
            raise ValueError('startup_code_context_source_path_invalid')
        if expected is None and absent_allowed:
            if Path(name).exists() or Path(name).is_symlink():
                raise ValueError('startup_code_context_absent_source_changed')
        elif not _hex(expected) or _sha(name) != expected:
            raise ValueError('startup_code_context_source_changed')


def _bound_source(sources, path):
    path = Path(path)
    values = {sources[name] for name in (str(path), str(path.resolve(strict=True))) if name in sources}
    if len(values) != 1 or _sha(path) not in values:
        raise ValueError('startup_code_context_source_not_bound')


def _git_head(root):
    """Read Git identity without spawning Git under seccomp."""
    root = Path(root)
    metadata = root / '.git'
    if metadata.is_file():
        line = _read(metadata, maximum=4096).decode().strip()
        if not line.startswith('gitdir: '):
            raise ValueError('startup_code_context_gitdir_invalid')
        directory = (root / line[8:]).resolve(strict=True)
    elif metadata.is_dir() and not metadata.is_symlink():
        directory = metadata
    else:
        raise ValueError('startup_code_context_gitdir_missing')
    head = _read(directory / 'HEAD', maximum=4096).decode().strip()
    if _hex(head, 40):
        return head
    if not head.startswith('ref: '):
        raise ValueError('startup_code_context_git_head_invalid')
    ref = head[5:]
    if not ref.startswith('refs/') or '..' in Path(ref).parts or not re.fullmatch('[A-Za-z0-9._/-]+', ref):
        raise ValueError('startup_code_context_git_ref_invalid')
    common = directory
    if (directory / 'commondir').is_file():
        common = (directory / _read(directory / 'commondir', maximum=4096).decode().strip()).resolve(strict=True)
    for parent in (directory, common):
        if (parent / ref).is_file():
            commit = _read(parent / ref, maximum=4096).decode().strip()
            if _hex(commit, 40):
                return commit
            raise ValueError('startup_code_context_git_ref_invalid')
    packed = common / 'packed-refs'
    if packed.is_file():
        for line in _read(packed).decode().splitlines():
            if line.startswith(('#', '^')):
                continue
            fields = line.split()
            if len(fields) == 2 and fields[1] == ref and _hex(fields[0], 40):
                return fields[0]
    raise ValueError('startup_code_context_git_ref_missing')


def _contract(root, paths, sources):
    if not isinstance(paths, dict) or not paths:
        raise ValueError('startup_code_context_contract_paths_invalid')
    values = {}
    for key, relative in paths.items():
        if (not isinstance(key, str) or not key or not isinstance(relative, str)
                or not relative or Path(relative).is_absolute()):
            raise ValueError('startup_code_context_contract_path_invalid')
        path = Path(root) / relative
        if not path.resolve(strict=True).is_relative_to(root):
            raise ValueError('startup_code_context_contract_path_escape')
        _bound_source(sources, path)
        values[key] = _sha(path)
    return _digest(values)


def _origin(proof, request):
    origin = proof.get('origin')
    if not isinstance(origin, dict):
        raise ValueError('startup_code_context_origin_required')
    sources = origin.get('sources')
    _check_sources(sources)
    if any(proof['source_hashes'].get(name) != sha for name, sha in sources.items()):
        raise ValueError('startup_code_context_origin_not_bound')
    selected = Path(origin.get('selected_release_root') or '')
    commit = origin.get('selected_release_commit')
    if (not selected.is_absolute() or str(selected.resolve(strict=True)) != str(selected)
            or not _hex(commit, 40) or _git_head(selected) != commit
            or not _hex(origin.get('origin_commit'), 40)
            or origin.get('original_code_sha256') != proof['original_code_sha256']):
        raise ValueError('startup_code_context_origin_identity_invalid')
    selected_paths = origin.get('selected_paths', proof['paths'])
    if (not isinstance(selected_paths, dict) or not selected_paths
            or any(proof['paths'].get(key) != name for key, name in selected_paths.items())):
        raise ValueError('startup_code_context_selected_inventory_invalid')
    selected_code = _contract(selected, selected_paths, sources)
    if selected_code != origin.get('selected_runtime_code_sha256'):
        raise ValueError('startup_code_context_selected_contract_changed')
    selector = Path(request['data_root']) / 'runtime/runtime_release_selection.json'
    _bound_source(sources, selector)
    selection = _json(selector)
    if (selection.get('schema') != 'runtime_release_selection_v1'
            or selection.get('release_root') != str(selected) or selection.get('git_commit') != commit):
        raise ValueError('startup_code_context_selected_identity_changed')
    basis = origin.get('basis')
    if basis == 'selected_exact_code_contract':
        if selected_code != proof['original_code_sha256'] or origin['origin_commit'] != commit:
            raise ValueError('startup_code_context_exact_origin_invalid')
    elif basis == 'verified_selected_prepared_code_handoff':
        path = Path(origin.get('code_handoff_receipt_path') or '')
        _bound_source(sources, path)
        receipt = _json(path)
        if (_sha(path) != origin.get('code_handoff_receipt_sha256')
                or receipt.get('schema') != 'prepared_policy_code_handoff_v1'
                or receipt.get('authority') != 'APPROVED_PREPARED_POLICY_PRESERVING_CODE_HANDOFF'
                or receipt.get('receipt_sha256') != _digest({k: v for k, v in receipt.items() if k != 'receipt_sha256'})
                or receipt.get('family') != proof['family'] or receipt.get('target_date') != proof['target_date']
                or receipt.get('policy_sha256') != proof['policy_sha256']
                or receipt.get('original_code_sha256') != proof['original_code_sha256']
                or receipt.get('runtime_code_sha256') != selected_code
                or receipt.get('paths') != selected_paths or receipt.get('release_root') != str(selected)
                or receipt.get('release_commit') != commit or receipt.get('origin_commit') != origin['origin_commit']
                or receipt.get('policy_effect') != 'unchanged'
                or any(receipt.get(k) is not False for k in ('actual_pid_consumed', 'policy_published', 'provider_called', 'broker_called'))):
            raise ValueError('startup_code_context_native_handoff_invalid')
        native_sources = receipt.get('sources')
        _check_sources(native_sources)
        if any(sources.get(name) != sha for name, sha in native_sources.items()):
            raise ValueError('startup_code_context_native_handoff_sources_not_bound')
    else:
        raise ValueError('startup_code_context_origin_basis_invalid')


def _proof(proof, family, request):
    if (family not in _FAMILIES or not isinstance(proof, dict)
            or proof.get('schema') != PROOF_SCHEMA or proof.get('status') != 'verified'
            or proof.get('target_date') != request['target_date'] or proof.get('family') != family
            or proof.get('execution_release_root') != request['execution_release_root']
            or proof.get('execution_release_commit') != request['execution_release_commit']
            or proof.get('policy_effect') != 'unchanged'
            or any(proof.get(key, False) is not False for key in ('runtime_effect', 'actual_pid_consumed', 'execution_authority', 'allowed_runtime_apply'))
            or not all(_hex(proof.get(key)) for key in ('policy_sha256', 'original_code_sha256', 'runtime_code_contract_sha256'))):
        raise ValueError('startup_code_context_handoff_invalid')
    field, key = _FAMILIES[family]
    bound = (request.get('manifest') or {}).get(field) or {}
    if bound.get('target_date') != request['target_date'] or bound.get(key) != proof['policy_sha256']:
        raise ValueError('startup_code_context_policy_binding_invalid')
    sources = proof.get('source_hashes')
    _check_sources(sources)
    if any(request['source_hashes'].get(name) != sha for name, sha in sources.items()):
        raise ValueError('startup_code_context_handoff_sources_not_bound')
    if _contract(ROOT, proof.get('paths'), sources) != proof['runtime_code_contract_sha256']:
        raise ValueError('startup_code_context_runtime_contract_changed')
    _origin(proof, request)


def _isolation(request):
    from src.engine.infrastructure.startup_validation_isolation import assert_no_forbidden_attempts
    checked = assert_no_forbidden_attempts()
    capabilities = checked.get('capabilities') or {}
    run = Path(request.get('run_directory') or '')
    if (checked.get('passed') is not True or checked.get('forbidden_attempt_count') != 0
            or not run.is_absolute() or str(run.resolve(strict=True)) != str(run)
            or capabilities.get('schema') != 'main_startup_validation_isolation_v1'
            or capabilities.get('filesystem_write_root') != str(run)
            or capabilities.get('process_group') != os.getpid() or capabilities.get('session_id') != os.getpid()
            or os.getpgrp() != os.getpid() or os.getsid(0) != os.getpid()
            or capabilities.get('landlock_abi', 0) < 3 or capabilities.get('no_new_privileges') is not True
            or any(capabilities.get(key) is not False for key in ('network_access', 'process_creation', 'metadata_changes', 'operational_file_locks'))):
        raise ValueError('startup_code_context_real_isolation_required')
    return run


def install_validation_code_context(request: dict) -> None:
    """Install once, only after the actual mandatory OS boundary is active."""
    global _CONTEXT
    from src.engine.infrastructure.startup_validation_isolation import assert_no_forbidden_attempts
    assert_no_forbidden_attempts()  # Outside isolation leaves the live lookup untouched.
    if _CONTEXT is not None:
        _CONTEXT = {'valid': False}
        raise ValueError('startup_code_context_already_installed')
    _CONTEXT = {'valid': False}
    run = _isolation(request)
    request = json.loads(json.dumps(request, allow_nan=False))
    if (request.get('schema') != REQUEST_SCHEMA or not _hex(request.get('run_id'), 32)
            or run.name != request['run_id'] or request.get('execution_release_root') != str(ROOT)
            or not _hex(request.get('execution_release_commit'), 40)
            or _git_head(ROOT) != request['execution_release_commit']
            or date.fromisoformat(request['target_date']).isoformat() != request['target_date']
            or request.get('request_sha256') != _digest({k: v for k, v in request.items() if k != 'request_sha256'})
            or any(request.get(key, False) is not False for key in ('runtime_effect', 'actual_pid_consumed', 'allowed_runtime_apply'))):
        raise ValueError('startup_code_context_request_invalid')
    request_path = run / 'request.json'
    if _json(request_path) != request:
        raise ValueError('startup_code_context_request_file_changed')
    sources = request.get('source_hashes')
    _check_sources(sources, absent_allowed=True)
    _bound_source(sources, Path(__file__))
    proofs = request.get('candidate_code_handoffs')
    if not isinstance(proofs, dict) or not proofs:
        raise ValueError('startup_code_context_handoffs_required')
    for family, proof in proofs.items():
        _proof(proof, family, request)
    _isolation(request)
    _CONTEXT = dict(valid=True, pid=os.getpid(), start_ticks=_read('/proc/self/stat', maximum=65536).decode().rsplit(')', 1)[1].split()[19],
                    request=request, request_path=str(request_path), request_sha256=_sha(request_path))


def verify_validation_consumer_code(day, *, family, policy_sha, expected, paths, actual):
    """Return None outside this context; never soften the ordinary live guard."""
    global _CONTEXT
    if _CONTEXT is None:
        return None
    context = _CONTEXT
    try:
        if context.get('valid') is not True:
            raise ValueError('startup_code_context_invalid')
        request = context['request']
        _isolation(request)
        if (os.getpid() != context['pid'] or _git_head(ROOT) != request['execution_release_commit']
                or _read('/proc/self/stat', maximum=65536).decode().rsplit(')', 1)[1].split()[19] != context['start_ticks']
                or _sha(context['request_path']) != context['request_sha256']
                or _json(context['request_path']) != request):
            raise ValueError('startup_code_context_execution_changed')
        proof = request['candidate_code_handoffs'].get(family)
        if (not isinstance(proof, dict) or day != request['target_date']
                or policy_sha != proof['policy_sha256'] or expected != proof['original_code_sha256']
                or actual != proof['runtime_code_contract_sha256'] or paths != proof['paths']):
            raise ValueError('startup_code_context_consumer_binding_invalid')
        _check_sources(request['source_hashes'], absent_allowed=True)
        _proof(proof, family, request)
        return dict(status='verified_intraday_consumer_repair', verification_basis=SCHEMA,
            basis=SCHEMA, target_date=day, policy_sha256=policy_sha,
            code_contract_sha256=expected, runtime_code_contract_sha256=actual,
            origin_commit=proof['origin']['origin_commit'], policy_effect='unchanged',
            actual_pid_consumed=False, execution_authority=False)
    except (OSError, ValueError, TypeError, KeyError):
        _CONTEXT = {'valid': False}
        raise
