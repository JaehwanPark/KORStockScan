"""Structural paths through real internal producers, with external IO frozen."""
from copy import deepcopy
from datetime import datetime
import hashlib
import json
from types import SimpleNamespace
import pytest

from src.engine.scalping import pre_submit_delay_initial_policy as delay
from src.engine.scalping import reversal_auxiliary_registry as registry
from src.engine.scalping import universal_trailing_replay as replay
from src.engine.lifecycle import research_storage as storage
from src.engine.automation.main_trailing_population_aggregation import aggregate


def test_sparse_horizons_compete_on_their_own_pairs_without_holdout_reselection():
    train=[dict(identity=str(i),pairs={30:10.,180:40.}) for i in range(240)]
    train.append(dict(identity='30-only',pairs={30:10.}))
    held=[dict(identity='held',pairs={30:10.,180:40.})]
    result=delay._selection(train,held)
    assert result['delay_sec']==180
    assert result['candidate_train_stats']['180']['n']==240
    assert result['candidate_train_stats']['30']['n']==241
    assert delay._selection(train,[dict(identity='h',pairs={30:50.})])['delay_sec'] is None
    assert delay._selection(train,[dict(identity='h',pairs={180:-40.})])['delay_sec']==0


def test_provider_request_identity_is_captured_from_actual_wire_with_only_transport_frozen(tmp_path,monkeypatch):
    from src.tests.test_ai_engine_openai_transport import _build_engine
    from src.engine.scalping import ai_decision_trace as writer
    engine=_build_engine();wire={}
    response=dict(schema='entry_setup_risk_adjudication_v1',risk_verdict='PASS',risk_codes=['NO_BLOCKING_RISK'],
        supporting_fact_ids=['first_price_uptick'],contradicting_fact_ids=[],confidence=60)
    def external_provider(**kwargs):
        wire.update(kwargs)
        return SimpleNamespace(id='frozen-response',model='gpt-5.4-nano',output_text=json.dumps(response))
    engine.client=SimpleNamespace(responses=SimpleNamespace(create=external_provider))
    engine._try_bedrock_primary_provider=lambda **kwargs:None
    monkeypatch.setattr(writer,'DATA_DIR',tmp_path);monkeypatch.setattr(writer,'trace_enabled',lambda:True)
    result=engine._call_openai_safe('Frozen prompt','{}',require_json=True,context_name='structural-proof',
        model_override='gpt-5.4-nano',schema_name='entry_setup_risk_adjudication_v1',endpoint_name='analyze_target',
        symbol='005930',transport_mode_override='http',
        auxiliary_identity_context={'policy_version':'continuous_reversal_policy_v4'})
    assert result['risk_verdict']=='PASS'
    identity=registry.validate_identity(engine._consume_last_transport_meta()['entry_auxiliary_policy_identity'])
    assert identity['semantic']['prompt']==wire['instructions']
    assert identity['semantic']['model']==wire['model']
    assert len(identity['provenance']['request_capture_sha256'])==64
    first={'format':{'schema':{'properties':{'supporting_fact_ids':{'items':{'enum':['source-a']}}}}}}
    other=deepcopy(first);other['format']['schema']['properties']['supporting_fact_ids']['items']['enum']=['source-b']
    base=dict(instructions='Same prompt',model='gpt-5.4-nano',text=first)
    context={'policy_version':'continuous_reversal_policy_v4'}
    assert registry.provider_identity(base,context)['identity_sha256']==registry.provider_identity({**base,'text':other},context)['identity_sha256']


def test_wire_fact_alias_is_request_provenance_not_a_new_timing_policy():
    from src.engine.scalping import reversal_auxiliary_registry as registry
    from src.engine.scalping import continuous_reversal_postclose as postclose
    schema = {'format': {'schema': {'properties': {'screen': {'anyOf': [
        {'properties': {'fact': {'type': 'string', 'enum': ['f6']},
                        'risk': {'enum': ['NO_BLOCKING_RISK']},
                        'verdict': {'enum': ['PASS']}}}]}}}}}
    payload = dict(instructions='Same reviewed prompt', model='gpt-5.4-nano', text=schema)
    context = dict(policy_version='continuous_reversal_policy_v6', registry_sha256='a'*64)
    other = deepcopy(payload)
    other['text']['format']['schema']['properties']['screen']['anyOf'][0]['properties']['fact']['enum'] = ['f7']
    one = registry.provider_identity(payload, context)
    two = registry.provider_identity(other, context)
    assert one['identity_sha256'] == two['identity_sha256']
    assert one['provenance']['response_schema_sha256'] != two['provenance']['response_schema_sha256']
    # Historical identities remain immutable and valid. Only the additional
    # research equivalence key normalizes their original request-local aliases.
    historical = deepcopy(one)
    historical['semantic']['response_contract'] = schema
    historical['identity_sha256'] = postclose.digest(historical['semantic'])
    original = deepcopy(historical)
    assert registry.timing_compatibility_identity(historical) == one['identity_sha256']
    assert historical == original
    for field, value in [('risk', 'STALE_SOURCE'), ('verdict', 'VETO'), ('fact', 'literal_contract_fact')]:
        changed = deepcopy(other)
        changed['text']['format']['schema']['properties']['screen']['anyOf'][0]['properties'][field]['enum'] = [value]
        assert registry.provider_identity(changed, context)['identity_sha256'] != one['identity_sha256']
    assert registry.provider_identity({**payload, 'instructions': 'Other prompt'}, context)['identity_sha256'] != one['identity_sha256']


@pytest.mark.parametrize('n',[60,240])
def test_new_classifier_generation_does_not_require_future_hash_on_original_ai_holding_pin(tmp_path,n):
    from src.tests.test_main_trailing_partitioned_research import minimal
    from src.engine.scalping import trailing_situation_policy as typed
    from src.engine.scalping.trailing_mechanical_policy import baseline_receipt
    from src.engine.automation.main_trailing_situation_aggregation import research
    parent=baseline_receipt({},source='operator_directed_m1_baseline')
    values=deepcopy(parent['market_values']);values['REGULAR']['SCALP_TRAILING_LIMIT_WEAK']=.1
    candidates={'candidate':values}
    config=dict(schema=typed.CLASSIFIER_SCHEMA,window_bars=2,trained_through=0,
        thresholds=dict(range_min=.5,spread_min=.5,trend_return_min=.2,trend_efficiency_min=.5,vwap_min=0,rebound_min=.5))
    config['classifier_sha256']=delay.digest(config)
    part=minimal(n)
    from src.tests.test_main_all_scope_trailing import at
    start=at('2026-09-29T09:00:00')
    original={}
    for index,(identity,context) in enumerate(part['population_context'].items()):
        clock=start+(index//(n//10))*86400+(index%(n//10))*5
        features=dict(range_pct=1.,return_pct=.1,trend_efficiency=.2,vwap_distance_pct=-1.,spread_pct=.1,rebound_pct=.1)
        source=dict(status='ready',window_bars=2,known_at=clock-1,features=features,
            feature_sha256=delay.digest(features),source_sha256='a'*64)
        pin=typed.pin_context(source,position_key=identity,entry_at=clock,classifier=config)
        original[identity]=deepcopy(pin)
        context.update(entry_at=clock,observation_end_at=clock+2,completion_at=clock+2,
            actual_cost_available_at=clock+2,
            evidence_kind='actual_completed',buy_basis_krw=1000,entry_context=source,
            operating_ai_required=True,situation_pin=pin)
        for sha,row in part['minimal_results'][identity].items():
            pnl=0 if sha==part['candidate_aliases']['incumbent'] else 5
            row.update(modeled_net_pnl_krw=pnl,actual_pnl_krw=0,slippage_net_pnl_krw=[pnl,pnl,pnl])
    resident=typed.research_registered_grid([part],grid=[config],candidates=candidates,
        parent_values=parent['market_values'],parent_classifier_parameters=parent['classifier_parameters'],
        evaluation=replay.common_evaluation([part]))
    external=research(lambda:iter([part]),grid=[config],candidates=candidates,
        parent_values=parent['market_values'],parent_classifier_parameters=parent['classifier_parameters'],
        evaluation=aggregate(lambda:iter([part]),output_root=tmp_path),output_root=tmp_path)
    for result in (resident,external):
        assert result['classifier']['classifier_sha256']!=config['classifier_sha256']
        assert result['cells']['actual_completed|REGULAR|HIGH_VARIABILITY']['disposition']=='research_candidate_requires_existing_selector_review'
    assert resident['classifier_generation_sha256']==external['classifier_generation_sha256']
    assert all(c['situation_pin']==original[i] for i,c in part['population_context'].items())


def test_legacy_algorithm_remains_verifiable_after_json_roundtrip(tmp_path,monkeypatch):
    from src.tests.test_pre_submit_delay_tuning import _price_pattern_fixture
    from src.engine.scalping import pre_submit_delay_tuning as source
    _price_pattern_fixture(tmp_path,monkeypatch,[{'prices':{0:10000,30:9900,180:9800}} for _ in range(10)])
    snapshot=source.SourceSnapshot.load('2026-10-02',tmp_path)
    try:
        report,policy=delay.build_initial(snapshot.rows,source_date='2026-10-02',publication_date='2026-10-03',
            effective_date='2026-10-05',source_sha256=snapshot.source['sha256'],code_contract_sha256=delay.code_contract(),
            _algorithm=delay.LEGACY_ALGORITHM,_projection_contract='d'*64)
    finally:snapshot.budget_claim.close()
    delay.validate(json.loads(json.dumps(policy)),json.loads(json.dumps(report)),target_date='2026-10-05')


@pytest.mark.parametrize('n',[60,240])
def test_healthy_native_rows_survive_one_bad_row_and_reach_prepared_lookup(tmp_path,monkeypatch,n):
    from src.tests.test_pre_submit_delay_tuning import _price_pattern_fixture
    from src.engine.scalping import pre_submit_delay_tuning as source
    proof=registry.provider_identity(dict(instructions='Frozen entry prompt',model='gpt-5.4-nano',
        text={'format':'json'},max_output_tokens=1024),dict(policy_version='continuous_reversal_policy_v1'))
    fields=dict(anchor_contract_version=3,evaluation_attempt_id='native-original',entry_mechanistic_policy_sha256='a'*64,
        entry_ai_soft_policy_sha256=proof['identity_sha256'],entry_auxiliary_policy_identity=proof,
        entry_auxiliary_policy_identity_version=registry.IDENTITY_SCHEMA)
    _price_pattern_fixture(tmp_path,monkeypatch,[{'prices':{0:10000,30:9900},'offset':i*60,'commit_overrides':fields} for i in range(n)]
        +[{'prices':{0:10000,30:9900},'offset':n*60,'commit_overrides':{**fields,'evaluation_attempt_id':'','request_id':''}}])
    # Run the real logger's string-field boundary, not a dict-only fixture.
    from src.engine.pipeline_event_summary import execution_projection_identity
    original=next((tmp_path/'threshold_cycle').glob('date=*/family=pre_submit_delay/*.jsonl'))
    wire=[]
    for event in map(json.loads,original.read_text().splitlines()):
        f=event['fields']
        if isinstance(f.get('entry_auxiliary_policy_identity'),dict):
            f['entry_auxiliary_policy_identity']=json.dumps(f['entry_auxiliary_policy_identity'],sort_keys=True,separators=(',',':'))
        event['fields']={k:str(v) for k,v in f.items()}
        event['execution_source_event_sha256']=execution_projection_identity(event);wire.append(event)
    original.write_text(''.join(json.dumps(e)+'\n' for e in wire))
    snapshot=source.SourceSnapshot.load('2026-10-02',tmp_path)
    try:
        report,policy=delay.build_initial(snapshot.rows,source_date='2026-10-02',publication_date='2026-10-10',
            effective_date='2026-10-12',source_sha256=snapshot.source['sha256'],code_contract_sha256=delay.code_contract())
    finally:snapshot.budget_claim.close()
    assert report['census']['raw_commit_n']==n+1
    assert len(report['partitions'][0]['qualified_ids'])==n
    delay.validate(policy,report,target_date='2026-10-12')
    assert any(c['delay_sec']==30 for c in policy['cells'].values())
    prepared=delay.PreparedPolicy.from_artifacts(policy,report,target_date='2026-10-12')
    assert prepared.lookup(target_date='2026-10-12',market='REGULAR',kind='ALL',parents=('a'*64,proof['identity_sha256']))['delay_sec']==30


def test_identity_tracks_meaning_and_compose_main_observer_preserve_original_request(tmp_path):
    from src.tests.test_continuous_reversal import family_reports,rows,K
    from src.tests.test_mechanistic_entry_runtime_policy import initial
    from src.engine.scalping import continuous_reversal_policy as compose
    from src.engine.scalping import mechanistic_entry_runtime_policy as native
    from src.engine.sniper_state_handlers import _machine_primary_entry_provenance_fields
    from src.engine.scalping import pre_submit_delay_observation as observer
    initial(tmp_path);m,a=family_reports();compose.publish(tmp_path,'2026-10-06','2026-10-06',m,a)
    selected=native.load_effective(data_root=tmp_path,target_date='2026-10-07')
    state=K.ReversalState()
    for r in rows([100,99,100]):state.observe(r,symbol='005930',venue='KRX',session='KRX_REGULAR')
    assessment,inp,_,_=compose.assess(selected['continuous_reversal'],state.snapshot(),symbol='005930',session='KRX_REGULAR')
    payload=dict(instructions='Frozen entry prompt',model='gpt-5.4-nano',text={'format':'json'})
    one=registry.provider_identity(payload,dict(policy_version='continuous_reversal_policy_v1',overlay_sha256='a'*64))
    two=registry.provider_identity(payload,dict(policy_version='continuous_reversal_policy_v1',overlay_sha256='b'*64))
    assert one['identity_sha256']==two['identity_sha256']
    assert one['identity_sha256']!=registry.provider_identity({**payload,'instructions':'Other prompt'},
        dict(policy_version='continuous_reversal_policy_v1'))['identity_sha256']
    context=dict(continuous_reversal_assessment=assessment,continuous_reversal_input=inp,
        continuous_reversal_arm='reversal_citation_v6',machine_bundle_sha256=selected['bundle_sha256'],
        entry_auxiliary_policy_identity=one)
    response=dict(schema='entry_setup_risk_adjudication_v1',risk_verdict='PASS',risk_codes=['NO_BLOCKING_RISK'],
        supporting_fact_ids=['first_price_uptick','observed_price_decline'],contradicting_fact_ids=[],confidence=60)
    result=compose.compose(response,context)
    assert result['entry_ai_effective_assessment']['effective_verdict']=='PASS'
    provenance=_machine_primary_entry_provenance_fields(result)
    assert provenance['entry_auxiliary_policy_identity']==one
    records=[];observer.configure_sink(lambda *args,**kwargs:records.append((args[-1],kwargs['fields'])) or {'status':'queued'})
    observer._ACTIVE.clear();observer._HEAPS.clear();observer._RECENT.clear()
    from src.engine.scalping.scanner_async_eval import _immutable_mapping
    original=SimpleNamespace(ai_payload=_immutable_mapping({**result,'machine_observation_sha256':'a'*64,'evaluation_attempt_id':'attempt-1'}),
        code='005930',request_id='original-request',completed_epoch=10.,deadline_epoch=11.,error_type=None,
        prepared_context={'ws_data':{'market_data_transport_epoch':7}},origin_fields={'market_session_bucket':'KRX_REGULAR'})
    try:
        assert observer.register_pass_result(original)
        assert records[0][1]['request_id']=='original-request'
        assert records[0][1]['entry_ai_soft_policy_sha256']==one['identity_sha256']
        original.completed_epoch=12.
        assert observer.register_pass_result(original) is False
        response['supporting_fact_ids']=['future_rebound']
        assert compose.compose(response,context)['entry_ai_effective_assessment']['effective_verdict']!='PASS'
    finally:
        observer.configure_sink(None);observer._ACTIVE.clear();observer._HEAPS.clear();observer._RECENT.clear()


def test_unsupported_candidate_does_not_erase_healthy_pairs_and_true_loss_is_distinct(tmp_path):
    from src.tests.test_main_trailing_partitioned_research import minimal
    part=minimal();part['eligible_ids']=list(part['population_context'])
    good=replay.common_evaluation([part])
    extended=deepcopy(part);extended['candidate_aliases']['unsupported']='c'*64
    extended['common_ids']=[]
    for identity,rows in extended['minimal_results'].items():
        rows['c'*64]=dict(modeled_net_pnl_krw=None,actual_pnl_krw=None,slippage_net_pnl_krw=None)
    new=aggregate(lambda:iter([extended]),output_root=tmp_path)
    old=good['strata']['enter_pass_opportunity_cf'];cohort=new['strata']['enter_pass_opportunity_cf']
    for split in ('train','holdout'):
        assert list(storage.iter_tree(tmp_path,cohort[split+'_ids_ref']))==old[split+'_ids']
        assert cohort['metrics']['candidate'][split]['paired_ev_pct']==old['metrics']['candidate'][split]['paired_ev_pct']
        assert cohort['metrics']['unsupported'][split]['n']==0
    first=next(iter(part['minimal_results']))
    part['minimal_results'][first]['a'*64]['modeled_net_pnl_krw']=10
    part['minimal_results'][first]['b'*64]['modeled_net_pnl_krw']=9
    metric=replay.common_evaluation([part])['strata']['enter_pass_opportunity_cf']['metrics']['candidate']['train']
    assert first in metric['worsened_ids'] and first not in metric['large_loss_worsened_ids']
    part['minimal_results'][first]['b'*64]['modeled_net_pnl_krw']=-1
    assert first in replay.common_evaluation([part])['strata']['enter_pass_opportunity_cf']['metrics']['candidate']['train']['large_loss_worsened_ids']


@pytest.mark.parametrize('verdict',["PASS","VETO"])
def test_holding_original_requests_pre_signal_replay_and_segment_rollover(tmp_path,monkeypatch,verdict):
    from src.engine.ai import holding_exit_vote as vote
    from src.engine.ai import holding_vote_replay_source as evidence
    from src.engine.scalping import ai_decision_trace as writer
    from src.tests.test_holding_path_vote_replay import _events,BUY_IDENTITY
    from src.tests.test_main_all_scope_trailing import position,quote,vector,at
    root=tmp_path/'data';out=tmp_path/'out';out.mkdir()
    monkeypatch.setattr(writer,'DATA_DIR',root);monkeypatch.setattr(writer,'trace_enabled',lambda:True)
    clock=at('2026-10-08T09:00:00')
    monkeypatch.setattr(writer,'_now',lambda:datetime.fromtimestamp(clock,__import__('zoneinfo').ZoneInfo('Asia/Seoul')))
    rows=_events('EXIT_TRAILING_TP','REGULAR',verdicts=(verdict,verdict),position_key='main:1',session_key='2026-10-08',base_at=clock+2)
    path=vote.path_vote_store_path(root,'main:1')
    for index,row in enumerate(rows):
        payload=dict(input_schema=vote.PATH_PROMPT_VERSION,requested_paths=['EXIT_TRAILING_TP'],
            position_key='main:1',buy_fill_identity=BUY_IDENTITY,market='REGULAR',session_key='2026-10-08',
            position={'buy_price':100,'curr_price':100},source={'route':'KRX','transport_epoch':'1'},
            flow={},quote={},source_quality={'allowed':True})
        hashes=vote.path_vote_input_hashes(payload,model=row['model']);payload['input_snapshot_id']=hashes['input_snapshot_id']
        raw=json.dumps(payload,ensure_ascii=True,separators=(',',':'))
        prompt='Actual wrapped holding prompt'
        captured=writer.capture_ai_request(prompt=prompt,user_input=raw,endpoint_name='holding_path_vote',
            request_id='original-'+str(index),symbol='123456',require_json=True,model=row['model'],schema_name=vote.PATH_PROMPT_VERSION,
            metadata={'holding_provider_contract':dict(instructions=prompt,model=row['model'],text={'format':'json'})})
        assert captured['ai_request_envelope_sha256']
        row.update(request_payload_sha256=hashes['request_payload_sha256'],input_snapshot_id=hashes['input_snapshot_id'],
            prompt_sha256=captured['ai_prompt_sha256'],actual_request_reference=dict(schema='holding_actual_request_reference_v1',
                date=captured['ai_input_payload_store_date'],request_id=captured['ai_decision_trace_id'],
                request_envelope_sha256=captured['ai_request_envelope_sha256'],payload_sha256=captured['ai_input_payload_sha256'],
                prompt_sha256=captured['ai_prompt_sha256'],response_sha256='e'*64,replay_exact=True))
        monkeypatch.setattr(vote.time,'time',lambda row=row:row['received_at']+.1)
        assert vote.append_path_events_file(path,'main:1',[row])[1]=='appended'
    source=dict(schema=evidence.SCHEMA,required=True,position_key='main:1',buy_fill_identity=BUY_IDENTITY,
        store_name=path.name,market='REGULAR',model=rows[0]['model'],policy=vote.PATH_POLICY_BY_MARKET[('EXIT_TRAILING_TP','REGULAR')],
        coverage_started_at=clock,coverage_checked_at=clock,coverage_complete=True,observed_at=clock)
    source['policy_sha256']=vote.input_snapshot_id(source['policy'])
    reference=evidence.assemble_votes(root,out,source,{})
    assert reference['status']=='source_bound'
    assert all(r['actual_input_verified'] for r in storage.iter_tree(out,reference['events_ref']))
    # Exact plain/gzip aliases are the same request, not a source conflict.
    import gzip
    for directory in ('ai_decision_payloads','ai_decision_requests','ai_decision_prompts'):
        for original in (root/directory).glob('*.jsonl'):
            with gzip.open(str(original)+'.gz','wb') as compressed:compressed.write(original.read_bytes())
    alias_root=out/'aliases';alias_root.mkdir()
    alias=evidence.assemble_votes(root,alias_root,source,{})
    assert alias['status']=='source_bound'
    assert all(r['actual_input_verified'] for r in storage.iter_tree(alias_root,alias['events_ref']))
    quotes=[quote(i+1,datetime.fromtimestamp(clock+i,__import__('zoneinfo').ZoneInfo('Asia/Seoul')).strftime('%Y-%m-%dT%H:%M:%S'),bid=100 if i<30 else 100.5-(i-30)*.002,peak=100 if i<30 else 101) for i in range(90)]
    for event in quotes:
        event['holding_vote_source']={**source,'coverage_checked_at':event['known_at'],'observed_at':event['known_at']}
        event['source_sha256']=replay.quote_source_digest(event)
    pos={**position(),'operating_ai_required':True,'holding_vote_replay_ref':reference}
    result=replay._replay(pos,quotes,vector())
    assert result['status']=='modeled_full_exit',result
    # Same original request/response bytes, one feature stream, bounded numeric arms.
    prepared=replay.prepare_path(quotes)
    base=source['policy'];candidate={**base,'max_defer_sec':base['max_defer_sec']/2}
    paired=replay.replay_many(pos,prepared,{'parent':vector(),'candidate':vector()},vote_policies={'parent':base,'candidate':candidate})
    assert all(r['status']=='modeled_full_exit' for r in paired.values()),paired
    if verdict=='VETO':
        assert paired['candidate']['last_sell_permission_at'] < paired['parent']['last_sell_permission_at']
        assert paired['candidate']['modeled_net_pnl_krw'] > paired['parent']['modeled_net_pnl_krw']
    receipt=dict(schema='original_trailing_decision_source_v1',owner='scalp_trailing_take_profit',runtime_effect=False,allowed_runtime_apply=False)
    original=deepcopy(quotes)
    for q in original:
        native=dict(receipt,observed_at=q['known_at'],market='REGULAR',values=vector()['REGULAR'],classifier_sha256=prepared.classifier_sha256)
        native['sha256']=replay.digest(native);q['original_trailing_source']=native;q['source_sha256']=replay.quote_source_digest(q)
    frozen=replay.prepare_path(original)
    strict=replay.replay_many(dict(pos,original_trailing_source_required=True),frozen,{'parent':vector(),'candidate':vector()},vote_policies={'parent':base,'candidate':candidate})
    assert all(r['status']=='modeled_full_exit' for r in strict.values()),strict
    late=deepcopy(quotes);late[30]['holding_vote_source']['coverage_complete']=False
    late[30]['source_sha256']=replay.quote_source_digest(late[30])
    assert replay._replay(pos,late,vector())['status']=='censored'
    # Crossing uses original full bytes, never dedup equivalence alone.
    original=next((root/'ai_decision_payloads').glob('*.jsonl'))
    stored=[json.loads(line) for line in original.read_text().splitlines()]
    altered=json.loads(stored[0]['holding_raw_user_input']);altered['position']['curr_price']=101
    stored[0]['holding_raw_user_input']=json.dumps(altered)
    original.write_text(''.join(json.dumps(r)+'\n' for r in stored))
    assert replay._replay(pos,quotes,vector())['status']=='censored'
    # Rollover keeps research history complete and runtime tail bounded.
    monkeypatch.setattr(vote,'PATH_MAX_STORE_BYTES',path.stat().st_size+10)
    third={**rows[1],'source_generation':'item:next','requested_at':clock+22,'received_at':clock+22.5,'quote_observed_at':clock+21.9}
    monkeypatch.setattr(vote.time,'time',lambda:clock+23)
    assert vote.append_path_events_file(path,'main:1',[third])[1]=='appended'
    assert list(path.parent.glob(path.name+'.segment-*'))
    assert len(vote.load_path_events_file(path,'main:1'))==3
    assert evidence.assemble_votes(root,out,{**source,'store_name':'other.jsonl'}, {})['status']=='source_gap'


def test_holding_coverage_uses_native_position_clocks_and_restarts_are_not_backfilled(tmp_path,monkeypatch):
    from src.engine.ai import holding_exit_vote as vote
    from src.engine.ai import holding_vote_replay_source as evidence
    from zoneinfo import ZoneInfo
    monkeypatch.setattr(evidence,'PROCESS_STARTED_AT',1000.)
    stock=dict(id=1,code='123456',buy_time=datetime.fromtimestamp(1010.,ZoneInfo('Asia/Seoul')),
        buy_qty=1,entry_filled_qty=1,_entry_receipt_filled_by_order_no={'1':1},
        _entry_receipt_executions_by_order_no={'1':{'11':{'cumulative_qty':1}}})
    evidence.begin_coverage(stock,1020.)
    assert stock['holding_vote_coverage_started_at']==1010.
    evidence.begin_coverage(stock,1021.)
    assert stock['holding_vote_coverage_started_at']==1010.
    policy=vote.PATH_POLICY_BY_MARKET[('EXIT_TRAILING_TP','REGULAR')]
    def source():
        return evidence.runtime_source(stock,position_key='record:1',
            buy_fill_identity=vote.buy_fill_identity_from_runtime(stock),market='REGULAR',
            now=1021.,policy=policy,data_root=tmp_path,model='gpt-5.4-nano')
    assert source()['coverage_complete'] is True
    stock['holding_path_vote_store_gap']='durable_vote_store_unavailable'
    assert source()['coverage_complete'] is False
    stock.pop('holding_path_vote_store_gap')
    # A different PID's historical coverage cannot become current coverage.
    stock['holding_vote_coverage_pid']=-1
    monkeypatch.setattr(evidence,'PROCESS_STARTED_AT',1025.)
    evidence.begin_coverage(stock,1030.)
    assert stock['holding_vote_coverage_started_at']==1030.
    # Accepted ADD creates a new native generation at its own receipt clock.
    stock.update(buy_qty=2,last_add_at=datetime.fromtimestamp(1035.,ZoneInfo('Asia/Seoul')),
        _add_receipt_filled_by_order_no={'2':1},
        _add_receipt_executions_by_order_no={'2':{'22':{'cumulative_qty':1}}})
    evidence.begin_coverage(stock,1040.)
    assert stock['holding_vote_coverage_started_at']==1035.
