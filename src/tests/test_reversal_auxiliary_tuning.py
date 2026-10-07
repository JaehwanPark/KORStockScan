"""Real shared-store comparisons and auxiliary-only handoff boundaries."""
import copy
import json
from datetime import datetime
import pytest
from src.engine.scalping import reversal_auxiliary_registry as G
from src.engine.scalping import reversal_auxiliary_tuning as T
from src.engine.scalping import reversal_auxiliary_intraday as I
from src.engine.scalping import continuous_reversal_policy_v5 as V
from src.engine.scalping import mechanistic_entry_runtime_policy as N
from src.engine.scalping import reversal_operating_runtime as R
from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.ai import offline_comparison_store as S
from src.tests.test_reversal_operating_policy import parent,replay,transport,authorize_initial,PC
from src.tests.test_continuous_reversal_policy_v3 import native


@pytest.fixture
def setup(replay,monkeypatch):
    root,parent,machine=replay
    PC.prepare_inputs(root,'2026-10-07',machine,parent)
    PC.L.calls(PC,root,'2026-10-07',transport=transport,call_limit=5)
    authorize_initial(root,parent)
    aux=PC.auxiliary_report(root,'2026-10-07','2026-10-07',parent,publish_policy=False)
    issued=json.loads((PC.directory(root,'2026-10-07')/'machine.json').read_text())
    b=V.stage(root,'2026-10-07','2026-10-07',issued,aux,target_date='2026-10-08',release_commit='a'*40)
    # Freeze a new evaluation against the now-authorized actual machine list.
    machine=P.seal(dict(machine,parent_bundle_sha256=b['bundle_sha256'],operating_manifest=b['continuous_reversal']['operating_manifest']))
    P.write(PC.directory(root,'2026-10-07')/'machine-comparison.json',machine)
    monkeypatch.setattr(N,'load_effective',lambda **kw:b)
    sid='samsung|REGULAR|ALL|SOR'
    value=G.definition(G.A.V1.ARMS[-1],prompt=G.A.PROMPT+'Use observed adverse evidence, not a compulsory new confirmation.\n',hypothesis='Context is not observed failure')
    ident=G.register(root,value)
    T.configure(root,candidate=ident,scopes=[sid],seed='fixed-test',max_pairs=50)
    return root,b,machine,sid,value


def test_registry_immutable_ascii_and_historical_request_parity(setup):
    root,b,m,sid,v=setup
    with S.Store(root) as store:
        p=store.get(m['partitions'][0]['records_object'])[0]
        snap=store.get(p['snapshot_obj'])
    for arm in G.A.V1.ARMS:
        old=G.definition(arm)
        assert G.request(snap,old)==PC.request(snap,arm)
    bad=dict(v,prompt='잘못된 문구');bad['registry_sha256']=P.digest({k:x for k,x in bad.items() if k!='registry_sha256'})
    with pytest.raises(ValueError):G.register(root,bad)
    with pytest.raises(ValueError):G.load(root,'../x')


def test_prepare_reuses_shared_requests_and_ignores_unrelated_arms(setup):
    root,b,m,sid,v=setup
    c=T.prepare(root,'2026-10-07',m,b)
    assert c['expected_pairs']>0 and c['expected_owner_requests']==2*c['expected_pairs']
    with S.Store(root) as store:
        count=store.db.execute('SELECT count(*) FROM requests').fetchone()[0]
    assert T.prepare(root,'2026-10-07',m,b)==c
    with S.Store(root) as store:
        assert store.db.execute('SELECT count(*) FROM requests').fetchone()[0]==count
    T.calls(root,'2026-10-07',transport=transport)
    result=T.evaluate(root,'2026-10-07')
    assert result['paired_metrics_ready'] and result['scopes'][sid]['paired_points']==c['expected_pairs']
    assert result['scopes'][sid]['current']['pass_win_rate']==1
    assert not result['scopes'][sid]['improved']
    assert T.calls(root,'2026-10-07',transport=lambda *a,**k:pytest.fail('cache called'))['new_calls']==0


def test_zero_budget_has_no_transport_and_no_false_winrate(setup):
    root,b,m,sid,v=setup;c=T.prepare(root,'2026-10-07',m,b)
    with S.Store(root) as store:
        for i in range(100):store.db.execute('INSERT OR IGNORE INTO attempt_budgets VALUES(?,?)',('spent-'+str(i),'postclose_auxiliary:2026-10-07'))
        store.commit()
    assert T.calls(root,'2026-10-07',transport=lambda *a,**kw:pytest.fail('over budget'))['new_calls']==0
    result=T.evaluate(root,'2026-10-07')
    assert result['scopes'][sid]['candidate']['pass_win_rate'] is None
    assert not result['scopes'][sid]['improved']
    # A later evaluation date does not replenish the old observations' budget.
    next_machine=P.seal(dict(m,source_date='2026-10-08',publication_date='2026-10-08'))
    T.prepare(root,'2026-10-08',next_machine,b)
    assert T.calls(root,'2026-10-08',transport=lambda *a,**kw:pytest.fail('old source reset'))['new_calls']==0


def test_sampling_ignores_label_and_excludes_development(setup):
    root,b,m,sid,v=setup;c=T.prepare(root,'2026-10-07',m,b)
    with S.Store(root) as store:
        revised=copy.deepcopy(m)
        for part in revised['partitions']:
            points=store.get(part['records_object'])
            for p in points:p['outcome']={'status':'FAIL_TIMEOUT'}
            part['records_object']=store.put(points);part['records_sha256']=P.digest(points)
        store.commit()
    revised=P.seal(revised)
    new=T.prepare(root,'2026-10-07',revised,b)
    assert new['selector']['selected_keys']==c['selector']['selected_keys']
    assert all(p['outcome']['status']=='FAIL_TIMEOUT' for p in new['pairs'])


def test_pair_corruption_rejected_before_calls(setup):
    root,b,m,_,_=setup;c=T.prepare(root,'2026-10-07',m,b)
    with S.Store(root) as store:
        row=next(iter(store.owners(c['artifact_content_sha256'])))
        store.db.execute('UPDATE members SET outcome=? WHERE id=?',('FAIL_STOP',row[7]));store.commit()
    with pytest.raises(ValueError,match='membership'):
        T.calls(root,'2026-10-07',transport=lambda *a,**kw:pytest.fail('corrupt pair'))


def test_metrics_and_all_blocked_null():
    a=T.matrix([('WIN','PASS'),('FAIL_STOP','PASS'),('WIN','VETO')])
    b=T.matrix([('WIN','PASS'),('FAIL_STOP','VETO'),('WIN','CAUTION')])
    assert a['TP']==1 and a['FP']==1 and a['FN']==1 and a['TN']==0
    assert T.improves(a,b)
    assert not T.improves(a,T.matrix([('WIN','VETO')]))
    assert T.matrix([])['pass_win_rate'] is None


def overlay(root,b,bindings,at,previous=None):
    record=P.seal(dict(schema=I.SCHEMA,authority=I.AUTHORITY,day=at.date().isoformat(),effective_from=at.isoformat(),
        base_bundle_sha256=b['bundle_sha256'],base_family_sha256=b['continuous_reversal']['family_sha256'],
        detector_manifest_hash=b['continuous_reversal']['operating_manifest']['detector_manifest_hash'],
        previous_overlay_sha256=previous,bindings=bindings,code_hashes=I.code_hashes(),revoked_overlays=[]))
    P.write(I.root(root)/'generations'/(record['artifact_content_sha256']+'.json'),record)
    P.write(I.root(root)/'current.json',record)
    return record


def test_overlay_uses_signal_clock_preserves_machine_and_old_requests(setup):
    root,b,m,sid,v=setup
    c=T.prepare(root,'2026-10-07',m,b)
    with S.Store(root) as store:snap=store.get(c['pairs'][0]['snapshot_obj'])
    epoch=snap[0]['epoch'];at=datetime.fromtimestamp(epoch-1,I.K.KST)
    baseline=V.assess(b['continuous_reversal'],snap,symbol=snap[0]['symbol'],session=snap[0]['market'])
    family_before=copy.deepcopy(b['continuous_reversal']);states_before=dict(R._STATES)
    first=overlay(root,b,{sid:v['registry_sha256']},at)
    updated=I.apply_request(root,dict(continuous_reversal=b['continuous_reversal'],machine_bundle_sha256=b['bundle_sha256']),snap,baseline)
    assert updated[2]==v['prompt'] and updated[0]['scope_execution_hash']==baseline[0]['scope_execution_hash']
    assert b['continuous_reversal']==family_before and R._STATES==states_before
    policy=dict(continuous_reversal_assessment=updated[0])
    I.validate_decision(root,policy,b,now=epoch+1)
    next_value=G.definition(v['base_arm'],prompt=v['prompt']+'Do not invent future evidence.\n');G.register(root,next_value)
    overlay(root,b,{sid:next_value['registry_sha256']},datetime.fromtimestamp(epoch+2,I.K.KST),first['artifact_content_sha256'])
    I.validate_decision(root,policy,b,now=epoch+3)
    I.validate_submit(root,dict(entry_mechanistic_policy_decision=updated[0]),now=epoch+3)
    with pytest.raises(ValueError):I.validate_decision(root,policy,b,now=epoch+6)
    with pytest.raises(ValueError):I.validate_submit(root,dict(entry_mechanistic_policy_decision=updated[0]),now=epoch+6)
    latest=I.read(I.root(root)/'current.json')
    latest=P.seal(dict(latest,revoked_overlays=[first['artifact_content_sha256']]))
    P.write(I.root(root)/'current.json',latest)
    with pytest.raises(ValueError,match='revoked'):
        I.validate_submit(root,dict(entry_mechanistic_policy_decision=updated[0]),now=epoch+3)


def test_next_session_carries_effective_registered_prompt(setup,monkeypatch):
    root,b,m,sid,v=setup
    at=datetime(2026,10,7,12,tzinfo=I.K.KST)
    overlay(root,b,{sid:v['registry_sha256']},at)
    T.prepare(root,'2026-10-07',m,b)
    result=T.auxiliary_report(root,'2026-10-07','2026-10-07',b,publish_policy=False)
    assert result['auxiliary_registry_bindings'][sid]==v['registry_sha256']
    assert result['scope_census']['new_ready']==128
    issued=json.loads((PC.directory(root,'2026-10-07')/'machine.json').read_text())
    monkeypatch.setattr(V.V4,'transition_parent',lambda *a:b)
    next_bundle=V.stage(root,'2026-10-07','2026-10-07',issued,result,target_date='2026-10-08',release_commit='a'*40)
    assert I.inherited(root,next_bundle)[sid]==v['registry_sha256']
    V.validate_sources(next_bundle,root)


def test_publish_requires_improvement_parent_and_preserves_initial_list(setup,monkeypatch):
    root,b,m,sid,v=setup
    T.prepare(root,'2026-10-07',m,b)
    actual=T.evaluate(root,'2026-10-07')
    path=T.directory(root,'2026-10-07')/'evaluation.json'
    clock=datetime(2026,10,8,10,tzinfo=I.K.KST)
    assert I.publish(root,path,expected_parent=None,confirm=I.AUTHORITY,now=clock)['status']=='incumbent_kept'
    report=copy.deepcopy(actual)
    report['scopes'][sid].update(improved=True,current=T.matrix([('WIN','PASS'),('FAIL_STOP','PASS')]),
        candidate=T.matrix([('WIN','PASS'),('FAIL_STOP','VETO')]))
    report=P.seal(report);P.write(path,report)
    P.write(T.directory(root,'2026-10-07')/'evaluations'/(report['artifact_content_sha256']+'.json'),report)
    monkeypatch.setattr(T,'evaluate',lambda *a:report)  # Publisher unit: reducer is tested independently.
    machine_before=copy.deepcopy(b['continuous_reversal']['machine_cells'])
    with pytest.raises(ValueError,match='parent_cas'):
        I.publish(root,path,expected_parent='f'*64,confirm=I.AUTHORITY,now=clock)
    result=I.publish(root,path,expected_parent=None,confirm=I.AUTHORITY,now=clock)
    assert result['changes'][sid]==v['registry_sha256']
    assert I.publish(root,path,expected_parent=None,confirm=I.AUTHORITY,now=clock)==result
    assert b['continuous_reversal']['machine_cells']==machine_before
    rolled=I.rollback(root,expected_parent=result['artifact_content_sha256'],reason='contract failure',confirm=I.AUTHORITY,now=clock)
    assert result['artifact_content_sha256'] in rolled['revoked_overlays']
    assert rolled['bindings'][sid]!=v['registry_sha256']


def test_sampled_failure_does_not_reopen_initial_machine_adoption(setup):
    root,b,m,sid,v=setup
    manifest=copy.deepcopy(b['continuous_reversal']['operating_manifest'])
    T.prepare(root,'2026-10-07',m,b)
    result=T.auxiliary_report(root,'2026-10-07','2026-10-07',b,publish_policy=False)
    assert result['comparison_complete'] is False
    issued=json.loads((PC.directory(root,'2026-10-07')/'machine.json').read_text())
    assert issued['operating_manifest']==manifest
    assert result['scope_census']['new_ready']==128 and result['scope_pending']==[]


def test_configured_calls_never_fall_back_to_legacy_full_queue(setup,monkeypatch):
    root,b,m,sid,v=setup
    monkeypatch.setattr(PC.L,'calls',lambda *a,**kw:pytest.fail('legacy full queue'))
    with pytest.raises(FileNotFoundError):PC.calls(root,'2026-10-07',transport=transport)
