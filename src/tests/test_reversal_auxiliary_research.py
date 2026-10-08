"""Research allowance isolation, shared custody, and explicit publication input."""
import copy
from datetime import datetime
import pytest
from src.engine.scalping import reversal_auxiliary_research as Q
from src.tests.test_reversal_auxiliary_tuning import setup, replay, parent, native, T, G, I, P, S, transport


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
