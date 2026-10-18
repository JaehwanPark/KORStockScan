"""Immutable source-code carry for an already authorized auxiliary overlay.

This is a single same-day code carry from an existing approved manifest. A
manifest already carrying this receipt is not a new predecessor. Ordinary
postclose preparation does not call this optional owner.

This owner returns read-only evidence. Native next-session preparation still
validates the original frozen research, ledger and publication guards. No
startup-isolation context is opened and no policy, registry or pointer is saved.
"""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import subprocess

from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.scalping import mechanistic_entry_runtime_policy as N

SCHEMA = 'auxiliary_next_session_source_code_handoff_v1'
ROOT = Path(__file__).resolve().parents[3]
MAX_BYTES = 8 * 1024 * 1024
SCOPES = ('034020|PRE|20000_TO_100000|NXT', '196170|PRE|GE_100000|NXT')
AUTHORITY_FALSE = ('runtime_effect', 'allowed_runtime_apply', 'policy_published',
                   'actual_pid_consumed', 'actual_order_submitted', 'provider_called')


def _require(value, reason):
    if not value:
        raise ValueError('auxiliary_source_handoff_' + reason)


def _path(value):
    path = Path(value)
    _require(path.is_absolute() and '..' not in path.parts, 'absolute_path_required')
    _require(not any(p.is_symlink() for p in (path, *path.parents)), 'source_symlink')
    _require(path.is_file() and str(path.resolve(strict=True)) == str(path), 'regular_source_required')
    return path


def _sha(value):
    path = _path(value)
    return N._source_hash(str(path), N._signature(path))


def _read(value):
    path = _path(value)
    before = N._signature(path)
    _require(path.stat().st_size <= MAX_BYTES, 'source_size_limit')
    with path.open('rb') as stream:
        opened = os.fstat(stream.fileno())
        identity = lambda st: (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns)
        _require(identity(opened) == before[1:6], 'source_changed_during_read')
        raw = stream.read(MAX_BYTES + 1)
        _require(identity(os.fstat(stream.fileno())) == identity(opened), 'source_changed_during_read')
    _require(len(raw) <= MAX_BYTES and N._signature(path) == before, 'source_changed_during_read')
    result = json.loads(raw)
    _require(isinstance(result, dict), 'object_required')
    import hashlib
    return result, dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest())


def _reference(value):
    _require(isinstance(value, dict) and set(value) == {'path', 'sha256'}, 'reference_invalid')
    result, actual = _read(value['path'])
    _require(actual == value, 'reference_changed')
    return result, actual


def _sealed(value):
    _require(value.get('artifact_content_sha256') == P.seal(value)['artifact_content_sha256'], 'seal_invalid')


def _bundle(value):
    _require(value.get('bundle_sha256') == N.digest({k:v for k,v in value.items() if k != 'bundle_sha256'}),
             'bundle_seal_invalid')


def _code_path(root, name):
    _require(isinstance(name, str) and Path(name).name == name and name.endswith('.py'), 'code_name_invalid')
    return Path(root)/('src/engine/' if name == 'ai_engine_openai.py' else 'src/engine/scalping/')/name


def _git_identity(root, sources, *, check_git):
    from src.engine.infrastructure import startup_validation_code_context as C
    root = Path(root)
    commit = C._git_head(root)
    if check_git:
        status = subprocess.check_output(['git', '-C', str(root), 'status', '--porcelain',
            '--untracked-files=all', '--', 'src'], text=True, timeout=30)
        _require(not status.strip(), 'dirty_source_root')
        for path, expected in sources.items():
            relative = str(Path(path).relative_to(root))
            raw = subprocess.check_output(['git', '-C', str(root), 'show', commit+':'+relative], timeout=10)
            import hashlib
            _require(hashlib.sha256(raw).hexdigest() == expected, 'source_git_object_changed')
        _require(C._git_head(root) == commit, 'source_git_head_changed')
    return commit


def _git_references(root):
    """Pin the small files that determine HEAD, including worktree indirection."""
    from src.engine.infrastructure import startup_validation_code_context as C
    def small(path):
        return C._read(_path(path), maximum=4096).decode().strip()
    root = Path(root); metadata = root/'.git'; paths = []
    if metadata.is_file():
        paths.append(metadata)
        line = small(metadata)
        _require(line.startswith('gitdir: '), 'git_metadata_invalid')
        directory = (root/line[8:]).resolve(strict=True)
    else:
        directory = metadata
    head = directory/'HEAD'; paths.append(head)
    common = directory
    if (directory/'commondir').is_file():
        paths.append(directory/'commondir')
        common = (directory/small(directory/'commondir')).resolve(strict=True)
    value = small(head)
    if value.startswith('ref: '):
        _require(value[5:].startswith('refs/') and '..' not in Path(value[5:]).parts, 'git_ref_invalid')
        for parent in (directory, common):
            ref = parent/value[5:]
            if ref.is_file():
                paths.append(ref); break
        else:
            paths.append(common/'packed-refs')
    return {str(path):_sha(path) for path in paths}


def _inspect(data_root, previous_manifest_path, previous_overlay_path, *, check_git, execution_root=None):
    from src.engine.infrastructure import startup_validation_code_context as C
    from src.engine.scalping import reversal_auxiliary_next_session as A
    from src.engine.scalping import reversal_auxiliary_input_transition as J
    from src.engine.scalping import reversal_auxiliary_intraday as I
    from src.engine.scalping import reversal_auxiliary_registry as G
    execution_root = Path(execution_root or ROOT)
    data_root = Path(data_root).resolve(strict=True)
    previous, previous_ref = _read(previous_manifest_path)
    overlay, overlay_ref = _read(previous_overlay_path)
    _sealed(previous); _sealed(overlay)
    _require(previous.get('source_code_handoff') is None, 'successor_predecessor_unsupported')
    _require(previous.get('schema') == A.SCHEMA and previous.get('status') == 'prepared'
        and previous.get('policy_data_root') == str(data_root), 'previous_manifest_invalid')
    _require(previous_ref['path'] == str(I.root(data_root)/'transitions'/(previous['artifact_content_sha256']+'.json')),
             'immutable_previous_manifest_required')
    source, source_ref = _reference(previous['source_manifest'])
    original, original_ref = _reference(previous['source_bundle'])
    prior, prior_ref = _reference(previous['target_bundle'])
    _sealed(source); _bundle(original); _bundle(prior)
    _require(source.get('schema') == J.SCHEMA and source.get('status') == 'prepared'
        and source['base_bundle_sha256'] == original['bundle_sha256']
        and source['bundle_target_date'] == original['target_date']
        and source['verified_pairs'] == 50 and source['verified_raw_responses'] == 100
        and previous['base_bundle_sha256'] == prior['bundle_sha256']
        and previous['bundle_target_date'] == previous['operating_day'] == prior['target_date']
        and previous['verified_pairs'] == 50 and previous['verified_raw_responses'] == 100,
        'original_source_binding_invalid')
    _require(overlay.get('schema') == I.SCHEMA and overlay.get('authority') == I.AUTHORITY
        and overlay.get('base_bundle_sha256') == prior['bundle_sha256']
        and overlay.get('base_family_sha256') == prior['continuous_reversal']['family_sha256']
        and overlay.get('detector_manifest_hash') == prior['continuous_reversal']['operating_manifest']['detector_manifest_hash']
        and overlay.get('day') == prior['target_date'], 'previous_overlay_invalid')
    _require(overlay_ref['path'] in {str(I.root(data_root)/'days'/prior['target_date']/(prior['bundle_sha256']+'.json')),
                str(I.root(data_root)/'generations'/(overlay['artifact_content_sha256']+'.json'))},
             'previous_overlay_path_invalid')
    A._record_behavior(previous, overlay)
    fields = ('base_bindings', 'changes', 'rollback_bindings', 'registry_definitions', 'scopes')
    _require(all(previous[field] == source[field] for field in fields)
        and len(source['base_bindings']) == 128 and tuple(sorted(source['changes'])) == SCOPES
        and previous['base_bindings_sha256'] == P.digest(source['base_bindings'])
        and previous.get('source_labels_rewritten') is False
        and previous.get('new_provider_calls') == 0
        and previous.get('policy_published') is False
        and previous.get('actual_pid_consumed') is False
        and previous.get('actual_order_submitted') is False, 'scope_or_authority_changed')
    expected_bindings = dict(source['base_bindings']); expected_bindings.update(source['changes'])
    _require(overlay['bindings'] == expected_bindings and len(expected_bindings) == 128,
             'effective_bindings_changed')
    for ident, value in source['registry_definitions'].items():
        G.validate(value)
        _require(value['registry_sha256'] == ident, 'registry_definition_changed')
        _require(G.load(data_root, ident) == value, 'registered_definition_changed')
    for sid in SCOPES:
        behavior = A._scope_behavior(original, sid)
        _require(A._scope_behavior(prior, sid) == behavior
            and previous['scope_behavior'][sid] == dict(source=behavior, target=behavior)
            and source['rollback_bindings'][sid] == source['base_bindings'][sid]
            and source['scopes'][sid]['before'] == source['rollback_bindings'][sid]
            and source['scopes'][sid]['after'] == source['changes'][sid], 'scope_behavior_changed')
    origin = Path(previous['code_origin_root'])
    frozen = Path(previous['frozen_validator_root'])
    _require(previous['frozen_validator_commit'] == A.FROZEN_COMMIT
        and C._git_head(frozen) == A.FROZEN_COMMIT, 'frozen_root_changed')
    _require(set(source['input_transition_code_hashes']) == set(J.code_hashes())
        and set(source['reader_code_hashes']) == set(I.code_hashes()), 'source_code_membership_changed')
    pins = dict(source['input_transition_code_hashes']); pins.update(source['reader_code_hashes'])
    semantic = {name:sha for name,sha in pins.items() if name != 'reversal_auxiliary_transition.py'}
    _require(semantic and previous['semantic_code_hashes'] == semantic, 'semantic_inventory_changed')
    _require(set(previous['next_session_code_hashes']) == set(A._code_hashes())
        and set(previous['reader_code_hashes']) == set(I.code_hashes()), 'code_inventory_membership_changed')
    refs = {ref['path']:ref['sha256'] for ref in (previous_ref, overlay_ref, source_ref, original_ref, prior_ref)}
    for name, expected in pins.items():
        path = _code_path(frozen, name)
        _require(_sha(path) == expected, 'frozen_semantic_code_changed')
        refs[str(path)] = expected
    original_codes, runtime_codes, current_refs = {}, {}, {}
    for historical_root, inventory in ((frozen, semantic), (origin, previous['next_session_code_hashes']),
                                       (origin, previous['reader_code_hashes'])):
        for name, expected in sorted(inventory.items()):
            old_path, current_path = _code_path(historical_root, name), _code_path(execution_root, name)
            _require(_sha(old_path) == expected, 'historical_code_changed')
            actual = _sha(current_path); relative = str(current_path.relative_to(execution_root))
            _require(actual == expected or C.reviewed_preparation_pair(relative, expected, actual),
                     'unreviewed_code_pair:' + relative)
            # Semantic originals retain their own historical identity even
            # when a later next-session reader already uses current bytes.
            original_codes.setdefault(relative, expected); runtime_codes[relative] = actual
            refs[str(old_path)] = expected; current_refs[str(current_path)] = actual
    # The evidence owner and the exact pair registry are themselves part of the
    # current clean-Git closure. There is no OS validation-context delegation.
    for path in (execution_root/'src/engine/scalping/reversal_auxiliary_source_handoff.py',
                 execution_root/'src/engine/infrastructure/startup_validation_code_context.py'):
        current_refs[str(path)] = _sha(path)
    commit = _git_identity(execution_root, current_refs, check_git=check_git)
    refs.update(current_refs)
    origin_commit = C._git_head(origin)
    for root in (execution_root, origin, frozen):
        refs.update(_git_references(root))
    for ident in source['registry_definitions']:
        path = G.directory(data_root)/(ident+'.json')
        refs[str(path)] = _sha(path)
    return dict(schema=SCHEMA, policy_data_root=str(data_root),
        previous_manifest=previous_ref, previous_overlay=overlay_ref,
        source_manifest=source_ref, source_bundle=original_ref, previous_target_bundle=prior_ref,
        code_origin_root=str(origin), code_origin_commit=origin_commit,
        frozen_validator_root=str(frozen), frozen_validator_commit=A.FROZEN_COMMIT,
        execution_release_root=str(execution_root), execution_release_commit=commit,
        original_code_hashes=original_codes, runtime_code_hashes=runtime_codes,
        current_code_references=current_refs, source_hashes=refs,
        base_bindings=copy.deepcopy(source['base_bindings']), effective_bindings=expected_bindings,
        changes=copy.deepcopy(source['changes']), rollback_bindings=copy.deepcopy(source['rollback_bindings']),
        registry_definitions_sha256=P.digest(source['registry_definitions']),
        scopes_sha256=P.digest(source['scopes']), scope_behavior=copy.deepcopy(previous['scope_behavior']),
        verified_pairs=50, verified_raw_responses=100, source_labels_rewritten=False,
        **{key:False for key in AUTHORITY_FALSE})


def inspect_previous(data_root, *, previous_manifest_path, previous_overlay_path):
    """Inspect the exact prior carry; this neither publishes nor selects it."""
    return P.seal(_inspect(data_root, previous_manifest_path, previous_overlay_path, check_git=True))


def _build(data_root, previous_manifest_path, previous_overlay_path, target_bundle_path, *, check_git, execution_root=None):
    from src.engine.scalping import reversal_auxiliary_next_session as A
    body = _inspect(data_root, previous_manifest_path, previous_overlay_path, check_git=check_git,
                    execution_root=execution_root)
    target, ref = _read(target_bundle_path)
    _bundle(target); N.validate(target, target_date=target['target_date'])
    _require(str(N.root(Path(data_root).resolve())/'generations'/(target['bundle_sha256']+'.json')) == ref['path'],
             'immutable_target_required')
    previous, _ = _reference(body['previous_target_bundle'])
    _require(target['source_date'] == previous['source_date'] and target['target_date'] == previous['target_date']
        and target['continuous_reversal']['effective_mode'] == 'next_session'
        and target['continuous_reversal']['release_commit'] == body['execution_release_commit'],
        'target_generation_invalid')
    bindings, refs, paths = A._bindings(data_root, target)
    if execution_root is not None:
        refs, paths = A._canonical_baseline_sources(refs, paths, execution_root)
    _require(bindings == body['base_bindings'] and len(bindings) == 128, 'target_baseline_changed')
    for sid in SCOPES:
        _require(A._scope_behavior(target, sid) == body['scope_behavior'][sid]['source'], 'target_scope_behavior_changed')
    for item in refs:
        _require(_sha(item['path']) == item['sha256'], 'target_baseline_source_changed')
        body['source_hashes'][item['path']] = item['sha256']
    body.update(target_bundle=ref, target_date=target['target_date'], target_source_date=target['source_date'],
                baseline_dependency_paths=sorted(set(paths)))
    body['source_hashes'][ref['path']] = ref['sha256']
    sealed = P.seal(body)
    _require(len(json.dumps(sealed, sort_keys=True, allow_nan=False).encode()) <= MAX_BYTES, 'artifact_size_limit')
    return sealed


def build(data_root, *, previous_manifest_path, previous_overlay_path, target_bundle_path):
    """Return an immutable code-carry artifact; the caller owns its storage."""
    return _build(data_root, previous_manifest_path, previous_overlay_path, target_bundle_path, check_git=True)


def validate(data_root, handoff, *, source_manifest_path, source_bundle_path, target_bundle_path, frozen_root):
    """Recheck the same sources without subprocesses or runtime authority."""
    _require(isinstance(handoff, dict) and handoff.get('schema') == SCHEMA, 'artifact_invalid')
    _sealed(handoff)
    for key, path in (('source_manifest', source_manifest_path), ('source_bundle', source_bundle_path),
                      ('target_bundle', target_bundle_path)):
        _require(handoff[key]['path'] == str(Path(path)), 'consumer_path_changed')
    _require(handoff['frozen_validator_root'] == str(Path(frozen_root)), 'consumer_frozen_root_changed')
    expected = _build(data_root, handoff['previous_manifest']['path'], handoff['previous_overlay']['path'],
                      target_bundle_path, check_git=False, execution_root=handoff['execution_release_root'])
    _require(expected == handoff, 'artifact_or_source_changed')
    # Rebuild the immutable historical issue at its original code root. A
    # later reader must separately preserve every reviewed runtime semantic
    # byte; moving code does not change the original target release identity.
    from src.engine.infrastructure import startup_validation_code_context as C
    for relative, original in handoff['runtime_code_hashes'].items():
        _require(relative.startswith('src/engine/') and '..' not in Path(relative).parts,
                 'runtime_code_path_invalid')
        actual = _sha(ROOT/relative)
        _require(actual == original or C.reviewed_preparation_pair(relative, original, actual),
                 'unreviewed_runtime_reader:' + relative)
    return handoff
