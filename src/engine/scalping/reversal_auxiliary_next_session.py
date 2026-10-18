"""Carry an immutable input-research proof to an unchanged future scope.

Research keeps its original parent, requests and labels. This owner prepares
only the auxiliary day pointer; PREOPEN still owns machine activation.
"""
from __future__ import annotations

import copy
import fcntl
import json
import os
import stat
import subprocess
from contextlib import ExitStack
from datetime import date, datetime, time, timedelta
from pathlib import Path

from src.engine.ai import offline_comparison_store as S
from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.scalping import mechanistic_entry_runtime_policy as N
from src.engine.scalping import reversal_auxiliary_input_transition as J
from src.engine.scalping import reversal_auxiliary_intraday as I
from src.engine.scalping import reversal_auxiliary_registry as G
from src.engine.scalping import reversal_auxiliary_wire as W

SCHEMA = 'auxiliary_next_session_input_transition_v1'
FROZEN_COMMIT = '108c75f91d3f8567707319454914130972412260'
_VERIFIED = {}


def _require(ok, reason):
    if not ok:
        raise ValueError('auxiliary_next_session_' + reason)


def _reference(path):
    from src.engine.scalping import reversal_auxiliary_transition as X
    return X.reference(path)


def _read_reference(ref):
    _require(isinstance(ref, dict) and set(ref) == {'path', 'sha256'}, 'reference_invalid')
    _require(P.file_hash(ref['path']) == ref['sha256'], 'source_changed:' + ref['path'])
    return N._read(Path(ref['path']))


def _source_path(root, name):
    return Path(root) / ('src/engine/' + name if name == 'ai_engine_openai.py'
                         else 'src/engine/scalping/' + name)


def _hash(path):
    path = Path(path)
    return N._source_hash(str(path), N._signature(path))


def _code_hashes():
    from src.engine.scalping import reversal_auxiliary_transition as X
    paths = [Path(__file__), Path(X.__file__)]
    return {path.name: _hash(path) for path in paths}


def _frozen_inventory(root):
    """Require an immutable managed release and pin its complete Python source."""
    from src.engine.infrastructure import runtime_release_router as router
    root = Path(root).resolve()
    identity = router._release_identity(root.parent.parent / 'KORStockScan',
        str(root / 'src'), 'auxiliary_next_session_frozen_validator', FROZEN_COMMIT)
    _require(identity['source_integrity'] == 'git_commit_and_clean_runtime_source'
             and identity['git_commit'] == FROZEN_COMMIT, 'frozen_validator_unattested')
    names = subprocess.check_output(['git', '-C', str(root), 'ls-files', 'src'], text=True).splitlines()
    paths = [root / name for name in names if name.endswith('.py')]
    _require(paths and all(path.is_file() for path in paths), 'frozen_inventory_invalid')
    return {str(path): _hash(path) for path in paths}


def _semantic_code_parity(source, frozen_root, validation_proof=None):
    """The reviewed dispatcher is the sole changed research-reader surface."""
    current_root = Path(__file__).resolve().parents[3]
    pins = dict(source['input_transition_code_hashes'])
    pins.update(source['reader_code_hashes'])
    result = {}
    for name, expected in sorted(pins.items()):
        original = _source_path(frozen_root, name)
        _require(_hash(original) == expected, 'frozen_semantic_code_changed:' + name)
        if name == 'reversal_auxiliary_transition.py':
            continue
        current = _source_path(current_root, name)
        actual = _hash(current)
        _require(actual == expected or _validation_code_pair(current, expected, actual, validation_proof),
                 'current_semantic_code_changed:' + name)
        result[name] = expected
    return result


def _code_reference(root, name, digest):
    path = Path(root) / ('src/engine/scalping/' + name)
    if name == 'ai_engine_openai.py':
        path = Path(root) / 'src/engine' / name
    _require(_hash(path) == digest, 'historical_code_origin_changed:' + name)
    return dict(path=str(path.resolve()), sha256=digest)


def _canonical_baseline_sources(refs, paths, origin, validation_proof=None):
    """Preserve historical paths when identical code moves to a new release."""
    current = Path(__file__).resolve().parents[3]
    def canonical(path):
        path = Path(path)
        if path.is_relative_to(current / 'src'):
            historical = Path(origin) / path.relative_to(current)
            old, actual = _hash(historical), _hash(path)
            _require(old == actual or _validation_code_pair(path, old, actual, validation_proof),
                     'historical_reader_origin_changed')
            return str(historical)
        return str(path)
    return ([dict(path=canonical(ref['path']), sha256=(
                _hash(canonical(ref['path'])) if validation_proof and Path(ref['path']).is_relative_to(current / 'src')
                else ref['sha256'])) for ref in refs],
            sorted(set(canonical(path) for path in paths)))


def _validation_code_pair(path, expected, actual, proof):
    if proof is None:
        return False
    root = Path(__file__).resolve().parents[3]
    path = Path(path)
    if not path.resolve(strict=True).is_relative_to(root / 'src'):
        return False
    relative = str(path.resolve().relative_to(root))
    return (proof['original_code_hashes'].get(relative) == expected
            and proof['runtime_code_hashes'].get(relative) == actual)


def _validation_code_inventory(expected, actual, proof):
    if expected == actual:
        return True
    if proof is None or not isinstance(expected, dict) or set(expected) != set(actual):
        return False
    root = Path(__file__).resolve().parents[3]
    return all(old == actual[name] or _validation_code_pair(_source_path(root, name), old, actual[name], proof)
               for name, old in expected.items())


_FROZEN_SCRIPT = r'''
import json, socket, sys
from pathlib import Path
def denied(*args, **kwargs):
    raise RuntimeError('network_forbidden_in_frozen_auxiliary_validator')
def audit(event, args):
    if event.startswith('socket.') and event not in {'socket.__new__'}:
        denied()
sys.addaudithook(audit)
for name in ('create_connection', 'getaddrinfo'):
    setattr(socket, name, denied)
for name in ('connect', 'connect_ex', 'send', 'sendall', 'sendto', 'sendmsg'):
    if hasattr(socket.socket, name): setattr(socket.socket, name, denied)
from src.engine.scalping import reversal_auxiliary_input_transition as J
from src.engine.scalping import reversal_auxiliary_intraday as I
from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.scalping import mechanistic_entry_runtime_policy as N
from src.engine.scalping import reversal_auxiliary_registry as G
P.write = N._atomic_write_json = G.register = denied
source = I.read(sys.argv[1])
bundle = N._read(Path(sys.argv[2]))
N.validate(bundle, target_date=bundle['target_date'])
J.validate_manifest(source['policy_data_root'], source, bundle)
print(json.dumps(dict(schema='frozen_auxiliary_input_validation_v1',
    source_manifest_sha256=source['artifact_content_sha256'],
    source_bundle_sha256=bundle['bundle_sha256'], verified_pairs=source['verified_pairs'],
    verified_raw_responses=source['verified_raw_responses'],
    input_transition_code_hashes=J.code_hashes(), network_forbidden=True,
    provider_called=False, policy_published=False)))
'''


def _verify_frozen(root, manifest_path, bundle_path):
    try:
        result = subprocess.run([str(Path(root) / '.venv/bin/python'), '-B', '-c', _FROZEN_SCRIPT,
            str(manifest_path), str(bundle_path)], cwd=root,
            env={**os.environ, 'PYTHONPATH': str(root), 'PYTHONDONTWRITEBYTECODE': '1'},
            capture_output=True, text=True, timeout=180, check=True)
        return json.loads(result.stdout.strip().splitlines()[-1])
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError, ValueError, IndexError) as exc:
        raise ValueError('auxiliary_next_session_frozen_validation_failed') from exc


def _scope_behavior(bundle, sid):
    family = bundle['continuous_reversal']; key, route = sid.rsplit('|', 1)
    cell = family['machine_cells'][key]['routes'][route]
    ids = family['operating_manifest']['scopes'][sid]
    return dict(backend=cell['backend'], payload=cell['payload'],
        payload_sha256=cell['payload_sha256'], branch_ids=ids,
        definitions={ident: family['operating_manifest']['definitions'][ident] for ident in ids},
        auxiliary_payload=family['auxiliary_cells'][key]['routes'][route]['payload'])


def _bindings(data_root, bundle):
    # Deliberately ignore the new target overlay: validate its immutable parent.
    return J._baseline(data_root, bundle, None)


def _file_state(path):
    path = Path(path)
    if not path.exists() and not path.is_symlink():
        return dict(path=str(path.resolve()), sha256=None)
    _require(path.is_file() and not path.is_symlink(), 'regular_cas_source_required')
    return _reference(path)


def _publication_cas(data_root, bundle, prepared_path):
    root = N.root(Path(data_root)); day = bundle['target_date']
    paths = [Path(data_root) / 'runtime/runtime_release_selection.json', root / 'current.json',
        I.root(data_root) / 'current.json',
        root / 'candidates' / ('policy_' + day + '.json'),
        Path(data_root) / 'runtime/policy_bootstrap/prepared' / day / 'latest.json',
        I.root(data_root) / 'days' / day / (bundle['bundle_sha256'] + '.json')]
    result = {str(path): _file_state(path) for path in paths}
    prepared = N._read(Path(prepared_path))
    _require(prepared.get('schema') == 'next_preopen_readiness_v1'
        and prepared.get('status') == 'prepared_verified' and prepared.get('target_date') == day
        and prepared.get('source_date') == bundle['source_date']
        and prepared.get('selected_release_commit') == bundle['continuous_reversal']['release_commit']
        and prepared.get('activation_candidate', {}).get('bundle_sha256') == bundle['bundle_sha256'],
        'prepared_contract_invalid')
    return result


def prepare(data_root, *, source_manifest_path, source_bundle_path, frozen_root,
            target_bundle_path, prepared_path, code_origin_root=None, _validation_manifest=None,
            source_code_handoff_path=None):
    """Return a sealed proof without writing policies, reports or registries."""
    data_root = Path(data_root).resolve(); frozen_root = Path(frozen_root).resolve()
    source_manifest_path = Path(source_manifest_path).resolve()
    source_bundle_path = Path(source_bundle_path).resolve()
    target_bundle_path = Path(target_bundle_path).resolve()
    code_origin_root = Path(code_origin_root or Path(__file__).resolve().parents[3]).resolve()
    source = I.read(source_manifest_path); original = N._read(source_bundle_path)
    bundle = N._read(target_bundle_path); day = bundle['target_date']
    source_code_handoff = None
    source_code_reference = None
    if source_code_handoff_path is not None:
        from src.engine.scalping import reversal_auxiliary_source_handoff as H
        source_code_reference = _reference(Path(source_code_handoff_path).resolve(strict=True))
        source_code_handoff = H.validate(data_root, _read_reference(source_code_reference),
            source_manifest_path=source_manifest_path, source_bundle_path=source_bundle_path,
            target_bundle_path=target_bundle_path, frozen_root=frozen_root)
        source_code_reference['artifact_content_sha256'] = source_code_handoff['artifact_content_sha256']
    validation_proof = None
    if _validation_manifest is not None:
        from src.engine.infrastructure.startup_validation_code_context import validation_auxiliary_preparation
        validation_proof = validation_auxiliary_preparation(_validation_manifest, bundle, data_root)
        _require(validation_proof is not None
            and _validation_manifest['source_manifest']['path'] == str(source_manifest_path)
            and _validation_manifest['source_bundle']['path'] == str(source_bundle_path)
            and _validation_manifest['target_bundle']['path'] == str(target_bundle_path)
            and _validation_manifest['prepared_reference']['path'] == str(Path(prepared_path).resolve())
            and _validation_manifest['frozen_validator_root'] == str(frozen_root)
            and _validation_manifest['code_origin_root'] == str(code_origin_root),
            'validation_delegation_arguments_changed')
        _require(_validation_manifest.get('source_code_handoff') == source_code_reference,
                 'validation_source_handoff_changed')
    N.validate(original, target_date=original['target_date']); N.validate(bundle, target_date=day)
    _require(source.get('schema') == J.SCHEMA and source.get('status') == 'prepared'
        and source['base_bundle_sha256'] == original['bundle_sha256']
        and source['bundle_target_date'] == original['target_date']
        and original['target_date'] < day and bundle['source_date'] >= original['target_date']
        and bundle['continuous_reversal'].get('effective_mode') == 'next_session'
        and source['verified_pairs'] == 50 and source['verified_raw_responses'] == 100,
        'source_or_target_invalid')
    selected = sorted(source['changes'])
    _require(selected == ['034020|PRE|20000_TO_100000|NXT', '196170|PRE|GE_100000|NXT'],
             'approved_scopes_required')
    _require(target_bundle_path == N.root(data_root) / 'generations' / (bundle['bundle_sha256'] + '.json'),
             'immutable_target_generation_required')
    inventory = (_frozen_inventory(frozen_root) if validation_proof is None
                 else validation_proof['frozen_inventory'])
    code_proof = source_code_handoff or validation_proof
    semantic = _semantic_code_parity(source, frozen_root, code_proof)
    frozen = (_verify_frozen(frozen_root, source_manifest_path, source_bundle_path) if validation_proof is None
              else validation_proof['frozen_validation'])
    _require(frozen == dict(schema='frozen_auxiliary_input_validation_v1',
        source_manifest_sha256=source['artifact_content_sha256'], source_bundle_sha256=original['bundle_sha256'],
        verified_pairs=50, verified_raw_responses=100, input_transition_code_hashes=source['input_transition_code_hashes'],
        network_forbidden=True, provider_called=False, policy_published=False), 'frozen_validation_invalid')
    bindings, baseline_sources, baseline_paths = _bindings(data_root, bundle)
    baseline_sources, baseline_paths = _canonical_baseline_sources(baseline_sources, baseline_paths, code_origin_root, code_proof)
    _require(len(bindings) == 128 and bindings == source['base_bindings'], 'baseline_changed')
    behaviors = {}
    for sid in selected:
        before = _scope_behavior(original, sid); after = _scope_behavior(bundle, sid)
        _require(before == after, 'scope_behavior_changed:' + sid)
        _require(bindings[sid] == source['rollback_bindings'][sid], 'incumbent_changed:' + sid)
        behaviors[sid] = dict(source=before, target=after)
    refs = [_reference(source_manifest_path), _reference(source_bundle_path),
            _reference(target_bundle_path), _reference(prepared_path)] + source['sources'] + baseline_sources
    for path, digest in inventory.items():
        refs.append(dict(path=path, sha256=digest))
    next_code = (_code_hashes() if validation_proof is None else _validation_manifest['next_session_code_hashes'])
    _require(_validation_code_inventory(next_code, _code_hashes(), validation_proof), 'next_session_code_changed')
    refs.extend(_code_reference(frozen_root if source_code_handoff else code_origin_root, name, digest)
                for name, digest in semantic.items())
    refs.extend(_code_reference(code_origin_root, name, digest) for name, digest in next_code.items())
    if source_code_handoff is not None:
        refs.append({k: source_code_reference[k] for k in ('path', 'sha256')})
        refs.extend(dict(path=path, sha256=digest) for path, digest in source_code_handoff['source_hashes'].items())
    sources = {ref['path']: ref for ref in refs}
    _require(len(sources) > 0, 'sources_missing')
    return P.seal(dict(schema=SCHEMA, status='prepared', policy_data_root=str(data_root),
        base_bundle_sha256=bundle['bundle_sha256'], bundle_target_date=day, operating_day=day,
        source_manifest=_reference(source_manifest_path), source_bundle=_reference(source_bundle_path),
        target_bundle=_reference(target_bundle_path), prepared_reference=_reference(prepared_path),
        frozen_validator_root=str(frozen_root), frozen_validator_commit=FROZEN_COMMIT,
        code_origin_root=str(code_origin_root),
        frozen_inventory=inventory, frozen_validation=frozen, semantic_code_hashes=semantic,
        next_session_code_hashes=next_code, reader_code_hashes=I.code_hashes(), wire_contract=W.contract(),
        base_bindings=bindings, base_bindings_sha256=P.digest(bindings), expected_parent=None,
        changes=copy.deepcopy(source['changes']), rollback_bindings=copy.deepcopy(source['rollback_bindings']),
        registry_definitions=copy.deepcopy(source['registry_definitions']), scopes=copy.deepcopy(source['scopes']),
        scope_behavior=behaviors, baseline_dependency_paths=baseline_paths,
        ledger_data_root=source['ledger_data_root'], ledger_pack_paths=source['ledger_pack_paths'],
        ledger_metadata=copy.deepcopy(source['ledger_metadata']),
        publication_cas=_publication_cas(data_root, bundle, prepared_path),
        sources=[sources[path] for path in sorted(sources)], verified_pairs=50, verified_raw_responses=100,
        **({'source_code_handoff': source_code_reference} if source_code_reference is not None else {}),
        source_labels_rewritten=False, new_provider_calls=0, policy_published=False,
        actual_pid_consumed=False, actual_order_submitted=False))


def _dependencies(manifest):
    paths = {ref['path'] for ref in manifest['sources']}
    paths.update(manifest['ledger_pack_paths']); paths.update(manifest['baseline_dependency_paths'])
    return [(path, N._signature(Path(path))) for path in sorted(paths)]


def _database_signature(manifest):
    database, wal = J._database_signature(manifest)
    # A read-only SQLite connection can create a zero-byte WAL. It contains
    # no frames and is equivalent to its absence; nonempty WALs remain pinned.
    return database, None if wal is not None and wal[3] == 0 else wal


def validate_manifest(data_root, manifest, bundle, *, cached_only=False):
    from src.engine.infrastructure.startup_validation_code_context import validation_auxiliary_preparation
    delegation = validation_auxiliary_preparation(manifest, bundle, data_root)
    _require(manifest.get('schema') == SCHEMA and manifest.get('status') == 'prepared'
        and manifest.get('artifact_content_sha256') == P.seal(manifest)['artifact_content_sha256']
        and manifest.get('policy_data_root') == str(Path(data_root).resolve())
        and manifest.get('base_bundle_sha256') == bundle['bundle_sha256']
        and manifest.get('bundle_target_date') == bundle['target_date']
        and _validation_code_inventory(manifest.get('next_session_code_hashes'), _code_hashes(), delegation)
        and manifest.get('reader_code_hashes') == I.code_hashes()
        and manifest.get('wire_contract') == W.contract(), 'manifest_invalid')
    key = (str(Path(data_root).resolve()), manifest['artifact_content_sha256'], bundle['bundle_sha256'])
    dependencies = _dependencies(manifest); database = _database_signature(manifest)
    cached = _VERIFIED.get(key)
    if cached and cached['dependencies'] == dependencies:
        if cached['database'] == database:
            return manifest
        _require(not cached_only, 'verification_cache_changed_before_publish')
        before = _database_signature(manifest)
        with S.Store(manifest['ledger_data_root'], readonly=True) as store:
            store.db.execute('BEGIN')
            fingerprint = J._ledger_fingerprint(store, manifest['ledger_metadata'])
        after = _database_signature(manifest)
        _require(fingerprint == manifest['ledger_metadata']['fingerprint_sha256'], 'selected_ledger_metadata_changed')
        _require(_dependencies(manifest) == dependencies, 'dependency_changed_during_validation')
        if before == after:
            _VERIFIED[key] = dict(dependencies=dependencies, database=after)
        return manifest
    _require(not cached_only, 'verification_cache_changed_before_publish')
    for ref in manifest['sources']:
        _require(_hash(ref['path']) == ref['sha256'], 'source_changed:' + ref['path'])
    rebuilt = prepare(data_root, source_manifest_path=manifest['source_manifest']['path'],
        source_bundle_path=manifest['source_bundle']['path'], frozen_root=manifest['frozen_validator_root'],
        target_bundle_path=manifest['target_bundle']['path'], prepared_path=manifest['prepared_reference']['path'],
        code_origin_root=manifest['code_origin_root'],
        **({'_validation_manifest': manifest} if delegation is not None else {}),
        **({'source_code_handoff_path': manifest['source_code_handoff']['path']}
           if manifest.get('source_code_handoff') is not None else {}))
    # Mutable publication selectors are consumed only by the future publisher.
    # Monday's normal PREOPEN activation must not invalidate the research proof.
    rebuilt['publication_cas'] = manifest['publication_cas']
    rebuilt = P.seal(rebuilt)
    _require(rebuilt == manifest, 'evidence_changed')
    _require(_dependencies(manifest) == dependencies, 'dependency_changed_during_validation')
    after = _database_signature(manifest)
    if len(_VERIFIED) >= 64:
        _VERIFIED.clear()
    _VERIFIED[key] = dict(dependencies=dependencies, database=database if database == after else None)
    return manifest


def _next_trading_day(day):
    from src.utils.market_day import is_krx_trading_day
    for delta in range(1, 15):
        candidate = day + timedelta(days=delta)
        if is_krx_trading_day(candidate):
            return candidate.isoformat()
    raise ValueError('auxiliary_next_session_trading_calendar_unavailable')


def _record_behavior(manifest, record):
    expected = dict(manifest['base_bindings']); expected.update(manifest['changes'])
    effective = datetime.combine(date.fromisoformat(manifest['operating_day']), time.min, I.K.KST).isoformat()
    _require(record.get('bindings') == expected and record.get('changes') == manifest['changes']
        and record.get('rollback_bindings') == manifest['rollback_bindings']
        and record.get('previous_overlay_sha256') is None
        and record.get('effective_mode') == 'next_session'
        and record.get('effective_from') == effective
        and record.get('revoked_overlays') == [] and record.get('revoked_scope_overlays') == {}
        and record.get('transition_manifest_sha256') == manifest['artifact_content_sha256']
        and not record.get('rollback_reason'), 'existing_target_overlay_behavior_changed')


def validate_published(data_root, record, bundle, *, manifest=None):
    """Preserve exact authorized bindings; later native rollbacks keep lineage."""
    if manifest is None:
        from src.engine.scalping import reversal_auxiliary_transition as X
        manifest = I.read(X.folder(data_root) / (record['transition_manifest_sha256'] + '.json'))
    validate_manifest(data_root, manifest, bundle)
    if not record.get('rollback_reason'):
        _record_behavior(manifest, record)
    return manifest


def _future_guard(data_root, manifest, bundle, *, committed=None):
    from src.engine.automation import ordered_intraday_deploy as ordered
    from src.engine.infrastructure import runtime_release_router as router
    root = Path(data_root).resolve(); workspace = root.parent
    current = datetime.now(I.K.KST); day = manifest['operating_day']
    _require(day > current.date().isoformat()
        and _next_trading_day(date.fromisoformat(bundle['source_date'])) == day, 'future_target_required')
    selected_root, selected_commit = router.selected_release(workspace)
    _require(selected_root == Path(__file__).resolve().parents[3]
        and bundle['continuous_reversal']['release_commit'] == selected_commit, 'selected_release_changed')
    selection = N._read(root / 'runtime/runtime_release_selection.json')
    _require(selection.get('approved_by') == 'user' and selection.get('actual_pid_consumed') is False
        and not selection.get('deployment_transition') and not selection.get('actual_pid_receipt'), 'stopped_selection_required')
    _require(not ordered._main_pids() and ordered._session_absent(), 'main_or_supervisor_running')
    _require(not (workspace / 'restart.flag').exists(), 'startup_requested')
    status = root / 'report/threshold_cycle_preopen_status' / ('threshold_cycle_preopen_' + day + '.status.json')
    live = root / 'runtime/policy_bootstrap'
    _require(not status.exists() and not status.is_symlink()
        and all(not p.exists() and not p.is_symlink() for p in
            [live / ('runtime_policy_bootstrap_' + day + '.json'),
             live / ('runtime_policy_bootstrap_' + day + '.env'),
             live / ('runtime_policy_bootstrap_verify_' + day + '.json')]), 'preopen_already_attempted')
    for path, ref in manifest['publication_cas'].items():
        if committed is not None and Path(path) == I.root(root) / 'days' / day / (bundle['bundle_sha256'] + '.json'):
            _require(I.read(path) == committed, 'committed_pointer_changed')
            continue
        _require(_file_state(path) == ref, 'publication_cas_changed:' + path)
    candidate = N._read(N.root(root) / 'candidates' / ('policy_' + day + '.json'))
    pointer = N._read(N.root(root) / 'current.json')
    _require(candidate == bundle and candidate['continuous_reversal']['parent_bundle_sha256'] == pointer['bundle_sha256'],
             'candidate_or_parent_changed')
    return current


def publish_future(data_root, manifest, *, confirm, reason):
    """Publish only a future day pointer after exact stopped-state CAS."""
    from src.engine.infrastructure import runtime_release_router as router
    from src.engine.scalping import reversal_auxiliary_transition as X
    _require(confirm == I.AUTHORITY and bool(str(reason).strip()), 'authority_required')
    data_root = Path(data_root).resolve(); bundle = _read_reference(manifest['target_bundle'])
    validate_manifest(data_root, manifest, bundle)
    day_path = I.root(data_root) / 'days' / manifest['operating_day'] / (bundle['bundle_sha256'] + '.json')
    existing = I.read(day_path) if day_path.exists() else None
    if existing is not None:
        _require(existing.get('transition_manifest_sha256') == manifest['artifact_content_sha256'],
                 'existing_target_overlay_conflict')
        _record_behavior(manifest, existing)
        I.validate_record(data_root, existing, bundle)
    _future_guard(data_root, manifest, bundle, committed=existing)
    with router.runtime_release_set_lock(data_root.parent), ExitStack() as locks:
        held = []
        def verify_locks():
            for path, identity, handle in held:
                current = path.lstat(); opened = os.fstat(handle.fileno())
                _require(stat.S_ISREG(current.st_mode)
                    and (current.st_dev, current.st_ino) == identity
                    and (opened.st_dev, opened.st_ino) == identity, 'publisher_lock_replaced')
        for path in [data_root.parent / 'logs/runtime_policy_preopen.lock',
                     I.root(data_root) / 'publisher.lock', N.root(data_root) / 'publisher.lock']:
            path.parent.mkdir(parents=True, exist_ok=True)
            before = path.lstat() if path.exists() or path.is_symlink() else None
            handle = locks.enter_context(os.fdopen(os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o666), 'a'))
            opened = os.fstat(handle.fileno()); identity = opened.st_dev, opened.st_ino
            _require(stat.S_ISREG(opened.st_mode) and (before is None
                or stat.S_ISREG(before.st_mode) and (before.st_dev, before.st_ino) == identity), 'publisher_lock_replaced')
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            held.append((path, identity, handle)); verify_locks()
        validate_manifest(data_root, manifest, bundle, cached_only=True)
        clock = _future_guard(data_root, manifest, bundle, committed=existing)
        if existing is not None:
            return existing
        bindings = dict(manifest['base_bindings']); bindings.update(manifest['changes'])
        body = P.seal(dict(schema=I.SCHEMA, authority=confirm, day=manifest['operating_day'],
            effective_from=datetime.combine(date.fromisoformat(manifest['operating_day']), time.min, I.K.KST).isoformat(),
            prepared_at_kst=clock.isoformat(), effective_mode='next_session', reason=reason,
            base_bundle_sha256=bundle['bundle_sha256'], base_family_sha256=bundle['continuous_reversal']['family_sha256'],
            detector_manifest_hash=bundle['continuous_reversal']['operating_manifest']['detector_manifest_hash'],
            previous_overlay_sha256=None, bindings=bindings, changes=manifest['changes'],
            independent_scopes=sorted(I.independent_scopes(data_root, bundle) | set(manifest['changes'])),
            code_hashes=I.code_hashes(), transition_manifest_sha256=manifest['artifact_content_sha256'],
            rollback_bindings=manifest['rollback_bindings'], revoked_overlays=[], revoked_scope_overlays={},
            actual_pid_consumed=False, actual_order_submitted=False))
        destination = X.folder(data_root) / (manifest['artifact_content_sha256'] + '.json')
        if destination.exists():
            _require(I.read(destination) == manifest, 'immutable_manifest_conflict')
        else:
            N._atomic_write_json(destination, manifest)
        J.register_definitions(data_root, manifest)
        I.validate_record(data_root, body, bundle)
        generation = I.root(data_root) / 'generations' / (body['artifact_content_sha256'] + '.json')
        if generation.exists():
            _require(I.read(generation) == body, 'immutable_generation_conflict')
        else:
            N._atomic_write_json(generation, body)
        verify_locks()
        validate_manifest(data_root, manifest, bundle, cached_only=True)
        _future_guard(data_root, manifest, bundle)
        I.write_day_pointer(data_root, body)
        _require(I.current(data_root, bundle, day=manifest['operating_day']) == body, 'publication_readback_failed')
        return body
