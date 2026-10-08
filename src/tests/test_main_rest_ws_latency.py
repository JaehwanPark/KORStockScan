"""Deadline, native async ownership and bounded physical transport contracts."""
from datetime import datetime, timedelta
from types import SimpleNamespace
from concurrent.futures import ThreadPoolExecutor
import threading
import time
import pytest
import ast
import inspect

from src.engine.scalping.entry_deadline import EntryDeadline, claim_deadline_epoch
from src.trading.market.entry_ws_source import select_trade_history
from src.trading.market.index_regime import index_regime
from src.utils import kiwoom_transport_telemetry as T


@pytest.mark.parametrize('code',['005930','034020','036930','196170','403870'])
def test_actual_main_watching_statement_forwards_created_coordinator(monkeypatch,code):
    """Run the real Main call expression and wrapper, without a broker loop."""
    from src.engine import kiwoom_sniper_v2 as M, sniper_state_handlers as H
    from src.engine.scalping.scanner_async_eval import ScannerAsyncEvalCoordinator
    from src.engine.ai.hot_path_ai_dispatcher import HotPathAIDispatcher
    tree=ast.parse(inspect.getsource(M.run_sniper))
    calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call)
        and isinstance(n.func,ast.Name) and n.func.id=='handle_watching_state'
        and not any(k.arg=='scanner_async_generation' for k in n.keywords)]
    assert len(calls)==1
    coordinator=ScannerAsyncEvalCoordinator(ai_dispatcher=HotPathAIDispatcher(loaded_key_count=1))
    monkeypatch.setattr(M.run_sniper,'scanner_async_eval_coordinator',coordinator,raising=False)
    seen=[]
    def handler(stock,code,ws,admin,**kw):
        seen.append(kw)
        # No native claim must keep the current safe no-dispatch behavior.
        return H._resolve_scanner_async_entry_ai(stock,code,ws,None,kw,
            trigger_reason='test',last_ai_time=0,current_ai_score=0)
    monkeypatch.setattr(H,'handle_watching_state',handler)
    monkeypatch.setattr(H,'_request_entry_capacity_preparation',lambda *a,**kw:None)
    monkeypatch.setattr(H,'_fixed_watch_entry_source_route',lambda *a:None)
    try:
        result=eval(compile(ast.Expression(calls[0]),'<actual-main-call>','eval'),{
            'handle_watching_state':M.handle_watching_state,'run_sniper':M.run_sniper,
            'stock':{'code':code,'status':'WATCHING'},'code':code,'ws_data':{},'admin_id':None,
            'now_ts':time.time(),'now':datetime.now(),'radar':None,'ai_engine':None})
        assert seen[0]['scanner_async_eval_coordinator'] is coordinator
        assert seen[0]['scanner_async_generation'] is None
        assert result['status']=='not_enabled'
    finally:coordinator.shutdown()


@pytest.mark.parametrize('role,failed',[('main',False),('main',True),('non_main',False)])
def test_actual_startup_policy_read_is_independent_of_entry_cutoff(monkeypatch,role,failed):
    from src.engine import kiwoom_sniper_v2 as M
    from src.engine.scalping import reversal_evaluation_context as C
    tree=ast.parse(inspect.getsource(M.run_sniper))
    node=next(n for n in ast.walk(tree) if isinstance(n,ast.If)
        and ast.unparse(n.test)=="runtime_role == 'main'"
        and 'MAIN_POLICY_STARTUP' in ast.unparse(n))
    calls=[];errors=[]
    def prepare(**kw):
        calls.append(kw)
        if failed:raise ValueError('invalid_policy')
    monkeypatch.setattr(C,'prepare',prepare)
    exec(compile(ast.Module(body=[node],type_ignores=[]),'<actual-startup-reader>','exec'),
        dict(runtime_role=role,datetime=datetime,time=time,log_info=lambda *a:None,log_error=errors.append))
    assert len(calls)==(role=='main')
    assert bool(errors)==failed


def test_original_claim_budget_survives_wall_clock_backwards(monkeypatch):
    monkeypatch.setattr(time,'time',lambda:100.)
    monkeypatch.setattr(time,'perf_counter',lambda:10.)
    claim={'snapshot':[{'epoch':98.}]}
    budget=EntryDeadline.create(claim,110.)
    assert budget.epoch == 103.
    assert budget.transport_ms(5000) == 3000
    monkeypatch.setattr(time,'time',lambda:99.)
    monkeypatch.setattr(time,'perf_counter',lambda:12.9)
    assert 0 < budget.transport_ms(5000) <= 100
    monkeypatch.setattr(time,'perf_counter',lambda:13.1)
    with pytest.raises(ValueError,match='deadline_expired'):
        budget.transport_ms(5000)


@pytest.mark.parametrize('claim',[{}, {'snapshot':[]}, {'snapshot':[{'epoch':float('nan')}]}, {'snapshot':[{'epoch':True}]}])
def test_malformed_claim_cannot_renew_deadline(claim):
    assert claim_deadline_epoch(claim) == 0
    with pytest.raises(ValueError,match='deadline_expired'):
        EntryDeadline.create(claim,time.time()+5).require()


def test_sub_fifty_ms_transport_has_no_budget_enlargement():
    from src.engine.ai_engine_openai import GPTSniperEngine, OpenAIResponseRequest
    engine=GPTSniperEngine.__new__(GPTSniperEngine)
    observed=[]
    engine.client=SimpleNamespace(responses=SimpleNamespace(create=lambda **kw: observed.append(kw['timeout']) or 'ok'))
    engine._http_deadline_executor=ThreadPoolExecutor(max_workers=1)
    request=OpenAIResponseRequest(None,'{}',True,'test','gpt-5.4-nano',None,None,'analyze_target','test','005930','key',time.perf_counter(),40)
    try:
        assert engine._create_openai_response_with_deadline(request,provider_payload={}) == 'ok'
        assert 0 < observed[0] <= .04
    finally:
        engine._http_deadline_executor.shutdown()


def test_queued_transport_expiry_never_sends_or_restarts_deadline():
    from src.engine.ai_engine_openai import GPTSniperEngine, OpenAIResponseRequest, OpenAIHTTPWallClockDeadlineError
    engine=GPTSniperEngine.__new__(GPTSniperEngine)
    calls=[]
    engine.client=SimpleNamespace(responses=SimpleNamespace(create=lambda **kw: calls.append(kw)))
    engine._http_deadline_executor=ThreadPoolExecutor(max_workers=1)
    release=threading.Event()
    engine._http_deadline_executor.submit(release.wait, .2)
    request=OpenAIResponseRequest(None,'{}',True,'test','gpt-5.4-nano',None,None,'analyze_target','test','005930','key',time.perf_counter(),20)
    try:
        with pytest.raises(OpenAIHTTPWallClockDeadlineError):
            engine._create_openai_response_with_deadline(request,provider_payload={})
        release.set()
    finally:
        engine._http_deadline_executor.shutdown()
    assert calls == []


def valid_ws():
    now=time.time()
    rows=[dict(item='005930_AL', transport_epoch=2, received_at_ms=(now-i*.1)*1000,
        provider_trade_epoch=now-i*.1-.2, route_sequence=20-i, market_suffix='_AL',
        market_route='krx_nxt_integrated',price=1000+i,volume=10,volume_source='15_abs') for i in range(10)]
    return now,dict(market_data_transport_epoch=2,last_realtime_type_item={'0B':'005930_AL'},
        last_realtime_type_ts={'0B':now},recent_trade_ticks_by_route={'_AL|krx_nxt_integrated':rows})


@pytest.mark.parametrize('defect',['none','short','epoch','sequence','future','route','item','delay'])
def test_ws_tape_reuse_preserves_original_clock_and_rejects_partial(defect):
    now,ws=valid_ws();rows=ws['recent_trade_ticks_by_route']['_AL|krx_nxt_integrated']
    if defect=='short':rows.pop()
    elif defect=='epoch':rows[-1]['transport_epoch']=1
    elif defect=='sequence':rows[-1]['route_sequence']-=1
    elif defect=='future':rows[-1]['received_at_ms']=(now+1)*1000
    elif defect=='route':rows[-1]['market_route']='nxt_only'
    elif defect=='item':ws['last_realtime_type_item']['0B']='005930'
    elif defect=='delay':rows[-1]['provider_trade_epoch']-=10
    result=select_trade_history(ws,'005930_AL',now=now)
    if defect=='none':
        assert result[0]['received_at_ms'] == rows[0]['received_at_ms']
        result[0]['volume']=999
        assert rows[0]['volume']==10
        assert select_trade_history(ws,'005930',now=now) is None
    else:assert result is None


@pytest.mark.parametrize('defect',['none','duplicate','nan','short','base_date','order'])
def test_index_twenty_dates_are_not_silently_dropped(defect):
    base=datetime(2026,10,8)
    days=[]
    while len(days)<20:
        if base.weekday()<5:days.append(base.strftime('%Y%m%d'))
        base-=timedelta(days=1)
    rows=[{'dt':day,'cur_prc':str(250000-i*100)} for i,day in enumerate(days)]
    if defect=='duplicate':rows[-1]['dt']=rows[-2]['dt']
    elif defect=='nan':rows[10]['cur_prc']='NaN'
    elif defect=='short':rows.pop()
    elif defect=='base_date':rows=rows[1:]+[{'dt':'20260901','cur_prc':'250000'}]
    elif defect=='order':rows.reverse()
    if defect=='none':assert index_regime(rows,base_date='20261008',scale=100)['current_close']==2500
    else:
        with pytest.raises(ValueError):index_regime(rows,base_date='20261008',scale=100)


def test_physical_timeout_count_and_inflight_equation_without_secret():
    class ReadTimeout(Exception):pass
    with pytest.raises(ReadTimeout):
        T.measured_http_call(lambda *a,**kw:(_ for _ in ()).throw(ReadTimeout()),
            'https://api.kiwoom.com/api/dostk/chart',telemetry_owner='test-timeout',
            headers={'api-id':'ka10080','authorization':'Bearer SECRET'})
    snapshot=T.snapshot()
    bucket=next(b for b in snapshot['buckets'] if b['owner']=='test-timeout')
    assert bucket['started']==bucket['terminal']+bucket['inflight_unknown']
    assert bucket['timeout']==1
    assert 'SECRET' not in str(snapshot)


def test_fixed_watch_context_uses_native_identity_not_scanner_promotion():
    from src.engine.scalping.scanner_async_eval import FixedWatchGeneration, ScannerAsyncEvalContext
    from src.engine.scalping.scanner_runtime_scheduler import ScannerGeneration
    now=time.time()
    claim={'token':'native','snapshot':[{'epoch':now,'symbol':'005930','venue':'SOR'}],
        'source_registration_receipt':{'sha256':'proof'}}
    native=FixedWatchGeneration.from_claim('005930',claim)
    assert not isinstance(native,ScannerGeneration)
    context=ScannerAsyncEvalContext.create(generation=native,cache_key='native',
        submitted_epoch=now,deadline_epoch=now+5,stock_snapshot={'claim':claim},ws_snapshot={},state_version='watch')
    claim['snapshot'][0]['epoch']=0
    assert context.stock_snapshot['claim']['snapshot'][0]['epoch']==now
    assert 'scanner_generation_id' not in native.timing_fields(now_epoch=now)


def test_counter_histogram_survives_deque_eviction():
    from src.engine.monitoring import runtime_performance as P
    P.observe('loop_work',6.,generation='cumulative-test')
    for _ in range(5000):P.observe('loop_work',.1)
    metric=P.snapshot()['metrics']['loop_work']
    assert metric['n']==4096 and metric['over_five_seconds']==0
    assert metric['cumulative_over_five_seconds']==1
    assert sum(metric['cumulative_histogram'].values())==5001


@pytest.mark.parametrize('decision,expected', [
    ('source_invalid',None), ('RECHECK',None), (None,None),
    ({'signal_id':'s'},'s'), ({'continuous_reversal_assessment':{'event_id':'e'}},'e'),
    ({'continuous_reversal_assessment':'source_invalid'},None),
    ({'signal_id':{}},None),
])
def test_diagnostic_signal_join_handles_native_decision_variants(decision,expected):
    from src.engine.monitoring.runtime_performance import machine_signal_id
    assert machine_signal_id({'entry_mechanistic_policy_decision':decision})==expected


@pytest.mark.parametrize('outer_drain',[False,True])
@pytest.mark.parametrize('commit_change',[None,'route','watch_generation'])
def test_fixed_watch_dispatch_keeps_claim_and_worker_state_private(monkeypatch,commit_change,outer_drain):
    from src.engine import sniper_state_handlers as H
    from src.engine.scalping import reversal_current_backend as B, reversal_source_diagnostics as D
    from src.engine.scalping.scanner_async_eval import ScannerAsyncEvalCoordinator
    from src.engine.ai.hot_path_ai_dispatcher import HotPathAIDispatcher
    now,ws=valid_ws()
    ws['orderbook']={'bids':[[999,10]],'asks':[[1000,10]]}
    ws['curr']=1000
    claim={'token':'native-test','generation':'family','snapshot':[dict(epoch=now,symbol='005930',
        venue='SOR',source_item='005930_AL',event_id='event',signal_id='signal')],
        'source_registration_receipt':{'sha256':'proof'}}
    stock=dict(code='005930',name='Samsung',status='WATCHING',effective_venue='SOR',buy_qty=0,
               _continuous_reversal_pending_claim=claim)
    monkeypatch.setattr(H,'_fixed_watch_entry_source_route',lambda *a:{'item':'005930_AL','broker_route':'SOR'})
    monkeypatch.setattr(H,'fetch_entry_candles_with_meta',lambda *a,**kw:([],{}))
    monkeypatch.setattr(H,'build_entry_candle_context',lambda *a,**kw:{})
    monkeypatch.setattr(H,'_extract_ai_overlap_snapshot',lambda **kw:{})
    monkeypatch.setattr(H,'_refresh_prepared_entry_inputs',lambda code,ws,ticks,ctx:(ws,ticks,ctx,{}))
    monkeypatch.setattr(H,'_prefetch_entry_capacity_for_async_evaluation',lambda *a,**kw:{'status':'test_cached'})
    monkeypatch.setattr(H,'_scanner_async_quote_is_fresh',lambda *a,**kw:True)
    monkeypatch.setattr(H,'_log_entry_pipeline',lambda *a,**kw:None)
    monkeypatch.setattr(B,'backend',lambda *a:SimpleNamespace(_GENERATION='family'))
    monkeypatch.setattr(B,'acknowledge_any',lambda *a,**kw:None)
    monkeypatch.setattr(D,'validate_claim_with_receipt',lambda *a,**kw:claim['snapshot'])
    def observe(private,code,ws,**kw):
        private['_machine_observation_revision']={'test_receipt':'captured'}
        return {}
    monkeypatch.setattr(H,'_observe_entry_economics_before_ai',observe)
    invoked=threading.Event()
    def analyze(*args,**kw):
        assert kw['reversal_signal_claim']['token']=='native-test'
        assert kw['entry_input_deadline_epoch']==now+5
        kw['entry_economics_observer'](exact_payload={},assessment={},capture={},bundle_sha256='b')
        assert '_machine_observation_revision' not in stock
        invoked.set()
        return dict(action='WAIT',entry_mechanistic_policy_decision='source_invalid')
    coordinator=ScannerAsyncEvalCoordinator(ai_dispatcher=HotPathAIDispatcher(loaded_key_count=1))
    runtime={'scanner_async_eval_coordinator':coordinator}
    try:
        result=H._resolve_scanner_async_entry_ai(stock,'005930',ws,SimpleNamespace(analyze_target=analyze),
            runtime,trigger_reason='continuous_reversal_first_uptick',last_ai_time=0,current_ai_score=50)
        assert result['status']=='dispatched'
        assert invoked.wait(1)
        refresh=H._resolve_watching_state_change_refresh(stock,ws,now_ts=now,
            last_ai_time=now,cooldown_sec=100)
        assert refresh['allowed'] and refresh['reason']=='fixed_watch_async_pending'
        if outer_drain:
            from src.engine import kiwoom_sniper_v2 as M
            tree=ast.parse(inspect.getsource(M.run_sniper))
            node=next(n for n in ast.walk(tree) if isinstance(n,ast.For)
                and ast.unparse(n.target)=='async_result'
                and 'drain_completed' in ast.unparse(n.iter))
            deadline=time.time()+1
            while not coordinator.has_undrained_result() and time.time()<deadline:time.sleep(.005)
            exec(compile(ast.Module(body=[node],type_ignores=[]),'<actual-main-outer-drain>','exec'),
                {'async_coordinator':coordinator})
            assert coordinator.has_completed_result()
        if commit_change=='route':
            monkeypatch.setattr(H,'_fixed_watch_entry_source_route',lambda *a:{'item':'005930_NX','broker_route':'NXT'})
        elif commit_change=='watch_generation':
            stock['watch_generation_id']='replacement'
        deadline=time.time()+1
        while time.time()<deadline:
            result=H._resolve_scanner_async_entry_ai(stock,'005930',ws,SimpleNamespace(analyze_target=analyze),
                runtime,trigger_reason='continuous_reversal_confirmed_uptick',last_ai_time=now,current_ai_score=90)
            if result['status']!='pending':break
            time.sleep(.005)
        if commit_change:
            assert result['status']=='commit_rejected'
            assert '_machine_observation_revision' not in stock
        else:
            assert result['status']=='completed'
            assert result['reversal_signal_claim']==claim
            assert result['reversal_signal_claim'] is not claim
            assert stock['_machine_observation_revision']=={'test_receipt':'captured'}
        assert '_fixed_watch_async_claim' not in stock
        assert not coordinator.has_completed_result()
        assert len(coordinator.drain_completed())==(0 if outer_drain else 1)
        assert coordinator.drain_completed()==[]
    finally:coordinator.shutdown()


@pytest.mark.parametrize('quote_age,transport_age,allowed',[(2.5,9.,True),(3.5,0.,False),(-1.,0.,False),(None,0.,False)])
def test_fixed_watch_quote_commit_uses_canonical_receipt(monkeypatch,quote_age,transport_age,allowed):
    from src.engine import sniper_state_handlers as H
    from src.trading.market import quote_consistency as Q
    monkeypatch.setattr(Q,'ws_quote_receive_age_ms',lambda *a,**kw:None if quote_age is None else quote_age*1000)
    monkeypatch.setattr(Q,'build_market_data_health',lambda *a,**kw:{})
    monkeypatch.setattr(H,'_rule',lambda key,default=None:3. if key=='SCALP_PRE_AI_MAX_WS_AGE_SEC' else default)
    monkeypatch.setattr(H,'_get_ws_snapshot_age_sec',lambda *a:transport_age)
    assert H._scanner_async_quote_is_fresh({'curr':1000},now_ts=time.time(),native_fixed_watch=True)==allowed
    if allowed:assert not H._scanner_async_quote_is_fresh({'curr':1000},now_ts=time.time())


def test_priority_queue_moves_confirmed_before_fresh_background_without_preemption():
    from src.engine.scalping.scanner_async_eval import ScannerAsyncEvalContext, ScannerAsyncEvalRequest, ScannerAsyncEvalCoordinator
    from src.engine.scalping.scanner_runtime_scheduler import ScannerGeneration
    from src.engine.ai.hot_path_ai_dispatcher import HotPathAIDispatcher
    now=time.time();entered=threading.Event();release=threading.Event();order=[]
    coordinator=ScannerAsyncEvalCoordinator(ai_dispatcher=HotPathAIDispatcher(loaded_key_count=1))
    def request(name,confirmed=False):
        generation=ScannerGeneration(code='005930',promotion_id=name,revision=1,record_id=1,
            venue='KRX',promotion_epoch=now,attach_epoch=now,observed_price=1000,source_signature='test')
        context=ScannerAsyncEvalContext.create(generation=generation,cache_key=name,submitted_epoch=now,
            deadline_epoch=now+2,stock_snapshot={'_continuous_reversal_pending_claim':
                {'snapshot':[{'decision_phase':'CONFIRMED_UPTICK' if confirmed else 'FIRST_UPTICK'}]}},
            ws_snapshot={},state_version='watch')
        def prepare(_):
            if name=='active':entered.set();release.wait(1)
            order.append(name);return {}
        return ScannerAsyncEvalRequest(context,prepare,lambda *a:{'action':'WAIT'},requires_ai_dispatch=False)
    try:
        coordinator.submit(request('active'));assert entered.wait(1)
        coordinator.submit(request('background'));coordinator.submit(request('confirmed',True))
        release.set()
        deadline=time.time()+1
        while len(order)<3 and time.time()<deadline:time.sleep(.005)
        assert order==['active','confirmed','background']
    finally:release.set();coordinator.shutdown()


def test_official_twenty_day_index_request_keeps_two_value_helper_separate(monkeypatch):
    from src.utils import kiwoom_utils as U
    rows=[{'dt':(datetime(2026,10,8)-timedelta(days=i)).strftime('%Y%m%d'),'cur_prc':'250000'} for i in range(20)]
    calls=[]
    def fetch(**kw):
        calls.append(kw)
        return [{'return_code':0,'inds_dt_pole_qry':rows}]
    monkeypatch.setattr(U,'fetch_kiwoom_api_continuous',fetch)
    result=U.get_index_twenty_day_regime_ka20006('not-a-real-token',base_date='20261008')
    assert result['current_close']==2500 and result['valid_dates']==20
    assert calls[0]['url'].endswith('/api/dostk/chart')
    assert calls[0]['payload']=={'inds_cd':'001','base_dt':'20261008'}
    assert calls[0]['use_continuous'] is False
    monkeypatch.setattr(U,'fetch_kiwoom_api_continuous',lambda **kw:[{'inds_dt_pole_qry':rows}])
    with pytest.raises(ValueError,match='missing_or_failed'):
        U.get_index_twenty_day_regime_ka20006('not-a-real-token',base_date='20261008')


def test_radar_worker_does_not_freshen_slow_query_or_fall_back_after_expiry(monkeypatch):
    from src.engine import signal_radar as R
    radar=R.SniperRadar.__new__(R.SniperRadar)
    radar._regime_age_sec=30
    clock=[100.]
    monkeypatch.setattr(R.time,'time',lambda:clock[0])
    monkeypatch.setattr(R.time,'perf_counter',lambda:clock[0])
    def slow(_):
        clock[0]=131.
        raise ValueError('incomplete')
    monkeypatch.setattr(R.fdr,'DataReader',slow)
    monkeypatch.setattr(R.kiwoom_utils,'get_index_twenty_day_regime_ka20006',lambda *a,**kw:pytest.fail('expired fallback request'))
    value=radar._fetch_market_regime('not-a-real-token')
    assert value['regime']=='BEAR' and value['source_quality']=='invalid'
    assert value['fetched_epoch']==100 and value['completed_epoch']==131


def test_transport_decoded_metadata_keeps_only_counts_and_exact_attempt(monkeypatch):
    response=SimpleNamespace(status_code=200,content=b'1234')
    result=T.measured_http_call(lambda *a,**kw:response,'https://api.kiwoom.com/api/dostk/chart',
        telemetry_owner='metadata-test',telemetry_code='005930_AL',headers={'api-id':'ka10080','authorization':'secret'})
    T.record_decoded_response(result,{'return_code':0,'acct_no':'PRIVATE'})
    rec=T.snapshot()['recent_attempts'][-1]
    assert rec['body_return_code']=='0' and rec['response_bytes']==4
    assert rec['route']=='SOR' and rec['started_kst_date']
    assert 'PRIVATE' not in str(T.snapshot())
    T.record_decoded_response(SimpleNamespace(),{'return_code':1})
    assert T.snapshot()['recent_attempts'][-1]['body_return_code']=='0'


@pytest.mark.parametrize('api,body,route', [
    ('kt00011', {}, 'unknown'), ('kt10000', {'dmst_stex_tp':'SOR'}, 'SOR'),
    ('kt10001', {'dmst_stex_tp':'NXT'}, 'NXT'),
    ('kt10000', {'dmst_stex_tp':{}}, 'unknown'), ('ka10080', {}, 'KRX'),
])
def test_account_symbol_does_not_invent_a_transport_venue(api, body, route):
    calls=[]
    def transport(url, **kwargs):
        calls.append(kwargs)
        return SimpleNamespace(status_code=200)
    T.measured_http_call(transport, 'https://api.kiwoom.com/api/dostk/acnt',
        telemetry_owner='route-test', telemetry_code='196170',
        headers={'api-id':api}, json=body)
    assert T.snapshot()['recent_attempts'][-1]['route']==route
    assert calls[0]['json'] is body


@pytest.mark.parametrize('hour,capacity', [(8,50),(14,390),(17,240)])
def test_main_full_history_retains_rest_before_dead_projection_binding(monkeypatch, hour, capacity):
    from zoneinfo import ZoneInfo
    from src.trading.market import shared_ws_snapshot as S
    from src.engine.scalping.entry_candle_context import fetch_entry_candles_with_meta
    monkeypatch.setenv('KORSTOCKSCAN_MAIN_BAR_SOURCE','ws_when_ready')
    monkeypatch.setenv('KORSTOCKSCAN_MAIN_BAR_WS_SYMBOLS','005930')
    monkeypatch.setattr(S,'read_shared_completed_bars',lambda *a,**kw:pytest.fail('unsupported history must not consult a retired writer'))
    calls=[]
    def rest(token, code, **kwargs):
        calls.append((code,kwargs))
        return [], {'api_id':'ka10080'}
    monkeypatch.setattr('src.utils.kiwoom_utils.get_minute_candles_ka10080_with_meta',rest)
    now=datetime(2026,10,8,hour,10,tzinfo=ZoneInfo('Asia/Seoul'))
    receipt={}
    assert S.selected_completed_bar_payload('005930_AL',now=now,minimum_bars=430,
        history_scope='session',selection_receipt=receipt) is None
    assert receipt['maximum_session_bars']==capacity
    if hour==14:
        ws={'last_realtime_type_ts':{'0B':now.timestamp()-.1},
            'last_realtime_type_market_suffix':{'0B':'_AL'},
            'last_realtime_type_market_route':{'0B':'krx_nxt_integrated'}}
        _, meta=fetch_entry_candles_with_meta('token','005930_AL',ws,
            venue='KRX_NXT_INTEGRATED',session='krx_regular',limit=40,now_ts=now,
            broker_route='SOR',allow_integrated_sor_execution_view=True)
        assert calls==[('005930_AL',{'limit':430,'explicit_request_code':True})]
        assert meta['completed_bar_selection']['reason']=='requested_history_exceeds_projection_scope'


@pytest.mark.parametrize('mode,floor',[('ws_when_ready',10),('ws',430)])
def test_supported_or_strict_ws_history_keeps_invalid_writer_fail_closed(monkeypatch,mode,floor):
    from zoneinfo import ZoneInfo
    from src.trading.market import shared_ws_snapshot as S
    monkeypatch.setenv('KORSTOCKSCAN_MAIN_BAR_SOURCE',mode)
    monkeypatch.setenv('KORSTOCKSCAN_MAIN_BAR_WS_SYMBOLS','005930')
    def invalid(*a,**kw):raise ValueError('completed_bar_live_binding_invalid')
    monkeypatch.setattr(S,'read_shared_completed_bars',invalid)
    with pytest.raises(RuntimeError,match='completed_bar_live_binding_invalid'):
        S.selected_completed_bar_payload('005930_AL',
            now=datetime(2026,10,8,14,10,tzinfo=ZoneInfo('Asia/Seoul')),minimum_bars=floor)


def test_carried_registered_scope_diagnostics_use_native_cell_and_original_rows(monkeypatch):
    from copy import deepcopy
    from src.engine.scalping import continuous_reversal as K, reversal_current_backend as D
    from src.engine.scalping.reversal_source_diagnostics import project
    from src.engine.scalping.reversal_path_catalog import cell_key
    from src.tests.test_continuous_reversal import rows
    state=K.ReversalState()
    seq=rows([100]*120+[99,100])
    for r in seq:state.observe(r,symbol='036930',venue='SOR',session='SOR_REGULAR')
    snapshot=deepcopy(state.snapshot())
    event=snapshot[0]
    event.update(native_epoch=seq[-1][1],native_sequence=seq[-1][2])
    at=seq[-1][0];day=datetime.fromtimestamp(at,K.KST).date().isoformat()
    cell=cell_key('036930','REGULAR',100)
    key=('036930','SOR','036930_AL','REGULAR',day,cell)
    carried=SimpleNamespace(_LOCK=threading.RLock(),_STATES={key:SimpleNamespace(legacy=state)})
    native=SimpleNamespace(_LOCK=threading.RLock(),_STATES={},R=carried,
        _FAMILY={'schema':'continuous_reversal_policy_v6','machine_cells':{cell:{'routes':{'SOR':{'backend':'registered_v4'}}}}})
    monkeypatch.setattr(D,'backend',lambda *a:native)
    result=project(snapshot,symbol='036930',venue='SOR',session='SOR_REGULAR',now=at,item='036930_AL')
    assert result['status']=='observed' and result['volume_ratio_source_status']=='ready'
    assert result['volume_ratio_observed_seconds']==121


def test_async_original_monotonic_budget_cannot_be_renewed_after_wall_clock_jump(monkeypatch):
    from src.engine.scalping.scanner_async_eval import ScannerAsyncEvalContext, FixedWatchGeneration
    monkeypatch.setattr(time,'time',lambda:100.)
    monkeypatch.setattr(time,'perf_counter',lambda:10.)
    ctx=ScannerAsyncEvalContext.create(generation=FixedWatchGeneration('005930','SOR','fixed-watch:x','sha',100.),
        cache_key='x',submitted_epoch=100,deadline_epoch=105,stock_snapshot={},ws_snapshot={},state_version='watch')
    monkeypatch.setattr(time,'time',lambda:101.)
    monkeypatch.setattr(time,'perf_counter',lambda:15.1)
    assert ctx.expired()
    with pytest.raises(ValueError,match='deadline_expired'):
        EntryDeadline.create({'snapshot':[{'epoch':100.}]},105,ctx.deadline_perf).require()
