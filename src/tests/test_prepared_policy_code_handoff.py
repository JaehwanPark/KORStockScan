"""Prepared code compatibility never supplies PREOPEN or PID authority."""
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from src.engine.automation import prepared_policy_code_handoff as C
from src.engine.automation import intraday_release_handoff as H
from src.engine.automation import ordered_intraday_deploy as O
from src.engine.infrastructure import runtime_release_router as R

DAY = '2026-10-19'
COMMIT = 'b'*40
ORIGIN = 'a'*40
NOW = datetime(2026,10,17,12,tzinfo=ZoneInfo('Asia/Seoul'))


@pytest.fixture
def prepared(tmp_path, monkeypatch, request):
    family = getattr(request, 'param', 'pre_submit_delay')
    data=tmp_path/'data'; data.mkdir()
    root=tmp_path/'release'; root.mkdir()
    source=root/'consumer.py'; source.write_text('reviewed code\n')
    policy=data/'policy.json'; policy.write_text('{}')
    paths={'consumer.py':'consumer.py'}
    actual=C._digest({'consumer.py':C._sha(source)})
    def write(name, value):
        path=tmp_path/name
        path.write_text(json.dumps(value)); return path
    env=tmp_path/'env'; env.write_text('export TEST=true\n')
    manifest={'target_date':DAY,'selected_release_sha':ORIGIN,
              C.FAMILIES[family][0]:{'target_date':DAY,C.FAMILIES[family][1]:'policy'}}
    manifest['manifest_sha256']=C._digest(manifest)
    mp=write('manifest.json',manifest)
    vp=write('verify.json',{'status':'pass','findings':[], 'manifest_sha256':manifest['manifest_sha256']})
    controller=write('controller.json',{'status':'done'})
    summary=write('summary.json',{'date':'2026-10-16'})
    body=dict(schema='next_preopen_readiness_v1',status='prepared_verified',target_date=DAY,
              selected_release_commit=ORIGIN,actual_pid_consumed=False,runtime_effect=False,
              policy_receipts=[])
    for field,digest,path in [('manifest_path','manifest_file_sha256',mp),('env_path','env_sha256',env),
                             ('verification_path','verification_sha256',vp),
                             ('controller_path','controller_sha256',controller),
                             ('summary_path','summary_sha256',summary)]:
        body[field]=str(path);body[digest]=C._sha(path)
    pp=write('prepared.json',body)
    monkeypatch.setattr(C,'_clock',lambda day,now=None: None)
    monkeypatch.setattr(C,'_policy',lambda *a: (policy,'expected'))
    monkeypatch.setattr(H,'_verify_entry_code_delta',lambda *a: ['consumer.py'])
    monkeypatch.setattr(R,'selected_release',lambda *a: (root,COMMIT))
    monkeypatch.setattr(R,'validate_release',lambda *a: (root,COMMIT))
    monkeypatch.setattr(O,'_main_pids',lambda: [])
    monkeypatch.setattr(O,'_session_absent',lambda: True)
    import subprocess
    monkeypatch.setattr(subprocess,'check_output',lambda *a,**kw: COMMIT+'\n')
    args=dict(family=family,policy_sha='policy',expected='expected',paths=paths)
    receipt=C.issue(data,DAY,**args,release_root=root,prepared_receipt=pp,
                    origin_verification=vp,confirm=C.AUTHORITY)
    return data,root,args,actual,receipt,pp


def test_future_and_target_day_proof_preserves_policy_without_pid(prepared):
    data,root,args,actual,receipt,pp=prepared
    before=pp.read_bytes()
    proof=C.verify(data,DAY,**args,actual=actual)
    assert proof['verification_basis']==C.SCHEMA
    assert proof['policy_effect']=='unchanged' and proof['actual_pid_consumed'] is False
    assert pp.read_bytes()==before


@pytest.mark.parametrize('fault',['runtime','policy','expected','source','receipt','origin','symlink'])
def test_invalid_binding_never_uses_prepared_code_authority(prepared,fault):
    data,root,args,actual,receipt,pp=prepared
    args=dict(args)
    if fault=='runtime': (root/'consumer.py').write_text('changed')
    elif fault=='policy': args['policy_sha']='different'
    elif fault=='expected': args['expected']='different'
    elif fault=='source': (data/'policy.json').write_text('{"changed":true}')
    elif fault=='origin':
        Path(receipt['historical_snapshots'][str(pp)]).write_text('changed')
    else:
        path=C.receipt_path(data,DAY,COMMIT,'pre_submit_delay')
        if fault=='receipt':
            receipt['actual_pid_consumed']=True;receipt['receipt_sha256']=C._digest({k:v for k,v in receipt.items() if k!='receipt_sha256'})
            path.write_text(json.dumps(receipt))
        else:
            target=path.with_suffix('.saved');path.rename(target);path.symlink_to(target)
    with pytest.raises(ValueError): C.verify(data,DAY,**args,actual=actual)


def test_missing_receipt_keeps_ordinary_native_path(tmp_path,monkeypatch):
    monkeypatch.setattr(R,'selected_release',lambda *a: (tmp_path,COMMIT))
    assert C.verify(tmp_path,DAY,family='main_stop',policy_sha='x',expected='x',paths={},actual='x') is None


def test_target_expiry_is_not_renewed():
    C._clock(DAY,NOW)
    C._clock(DAY,NOW.replace(day=19))
    with pytest.raises(ValueError,match='expired'):C._clock(DAY,NOW.replace(day=20))


def test_origin_rejects_modified_prepared_hashes(prepared):
    data,root,args,actual,receipt,pp=prepared
    body=json.loads(pp.read_text());body['manifest_file_sha256']='0'*64;pp.write_text(json.dumps(body))
    with pytest.raises(ValueError):C._origin(pp,args['family'],DAY)


def test_original_closure_can_advance_without_rewriting_historical_authority(prepared):
    data,root,args,actual,receipt,pp=prepared
    body=json.loads(pp.read_text())
    Path(body['controller_path']).write_text('{"status":"new generation"}')
    assert C.verify(data,DAY,**args,actual=actual)['actual_pid_consumed'] is False
    # The current policy remains independently pinned despite historical retention.
    (data/'policy.json').write_text('{"different":true}')
    with pytest.raises(ValueError):C.verify(data,DAY,**args,actual=actual)


def test_native_code_inventory_accepts_utils_paths_and_rejects_escape(tmp_path):
    import subprocess
    import hashlib
    root=tmp_path/'repo';root.mkdir()
    own=root/'src/engine/automation/intraday_release_handoff.py'
    own.parent.mkdir(parents=True);own.write_bytes(Path(H.__file__).read_bytes())
    utility=root/'src/utils/market_day.py';utility.parent.mkdir();utility.write_text('value = 1\n')
    subprocess.run(['git','init','-q',str(root)],check=True)
    subprocess.run(['git','-C',str(root),'add','.'],check=True)
    subprocess.run(['git','-C',str(root),'-c','user.name=Test','-c','user.email=test@example.invalid',
                    'commit','-qm','fixture'],check=True)
    commit=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
    expected=C._digest({'market_day':hashlib.sha256(utility.read_bytes()).hexdigest()})
    assert H._verify_entry_code_delta(root,commit,commit,
        {'market_day':'src/engine/../utils/market_day.py'},expected)==[]
    (tmp_path/'outside.py').write_text('private fixture\n')
    with pytest.raises(ValueError,match='outside_release'):
        H._verify_entry_code_delta(root,commit,commit,{'outside':'../outside.py'},expected)


@pytest.mark.parametrize('family,expected', [
    ('pre_submit_delay', 'bd5767c2b6b9dcfe738d2b61740e5a980b965ccfdc2c11ebc197b839da4a4256'),
    ('holding_vote', '6c664915b34289cddceeaf20399cce45f5e9e3f3373fdeae885910043f343112'),
    ('main_stop', '687c06b51d0e4b581f1927151b31483d5f979e438cc67a726e6718f84bead533'),
])
def test_delay_research_exact_original_policy_inventory_is_preserved(monkeypatch, family, expected):
    """Bind reviewed bytes to the real frozen origin, without issuing a receipt."""
    import hashlib
    from src.engine.scalping import pre_submit_delay_initial_policy as delay
    from src.engine.scalping import holding_vote_experiment as holding
    from src.engine.scalping import main_stop_policy as stop
    root = Path(H.__file__).resolve().parents[3]
    origin = '7f2552aedde8fec6ef904a43105827907e50dfc8'
    candidate = 'b' * 40
    paths = ({name:name for name in delay.CONTRACT_PATHS} if family == 'pre_submit_delay'
             else {name:'src/engine/'+name for name in
                   (holding._code_paths() if family == 'holding_vote' else stop.implementation_paths())})
    real_git = H.subprocess.check_output
    def fixture_revision(command, **kwargs):
        revision, name = command[-1].split(':', 1)
        return (root/name).read_bytes() if revision == candidate else real_git(command, **kwargs)
    monkeypatch.setattr(H.subprocess, 'check_output', fixture_revision)
    before = {name:(root/name).read_bytes() for name in paths.values()}
    changed = H._verify_entry_code_delta(root, candidate, origin, paths, expected)
    assert 'src/engine/sniper_state_handlers.py' in changed
    assert before == {name:(root/name).read_bytes() for name in paths.values()}
    if family == 'pre_submit_delay':
        extensions = H.REVIEWED_DELAY_CONTRACT_EXTENSIONS[(origin, expected)]
        assert set(extensions) == {'src/engine/pipeline_event_summary.py', 'src/utils/threshold_cycle_registry.py',
                                   'src/engine/infrastructure/main_policy_loading.py'}
        assert all(hashlib.sha256((root/name).read_bytes()).hexdigest() == digest
                   for name, digest in extensions.items())
        for name, pair in H.REVIEWED_DELAY_RESEARCH_SOURCES.items():
            prior = real_git(['git', '-C', str(root), 'show', origin+':'+name])
            assert pair[0] == hashlib.sha256(prior).hexdigest()
            current = hashlib.sha256((root/name).read_bytes()).hexdigest()
            reviewed = {pair[1]}
            if name in H.REVIEWED_MAIN_POLICY_LOAD_EXIT_SOURCES:
                reviewed.add(H.REVIEWED_MAIN_POLICY_LOAD_EXIT_SOURCES[name][1])
            if name in H.REVIEWED_HOLDING_RESEARCH_INTEGRATION_SOURCES:
                reviewed.add(H.REVIEWED_HOLDING_RESEARCH_INTEGRATION_SOURCES[name][1])
            if name in H.REVIEWED_COMPLETED_RESEARCH_INTEGRATION_SOURCES:
                reviewed.add(H.REVIEWED_COMPLETED_RESEARCH_INTEGRATION_SOURCES[name][1])
            assert current in reviewed


def _origin_resolution_arguments(prepared):
    data, root, args, actual, receipt, pp = prepared
    selector = data/'runtime/runtime_release_selection.json'
    selector.parent.mkdir(parents=True, exist_ok=True)
    selector.write_text('{"fixture_selection":"unchanged"}\n')
    return data, root, {**args, 'selected_root':root, 'selected_commit':COMMIT}, selector


def test_resolve_selected_exact_code_origin_without_new_handoff(prepared, monkeypatch):
    data, root, args, selector = _origin_resolution_arguments(prepared)
    args['expected'] = prepared[3]
    def forbidden_verify(*args, **kwargs):
        pytest.fail('exact selected code must not require a predecessor handoff')
    monkeypatch.setattr(C, 'verify', forbidden_verify)
    before = selector.read_bytes()
    result = C.resolve_prepared_code_origin(data, DAY, **args)
    assert result['origin_commit'] == COMMIT
    assert result['basis'] == 'selected_exact_code_contract'
    assert result['sources'][str(selector)] == C._sha(selector)
    assert result['sources'][str(root/'consumer.py')] == C._sha(root/'consumer.py')
    assert result['selected_paths'] == args['paths']
    assert selector.read_bytes() == before


def test_resolve_selected_handoff_keeps_original_frozen_origin_and_sources(prepared):
    data, root, args, selector = _origin_resolution_arguments(prepared)
    before = {str(p):p.read_bytes() for p in data.rglob('*') if p.is_file()}
    result = C.resolve_prepared_code_origin(data, DAY, **args)
    receipt = C.receipt_path(data,DAY,COMMIT,args['family'])
    assert result['origin_commit'] == ORIGIN != COMMIT
    assert result['basis'] == 'verified_selected_prepared_code_handoff'
    assert result['code_handoff_receipt_path'] == str(receipt)
    assert result['sources'][str(receipt)] == C._sha(receipt)
    assert result['sources'].items() >= prepared[4]['sources'].items()
    assert before == {str(p):p.read_bytes() for p in data.rglob('*') if p.is_file()}


def test_resolve_origin_authenticates_issued_inventory_before_known_new_extension(prepared, monkeypatch):
    data, root, args, selector = _origin_resolution_arguments(prepared)
    addition = 'new_startup_consumer.py'
    monkeypatch.setitem(H.REVIEWED_DELAY_CONTRACT_EXTENSIONS, (ORIGIN,args['expected']),
                        {addition:'d'*64})
    args['paths'] = {**args['paths'],addition:addition}
    assert not (root/addition).exists()  # The selected old release lacks it.
    result = C.resolve_prepared_code_origin(data,DAY,**args)
    assert result['origin_commit'] == ORIGIN
    assert result['selected_paths'] == prepared[2]['paths']
    assert result['selected_runtime_code_sha256'] == prepared[3]
    assert result['reviewed_extension_hashes'] == {addition:'d'*64}


@pytest.mark.parametrize('fault',['unknown','missing'])
def test_resolve_origin_rejects_unknown_or_omitted_inventory_extension(prepared, monkeypatch, fault):
    data, root, args, selector = _origin_resolution_arguments(prepared)
    addition = 'new_startup_consumer.py'
    monkeypatch.setitem(H.REVIEWED_DELAY_CONTRACT_EXTENSIONS, (ORIGIN,args['expected']),
                        {addition:'d'*64})
    if fault == 'unknown':
        args['paths'] = {**args['paths'],addition:addition,'unreviewed.py':'unreviewed.py'}
    with pytest.raises(ValueError,match='inventory_extension_unreviewed'):
        C.resolve_prepared_code_origin(data,DAY,**args)


@pytest.mark.parametrize('fault', ['selected_commit','policy','frozen_source','receipt','selected_code'])
def test_resolve_origin_rejects_changed_or_unbound_selected_handoff(prepared, fault):
    data, root, args, selector = _origin_resolution_arguments(prepared)
    if fault == 'selected_commit':
        args['selected_commit'] = 'c'*40
    elif fault == 'policy':
        args['policy_sha'] = 'another-policy'
    elif fault == 'selected_code':
        (root/'consumer.py').write_text('unreviewed changed source\n')
    elif fault == 'frozen_source':
        frozen = next(iter(prepared[4]['sources']))
        Path(frozen).write_text('changed original evidence\n')
    else:
        C.receipt_path(data,DAY,COMMIT,args['family']).unlink()
    with pytest.raises(ValueError):
        C.resolve_prepared_code_origin(data,DAY,**args)


def test_resolve_origin_rejects_selector_change_during_native_verification(prepared, monkeypatch):
    data, root, args, selector = _origin_resolution_arguments(prepared)
    native_verify = C.verify
    def changed_selection(*args, **kwargs):
        result = native_verify(*args, **kwargs)
        selector.write_text('{"fixture_selection":"different_generation"}\n')
        return result
    monkeypatch.setattr(C,'verify',changed_selection)
    with pytest.raises(ValueError,match='prepared_code_origin_sources_changed'):
        C.resolve_prepared_code_origin(data,DAY,**args)


def test_new_startup_handoff_accepts_only_exact_reviewed_delay_source_pair(tmp_path, monkeypatch):
    import hashlib
    from src.engine.scalping.pre_submit_delay_initial_policy import CONTRACT_PATHS
    canonical = Path(H.__file__).resolve().parents[3]
    fixture = tmp_path/'code'
    own = 'src/engine/automation/intraday_release_handoff.py'
    dependencies = H.REVIEWED_HOLDING_RESEARCH_DEPENDENCIES['src/engine/sniper_state_handlers.py'][
        H._sha(canonical/'src/engine/sniper_state_handlers.py')]
    for name in (*CONTRACT_PATHS,own,*dependencies):
        destination=fixture/name
        destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_bytes((canonical/name).read_bytes())
    origin = '7f2552aedde8fec6ef904a43105827907e50dfc8'
    candidate = 'd'*40
    real_git = H.subprocess.check_output
    def revision(command, **kwargs):
        rev, name = command[-1].split(':',1)
        if rev == candidate:
            return (fixture/name).read_bytes()
        return real_git(['git','-C',str(canonical),'show',rev+':'+name],**kwargs)
    monkeypatch.setattr(H.subprocess,'check_output',revision)
    paths={name:name for name in CONTRACT_PATHS}
    expected='bd5767c2b6b9dcfe738d2b61740e5a980b965ccfdc2c11ebc197b839da4a4256'
    changed = H._verify_entry_code_delta(fixture,candidate,origin,paths,expected)
    assert set(H.REVIEWED_MAIN_POLICY_LOAD_EXIT_SOURCES).issubset(changed)
    for name, pair in H.REVIEWED_MAIN_POLICY_LOAD_EXIT_SOURCES.items():
        final_pair = H.REVIEWED_COMPLETED_RESEARCH_INTEGRATION_SOURCES.get(name, pair)
        assert hashlib.sha256((fixture/name).read_bytes()).hexdigest() == final_pair[1]
    # Model a clean committed candidate with an unknown replacement. The Git
    # fixture returns those same bytes, so rejection must be semantic/code-pair,
    # rather than the dirty-worktree check.
    unknown = fixture/'src/engine/scalping/pre_submit_delay_tuning.py'
    unknown.write_text(unknown.read_text()+'\nUNKNOWN_STARTUP_CHANGE = True\n')
    with pytest.raises(ValueError,match='entry_consumer_unreviewed_change'):
        H._verify_entry_code_delta(fixture,candidate,origin,paths,expected)
    unknown.write_bytes((canonical/'src/engine/scalping/pre_submit_delay_tuning.py').read_bytes())
    new_helper=fixture/'src/engine/infrastructure/main_policy_loading.py'
    new_helper.write_text(new_helper.read_text()+'\nUNKNOWN_HELPER_CHANGE = True\n')
    with pytest.raises(ValueError,match='entry_consumer_contract_extension_unreviewed'):
        H._verify_entry_code_delta(fixture,candidate,origin,paths,expected)


@pytest.mark.parametrize('prepared', ['main_stop', 'holding_vote'], indirect=True)
@pytest.mark.parametrize('fault', [None, 'missing', 'extra', 'full_key', 'normalized_key',
                                   'bad_extension_prefix', 'other_family'])
def test_engine_relative_extension_preserves_native_family_keys(prepared, monkeypatch, fault):
    data, root, args, selector = _origin_resolution_arguments(prepared)
    addition = 'src/engine/../utils/new_source.py'
    extensions = {addition: 'd'*64}
    monkeypatch.setitem(H.REVIEWED_DELAY_CONTRACT_EXTENSIONS, (ORIGIN, args['expected']), extensions)
    args['paths'] = {**args['paths'], '../utils/new_source.py': addition}
    if fault == 'missing': args['paths'].pop('../utils/new_source.py')
    elif fault == 'extra': args['paths']['unreviewed.py'] = 'src/engine/unreviewed.py'
    elif fault == 'full_key': args['paths'] = {'consumer.py': 'consumer.py', addition: addition}
    elif fault == 'normalized_key': args['paths'] = {'consumer.py': 'consumer.py', 'src/utils/new_source.py': addition}
    elif fault == 'bad_extension_prefix':
        monkeypatch.setitem(H.REVIEWED_DELAY_CONTRACT_EXTENSIONS, (ORIGIN, args['expected']),
                            {'src/utils/new_source.py': 'd'*64})
    elif fault == 'other_family': args['family'] = 'pre_submit_delay'
    before = {str(p): p.read_bytes() for p in data.rglob('*') if p.is_file()}
    if fault:
        with pytest.raises(ValueError): C.resolve_prepared_code_origin(data, DAY, **args)
    else:
        result = C.resolve_prepared_code_origin(data, DAY, **args)
        assert result['selected_paths'] == prepared[2]['paths']
        assert result['reviewed_extension_hashes'] == extensions
        assert result['original_code_sha256'] == args['expected']
    assert before == {str(p): p.read_bytes() for p in data.rglob('*') if p.is_file()}
