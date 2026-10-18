"""Source-only carry uses exact private Git fixtures, never live policy proof."""
import copy
import hashlib
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from src.engine.scalping import reversal_auxiliary_source_handoff as H
from src.engine.scalping import reversal_auxiliary_next_session as A
from src.engine.scalping import reversal_auxiliary_input_transition as J
from src.engine.scalping import reversal_auxiliary_intraday as I
from src.engine.scalping import reversal_auxiliary_registry as G
from src.engine.infrastructure import startup_validation_code_context as C
from src.tests.test_reversal_auxiliary_next_session import carry

P, N = H.P, H.N
REAL_GIT = subprocess.check_output


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def commit(root):
    subprocess.run(['git', 'init', '-q', str(root)], check=True)
    subprocess.run(['git', '-C', str(root), 'add', '.'], check=True)
    subprocess.run(['git', '-C', str(root), '-c', 'user.name=fixture', '-c',
                    'user.email=fixture@example.test', 'commit', '-qm', 'source fixture'], check=True)
    return REAL_GIT(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()


def sealed_bundle(value):
    body = copy.deepcopy(value)
    body['bundle_sha256'] = N.digest({k:v for k,v in body.items() if k != 'bundle_sha256'})
    return body


@pytest.fixture
def source(carry, tmp_path, monkeypatch):
    """Native registry/128 scope shape; private source files test code contracts.

    The imported carry fixture isolates machine validation/frozen replay. This
    suite does not manufacture an operational P5 or publication receipt.
    """
    f = carry
    current = tmp_path/'candidate'; origin = tmp_path/'origin'; frozen = f.frozen
    input_names = set(J.code_hashes()); reader_names = set(I.code_hashes()); next_names = set(A._code_hashes())
    names = input_names | reader_names | next_names
    old, new = {}, {}
    for name in names:
        old[name] = ('# original fixture source '+name+'\n').encode()
        new[name] = old[name] + (b'# reviewed source-only change\n' if name in {
            'reversal_auxiliary_input_transition.py', 'reversal_auxiliary_next_session.py'} else b'')
        for root, raw in ((frozen, old[name]), (origin, old[name]), (current, new[name])):
            path = H._code_path(root, name); path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
    for name in ('src/engine/scalping/reversal_auxiliary_source_handoff.py',
                 'src/engine/infrastructure/startup_validation_code_context.py'):
        path = current/name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes((H.ROOT/name).read_bytes())
    frozen_commit = commit(frozen); origin_commit = commit(origin); current_commit = commit(current)
    monkeypatch.setattr(H, 'ROOT', current)
    monkeypatch.setattr(A, 'FROZEN_COMMIT', frozen_commit)
    pairs = {str(H._code_path(current, name).relative_to(current)):(sha(old[name]),sha(new[name]))
             for name in names if old[name] != new[name]}
    monkeypatch.setattr(C, 'REVIEWED_PREPARATION_SOURCES', pairs)
    original = sealed_bundle(f.old)
    prior = copy.deepcopy(f.target)
    prior['continuous_reversal'].update(parent_bundle_sha256=original['bundle_sha256'], release_commit=origin_commit)
    prior = sealed_bundle(prior)
    target = copy.deepcopy(prior); target['continuous_reversal']['release_commit'] = current_commit
    target = sealed_bundle(target)
    original_path = N.root(f.data)/'generations'/(original['bundle_sha256']+'.json')
    prior_path = N.root(f.data)/'generations'/(prior['bundle_sha256']+'.json')
    target_path = N.root(f.data)/'generations'/(target['bundle_sha256']+'.json')
    for path,value in ((original_path,original),(prior_path,prior),(target_path,target)):
        P.write(path,value)
    original_source = copy.deepcopy(f.source)
    original_source.update(base_bundle_sha256=original['bundle_sha256'],
        input_transition_code_hashes={name:sha(old[name]) for name in input_names},
        reader_code_hashes={name:sha(old[name]) for name in reader_names})
    original_source = P.seal(original_source)
    source_path = I.root(f.data)/'transitions'/(original_source['artifact_content_sha256']+'.json')
    P.write(source_path,original_source)
    for value in original_source['registry_definitions'].values():G.register(f.data,value)
    semantic = dict(original_source['input_transition_code_hashes']); semantic.update(original_source['reader_code_hashes'])
    semantic.pop('reversal_auxiliary_transition.py',None)
    previous = dict(schema=A.SCHEMA,status='prepared',policy_data_root=str(f.data.resolve()),
        source_manifest=A._reference(source_path),source_bundle=A._reference(original_path),
        target_bundle=A._reference(prior_path),base_bundle_sha256=prior['bundle_sha256'],
        bundle_target_date=prior['target_date'],operating_day=prior['target_date'],
        code_origin_root=str(origin),frozen_validator_root=str(frozen),frozen_validator_commit=frozen_commit,
        semantic_code_hashes=semantic,next_session_code_hashes={name:sha(old[name]) for name in next_names},
        reader_code_hashes=original_source['reader_code_hashes'],base_bindings_sha256=P.digest(f.bindings),
        scope_behavior={sid:dict(source=A._scope_behavior(original,sid),target=A._scope_behavior(prior,sid)) for sid in H.SCOPES},
        verified_pairs=50,verified_raw_responses=100,source_labels_rewritten=False,new_provider_calls=0,
        policy_published=False,actual_pid_consumed=False,actual_order_submitted=False,
        **{key:copy.deepcopy(original_source[key]) for key in ('base_bindings','changes','rollback_bindings','registry_definitions','scopes')})
    previous = P.seal(previous)
    previous_path = I.root(f.data)/'transitions'/(previous['artifact_content_sha256']+'.json');P.write(previous_path,previous)
    effective = dict(f.bindings);effective.update(previous['changes'])
    overlay = P.seal(dict(schema=I.SCHEMA,authority=I.AUTHORITY,day=prior['target_date'],
        base_bundle_sha256=prior['bundle_sha256'],base_family_sha256=prior['continuous_reversal']['family_sha256'],
        detector_manifest_hash=prior['continuous_reversal']['operating_manifest']['detector_manifest_hash'],
        bindings=effective,changes=previous['changes'],rollback_bindings=previous['rollback_bindings'],
        previous_overlay_sha256=None,effective_mode='next_session',effective_from=prior['target_date']+'T00:00:00+09:00',
        revoked_overlays=[],revoked_scope_overlays={},transition_manifest_sha256=previous['artifact_content_sha256']))
    overlay_path = I.root(f.data)/'days'/prior['target_date']/(prior['bundle_sha256']+'.json');P.write(overlay_path,overlay)
    return SimpleNamespace(data=f.data,current=current,origin=origin,frozen=frozen,current_commit=current_commit,
        previous=previous,previous_path=previous_path,overlay=overlay,overlay_path=overlay_path,
        source=original_source,source_path=source_path,original_path=original_path,
        target=target,target_path=target_path,bindings=f.bindings,pairs=pairs)


def build(f):
    return H.build(f.data,previous_manifest_path=f.previous_path,previous_overlay_path=f.overlay_path,
                   target_bundle_path=f.target_path)


def validate(f, value):
    return H.validate(f.data,value,source_manifest_path=f.source_path,source_bundle_path=f.original_path,
                      target_bundle_path=f.target_path,frozen_root=f.frozen)


def test_native_source_owner_is_readonly_and_runtime_validation_spawns_nothing(source, monkeypatch):
    f=source;before={p:p.read_bytes() for p in f.data.rglob('*') if p.is_file()}
    inspected=H.inspect_previous(f.data,previous_manifest_path=f.previous_path,previous_overlay_path=f.overlay_path)
    value=build(f)
    assert inspected['source_manifest']==value['source_manifest']
    assert len(value['base_bindings'])==len(value['effective_bindings'])==128
    assert tuple(sorted(value['changes']))==H.SCOPES
    assert sum(value['base_bindings'][k]!=v for k,v in value['effective_bindings'].items())==2
    assert all(value[key] is False for key in H.AUTHORITY_FALSE)
    assert value['execution_release_commit']==f.current_commit
    assert value['original_code_hashes']!=value['runtime_code_hashes']
    assert set(value['current_code_references'])<=set(value['source_hashes'])
    monkeypatch.setattr(H.subprocess,'check_output',lambda *a,**k:pytest.fail('runtime subprocess'))
    for _ in range(2):assert validate(f,value)==value
    assert before=={p:p.read_bytes() for p in f.data.rglob('*') if p.is_file()}


@pytest.mark.parametrize('damage', [None, 'current_semantics', 'historical_semantics',
                                   'historical_commit', 'historical_root', 'target_commit'])
def test_historical_issue_survives_reader_move_only_with_exact_sources(source, monkeypatch, tmp_path, damage):
    import shutil
    f=source
    monkeypatch.setattr(A,'__file__',str(H._code_path(f.current,'reversal_auxiliary_next_session.py')))
    def bindings(*args):
        path=Path(A.__file__).parent/'reversal_auxiliary_input_transition.py'
        return f.bindings,[dict(path=str(path),sha256=sha(path.read_bytes()))],[str(path)]
    monkeypatch.setattr(A,'_bindings',bindings)
    value=build(f);before=copy.deepcopy(value)
    moved=tmp_path/'later-reader';shutil.copytree(f.current,moved)
    monkeypatch.setattr(H,'ROOT',moved)
    monkeypatch.setattr(A,'__file__',str(H._code_path(moved,'reversal_auxiliary_next_session.py')))
    name='reversal_auxiliary_input_transition.py'
    if damage=='current_semantics':H._code_path(moved,name).write_text('unreviewed reader\n')
    elif damage=='historical_semantics':H._code_path(f.current,name).write_text('changed historical code\n')
    elif damage=='historical_commit':(f.current/'.git/HEAD').write_text('0'*40+'\n')
    elif damage=='historical_root':value=P.seal(dict(value,execution_release_root=str(moved)))
    elif damage=='target_commit':value=P.seal(dict(value,execution_release_commit='0'*40))
    monkeypatch.setattr(H.subprocess,'check_output',lambda *a,**k:pytest.fail('runtime subprocess'))
    if damage:
        with pytest.raises(ValueError):validate(f,value)
    else:
        assert validate(f,value)==before
        assert value['execution_release_root']==str(f.current)
        assert value['execution_release_commit']==f.current_commit
        assert all(value[key] is False for key in H.AUTHORITY_FALSE)


@pytest.mark.parametrize('fault',['dirty','untracked','unknown_pair','frozen','origin','symlink','ancestor_symlink'])
def test_unreviewed_source_cannot_create_a_handoff(source,monkeypatch,fault):
    f=source;name='reversal_auxiliary_input_transition.py'
    if fault in {'dirty','untracked'}:
        path=f.current/'src/extra.py' if fault=='untracked' else f.current/'src/engine/scalping/reversal_auxiliary_source_handoff.py'
        path.write_text('not committed\n')
    elif fault=='unknown_pair':monkeypatch.setattr(C,'REVIEWED_PREPARATION_SOURCES',{})
    elif fault in {'frozen','origin'}:H._code_path(getattr(f,fault),name if fault=='frozen' else 'reversal_auxiliary_next_session.py').write_text('changed\n')
    elif fault=='symlink':
        path=H._code_path(f.current,name);saved=path.with_suffix('.saved');path.rename(saved);path.symlink_to(saved)
    else:
        parent=f.current/'src/engine/scalping';saved=parent.with_name('saved');parent.rename(saved);parent.symlink_to(saved,target_is_directory=True)
    with pytest.raises(ValueError):build(f)


@pytest.mark.parametrize('field',['runtime_effect','allowed_runtime_apply','provider_called','execution_release_commit',
    'original_code_hashes','runtime_code_hashes','source_hashes','base_bindings','changes','rollback_bindings','target_bundle'])
def test_resealed_artifact_cannot_change_source_or_authority(source,field):
    f=source;value=build(f);bad=copy.deepcopy(value)
    if field in H.AUTHORITY_FALSE:bad[field]=True
    elif field=='execution_release_commit':bad[field]='0'*40
    elif field=='target_bundle':bad[field]['sha256']='0'*64
    else:bad[field]={}
    with pytest.raises(ValueError):validate(f,P.seal(bad))


@pytest.mark.parametrize('path',['previous_path','overlay_path','source_path','original_path','target_path'])
def test_original_artifact_bytes_are_rechecked_after_build(source,path):
    f=source;value=build(f);p=getattr(f,path);p.write_bytes(p.read_bytes()+b' ')
    with pytest.raises(ValueError):validate(f,value)


def test_same_day_handoff_does_not_authorize_a_new_target_date(source):
    f=source;value=copy.deepcopy(f.target);value['target_date']='2026-10-20';value=sealed_bundle(value)
    path=N.root(f.data)/'generations'/(value['bundle_sha256']+'.json');P.write(path,value)
    with pytest.raises(ValueError,match='target_generation_invalid'):
        H.build(f.data,previous_manifest_path=f.previous_path,previous_overlay_path=f.overlay_path,target_bundle_path=path)


def test_successor_carry_is_an_explicitly_unsupported_new_predecessor(source):
    f=source;previous=copy.deepcopy(f.previous);previous['source_code_handoff']={'path':'not a new authority'}
    previous=P.seal(previous);path=I.root(f.data)/'transitions'/(previous['artifact_content_sha256']+'.json');P.write(path,previous)
    with pytest.raises(ValueError,match='successor_predecessor_unsupported'):
        H.inspect_previous(f.data,previous_manifest_path=path,previous_overlay_path=f.overlay_path)


def test_native_baseline_and_two_scope_behavior_are_rechecked(source):
    f=source;unselected=next(k for k in f.bindings if k not in H.SCOPES);f.bindings[unselected]='0'*64
    with pytest.raises(ValueError,match='target_baseline_changed'):build(f)
