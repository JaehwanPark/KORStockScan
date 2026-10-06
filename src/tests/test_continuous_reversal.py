from copy import deepcopy
import json
import pytest
from src.engine.scalping import continuous_reversal as K
from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.scalping.reversal_auxiliary_contract import production_request, ARMS


def rows(prices):
    return [[float(i),1,i+1,float(p),float(p)-.1,float(p)+.1,1.,1,1,'005930',0] for i,p in enumerate(prices)]


def test_all_turns_prefix_and_flat_prices():
    r=rows([100,99,99,98,99,100,99,100])
    state=K.ReversalState(); live=[]
    for i,row in enumerate(r):
        state.observe(row,symbol='005930',venue='KRX',session='KRX_REGULAR')
        if state.turn and state.turn['epoch']==row[0]:
            live.append(i)
            assert [t['entry_index'] for t in K.turns(r[:i+1])][-1]==i
            event,inp=state.snapshot()
            batch,_=K.analyze_symbol(r[:i+1],'1970-01-01','KRX','KRX_REGULAR','005930')
            for key in ['drop_pct','drawdown_5m_pct','confirmation_pct','down_steps']:
                assert event[key]==batch[-1][key]
            assert all(p['age_sec']>=0 for p in inp['recent_observed_prices'])
    assert live==[4,7]


def test_duplicate_gap_epoch_and_market_isolation():
    state=K.ReversalState(); r=rows([100,99,100])
    for row in r[:2]:state.observe(row,symbol='005930',venue='KRX',session='KRX_REGULAR')
    state.observe(r[1],symbol='005930',venue='KRX',session='KRX_REGULAR')
    state.observe(r[2],symbol='005930',venue='KRX',session='KRX_REGULAR')
    assert state.turn
    changed=r[2][:];changed[3]=101
    state.observe(changed,symbol='005930',venue='KRX',session='KRX_REGULAR')
    assert state.turn is None
    assert K.cell_key('005930','PREMARKET_KRX_LIKE',20000)=='samsung|PRE|ALL'
    assert K.cell_key('123456','REGULAR',20000)=='other|REGULAR|20000_TO_100000'
    assert K.cell_key('123456','NXT_AFTERMARKET',100000)=='other|AFTER|GE_100000'
    with pytest.raises(ValueError):K.market_bucket('UNKNOWN')


def test_target_deadline_stop_first_and_censoring():
    ask=100.; target=ask*1.004/.9977;stop=ask*.97/.9977
    r=rows([100,99,100,target]);r[-1][0]=1802.
    times=[x[0] for x in r];_,ends,valid=K.segments(r);tree=K.Tree([x[3] for x in r])
    assert K.label(r,times,tree,ends,valid,2,ask)['status']=='WIN'
    r[-1][0]=1802.001
    assert K.label(r,[x[0] for x in r],tree,ends,valid,2,ask)['status']=='FAIL_TIMEOUT'
    r[2][3]=stop
    tree=K.Tree([x[3] for x in r])
    assert K.label(r,[x[0] for x in r],tree,ends,valid,2,ask)['status']=='FAIL_STOP'
    r=rows([100,99,100,100]);_,ends,valid=K.segments(r)
    assert K.label(r,[x[0] for x in r],K.Tree([x[3] for x in r]),ends,valid,2,ask)['status']=='UNRESOLVED'


def test_no_sample_inherits_exact_regular_payload():
    cells=[dict(key=k,payload={'rule':'DD5_GE_1_2'} if '|REGULAR|' in k else None,
                local_metrics=None,inherited_from=None) for k in P.expected_cells()]
    P.inherit(cells)
    for c in cells:
        assert c['payload']=={'rule':'DD5_GE_1_2'}
        if '|REGULAR|' not in c['key']:
            assert c['local_metrics'] is None
            assert c['parent_payload_sha256']==c['payload_sha256']


def test_production_request_allowlist_and_identity():
    # A real frozen as-of point, private outcome never enters the request.
    state=K.ReversalState()
    for row in rows([100,99,100]):
        state.observe(row,symbol='005930',venue='KRX',session='KRX_REGULAR')
    _,source=state.snapshot()
    other=deepcopy(source);other['outcome']={'future':'WIN'}
    for arm in ARMS:
        a=production_request(source,arm);b=production_request(other,arm)
        assert a==b
        assert a[1].isascii()
        assert 'Offline' not in a[0]['context']
    other['entry_setup_evidence_v1']['positive_facts'][0]['value']={'future':'WIN'}
    with pytest.raises(ValueError):production_request(other,ARMS[-1])


def test_production_registry_and_schema_are_exact():
    from src.engine.ai_prompt_contracts import machine_auxiliary_compact_entry_system_prompt
    from src.engine.scalping.reversal_auxiliary_contract import PRODUCTION_VERSION
    from src.engine.ai_engine_openai import OpenAIResponseRequest
    state=K.ReversalState()
    for row in rows([100,99,100]):state.observe(row,symbol='005930',venue='KRX',session='KRX_REGULAR')
    _,source=state.snapshot()
    for arm in ARMS:
        inp,prompt,schema=production_request(source,arm)
        assert machine_auxiliary_compact_entry_system_prompt('entry',prompt_version=PRODUCTION_VERSION+':'+arm)==prompt
        req=OpenAIResponseRequest(prompt=prompt,user_input=json.dumps(inp),require_json=True,context_name='fixture',
            model_name='gpt-5.4-nano',temperature=None,schema_name='entry_setup_risk_adjudication_v1',
            endpoint_name='analyze_target',request_id='fixture',symbol='005930',cache_key='fixture',
            submitted_at_perf=0,timeout_ms=5000,response_schema_override=schema)
        assert req.build_provider_payload(use_schema_registry=True)['text']['format']['schema']==schema


def family_reports():
    machine=[];aux=[]
    for key in P.expected_cells():
        m=dict(key=key,payload=dict(rule='ALL'),local_metrics=dict(wins=1,resolved=1),inherited_from=None)
        a=dict(key=key,payload=dict(arm='reversal_citation_v6'),local_metrics=dict(pass_wins=1,pass_count=1),inherited_from=None)
        m['payload_sha256']=P.digest(m['payload']);a['payload_sha256']=P.digest(a['payload'])
        machine.append(m);aux.append(a)
    return P.seal(dict(schema=P.SCHEMA,source_date='2026-10-06',status='completed',cells=machine,
               source_manifest_sha256='a'*64,label_contract=dict(target_net_pct=.4,stop_net_pct=-3.,cost_rate=.0023,horizon_seconds=1800))), P.seal(dict(schema=P.SCHEMA,source_date='2026-10-06',status='completed',cells=aux))


def test_dated_publish_loader_nonentry_and_schema_failure(tmp_path):
    from src.tests.test_mechanistic_entry_runtime_policy import initial
    from src.engine.scalping import mechanistic_entry_runtime_policy as native
    from src.engine.scalping import continuous_reversal_policy as policy
    initial(tmp_path)
    m,a=family_reports()
    staged=policy.publish(tmp_path,'2026-10-06','2026-10-06',m,a)
    assert staged['target_date']=='2026-10-07'
    assert native._load_current(tmp_path,'2026-10-06') is None
    selected=native.load_effective(data_root=tmp_path,target_date='2026-10-07')
    assert selected['continuous_reversal']['machine_cells']['samsung|PRE|ALL']['payload']=={'rule':'ALL'}
    state=K.ReversalState()
    for row in rows([100,99,100]):state.observe(row,symbol='005930',venue='KRX',session='KRX_REGULAR')
    assessment,inp,_,_=policy.assess(selected['continuous_reversal'],state.snapshot(),symbol='005930',session='KRX_REGULAR')
    assert assessment['action']=='ENTER_NOW'
    ctx=dict(continuous_reversal_assessment=assessment,continuous_reversal_input=inp,
             continuous_reversal_arm='reversal_citation_v6',machine_bundle_sha256=selected['bundle_sha256'])
    response=dict(schema='entry_setup_risk_adjudication_v1',risk_verdict='PASS',risk_codes=['NO_BLOCKING_RISK'],
                  supporting_fact_ids=['first_price_uptick','observed_price_decline'],contradicting_fact_ids=[],confidence=60)
    assert policy.compose(response,ctx)['action']=='BUY'
    response['supporting_fact_ids']=['future_rebound']
    assert policy.compose(response,ctx)['action']=='WAIT'
    ctx['continuous_reversal_assessment']={**assessment,'action':'BLOCK'}
    assert policy.compose(response,ctx)['action']=='DROP'
    # A corrupt dated native source cannot silently fall through to legacy.
    path=native.root(tmp_path)/'sources'/f"reversal-{m['artifact_content_sha256']}.json"
    path.write_text('{}')
    with pytest.raises(ValueError):native.load_effective(data_root=tmp_path,target_date='2026-10-07')


def synthetic_family():
    from src.engine.scalping import continuous_reversal_policy as policy
    from src.engine.scalping.reversal_auxiliary_contract import PRODUCTION_VERSION
    m,a=family_reports()
    family=dict(schema=policy.SCHEMA,kernel_version=K.VERSION,auxiliary_version=PRODUCTION_VERSION,
        selection_metric='cumulative_raw_win_fraction',label_contract=m['label_contract'],
        machine_cells={c['key']:c for c in m['cells']},auxiliary_cells={c['key']:c for c in a['cells']})
    family['family_sha256']=P.digest(family)
    return family


@pytest.mark.parametrize('key',P.expected_cells())
def test_twelve_cell_runtime_routes(key):
    from src.engine.scalping import continuous_reversal_policy as policy
    g,market,band=key.split('|')
    symbol='005930' if g=='samsung' else '123456'
    price={'ALL':200000,'LT_20000':10000,'20000_TO_100000':50000,'GE_100000':200000}[band]
    state=K.ReversalState()
    for row in rows([price,price-100,price]):state.observe(row,symbol=symbol,venue='SOR',session=market)
    assessment,inp,_,_=policy.assess(synthetic_family(),state.snapshot(),symbol=symbol,session=market)
    assert assessment['action']=='ENTER_NOW'
    assert assessment['cell_key']==key
    assert inp['objective']['horizon_seconds']==1800
    assert inp['objective']['cost_rate']==.0023


@pytest.mark.parametrize("arm",ARMS)
def test_live_engine_uses_production_bytes_without_legacy_strategy_veto(monkeypatch, arm):
    from dataclasses import replace
    from src.tests.test_ai_engine_openai_transport import _build_engine,_sample_ws_data,_sample_ticks,_sample_candles,_allowed_entry_candle_context
    from src.tests.test_entry_setup_evidence import _exact_analysis,_recovery_analysis
    from src.engine import ai_engine_openai as E
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    from src.engine.scalping.reversal_auxiliary_contract import PRODUCTION_VERSION
    state=K.ReversalState()
    for row in rows([100,99,100]):state.observe(row,symbol='005930',venue='SOR',session='SOR_REGULAR')
    frozen=state.snapshot()
    engine=_build_engine()
    live=dict(enabled=True,status='active_bounded_krx_canary',selected_prompt_version=PRODUCTION_VERSION+':reversal_citation_v6',
        primary_decision_owner='mechanistic_entry_adjudicator',ai_role='auxiliary_risk_screen_pass_veto_no_promotion',
        mechanistic_threshold_policy=N.MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1,machine_bundle_sha256='b'*64,
        continuous_reversal=synthetic_family(),auxiliary_system_prompt='carrier',auxiliary_system_prompt_sha256='c'*64,
        auxiliary_prompt_variant='carrier')
    for cell in live["continuous_reversal"]["auxiliary_cells"].values():
        cell["payload"]={"arm":arm};cell["payload_sha256"]=P.digest(cell["payload"])
    live["continuous_reversal"]["family_sha256"]=P.digest({k:v for k,v in live["continuous_reversal"].items() if k!="family_sha256"})
    monkeypatch.setattr(E,'resolve_live_prompt_policy',lambda **kw:live)
    monkeypatch.setattr(K,'current_snapshot',lambda symbol,venue,session,**kw:frozen)
    monkeypatch.setattr(E,'build_exact_payload_analysis_v1',lambda *a,**kw:_exact_analysis())
    monkeypatch.setattr(E,'build_v2_13_recovery_confirmation_analysis_v1',lambda *a,**kw:_recovery_analysis(clean=True))
    monkeypatch.setattr(E,'mechanistic_entry_policy_decision',lambda *a,**kw:pytest.fail('old machine strategy must not run'))
    monkeypatch.setattr(E,'TRADING_RULES',replace(E.TRADING_RULES,OPENAI_ANALYZE_TARGET_PROMPT_VERSION='V2.13'))
    called=[]
    def provider(prompt,data,**kwargs):
        expected=production_request(frozen[1],arm)
        assert (json.loads(data),prompt,kwargs['response_schema_override'])==expected
        called.append(True)
        return dict(schema='entry_setup_risk_adjudication_v1',risk_verdict='PASS',risk_codes=['NO_BLOCKING_RISK'],
                    supporting_fact_ids=['first_price_uptick','observed_price_decline'],contradicting_fact_ids=[],confidence=60)
    monkeypatch.setattr(engine,'_call_openai_safe',provider)
    ws=_sample_ws_data();ws['stock_code']='005930';ws['last_realtime_type_item']={'0B':'005930_AL'}
    result=engine.analyze_target('test',ws,_sample_ticks(),_sample_candles(),strategy='SCALPING',prompt_profile='watching',
                                candle_context=_allowed_entry_candle_context())
    assert called,result
    assert result['action']=='BUY',result
    assert result['entry_ai_screen_pass'] is True


def test_missing_quote_returns_recheck_and_quiet_tape_keeps_ten_trades():
    from src.engine.scalping.continuous_reversal_policy import assess
    state=K.ReversalState();r=rows([100]*9+[99,100,100.1,100.2])
    for i,row in enumerate(r):
        row[0]=i*100.
        state.observe(row,symbol='005930',venue='KRX',session='KRX_REGULAR')
        if i==10:
            expected=K.build_features(r[:11])
            event,inp=state.snapshot()
            assert inp['entry_setup_evidence_v1']['facts']['return_10t_pct']==expected['return_10t_pct'][-1]
    assert len(state.snapshot()[1]['recent_observed_prices'])==10
    state=K.ReversalState();r=rows([100,99,100]);r[-1][5]=None
    for row in r:state.observe(row,symbol='005930',venue='KRX',session='KRX_REGULAR')
    assert assess(synthetic_family(),state.snapshot(),symbol='005930',session='KRX_REGULAR')[0]['action']=='RECHECK'


def test_regular_previous_parent_and_zero_wins_are_distinct():
    prev={k:dict(payload={'rule':'ALL'}) for k in P.expected_cells() if '|REGULAR|' in k}
    cells=[dict(key=k,payload=None,local_metrics=None,inherited_from=None) for k in P.expected_cells()]
    P.inherit(cells,prev)
    for c in cells:
        assert c['payload']=={'rule':'ALL'} and c['local_metrics'] is None
        assert c['parent_payload_sha256']==P.digest(c['payload'])
    family=synthetic_family();family['machine_cells']['samsung|REGULAR|ALL']['local_metrics']={'wins':0,'resolved':1}
    from src.engine.scalping.continuous_reversal_policy import validate_family
    family['family_sha256']=P.digest({k:v for k,v in family.items() if k!='family_sha256'})
    validate_family(family)
    family['machine_cells']['samsung|REGULAR|ALL']['local_metrics']['resolved']=0
    family['family_sha256']=P.digest({k:v for k,v in family.items() if k!='family_sha256'})
    with pytest.raises(ValueError,match='metrics'):validate_family(family)


def test_activation_same_bundle_parent_and_cache_revalidation(tmp_path,monkeypatch):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from src.tests.test_mechanistic_entry_runtime_policy import initial
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    from src.engine.scalping import continuous_reversal_policy as C
    parent=initial(tmp_path);m,a=family_reports();staged=C.publish(tmp_path,'2026-10-06','2026-10-06',m,a)
    original=N._load_current
    monkeypatch.setattr(N,'_load_current',lambda root,day:original(root,day) if (N.root(root)/'current.json').exists() else parent)
    receipt=C.activate(tmp_path,'2026-10-07',now=datetime(2026,10,7,0,0,tzinfo=ZoneInfo('Asia/Seoul')))
    assert receipt['bundle_sha256']==staged['bundle_sha256']
    assert N.load_effective(data_root=tmp_path,target_date='2026-10-07')['bundle_sha256']==staged['bundle_sha256']
    assert original(tmp_path,'2026-10-07')['bundle_sha256']==staged['bundle_sha256']
    (N.root(tmp_path)/'generations'/f"{parent['bundle_sha256']}.json").write_text('{}')
    with pytest.raises(ValueError):original(tmp_path,'2026-10-07')


def test_native_next_day_population_and_previous_regular_inheritance(tmp_path):
    from datetime import datetime,timedelta
    from zoneinfo import ZoneInfo
    day='2026-10-06';prior=P.directory(tmp_path,'2026-10-02');prior.mkdir(parents=True)
    m,_=family_reports();m['source_date']='2026-10-02';P.write(prior/'machine.json',P.seal(m))
    P.write(prior/'source.json',P.seal(dict(source_date='2026-10-02',reviewed_events=[],selected_routes={},normalized_sources=dict(partitions=[]))))
    folder=tmp_path/'observations/scalp_micro_reversion_forward'/f'trade_date={day}'/'venue=KRX'/'session=KRX_REGULAR'
    folder.mkdir(parents=True);stamp=datetime(2026,10,6,9,tzinfo=ZoneInfo('Asia/Seoul'));points=[]
    for i,price in enumerate([100,99,100,101]):
        at=(stamp+timedelta(seconds=i)).isoformat()
        points.append(dict(schema='scalp_micro_reversion_market_stream_point_v3',symbol='005930',venue='KRX',
            session_bucket='KRX_REGULAR',local_receive_timestamp=at,exchange_timestamp=at,sequence_epoch=1,series_sequence=i+1,
            trade_price=price,best_bid=price,best_ask=price,trade_qty=1,aggressor_side='BUY',
            path_consumer_eligible=True,path_order_status='accept',source_item='005930',quote_age_ms=0))
    (folder/'market_stream.jsonl').write_text(''.join(json.dumps(p)+'\n' for p in points)+'{"partial":')
    report=P.machine_report(tmp_path,day,day)
    assert report['input_turn_count']==1
    cells={c['key']:c for c in report['cells']}
    assert cells['samsung|REGULAR|ALL']['local_metrics']['wins']==1
    assert cells['samsung|PRE|ALL']['payload']==cells['samsung|REGULAR|ALL']['payload']
    assert cells['other|REGULAR|LT_20000']['inherited_from']=='previous:other|REGULAR|LT_20000'
    source=json.loads((P.directory(tmp_path,day)/'source.json').read_text())
    assert source['new_raw_partition_count']==1 and source['machine_decisions_used'] is False


def test_new_turn_after_block_wakes_machine_and_preserves_transport_backoff(monkeypatch):
    from src.engine import sniper_state_handlers as H
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    state=K.ReversalState()
    for row in rows([100,99,100]):state.observe(row,symbol='005930',venue='SOR',session='SOR_REGULAR')
    snapshot=state.snapshot();stock=dict(code='005930',market_session_bucket='KRX_REGULAR')
    ws=dict(last_realtime_type_item={'0B':'005930_AL'})
    monkeypatch.setattr(K,'current_snapshot',lambda *a,**kw:snapshot)
    monkeypatch.setattr(N,'load_effective',lambda **kw:dict(continuous_reversal=synthetic_family()))
    monkeypatch.setattr(H,'machine_source_recovery_refresh',lambda *a,**kw:None)
    r=H._resolve_watching_state_change_refresh(stock,ws,now_ts=3,last_ai_time=2,cooldown_sec=60)
    assert r['allowed'] and r['decision_authority']=='machine_evaluation_only'
    stock['_scanner_entry_ai_transport_retry_after_epoch']=10
    r=H._resolve_watching_state_change_refresh(stock,ws,now_ts=4,last_ai_time=2,cooldown_sec=60)
    assert not r['allowed'] and r['reason']=='transport_timeout_retry_backoff'
