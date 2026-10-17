"""Strict offline risk-role interventions preserve the actual baseline."""
import copy
import pytest
from src.engine.scalping import reversal_auxiliary_risk_role_experiment as X
from src.engine.scalping import reversal_auxiliary_wire as W
from src.engine.scalping import reversal_auxiliary_research_wire as OLD_W
from src.engine.scalping import reversal_extended_union as U
from src.engine.scalping import continuous_reversal_postclose as P
from src.tests.test_reversal_auxiliary_causal_experiment import source as source_fixture,request


def source():
    logical,registry=source_fixture()
    for signal in logical['signals']:
        scale=logical['common_context']['confirmation_price']/signal['recent_observed_prices'][-1]['price']
        for row in signal['recent_observed_prices']:row['price']*=scale
        for field in ('context_facts','contradicting_facts'):
            for fact in logical['entry_setup_evidence_v1'][field]:
                if fact['id']==signal['ref']+'/observed_spread':fact['value']=signal['facts']['spread_pct']
    return logical,registry


def legacy(spread=.2):
    logical,registry=source()
    setup=logical['entry_setup_evidence_v1']
    setup['contradicting_facts']=[f for f in setup['contradicting_facts'] if not f['id'].endswith('/observed_spread')]
    setup['risk_fact_bindings'].pop('ENTRY_SPREAD_CONCERN',None)
    for signal in logical['signals']:
        signal['policy_id']='legacy_fixture_v1'
        signal['facts']['spread_pct']=spread
    return logical,registry


@pytest.mark.parametrize('codec',[None,W,OLD_W])
def test_baseline_exact_and_every_intervention_preserves_prompt_model(codec):
    logical,_=legacy()
    req=request(logical)
    if codec:req=codec.request(req,logical,codec.contract())
    before=copy.deepcopy((req,logical))
    assert X.project(logical,expected_contract=X.contract('BASELINE'))==logical
    assert X.transform_request(req,logical,contract=X.contract('BASELINE'))==req
    for mode in sorted(X.MODES-{'BASELINE'}):
        actual=X.transform_request(req,logical,contract=X.contract(mode))
        projected=X.project(logical,expected_contract=X.contract(mode))
        assert actual['candidate_input']==(codec.encode(projected)[0] if codec else projected)
        assert actual['candidate']['system_prompt']==req['candidate']['system_prompt']
        assert actual['control']==req['control']
        for key in ('model','max_output_tokens','reasoning_effort'):
            assert actual['candidate'][key]==req['candidate'][key]
        if projected==logical:
            assert actual==req
        else:
            assert actual['candidate']['offline_risk_role_contract']=={k:v for k,v in X.contract(mode).items() if k!='mode'}
            assert actual['paired_replay_id']!=req['paired_replay_id']
    assert (req,logical)==before


def test_role_moves_existing_fact_only_preserving_values_ids_and_bindings():
    logical,_=source();before=copy.deepcopy(logical)
    projected=X.project(logical,expected_contract=X.contract('ROLE'))
    a,b=logical['entry_setup_evidence_v1'],projected['entry_setup_evidence_v1']
    assert a['risk_fact_bindings']==b['risk_fact_bindings']
    moved=[f for f in a['contradicting_facts'] if f['id'].endswith('/observed_spread')]
    assert moved and all(f in b['context_facts'] for f in moved)
    for field in ('positive_facts',):assert a[field]==b[field]
    assert {k:v for k,v in logical.items() if k!='entry_setup_evidence_v1'}=={k:v for k,v in projected.items() if k!='entry_setup_evidence_v1'}
    assert logical==before


@pytest.mark.parametrize('spread',[0.,.2,.4])
def test_vocabulary_positive_exact_numeric_and_zero_stays_unbound(spread):
    logical,registry=legacy(spread)
    old=copy.deepcopy(logical['entry_setup_evidence_v1']['risk_fact_bindings'])
    projected=X.project(logical,expected_contract=X.contract('VOCAB'))
    setup=projected['entry_setup_evidence_v1']
    assert all(setup['risk_fact_bindings'][k]==v for k,v in old.items())
    if spread==0:
        assert projected==logical and 'ENTRY_SPREAD_CONCERN' not in setup['risk_fact_bindings']
    else:
        fid=setup['risk_fact_bindings']['ENTRY_SPREAD_CONCERN'][0]
        assert next(f for f in setup['context_facts'] if f['id']==fid)['value']==spread
        aliases=W.encode(projected)[2]
        raw=dict(assessed={aliases[s['ref']]:True for s in projected['signals']},
            screen=dict(verdict='CAUTION',risk='ENTRY_SPREAD_CONCERN',fact=aliases[fid]),confidence=50)
        assert W.decode(raw,projected,registry['base_arm'])['contradicting_fact_ids']==[fid]


def test_vocabulary_is_noop_for_existing_typed_input_and_path_is_separate():
    logical,_=source()
    assert X.project(logical,expected_contract=X.contract('VOCAB'))==logical
    assert X.project(logical,expected_contract=X.contract('ROLE_VOCAB'))==X.project(logical,expected_contract=X.contract('ROLE'))


def test_wide_legacy_keeps_liquidity_binding_and_combines_effective_role_change():
    logical,_=legacy(.4)
    ref=logical['signals'][0]['ref'];fid=ref+'/observable_wide_spread'
    fact=dict(id=fid,value=.4,source_feature='spread_pct',disposition='research_context_not_proven_invalidation')
    setup=logical['entry_setup_evidence_v1']
    setup['contradicting_facts'].append(fact)
    setup['risk_fact_bindings']['LIQUIDITY_FRAGILE']=[fid]
    vocab=X.project(logical,expected_contract=X.contract('VOCAB'))
    both=X.project(logical,expected_contract=X.contract('ROLE_VOCAB'))
    assert both==X.project(X.project(logical,expected_contract=X.contract('ROLE')),expected_contract=X.contract('VOCAB'))
    assert vocab['entry_setup_evidence_v1']['risk_fact_bindings']==both['entry_setup_evidence_v1']['risk_fact_bindings']
    assert both['entry_setup_evidence_v1']['risk_fact_bindings']['LIQUIDITY_FRAGILE']==[fid]
    assert fact in vocab['entry_setup_evidence_v1']['contradicting_facts']
    assert fact in both['entry_setup_evidence_v1']['context_facts']
    req=W.request(request(logical),logical,W.contract())
    assert X.transform_request(req,logical,contract=X.contract('VOCAB'))!=X.transform_request(req,logical,contract=X.contract('ROLE_VOCAB'))


def test_path_uses_current_ask_cost_once_and_can_cite_actual_zero_spread_geometry():
    logical,registry=legacy(0.)
    common=logical['common_context'];ask=common['entry_ask'];trade=common['confirmation_price']
    projected=X.project(logical,expected_contract=X.contract('ROLE_VOCAB_PATH'))
    setup=projected['entry_setup_evidence_v1'];ids=setup['risk_fact_bindings']['OBSERVED_TARGET_PROGRESS_CONCERN']
    assert 'observed_machine_signal' not in ids
    fid=next(i for i in ids if i.endswith('/target_gap_from_confirmation_trade_pct'))
    value=next(f['value'] for f in setup['context_facts'] if f['id']==fid)
    assert value==pytest.approx(100*(ask*1.004/.9977/trade-1))
    aliases=W.encode(projected)[2]
    raw=dict(assessed={aliases[s['ref']]:True for s in projected['signals']},
        screen=dict(verdict='CAUTION',risk='OBSERVED_TARGET_PROGRESS_CONCERN',fact=aliases[fid]),confidence=50)
    assert not U.validate_response(W.decode(raw,projected,registry['base_arm']),projected,arm=registry['base_arm'])
    assert 'ENTRY_SPREAD_CONCERN' not in setup['risk_fact_bindings']


def test_missing_price_history_remains_unknown_with_explicit_zero_observation_count():
    logical,_=legacy()
    for signal in logical['signals']:signal['recent_observed_prices']=[]
    projected=X.project(logical,expected_contract=X.contract('ROLE_VOCAB_PATH'))
    facts=projected['entry_setup_evidence_v1']['context_facts']
    assert not any(f['id'].endswith('/observed_recent_return_pct') for f in facts)
    assert next(f['value'] for f in facts if f['id'].endswith('/observed_recent_price_count'))==0


@pytest.mark.parametrize('defect',['future','order','objective','ask','spread','schema'])
def test_invalid_source_or_objective_never_repaired(defect):
    logical,_=legacy()
    if defect=='future':logical['signals'][0]['recent_observed_prices'][-1]['age_sec']=-1
    if defect=='order':logical['signals'][0]['recent_observed_prices'][-1]['age_sec']=100
    if defect=='objective':logical['common_context']['objective']['cost_rate']=0
    if defect=='ask':logical['signals'][0]['facts']['entry_ask']+=1
    if defect=='spread':logical['signals'][0]['facts']['spread_pct']=None
    if defect=='schema':logical['schema']='other'
    with pytest.raises(ValueError):X.project(logical,expected_contract=X.contract('ROLE_VOCAB_PATH'))


def test_tampered_contract_and_wire_do_not_silently_change_the_baseline():
    logical,_=legacy();req=W.request(request(logical),logical,W.contract())
    bad=copy.deepcopy(X.contract('ROLE'));bad['runtime_effect']=True
    with pytest.raises(ValueError):X.project(logical,expected_contract=bad)
    req['candidate']['citation_map_sha256']='f'*64
    with pytest.raises(ValueError,match='original_request_changed'):
        X.transform_request(req,logical,contract=X.contract('ROLE'))


@pytest.mark.parametrize('codec',[None,W,OLD_W])
def test_branch_conditional_effective_request_dedup_ignores_mode(codec):
    typed,_=source();old,_=legacy()
    for logical,left,right in [(typed,'ROLE','ROLE_VOCAB'),(old,'VOCAB','ROLE_VOCAB')]:
        req=request(logical)
        if codec:req=codec.request(req,logical,codec.contract())
        a=X.transform_request(req,logical,contract=X.contract(left))
        b=X.transform_request(req,logical,contract=X.contract(right))
        assert a==b and a['paired_replay_id']==b['paired_replay_id']
    req=request(typed)
    if codec:req=codec.request(req,typed,codec.contract())
    assert X.transform_request(req,typed,contract=X.contract('VOCAB'))==req


@pytest.fixture
def risk_campaign(tmp_path, monkeypatch):
    """One real v6 confirmation with its original compact baseline registry."""
    from src.engine.ai import offline_comparison_store as S
    from src.engine.scalping import reversal_auxiliary_registry as G
    from src.engine.scalping import reversal_auxiliary_research as Q
    from src.tests.test_offline_comparison_store import activate
    from src.tests.test_reversal_extended_policy import FIXTURES
    fixture = FIXTURES['manual_extended_f9a43c88911fdc0b']
    snapshot = [fixture['event'],fixture['source']]
    original = G.definition(U.V1.ARMS[1],input_version=U.VERSION)
    G.register(tmp_path,original)
    registry = G.compact_definition(original,research_wire_contract=OLD_W.contract())
    G.register(tmp_path,registry)
    sid = 'samsung|PRE|ALL|NXT'
    manifest = dict(scopes={sid:list(fixture['event']['branch_signals'])},detector_manifest_hash='a'*64)
    parent = dict(bundle_sha256='b'*64,continuous_reversal=dict(
        schema='continuous_reversal_policy_v6',operating_manifest=manifest))
    with S.Store(tmp_path) as store:
        activate(store)
        points = [dict(opportunity_key=U.opportunity(fixture['event']),scope=sid,
            symbol=fixture['event']['symbol'],day='2026-10-07',outcome={'status':'WIN'},
            snapshot_obj=store.put(snapshot))]
        partition = dict(records_object=store.put(points),records_sha256=P.digest(points))
    machine = P.seal(dict(source_date='2026-10-07',policy_schema='continuous_reversal_policy_v6',
        operating_manifest=manifest,partitions=[partition]))
    monkeypatch.setattr(Q,'current_bindings',lambda *a:{sid:registry['registry_sha256']})
    Q.authorize(tmp_path,confirm=Q.AUTHORITY,source_dates=['2026-10-07'],
        approval_reference='User: isolated risk-role research fixture')
    return tmp_path,parent,machine,sid,registry,snapshot


def test_actual_campaign_same_registry_modes_dedup_noop_and_never_publish(risk_campaign):
    from datetime import datetime
    from src.engine.ai import offline_comparison_store as S
    from src.engine.scalping import reversal_auxiliary_registry as G
    from src.engine.scalping import reversal_auxiliary_research as Q
    from src.engine.scalping import reversal_auxiliary_tuning as T
    from src.engine.scalping import reversal_auxiliary_intraday as I
    root,parent,machine,sid,registry,snapshot = risk_campaign
    baseline = G.request(snapshot,registry)
    common_positive = W.encode(G.production_request(snapshot,registry)[0])[2]['observed_machine_signal']
    before = copy.deepcopy((snapshot,registry))
    campaigns = {};evaluations = {};actual = [];new_calls = []
    def transport(req,timeout_sec):
        wire = req['candidate_input']
        risk = wire['entry_setup_evidence_v1']['risk_fact_bindings']
        if 'OBSERVED_TARGET_PROGRESS_CONCERN' in risk:
            screen = dict(verdict='CAUTION',risk='OBSERVED_TARGET_PROGRESS_CONCERN',
                fact=risk['OBSERVED_TARGET_PROGRESS_CONCERN'][0])
        else:
            screen = dict(verdict='PASS',risk='NO_BLOCKING_RISK',fact=common_positive)
        actual.append(req['paired_replay_id'])
        return dict(provider_provenance=dict(response_id='fixture-'+req['paired_replay_id']),
            candidate_response=dict(assessed={s['ref']:True for s in wire['signals']},
                screen=screen,confidence=50))
    for mode in ('BASELINE','ROLE','VOCAB','ROLE_VOCAB','ROLE_VOCAB_PATH'):
        experiment = 'risk-'+mode.lower()
        Q.configure(root,experiment=experiment,candidate=registry['registry_sha256'],
            scopes=[sid],seed='frozen',max_pairs=1,risk_role_mode=mode)
        campaign = T.prepare(root,'2026-10-07',machine,parent,research=experiment)
        campaigns[mode] = campaign
        path = Q.directory(root,experiment)/'campaigns'/(campaign['artifact_content_sha256']+'.json')
        pair = campaign['pairs'][0]
        assert pair['current_registry']==pair['candidate_registry']==registry['registry_sha256']
        with S.Store(root,readonly=True) as store:
            current = store.request(pair['requests']['current'])
            candidate = store.request(pair['requests']['candidate'])
            assert current==baseline
            assert current['candidate_input']==baseline['candidate_input']
            assert current['candidate']==baseline['candidate']
            assert candidate['candidate']['system_prompt']==baseline['candidate']['system_prompt']
            assert candidate['control']==baseline['control']
        called = T.calls(root,'2026-10-07',campaign_path=path,transport=transport)
        new_calls.append(called['new_calls'])
        evaluated = T.evaluate(root,'2026-10-07',campaign_path=path)
        evaluations[mode] = evaluated
        assert evaluated['scopes'][sid]['paired_points']==1
        assert evaluated['comparison_complete'] is True
        assert evaluated['operating_compatibility']=='requires_separate_input_implementation'
        assert evaluated['offline_input_experiment']==X.contract(mode)
        assert T.prepare(root,'2026-10-07',machine,parent,research=experiment)==campaign
        with S.Store(root,readonly=True) as store:
            assert len(list(store.owners(campaign['artifact_content_sha256'])))==2
            for rid in pair['requests'].values():
                state,obj = store.db.execute('SELECT state,result_obj FROM requests WHERE id=?',(rid,)).fetchone()
                assert state=='completed' and store.get(obj)['validation_errors']==[]
        evaluation_path = Q.directory(root,experiment)/'evaluations'/(evaluated['artifact_content_sha256']+'.json')
        with pytest.raises(ValueError,match='research_native_comparison_required'):
            I.publish(root,evaluation_path,expected_parent=None,confirm=I.AUTHORITY,
                now=datetime(2026,10,8,10,tzinfo=I.K.KST))
    assert new_calls==[1,1,0,0,1]
    ids = {mode:c['pairs'][0]['requests'] for mode,c in campaigns.items()}
    assert ids['BASELINE']['current']==ids['BASELINE']['candidate']==ids['VOCAB']['candidate']
    assert ids['ROLE']['candidate']==ids['ROLE_VOCAB']['candidate']
    assert len(set(actual))==3 and len(actual)==3
    assert evaluations['ROLE_VOCAB_PATH']['pairs'][0]['verdicts']['candidate']=='CAUTION'
    assert (snapshot,registry)==before


@pytest.mark.parametrize('options', [dict(native_current=True),dict(causal_prefix=True)])
def test_risk_experiment_config_cannot_claim_native_or_combine_inputs(risk_campaign,monkeypatch,options):
    from src.engine.scalping import reversal_auxiliary_research as Q
    root,_,_,sid,registry,_ = risk_campaign
    monkeypatch.setattr(Q,'native_contract',lambda:dict(proof='fixture'))
    with pytest.raises(ValueError,match='risk_role_input_unsupported'):
        Q.configure(root,experiment='unsupported',candidate=registry['registry_sha256'],scopes=[sid],
            seed='frozen',max_pairs=1,risk_role_mode='ROLE',**options)
    assert not (Q.directory(root,'unsupported')/'configuration.json').exists()


@pytest.mark.parametrize('value', [None,False,{},[], '',{'mode':'ROLE'},
    dict(X.contract('ROLE'),source_sha256='0'*64),dict(X.contract('ROLE'),allowed_runtime_apply=True)])
def test_present_malformed_risk_contract_cannot_be_silently_treated_as_baseline(risk_campaign,value):
    from src.engine.scalping import reversal_auxiliary_research as Q
    root,_,_,sid,registry,_ = risk_campaign
    configuration = Q.configure(root,experiment='tampered',candidate=registry['registry_sha256'],
        scopes=[sid],seed='frozen',max_pairs=1,risk_role_mode='ROLE')
    changed = P.seal(dict(configuration['config'],risk_role_contract=value))
    P.write(Q.directory(root,'tampered')/'configuration.json',P.seal(dict(configuration,config=changed)))
    with pytest.raises(ValueError,match='risk_role_'):
        Q.context(root,'tampered')
