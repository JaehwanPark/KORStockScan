"""Research allowance isolation, shared custody, and explicit publication input."""
import copy
from datetime import datetime
import pytest
from src.engine.scalping import reversal_auxiliary_research as Q
from src.tests.test_reversal_auxiliary_tuning import setup, replay, parent, native, T, G, I, P, S, transport


def test_cumulative_scope_extends_sources_without_resetting_or_adding_call_funds(setup):
    root, b, m, sid, v = setup
    old, path = campaign(setup)
    T.calls(root, '2026-10-07', campaign_path=path, transport=transport, max_new_calls=1)
    original = Q.grant(root)
    scope = Q.authorize_source_scope(root, source_dates=['2026-10-07', '2026-10-15'],
        as_of='2026-10-15', confirm=Q.SOURCE_SCOPE_AUTHORITY,
        approval_reference='User: cumulative source scope, no extra funds')
    assert Q.grant(root) == original
    assert Q.budget(root)['call_limit'] == 200
    with S.Store(root, readonly=True) as store:
        assert store.budget_used(original['budget_key']) == 1
    Q.configure(root, experiment='cumulative', candidate=v['registry_sha256'],
        scopes=[sid], seed='cumulative', max_pairs=3,
        source_scope_sha256=scope['artifact_content_sha256'])
    m = P.seal(dict(m, source_date='2026-10-15'))
    new = T.prepare(root, '2026-10-15', m, b, research='cumulative')
    assert new['research']['source_scope_sha256'] == scope['artifact_content_sha256']
    assert Q.validate_campaign(root, new)['budget_key'] == original['budget_key']
    assert Q.validate_campaign(root, old)['call_limit'] == 200
    missing = copy.deepcopy(new)
    missing['research'].pop('source_scope_sha256')
    with pytest.raises(ValueError, match='research_campaign_invalid'):
        Q.validate_campaign(root, missing)


@pytest.mark.parametrize('dates,as_of,confirm', [
    (['2026-09-28'], '2026-10-15', Q.SOURCE_SCOPE_AUTHORITY),
    (['2026-10-16'], '2026-10-15', Q.SOURCE_SCOPE_AUTHORITY),
    (['2026-10-15'], '2026-10-15', 'unapproved'),
    (['2099-10-15'], '2099-10-15', Q.SOURCE_SCOPE_AUTHORITY),
])
def test_cumulative_scope_cannot_expand_without_current_instruction(setup, dates, as_of, confirm):
    root, *_ = setup
    campaign(setup)
    with pytest.raises(ValueError, match='source_scope_invalid'):
        Q.authorize_source_scope(root, source_dates=dates, as_of=as_of,
            confirm=confirm, approval_reference='explicit instruction')


def test_source_scope_cannot_gain_runtime_authority_even_when_resealed(setup):
    root, *_ = setup
    campaign(setup)
    scope = Q.authorize_source_scope(root, source_dates=['2026-10-15'],
        as_of='2026-10-15', confirm=Q.SOURCE_SCOPE_AUTHORITY, approval_reference='User')
    bad = P.seal(dict(scope, allowed_runtime_apply=True))
    P.write(Q.root(root)/'source-scopes'/(bad['artifact_content_sha256']+'.json'), bad)
    with pytest.raises(ValueError, match='source_scope_invalid'):
        Q.source_scope(root, bad['artifact_content_sha256'])


def campaign(setup, *, name='trial', purpose='evaluation', include_keys=()):
    root,b,m,sid,v = setup
    Q.authorize(root,confirm=Q.AUTHORITY,source_dates=['2026-10-07'],approval_reference='User: additional 200 calls')
    Q.configure(root,experiment=name,candidate=v['registry_sha256'],scopes=[sid],seed='research-seed',
                max_pairs=50,purpose=purpose,include_keys=include_keys)
    c=T.prepare(root,'2026-10-07',m,b,research=name)
    return c,Q.directory(root,name)/'campaigns'/(c['artifact_content_sha256']+'.json')


def test_separate_allowance_exhaustion_and_unknown_attempt_retained(setup):
    root,b,m,sid,v=setup
    regular=T.prepare(root,'2026-10-07',m,b)
    c,path=campaign(setup)
    grant=Q.grant(root)
    with S.Store(root) as st:
        for n in range(100):st.db.execute('INSERT INTO attempt_budgets VALUES(?,?)',('old'+str(n),'postclose_auxiliary:2026-10-07'))
        for n in range(199):st.db.execute('INSERT INTO attempt_budgets VALUES(?,?)',('research'+str(n),grant['budget_key']))
    def uncertain(*a,**kw):raise TimeoutError()
    got=T.calls(root,'2026-10-07',campaign_path=path,transport=uncertain,max_new_calls=20)
    assert got['new_calls']==1 and got['call_budget']['used_after']==200
    assert T.calls(root,'2026-10-07',campaign_path=path,transport=lambda *a,**k:pytest.fail('retry'))['new_calls']==0
    assert T.calls(root,'2026-10-07',transport=lambda *a,**k:pytest.fail('ordinary cap'))['new_calls']==0
    assert T.read(T.directory(root,'2026-10-07')/'latest-campaign.json')==regular
    assert T.evaluate(root,'2026-10-07',campaign_path=path)['scopes'][sid]['candidate']['pass_win_rate'] is None


def test_researches_share_exact_cache_but_not_latest_or_allowance(setup):
    root,b,m,sid,v=setup
    c,p=campaign(setup,name='first');second,q=campaign(setup,name='second')
    assert c['artifact_content_sha256']!=second['artifact_content_sha256']
    assert c['pairs'][0]['requests']==second['pairs'][0]['requests']
    first=T.calls(root,'2026-10-07',campaign_path=p,transport=transport,max_new_calls=1)
    assert first['new_calls']==1
    T.calls(root,'2026-10-07',campaign_path=p,transport=transport)
    assert T.calls(root,'2026-10-07',campaign_path=q,transport=lambda *a,**k:pytest.fail('cache'))['new_calls']==0
    r=T.evaluate(root,'2026-10-07',campaign_path=p)
    assert r['research']['experiment']=='first'
    assert r['scopes'][sid]['paired_points']==len(c['pairs'])
    with pytest.raises(ValueError,match='immutable_conflict'):
        Q.authorize(root,confirm=Q.AUTHORITY,source_dates=['2026-10-07','2026-10-08'],approval_reference='changed')


def test_development_membership_cannot_be_promoted_or_leak_into_evaluation(setup):
    root,b,m,sid,v=setup
    c,p=campaign(setup,name='dev',purpose='development')
    T.calls(root,'2026-10-07',campaign_path=p,transport=transport)
    r=T.evaluate(root,'2026-10-07',campaign_path=p)
    ep=Q.directory(root,'dev')/'evaluations'/(r['artifact_content_sha256']+'.json')
    with pytest.raises(ValueError,match='development'):
        I.publish(root,ep,expected_parent=None,confirm=I.AUTHORITY,now=datetime(2026,10,8,10,tzinfo=I.K.KST))
    dev=[p['opportunity_key'] for p in c['pairs']]
    value=G.definition(v['base_arm'],prompt=v['prompt'],development_keys=dev)
    G.register(root,value)
    Q.configure(root,experiment='eval',candidate=value['registry_sha256'],scopes=[sid],seed='eval',max_pairs=50)
    evaluated=T.prepare(root,'2026-10-07',m,b,research='eval')
    assert not set(dev)&{p['opportunity_key'] for p in evaluated['pairs']}
    with pytest.raises(ValueError,match='config_invalid'):
        Q.configure(root,experiment='leak',candidate=value['registry_sha256'],scopes=[sid],seed='x',max_pairs=1,include_keys=dev)


def test_explicit_research_campaign_used_even_with_other_latest(setup,monkeypatch):
    root,b,m,sid,v=setup
    c,p=campaign(setup,name='candidate')
    T.calls(root,'2026-10-07',campaign_path=p,transport=transport)
    result=T.evaluate(root,'2026-10-07',campaign_path=p)
    other,q=campaign(setup,name='unrelated')
    P.write(T.directory(root,'2026-10-07')/'latest-campaign.json',other)
    path=Q.directory(root,'candidate')/'evaluations'/(result['artifact_content_sha256']+'.json')
    # The explicit campaign is checked even when the ordinary latest changed;
    # a normalized wording control cannot authorize replacement of native wire.
    with pytest.raises(ValueError,match='research_native_comparison_required'):
        I.publish(root,path,expected_parent=None,confirm=I.AUTHORITY,now=datetime(2026,10,8,10,tzinfo=I.K.KST))
    bad=copy.deepcopy(c);bad['research']['allowance_sha256']='bad';bad=P.seal(bad)
    P.write(p,bad)
    with pytest.raises(ValueError,match='research_campaign'):
        T.calls(root,'2026-10-07',campaign_path=p,transport=lambda *a,**k:pytest.fail('changed authority'))


def test_native_current_wire_is_distinct_and_matches_runtime_builder(setup):
    import json
    from src.tests.test_ai_engine_openai_transport import _build_engine
    from src.engine import ai_engine_openai as E
    from src.engine.scalping.ai_decision_quality import execute_openai_prompt_v2_candidate
    root,b,m,sid,v=setup
    c,p=campaign(setup)
    contract=Q.native_contract()
    with S.Store(root) as st:snapshot=st.get(c['pairs'][0]['snapshot_obj'])
    old=G.load(root,c['pairs'][0]['current_registry'])
    offline=Q.request(snapshot,old,contract);normalized=G.request(snapshot,old)
    projection=execute_openai_prompt_v2_candidate(offline,_request_projection_only=True)['provider_request_projection']
    assert projection['max_output_tokens']==contract['max_output_tokens']
    engine=_build_engine()
    request=engine._build_openai_response_request(prompt=old['prompt'],user_input=S.encode(normalized['candidate_input']).decode(),
        require_json=True,context_name='test',model_name=old['model'],temperature=contract['temperature'],
        max_output_tokens=contract['max_output_tokens'],reasoning_effort=contract['reasoning_effort'],
        schema_name=E.ENTRY_RISK_ADJUDICATION_SCHEMA,endpoint_name='analyze_target',symbol='-',cache_key='-',metadata_extra={})
    request.response_schema_override=normalized['candidate']['response_schema']
    wire=request.build_provider_payload(use_schema_registry=True)
    assert offline['candidate_input']==wire['input']
    assert offline['candidate']['system_prompt']==wire['instructions']
    assert offline['candidate']['schema_name']==wire['text']['format']['name']
    assert offline['paired_replay_id']!=normalized['paired_replay_id']
    repaired=Q.request(snapshot,old,contract,output_tokens_override=1024)
    assert repaired['candidate_input']==offline['candidate_input']
    assert repaired['candidate']['system_prompt']==offline['candidate']['system_prompt']
    assert repaired['candidate']['response_schema']==offline['candidate']['response_schema']
    assert repaired['candidate']['max_output_tokens']==1024
    assert repaired['paired_replay_id']!=offline['paired_replay_id']
    assert Q.request(snapshot,v,contract)==G.request(snapshot,v)
    with pytest.raises(ValueError,match='output_override_invalid'):
        Q.request(snapshot,old,contract,output_tokens_override=999)
    Q.configure(root,experiment='native',candidate=v['registry_sha256'],scopes=[sid],seed='native',max_pairs=50,native_current=True)
    native=T.prepare(root,'2026-10-07',m,b,research='native')
    path=Q.directory(root,'native')/'campaigns'/(native['artifact_content_sha256']+'.json')
    def replay_transport(req,timeout_sec):
        req=copy.deepcopy(req)
        if isinstance(req['candidate_input'],str):
            req['candidate_input']=json.loads(req['candidate_input'].split('\n\nReturn JSON only.')[0])
        return transport(req,timeout_sec)
    T.calls(root,'2026-10-07',campaign_path=path,transport=replay_transport)
    assert T.evaluate(root,'2026-10-07',campaign_path=path)['scopes'][sid]['paired_points']==len(native['pairs'])
    with pytest.raises(ValueError,match='native_wire_contract_changed'):
        Q.request(snapshot,old,dict(contract,max_output_tokens=999))


def test_corrected_unresolved_source_removed_from_research_cumulative(setup):
    root,b,m,sid,v=setup
    campaign(setup)
    Q.configure(root,experiment='resolved',candidate=v['registry_sha256'],scopes=[sid],seed='fixed',max_pairs=50,resolved_only=True)
    c=T.prepare(root,'2026-10-07',m,b,research='resolved')
    assert c['pairs']
    with S.Store(root) as st:
        revised=copy.deepcopy(m)
        for part in revised['partitions']:
            points=st.get(part['records_object'])
            for p in points:p['outcome']={'status':'UNRESOLVED','reason':'source_correction'}
            part['records_object']=st.put(points);part['records_sha256']=P.digest(points)
    revised=P.seal(revised)
    new=T.prepare(root,'2026-10-07',revised,b,research='resolved')
    assert new['pairs']==[]
    assert new['eligible_census']['outcome_not_evaluable']>0


def test_local_transport_exception_stops_batch_without_resetting_attempt(setup):
    root,b,m,sid,v=setup
    c,path=campaign(setup)
    def broken(*args,**kwargs):
        raise ImportError('local transport dependency')
    result=T.calls(root,'2026-10-07',campaign_path=path,transport=broken,max_new_calls=20)
    assert result['new_calls']==1
    assert result['call_budget']['used_after']==1
    with S.Store(root,readonly=True) as st:
        row=st.db.execute('''SELECT a.state,a.result_obj,a.attempt FROM attempts a
            JOIN attempt_budgets b ON a.attempt=b.attempt WHERE b.budget_key=?''',
            (Q.grant(root)['budget_key'],)).fetchone()
        assert row[0]=='reserved'
        # The failed response is durably landed even if the reservation cannot
        # become a completed provider result.
        landed=st.db.execute('SELECT result_obj FROM attempt_responses WHERE attempt=?',(row[2],)).fetchone()
        record=st.get(landed[0])
        assert record['error_type']=='ImportError'
        assert record['error_frames'][-1]['function']=='broken'


def test_research_calls_follow_frozen_selector_instead_of_storage_order(setup):
    root,b,m,sid,v=setup
    c,path=campaign(setup)
    with S.Store(root,readonly=True) as st:
        bykey={p['opportunity_key']:p for p in c['pairs']}
        expected=[rid for key in c['selector']['selected_keys']
                  for rid in bykey[key]['requests'].values()
                  if st.db.execute('SELECT state FROM requests WHERE id=?',(rid,)).fetchone()[0]=='planned']
        identities={rid:st.request(rid)['paired_replay_id'] for rid in expected}
    seen=[]
    def capture(req,timeout_sec):
        seen.append(req['paired_replay_id'])
        return transport(req,timeout_sec=timeout_sec)
    T.calls(root,'2026-10-07',campaign_path=path,transport=capture,max_new_calls=2)
    assert seen==[identities[rid] for rid in expected[:2]]


def test_explicit_topup_extends_same_budget_without_changing_old_campaign(setup):
    root,b,m,sid,v=setup
    c,path=campaign(setup)
    original=Q.grant(root)
    with S.Store(root) as st:
        for n in range(200):
            st.db.execute('INSERT INTO attempt_budgets VALUES(?,?)',('charged'+str(n),original['budget_key']))
    assert T.calls(root,'2026-10-07',campaign_path=path,transport=transport)['new_calls']==0
    with pytest.raises(ValueError,match='topup_authority_required'):
        Q.authorize_topup(root,confirm='unapproved',approval_reference='no')
    Q.authorize_topup(root,confirm=Q.TOPUP_AUTHORITY,approval_reference='User: additional 200, total 400')
    result=T.calls(root,'2026-10-07',campaign_path=path,transport=transport,max_new_calls=1)
    assert result['call_limit']==400 and result['call_budget']['used_after']==201
    assert Q.grant(root)==original and T.read(path)==c
    assert result['research_funding_sha256']==Q.budget(root)['funding_sha256']


def test_binding_capture_requires_complete_parent_scopes_and_intact_reader(setup):
    root,b,m,sid,v=setup
    campaign(setup)
    bindings=I.effective_bindings(root,b)
    receipt=root/'actual-reader.py';receipt.write_text('immutable reader fixture')
    value=P.seal(dict(parent_bundle_sha256=b['bundle_sha256'],family_sha256=b['continuous_reversal']['family_sha256'],
        reader_validated=True,bindings=bindings,source_receipts=[dict(path=str(receipt),sha256=P.file_hash(receipt))]))
    path=Q.root(root)/'current-bindings'/(b['bundle_sha256']+'.json');P.write(path,value)
    assert Q.current_bindings(root,b)==bindings
    incomplete=copy.deepcopy(value);incomplete['bindings'].pop(next(iter(bindings)))
    P.write(path,P.seal(incomplete))
    with pytest.raises(ValueError,match='capture_scope_changed'):Q.current_bindings(root,b)
    P.write(path,value);receipt.write_text('changed reader fixture')
    with pytest.raises(ValueError,match='capture_source_changed'):Q.current_bindings(root,b)


def test_continuation_preserves_400_campaign_and_unknown_charges(setup):
    root,b,m,sid,v=setup
    campaign(setup,name='old-200')
    Q.authorize_topup(root,confirm=Q.TOPUP_AUTHORITY,approval_reference='User: total 400')
    c,path=campaign(setup,name='old-400')
    with S.Store(root) as st:
        for i in range(398):
            st.db.execute('INSERT INTO attempt_budgets VALUES(?,?)',('old-or-uncertain-'+str(i),Q.grant(root)['budget_key']))
    old=Q.read(Q.root(root)/'allowance-topup-400.json')
    Q.authorize_continuation(root,confirm=Q.CONTINUATION_AUTHORITY,approval_reference='User: finish research, allow more; total 600')
    assert Q.budget(root)['call_limit']==600
    assert Q.read(Q.root(root)/'allowance-topup-400.json')==old
    assert Q.validate_campaign(root,c)['call_limit']==600
    result=T.calls(root,'2026-10-07',campaign_path=path,transport=transport,max_new_calls=1)
    assert result['call_budget']['used_after']==399 and T.read(path)==c
    Q.authorize_followup(root,confirm=Q.FOLLOWUP_AUTHORITY,approval_reference='User: complete study; announced total 800')
    assert Q.budget(root)['call_limit']==800
    assert Q.validate_campaign(root,c)['call_limit']==800
    with S.Store(root,readonly=True) as st:assert st.budget_used(Q.grant(root)['budget_key'])==399
    with pytest.raises(ValueError,match='authority_required'):
        Q.authorize_continuation(root,confirm='bad',approval_reference='bad')


def _fund_research_to_800(root):
    Q.authorize_topup(root, confirm=Q.TOPUP_AUTHORITY, approval_reference='User: total 400')
    Q.authorize_continuation(root, confirm=Q.CONTINUATION_AUTHORITY, approval_reference='User: total 600')
    Q.authorize_followup(root, confirm=Q.FOLLOWUP_AUTHORITY, approval_reference='User: total 800')


def _fund_research_to_1400(root):
    _fund_research_to_800(root)
    Q.authorize_discriminative(root, confirm=Q.DISCRIMINATIVE_AUTHORITY,
        approval_reference='User: additional 600; total 1400')


def test_next_study_grant_preserves_1363_spent_and_37_unspent_then_enforces_2000(setup):
    root, b, m, sid, v = setup
    old, old_path = campaign(setup, name='before-2000')
    _fund_research_to_1400(root)
    scope = Q.authorize_source_scope(root, source_dates=['2026-10-07', '2026-10-15'],
        as_of='2026-10-15', confirm=Q.SOURCE_SCOPE_AUTHORITY, approval_reference='User: cumulative')
    original = Q.grant(root)
    historical = {path:path.read_bytes() for path in Q.root(root).rglob('*.json')}
    with S.Store(root) as store:
        for i in range(1363):
            store.db.execute('INSERT INTO attempt_budgets VALUES(?,?)',
                ('prior-study-' + str(i), original['budget_key']))
    approval = 'User: increase allowance and execute next study; additional 600 total 2000'
    result = Q.authorize_next_study(root, confirm=Q.NEXT_STUDY_AUTHORITY, approval_reference=approval)
    assert result['call_limit'] == 2000 and result['budget_key'] == original['budget_key']
    assert Q.grant(root) == original and Q.source_scope(root, scope['artifact_content_sha256']) == scope
    assert all(path.read_bytes() == value for path,value in historical.items())
    assert T.read(old_path) == old and Q.validate_campaign(root, old)['call_limit'] == 2000
    with S.Store(root, readonly=True) as store:
        assert store.budget_used(original['budget_key']) == 1363
        assert result['call_limit'] - store.budget_used(original['budget_key']) == 637
    assert Q.authorize_next_study(root, confirm=Q.NEXT_STUDY_AUTHORITY, approval_reference=approval) == result
    with pytest.raises(ValueError, match='immutable_conflict'):
        Q.authorize_next_study(root, confirm=Q.NEXT_STUDY_AUTHORITY, approval_reference='different reference')
    new, path = campaign(setup, name='after-2000')
    assert new['call_limit'] == 2000 and Q.validate_campaign(root, new) == result
    with S.Store(root) as store:
        for i in range(636):
            store.db.execute('INSERT INTO attempt_budgets VALUES(?,?)',
                ('new-study-' + str(i), original['budget_key']))
    def uncertain(*args, **kwargs):
        raise TimeoutError('outcome unknown remains charged')
    called = T.calls(root, '2026-10-07', campaign_path=path, transport=uncertain, max_new_calls=1)
    assert called['new_calls'] == 1 and called['call_budget']['used_after'] == 2000
    assert called['research_funding_sha256'] == result['funding_sha256']
    assert T.calls(root, '2026-10-07', campaign_path=old_path,
        transport=lambda *a, **k:pytest.fail('budget must not reset'))['new_calls'] == 0


@pytest.mark.parametrize('confirm,approval', [
    ('unapproved', 'User'), (Q.NEXT_STUDY_AUTHORITY, ''), (Q.NEXT_STUDY_AUTHORITY, ' '),
])
def test_next_study_grant_requires_explicit_authority(setup, confirm, approval):
    root, *_ = setup
    campaign(setup)
    _fund_research_to_1400(root)
    with pytest.raises(ValueError, match='next_study_authority_required'):
        Q.authorize_next_study(root, confirm=confirm, approval_reference=approval)
    assert Q.budget(root)['call_limit'] == 1400
    assert not (Q.root(root) / 'allowance-topup-2000.json').exists()


def test_next_study_grant_cannot_skip_1400_predecessor(setup):
    root, *_ = setup
    campaign(setup)
    _fund_research_to_800(root)
    with pytest.raises(ValueError, match='previous_funding_required'):
        Q.authorize_next_study(root, confirm=Q.NEXT_STUDY_AUTHORITY, approval_reference='User')


@pytest.mark.parametrize('missing', [400, 600, 800, 1400])
def test_next_study_grant_rejects_any_missing_predecessor(setup, missing):
    root, *_ = setup
    campaign(setup)
    _fund_research_to_1400(root)
    Q.authorize_next_study(root, confirm=Q.NEXT_STUDY_AUTHORITY, approval_reference='User')
    (Q.root(root) / f'allowance-topup-{missing}.json').unlink()
    with pytest.raises(ValueError, match='research_.*(required|invalid)'):
        Q.budget(root)


@pytest.mark.parametrize('change', [
    {'previous_funding_sha256':'0' * 64}, {'from_limit':800}, {'call_limit':2001},
    {'budget_key':'research_auxiliary:new-date'}, {'authority':'unapproved'},
    {'allowed_runtime_apply':True}, {'approval_reference':''},
])
def test_next_study_grant_rejects_resealed_funding_changes(setup, change):
    root, *_ = setup
    campaign(setup)
    _fund_research_to_1400(root)
    Q.authorize_next_study(root, confirm=Q.NEXT_STUDY_AUTHORITY, approval_reference='User')
    path = Q.root(root) / 'allowance-topup-2000.json'
    P.write(path, P.seal(dict(Q.read(path), **change)))
    with pytest.raises(ValueError, match='next_study_funding_invalid'):
        Q.budget(root)


def _fund_research_to_2000(root):
    _fund_research_to_1400(root)
    Q.authorize_next_study(root, confirm=Q.NEXT_STUDY_AUTHORITY,
        approval_reference='User: additional 600; total 2000')


def test_direct_grant_preserves_1997_spent_3_remaining_and_enforces_2047(setup):
    root,*_=setup
    old,old_path=campaign(setup,name='before-direct')
    _fund_research_to_2000(root)
    before=Q.budget(root);original=Q.grant(root)
    historical={path:path.read_bytes() for path in Q.root(root).rglob('*.json')}
    with S.Store(root) as store:
        for i in range(1997):
            store.db.execute('INSERT INTO attempt_budgets VALUES(?,?)',
                ('prior-direct-'+str(i),original['budget_key']))
    approval='User: add 47 attempts; total 2047; direct 50-pair comparison'
    result=Q.authorize_direct_comparison(root,confirm=Q.DIRECT_AUTHORITY,approval_reference=approval)
    assert result['call_limit']==2047 and result['budget_key']==before['budget_key']
    assert Q.grant(root)==original and all(path.read_bytes()==value for path,value in historical.items())
    assert T.read(old_path)==old and Q.validate_campaign(root,old)==result
    with S.Store(root,readonly=True) as store:
        assert store.budget_used(result['budget_key'])==1997
        assert result['call_limit']-store.budget_used(result['budget_key'])==50
    assert Q.authorize_direct_comparison(root,confirm=Q.DIRECT_AUTHORITY,approval_reference=approval)==result
    with pytest.raises(ValueError,match='immutable_conflict'):
        Q.authorize_direct_comparison(root,confirm=Q.DIRECT_AUTHORITY,approval_reference='different reference')
    new,path=campaign(setup,name='direct-2047')
    assert new['call_limit']==2047 and Q.validate_campaign(root,new)==result
    with S.Store(root) as store:
        for i in range(49):
            store.db.execute('INSERT INTO attempt_budgets VALUES(?,?)',
                ('direct-study-'+str(i),original['budget_key']))
    def uncertain(*args,**kwargs):raise TimeoutError('uncertain attempt stays charged')
    called=T.calls(root,'2026-10-07',campaign_path=path,transport=uncertain,max_new_calls=1)
    assert called['new_calls']==1 and called['call_budget']['used_after']==2047
    assert called['research_funding_sha256']==result['funding_sha256']
    assert T.calls(root,'2026-10-07',campaign_path=old_path,
        transport=lambda *a,**k:pytest.fail('direct budget must not reset'))['new_calls']==0


@pytest.mark.parametrize('confirm,approval',[
    ('unapproved','User'),(Q.DIRECT_AUTHORITY,''),(Q.DIRECT_AUTHORITY,' '),
])
def test_direct_grant_requires_explicit_authority(setup,confirm,approval):
    root,*_=setup;campaign(setup);_fund_research_to_2000(root)
    with pytest.raises(ValueError,match='direct_authority_required'):
        Q.authorize_direct_comparison(root,confirm=confirm,approval_reference=approval)
    assert Q.budget(root)['call_limit']==2000
    assert not (Q.root(root)/'allowance-topup-2047.json').exists()


def test_direct_grant_cannot_skip_2000_predecessor(setup):
    root,*_=setup;campaign(setup);_fund_research_to_1400(root)
    with pytest.raises(ValueError,match='previous_funding_required'):
        Q.authorize_direct_comparison(root,confirm=Q.DIRECT_AUTHORITY,approval_reference='User')


@pytest.mark.parametrize('missing',[400,600,800,1400,2000])
def test_direct_grant_rejects_any_missing_predecessor(setup,missing):
    root,*_=setup;campaign(setup);_fund_research_to_2000(root)
    Q.authorize_direct_comparison(root,confirm=Q.DIRECT_AUTHORITY,approval_reference='User')
    (Q.root(root)/f'allowance-topup-{missing}.json').unlink()
    with pytest.raises(ValueError,match='research_.*(required|invalid)'):Q.budget(root)


@pytest.mark.parametrize('change',[
    {'previous_funding_sha256':'0'*64},{'from_limit':1400},{'call_limit':2048},
    {'budget_key':'research_auxiliary:new-date'},{'authority':'unapproved'},
    {'allowed_runtime_apply':True},{'approval_reference':''},
])
def test_direct_grant_rejects_resealed_funding_changes(setup,change):
    root,*_=setup;campaign(setup);_fund_research_to_2000(root)
    Q.authorize_direct_comparison(root,confirm=Q.DIRECT_AUTHORITY,approval_reference='User')
    path=Q.root(root)/'allowance-topup-2047.json'
    P.write(path,P.seal(dict(Q.read(path),**change)))
    with pytest.raises(ValueError,match='direct_funding_invalid'):Q.budget(root)


def _missing_key_attempt(root, value, *, defect=None):
    contract = Q.not_sent_executor_contract()
    with S.Store(root) as store:
        selected = {p['opportunity_key']:p for p in value['pairs']}
        candidates = [selected[key]['requests'][role]
            for key in value['selector']['selected_keys'] for role in ('current', 'candidate')]
        rid = next(ident for ident in candidates if store.db.execute(
            'SELECT state FROM requests WHERE id=?', (ident,)).fetchone()[0] == 'planned')
        attempt = store.reserve(rid, store.activation()['writer_epoch'],
            budget_key=Q.grant(root)['budget_key'], call_limit=200)
        record = dict(error_type='RuntimeError', transport_invoked=True,
            validation_errors=['provider_attempt_uncertain'], error_frames=[
                dict(file='reversal_auxiliary_tuning.py', function='calls', line=415),
                dict(file='ai_decision_quality.py', function='execute_openai_prompt_v2_candidate',
                    line=contract['executor_raise_line'])])
        if defect == 'timeout': record['error_type'] = 'TimeoutError'
        if defect == 'unknown_frame': record['error_frames'][-1]['line'] += 1
        if defect == 'result': record['result'] = {'provider_provenance':{'response_id':'actual-response'}}
        if defect != 'unlanded': store.finish(attempt, record)
        if defect == 'foreign_budget':
            store.db.execute('INSERT INTO attempt_budgets VALUES(?,?)', (attempt, 'another-budget'))
        if defect == 'ambiguous_prior':
            store.db.execute('INSERT INTO attempts VALUES(?,?,?,?,?,?,?)',
                ('a' * 32, rid, 'reserved', None, 'test', 0, 'provider'))
    proof = dict(contract, authority=Q.NOT_SENT_RECOVERY_AUTHORITY,
        approval_reference='User: continue approved research; exact guard proves no send', attempt_ids=[attempt])
    return rid, attempt, proof


def test_requeue_not_sent_preserves_attempt_charge_and_journal_then_allows_actual_attempt(setup):
    root, *_ = setup
    value, path = campaign(setup)
    rid, attempt, proof = _missing_key_attempt(root, value)
    with S.Store(root, readonly=True) as store:
        before = store.db.execute('SELECT * FROM attempts WHERE attempt=?', (attempt,)).fetchone()
    receipt = Q.requeue_not_sent(root, path, proof=proof)
    assert receipt['requeued_requests'] == 1 and receipt['budget_used_unchanged'] == 1
    assert receipt['requests'][0]['attempts'][0]['attempt_id'] == attempt
    with S.Store(root) as store:
        store.reconcile()
        assert store.db.execute('SELECT state FROM requests WHERE id=?', (rid,)).fetchone()[0] == 'planned'
        assert store.db.execute('SELECT * FROM attempts WHERE attempt=?', (attempt,)).fetchone() == before
        assert store.budget_used(Q.grant(root)['budget_key']) == 1
        assert store.checkpoint('auxiliary-not-sent-recovery:' + receipt['artifact_content_sha256']) == receipt
    assert Q.requeue_not_sent(root, path, proof=proof)['requeued_requests'] == 0
    result = T.calls(root, '2026-10-07', campaign_path=path, transport=transport, max_new_calls=1)
    assert result['new_calls'] == 1 and result['call_budget']['used_after'] == 2
    with S.Store(root, readonly=True) as store:
        assert store.db.execute('SELECT count(*) FROM attempts WHERE request_id=?', (rid,)).fetchone()[0] == 2


@pytest.mark.parametrize('defect', ['timeout', 'unknown_frame', 'unlanded', 'foreign_budget', 'ambiguous_prior'])
def test_requeue_not_sent_never_resets_genuine_or_ambiguous_uncertainty(setup, defect):
    root, *_ = setup
    value, path = campaign(setup)
    rid, attempt, proof = _missing_key_attempt(root, value, defect=defect)
    with pytest.raises(ValueError, match='not_sent_'):
        Q.requeue_not_sent(root, path, proof=proof)
    with S.Store(root, readonly=True) as store:
        assert store.db.execute('SELECT state FROM requests WHERE id=?', (rid,)).fetchone()[0] == 'reserved'
        assert store.budget_used(Q.grant(root)['budget_key']) == 1
    assert not list((Q.root(root) / 'not-sent-recoveries').glob('*.json'))


def test_requeue_not_sent_reconciles_actual_late_response_and_does_not_requeue(setup):
    root, *_ = setup
    value, path = campaign(setup)
    rid, attempt, proof = _missing_key_attempt(root, value)
    with S.Store(root) as store:
        store.land_response(attempt, dict(result=dict(provider_provenance={'response_id':'late-actual'})))
    assert Q.requeue_not_sent(root, path, proof=proof)['requeued_requests'] == 0
    with S.Store(root, readonly=True) as store:
        assert store.db.execute('SELECT state FROM requests WHERE id=?', (rid,)).fetchone()[0] == 'completed'
        assert store.budget_used(Q.grant(root)['budget_key']) == 1


@pytest.mark.parametrize('change', [
    {'authority':'unapproved'}, {'approval_reference':''}, {'executor_source_sha256':'0' * 64},
    {'executor_raise_line':1}, {'attempt_ids':['0' * 32]},
])
def test_requeue_not_sent_requires_exact_frozen_executor_and_attempt_authority(setup, change):
    root, *_ = setup
    value, path = campaign(setup)
    rid, _, proof = _missing_key_attempt(root, value)
    with pytest.raises(ValueError, match='not_sent_'):
        Q.requeue_not_sent(root, path, proof=dict(proof, **change))
    with S.Store(root, readonly=True) as store:
        assert store.db.execute('SELECT state FROM requests WHERE id=?', (rid,)).fetchone()[0] == 'reserved'


def test_real_transport_missing_credentials_fails_before_any_reservation(setup, monkeypatch):
    from src.engine.scalping import ai_decision_quality as executor
    root, *_ = setup
    _, path = campaign(setup)
    monkeypatch.setattr(executor, '_offline_openai_api_keys', lambda:[])
    monkeypatch.setattr(executor, 'execute_openai_prompt_v2_candidate',
        lambda *a, **k:pytest.fail('missing credentials must never reach executor'))
    with S.Store(root, readonly=True) as store:
        attempts_before = store.db.execute('SELECT count(*) FROM attempts').fetchone()[0]
    with pytest.raises(ValueError, match='research_credential_unavailable'):
        T.calls(root, '2026-10-07', campaign_path=path, max_new_calls=1)
    with S.Store(root, readonly=True) as store:
        assert store.db.execute('SELECT count(*) FROM attempts').fetchone()[0] == attempts_before
        assert store.budget_used(Q.grant(root)['budget_key']) == 0


def test_discriminative_extension_preserves_chain_scope_and_cumulative_charges(setup):
    root, b, m, sid, v = setup
    old, old_path = campaign(setup, name='before-extension')
    _fund_research_to_800(root)
    scope = Q.authorize_source_scope(root, source_dates=['2026-10-07', '2026-10-15'],
        as_of='2026-10-15', confirm=Q.SOURCE_SCOPE_AUTHORITY, approval_reference='User: cumulative')
    historical = {path: path.read_bytes() for path in Q.root(root).rglob('*.json')}
    original = Q.grant(root)
    with S.Store(root) as store:
        for i in range(800):
            store.db.execute('INSERT INTO attempt_budgets VALUES(?,?)',
                ('prior-completed-or-uncertain-' + str(i), original['budget_key']))
    assert T.calls(root, '2026-10-07', campaign_path=old_path, transport=transport)['new_calls'] == 0
    approval = 'User 2026-10-17: execute detailed study, additional 600 attempts, total 1400'
    grant = Q.authorize_discriminative(root, confirm=Q.DISCRIMINATIVE_AUTHORITY,
        approval_reference=approval)
    assert grant['call_limit'] == 1400 and grant['budget_key'] == original['budget_key']
    assert Q.grant(root) == original
    assert all(path.read_bytes() == content for path, content in historical.items())
    assert Q.source_scope(root, scope['artifact_content_sha256']) == scope
    assert T.read(old_path) == old and Q.validate_campaign(root, old)['call_limit'] == 1400
    assert Q.authorize_discriminative(root, confirm=Q.DISCRIMINATIVE_AUTHORITY,
        approval_reference=approval) == grant
    with pytest.raises(ValueError, match='immutable_conflict'):
        Q.authorize_discriminative(root, confirm=Q.DISCRIMINATIVE_AUTHORITY,
            approval_reference='different authority record must not replace the original')
    new, path = campaign(setup, name='after-extension')
    assert new['call_limit'] == 1400 and Q.validate_campaign(root, new) == grant
    def uncertain(*args, **kwargs):
        raise TimeoutError('provider outcome unknown')
    called = T.calls(root, '2026-10-07', campaign_path=path, transport=uncertain, max_new_calls=1)
    assert called['new_calls'] == 1 and called['call_budget']['used_after'] == 801
    assert called['research_funding_sha256'] == grant['funding_sha256']
    with S.Store(root) as store:
        for i in range(599):
            store.db.execute('INSERT INTO attempt_budgets VALUES(?,?)',
                ('other-experiment-or-date-' + str(i), original['budget_key']))
    assert T.calls(root, '2026-10-07', campaign_path=path,
        transport=lambda *a, **k: pytest.fail('exhausted shared budget'))['new_calls'] == 0
    with S.Store(root, readonly=True) as store:
        assert store.budget_used(original['budget_key']) == 1400


@pytest.mark.parametrize('confirm,approval', [
    ('unapproved', 'User'), (Q.DISCRIMINATIVE_AUTHORITY, ''),
    (Q.DISCRIMINATIVE_AUTHORITY, '   '), (Q.DISCRIMINATIVE_AUTHORITY, True),
])
def test_discriminative_extension_requires_explicit_authority(setup, confirm, approval):
    root, *_ = setup
    campaign(setup)
    _fund_research_to_800(root)
    with pytest.raises(ValueError, match='discriminative_authority_required'):
        Q.authorize_discriminative(root, confirm=confirm, approval_reference=approval)
    assert Q.budget(root)['call_limit'] == 800
    assert not (Q.root(root) / 'allowance-topup-1400.json').exists()


def test_discriminative_extension_cannot_skip_preceding_allowances(setup):
    root, *_ = setup
    campaign(setup)
    with pytest.raises(ValueError, match='previous_funding_required'):
        Q.authorize_discriminative(root, confirm=Q.DISCRIMINATIVE_AUTHORITY,
            approval_reference='User: additional 600')


@pytest.mark.parametrize('missing', [400, 600, 800])
def test_discriminative_extension_rejects_missing_chain_links(setup, missing):
    root, *_ = setup
    campaign(setup)
    _fund_research_to_800(root)
    Q.authorize_discriminative(root, confirm=Q.DISCRIMINATIVE_AUTHORITY, approval_reference='User')
    (Q.root(root) / f'allowance-topup-{missing}.json').unlink()
    with pytest.raises(ValueError, match='research_(previous_funding_required|followup_invalid|discriminative_funding_invalid)'):
        Q.budget(root)


@pytest.mark.parametrize('change', [
    {'schema': 'wrong'}, {'research_id': 'another-research'}, {'authority': 'unapproved'},
    {'previous_funding_sha256': '0' * 64}, {'from_limit': 600}, {'call_limit': 1401},
    {'budget_key': 'research_auxiliary:new-session'}, {'approval_reference': ''},
    {'approval_reference': '  '}, {'allowed_runtime_apply': True},
])
def test_discriminative_extension_rejects_resealed_funding_changes(setup, change):
    root, *_ = setup
    campaign(setup)
    _fund_research_to_800(root)
    Q.authorize_discriminative(root, confirm=Q.DISCRIMINATIVE_AUTHORITY, approval_reference='User')
    path = Q.root(root) / 'allowance-topup-1400.json'
    P.write(path, P.seal(dict(Q.read(path), **change)))
    with pytest.raises(ValueError, match='discriminative_funding_invalid'):
        Q.budget(root)


def test_format_only_control_retains_exact_original_request(setup,monkeypatch):
    from src.engine.scalping import reversal_auxiliary_research_wire as W
    root,b,m,sid,v=setup
    campaign(setup,name='funding')
    monkeypatch.setattr(W,'request',lambda req,*a:dict(req,paired_replay_id='compact-'+req['paired_replay_id']))
    Q.configure(root,experiment='format-only',candidate=v['registry_sha256'],scopes=[sid],seed='x',max_pairs=1,
                compact_wire=True,compact_candidate_only=True)
    c=T.prepare(root,'2026-10-07',m,b,research='format-only');pair=c['pairs'][0]
    with S.Store(root) as store:
        snapshot=store.get(pair['snapshot_obj'])
        for role in ('current','candidate'):
            registry=G.load(root,pair[role+'_registry'])
            expected=T.expected_request(root,c,pair,role,snapshot,registry)
            actual=store.request(pair['requests'][role])
            assert actual['paired_replay_id']==expected['paired_replay_id']
            assert actual['paired_replay_id'].startswith('compact-') == (role=='candidate')
