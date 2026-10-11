"""Integration regressions for quantity source, clocks and frozen selection."""
import copy
import json
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.database.models import TradePerformanceFact, StrategyPositionPerformanceDaily
from src.engine.scalping import initial_quantity_policy as policy
from src.engine.scalping.initial_quantity_refresh_evaluation import cap_selection, execution_case
from src.tests.test_initial_quantity_policy import _cap_context, _quality, _facts, _event
from src.tests.test_initial_quantity_timeout import _research_trade_path


def test_native_fact_sync_preserves_null_real_zero_and_provenance(monkeypatch,tmp_path):
    from src.engine import strategy_position_performance_report as mod
    from src.engine.scalping import scale_in_split_order_plan as scale
    engine=create_engine('sqlite:///:memory:')
    TradePerformanceFact.__table__.create(engine)
    StrategyPositionPerformanceDaily.__table__.create(engine)
    class DB:
        def init_db(self):pass
        def analyze_performance_tables(self):pass
        @contextmanager
        def get_session(self):
            with Session(engine) as session, session.begin():yield session
    day='2026-10-08'
    facts=[]
    for rid,value in ((1,None),(2,0)):
        facts.append(dict(recommendation_id=rid,rec_date=date.fromisoformat(day),stock_code='005930',strategy='SCALPING',position_tag='SCANNER',status='COMPLETED',buy_price=100,buy_qty=1,sell_price=100,buy_time=datetime(2026,10,8,9),sell_time=datetime(2026,10,8,10),profit_rate=value,realized_pnl_krw=value,
                          economics_source_status='unresolved' if value is None else 'broker_actual_cost_reconciled',actual_cost_reconciliation_status='actual_cost_reconciled' if value==0 else 'cost_source_unavailable',actual_cost_source_generation='generation',completion_census_run_id='run',completion_census_projection_sha256='projection',broker_actual_fees_taxes_krw=value))
    monkeypatch.setattr(mod,'_DB',DB())
    monkeypatch.setattr(mod,'_FACT_SYNC_STATUS_DIR',tmp_path)
    monkeypatch.setattr(mod,'_build_trade_fact_rows',lambda *a,**k:(facts,[]))
    monkeypatch.setattr(scale,'_query_actual_fill_inventory',lambda *a:[])
    result=mod.sync_trade_performance_for_date(day)
    assert result['status']=='succeeded'
    with Session(engine) as session:
        a=session.get(TradePerformanceFact,1);b=session.get(TradePerformanceFact,2)
        assert (a.profit_rate,a.realized_pnl_krw)==(None,None)
        assert (b.profit_rate,b.realized_pnl_krw)==(0,0)
        assert b.actual_cost_source_generation=='generation'
        assert b.broker_actual_fees_taxes_krw==0
        summary=session.get(StrategyPositionPerformanceDaily,(date.fromisoformat(day),'SCALPING','SCANNER'))
        assert summary.realized_pnl_krw==0


def actual_fact(rid=1,day='2026-10-08',fees=200):
    return dict(recommendation_id=rid,rec_date=day,stock_code='005930',strategy='SCALPING',position_tag='SCANNER',status='COMPLETED',buy_price=100000,buy_qty=1,sell_price=101000,buy_time=day+'T09:30:00+09:00',sell_time=day+'T10:00:00+09:00',profit_rate=(1000-fees)/1000,realized_pnl_krw=1000-fees,
                economics_source_status='broker_actual_cost_reconciled',actual_cost_reconciliation_status='actual_cost_reconciled',actual_cost_source_generation='a'*64,completion_census_run_id='run',completion_census_projection_sha256='b'*64,broker_actual_fees_taxes_krw=fees)


def test_actual_cost_census_accepts_broker_cost_not_configured_rate(tmp_path):
    fact=actual_fact();_quality(tmp_path,'2026-10-08')
    rows,census=policy.completed_trade_fact_census('2026-10-08',data_dir=tmp_path,fact_rows=[fact],entry_on_or_after='2026-09-29')
    assert len(rows)==1 and rows[0]['realized_net_pnl_krw']==800
    assert rows[0]['cost_basis']=='broker_actual'
    assert rows[0]['modeled_parent_net_pnl_krw']!=800
    bad={**fact,'completion_census_run_id':None}
    good,census=policy.completed_trade_fact_census('2026-10-08',data_dir=tmp_path,fact_rows=[fact,{**bad,'recommendation_id':2}],entry_on_or_after='2026-09-29')
    assert len(good)==1 and census['excluded']=={'actual_cost_identity_or_amount_invalid':1}


@pytest.mark.parametrize('value,expected',[('4',4),(4,4),(True,None),('4.0',None),(4.0,None),('',None),('nan',None),('-1',None),('0',0)])
def test_epoch_is_canonical_and_never_default_zero(value,expected):
    assert policy.canonical_epoch(value)==expected


def test_wire_epoch_connects_and_same_execution_has_zero_modeled_delta():
    start=datetime.fromisoformat('2026-10-08T09:30:00+09:00').timestamp()
    context=_cap_context(actual_qty=2)
    context['ask_depth_source']=dict(source_type='ws_0D_bound_snapshot',market_route='KRX',transport_epoch=4,observed_epoch=start-1,item='005930',levels=[dict(price_krw=101,quantity=2)])
    source=dict(context=context,attempt_id='attempt',plan_sha256='a'*64,fills=[dict(at='2026-10-08T09:30:00+09:00',price=100,qty=1,venue='KRX')],following_ticks=[dict(observed_epoch=start+1,price_krw=101,quantity=2,item='005930',depth_item='005930',market_route='KRX',transport_epoch='4',attempt_id='attempt',plan_sha256='a'*64)])
    trade=dict(buy_qty=1,buy_price=100,sell_price=110,realized_net_pnl_krw=8)
    assert policy._cap_candidate_trade(trade,source,'cap_20pct',.0023)['modeled_filled_qty']==2
    result=policy._cap_candidate_trade(trade,source,'cap_10pct',.0023)
    assert result['candidate_net_pnl_krw']==pytest.approx(result['modeled_parent_net_pnl_krw'],abs=.001)
    assert result['actual_net_pnl_krw']==8


def test_holdout_changes_acceptance_never_train_choice_or_next_best():
    rows=[]
    for day in ('2026-10-05','2026-10-06','2026-10-07'):
        for i in range(20):
            rows.append(dict(trade_id=f'{day}:{i}',entry_date=day,actual_net_pnl_krw=10,actual_profit_rate=1,
                cap_candidates={mode:dict(status='partial_unfilled',candidate_net_pnl_krw=value,candidate_net_pct_on_parent_notional=value/10) for mode,value in [('cap_10pct',20),('cap_15pct',15)]}))
    selected,metrics=cap_selection(rows,'parent_5stage',30)
    assert selected=='cap_10pct'
    before=metrics['cap_10pct']['train_selected_candidate_sha256']
    for row in rows[-20:]:row['cap_candidates']['cap_10pct']['candidate_net_pnl_krw']=-100
    selected,metrics=cap_selection(rows,'parent_5stage',30)
    assert selected=='parent_5stage'
    assert metrics['cap_10pct']['train_selected_candidate_sha256']==before
    assert metrics['cap_15pct']['selection_eligible'] is False


def test_joint_replay_probe_is_two_slots_and_price_time_bound():
    trade,path=_research_trade_path();trade['quantity_type']='KRX_PARENT';trade['comparison_cost_rate']=.0023
    start=path['order_starts'][0];start.update(source='initial_quantity_bundle_order_start_at',total_wait_sec=60,probe_applied=True)
    path['fills'][0]['qty']=1
    path['fills'].append({**path['fills'][0], 'at':path['fills'][0]['at']+timedelta(seconds=1), 'qty':3, 'execution_no':'residual'})
    context=_cap_context(budget=1600,actual_qty=4)
    source=dict(context=context,attempt_id='a',plan_sha256='b'*64,following_ticks=[])
    path['decisions'][0]['fields'].update(entry_submit_attempt_id='a',entry_execution_sizing_plan_sha256='b'*64)
    result=execution_case(trade,path,source,mode='parent_5stage',shape='two_leg_0_1tick',horizon=60)
    assert result['target_qty']==4 and result['modeled_filled_qty']==1
    assert result['status']=='partial_unfilled'
    # A fill outside the active second slot cannot complete a hypothetical leg.
    path['fills'][1]['at']=path['fills'][0]['at']+timedelta(seconds=90)
    result=execution_case(trade,path,source,mode='parent_5stage',shape='two_leg_0_1tick',horizon=60)
    assert result['modeled_filled_qty']==1


def test_refresh_window_and_empty_policy_consumption_are_independent(tmp_path):
    assert policy.refresh_window({'effective_from':'2026-09-24'})=='2026-09-29'
    assert policy.refresh_window({'effective_from':'2026-10-01'})=='2026-10-01'
    assert policy._natural_refresh_pid_receipt({'trades':[],'source_date':'2026-10-08'},dict(effective_from='2026-09-24'),tmp_path/'parent.json',tmp_path) is None


def test_cost_only_warm_features_do_not_decode_pipeline(tmp_path,monkeypatch):
    day='2026-10-08';_quality(tmp_path,day)
    facts=[actual_fact()]
    pipeline=tmp_path/'pipeline_events';pipeline.mkdir()
    (pipeline/f'pipeline_events_{day}.jsonl').write_text(json.dumps(_event(1,'nothing',day+'T09:30:00+09:00'))+'\n')
    cold=policy.build_initial_quantity_replay(day,data_dir=tmp_path,fact_rows=facts,entry_on_or_after='2026-09-29')
    def forbidden(*a,**k):raise AssertionError('warm feature cache rescanned the source')
    monkeypatch.setattr(policy,'_join_post_fill_paths_uncached',forbidden)
    warm=policy.build_initial_quantity_replay(day,data_dir=tmp_path,fact_rows=facts,entry_on_or_after='2026-09-29')
    assert warm==cold
    corrected=policy.build_initial_quantity_replay(day,data_dir=tmp_path,fact_rows=[actual_fact(fees=300)],entry_on_or_after='2026-09-29')
    assert corrected['census']['actual_completed_net_pnl_krw']==700
    assert corrected['report_content_sha256']!=cold['report_content_sha256']


def parent_fixture(tmp_path):
    from src.engine.scalping.initial_quantity_activation import build_initial_quantity_baseline
    from src.engine.scalping.initial_quantity_following_bars import build_following_bar_source
    day='2026-09-24';_quality(tmp_path,day)
    facts=_facts([dict(recommendation_id=9,stock_code='005930',strategy='SCALPING',position_tag='SCANNER',buy_price=100,sell_price=99,buy_qty=4,sell_time='09:35:00',held_sec=300)],day)
    seed=policy.build_initial_quantity_replay(day,data_dir=tmp_path,fact_rows=facts)
    following=build_following_bar_source(seed,fetch=lambda *a: (_ for _ in ()).throw(AssertionError('no winners')))
    stage=policy.publish_initial_quantity_candidate(seed,output_dir=tmp_path/'seed',following_bars=following)
    parent=build_initial_quantity_baseline(stage);path=(tmp_path/'parent.json').resolve();policy._write_immutable_json(path,parent)
    return parent,path


def test_v2_same_date_successors_and_consumer_pointer(tmp_path):
    from src.engine.scalping.initial_quantity_timeout_research import build_timeout_research
    parent,path=parent_fixture(tmp_path);base=tmp_path/'refresh';day='2026-10-08'
    before=None
    for facts in ([],[{**actual_fact(),'profit_rate':None,'realized_pnl_krw':None}]):
        shared={};report=policy.build_initial_quantity_replay(day,data_dir=tmp_path,fact_rows=facts,entry_on_or_after=policy.refresh_window(parent),path_cache=shared)
        timeout=build_timeout_research(day,data_dir=tmp_path,fact_rows=facts,entry_on_or_after=policy.refresh_window(parent),path_cache=shared,replay=report)
        stage=policy.publish_refresh_quantity_evaluation(report,parent_policy=parent,parent_policy_path=path,output_dir=base,timeout_research=timeout,terminal_receipt=policy._natural_refresh_terminal_receipt(report))
        assert policy.refresh_quantity_stage_terminal_valid(stage)
        current=policy.committed_refresh_stage_path(base,day)
        assert current.exists() and json.loads(current.read_bytes())==stage
        assert stage['decision']=='carry_parent'
        if before:
            assert before!=current and before.exists()
        before=current
    ref=json.loads((base/'committed_stage.json').read_bytes());ref['stage_sha256']='0'*64
    (base/'committed_stage.json').write_text(json.dumps(ref))
    with pytest.raises(ValueError,match='quantity_stage_reference_invalid'):policy.committed_refresh_stage_path(base,day)


def test_recent_replay_missing_cost_is_not_no_real_trade_or_no_pid(tmp_path):
    from src.engine.scalping.initial_quantity_refresh_evaluation import evaluate
    parent,path=parent_fixture(tmp_path)
    report=policy.build_initial_quantity_replay('2026-10-08',data_dir=tmp_path,fact_rows=[{**actual_fact(),'profit_rate':None}],entry_on_or_after=policy.refresh_window(parent))
    result=evaluate(report,parent_policy=parent,parent_policy_file_sha256=policy._file_sha256(path),pid_receipt=dict(actual_pid_consumed=True,policy_content_sha256=parent['policy_content_sha256'],daily_pid_receipts=[dict(entry_date='2026-10-08',pid=123,verified_at='2026-10-08T08:00:00+09:00')]),terminal_receipt=policy._natural_refresh_terminal_receipt(report))
    assert result['policy_pid_status']=='verified_archive'
    assert result['economic_sample_status']=='cost_missing'
    assert 'parent_pid_consumption_missing' not in result['global_blockers']


def test_actual_cost_object_survives_text_db_and_quantity_consumer(monkeypatch,tmp_path):
    from src.engine import strategy_position_performance_report as mod
    native=dict(schema='holding_actual_cost_source_generation_v1',completion_date='2026-10-08',count=1,sha256='a'*64,status='observed')
    fact={**actual_fact(),'actual_cost_source_generation':native}
    persisted=mod._trade_fact_db_payload(fact)
    assert json.loads(persisted['actual_cost_source_generation'])==native
    _quality(tmp_path,'2026-10-08')
    rows,_=policy.completed_trade_fact_census('2026-10-08',data_dir=tmp_path,fact_rows=[persisted],entry_on_or_after='2026-09-29')
    assert len(rows)==1


def test_late_invalid_fact_duplicate_invalidates_earlier_good_row(tmp_path):
    _quality(tmp_path,'2026-10-08')
    good=actual_fact();bad={**good,'realized_pnl_krw':None}
    rows,census=policy.completed_trade_fact_census('2026-10-08',data_dir=tmp_path,fact_rows=[good,bad],entry_on_or_after='2026-09-29')
    assert rows==[] and census['excluded']=={'conflicting_duplicate_fact':2}


def test_frozen_order_start_extends_capture_once_and_queue_is_nonblocking(monkeypatch):
    from src.engine import sniper_state_handlers as handler
    from src.engine.scalping import initial_quantity_cap_observation as observer
    from src.trading.market import quote_consistency
    start=datetime.fromisoformat('2026-10-08T09:30:00+09:00').timestamp()
    stock=dict(id=1,name='test',_initial_quantity_cap_trace=dict(started_at_epoch=start-1100,entry_submit_attempt_id='a',entry_execution_sizing_plan_sha256='b'*64,depth_item='005930',depth_route='KRX',transport_epoch=4))
    handler._start_initial_quantity_cap_capture(stock,attempt_id='a',submission_fields=dict(entry_cancel_wait_submission_context=json.dumps(dict(frozen_at=datetime.fromtimestamp(start,handler._KST).isoformat()))))
    handler._start_initial_quantity_cap_capture(stock,attempt_id='a',submission_fields=dict(entry_cancel_wait_submission_context=json.dumps(dict(frozen_at=datetime.fromtimestamp(start+100,handler._KST).isoformat()))))
    assert stock['_initial_quantity_cap_trace']['order_capture_end_epoch']==start+1200
    events=[]
    observer.configure_sink(lambda *args,**kw:(events.append((args,kw)) or {'status':'queued'}))
    monkeypatch.setattr(handler,'_log_holding_pipeline',lambda *a,**k:pytest.fail('synchronous cap writer'))
    monkeypatch.setattr(quote_consistency,'ws_quote_source_receipt',lambda *a,**kw:dict(source_type='0B',observed_epoch=start+200,item='005930',market_route='KRX',transport_epoch=4,depth_receipt=dict(item='005930',market_route='KRX',transport_epoch=4)))
    tick=dict(aggressor_source='kiwoom_0b_signed_trade_volume',signed_trade_volume='+10',price=100,ts=start+200)
    handler._observe_initial_quantity_cap_following_tick(stock,'005930',dict(last_trade_tick=tick),now_ts=start+200)
    assert len(events)==1 and events[0][1]['record_id']==1
    assert events[0][1]['fields']['cap_tick_observation_coverage']=='sampled_last_trade_tick'
    handler._observe_initial_quantity_cap_following_tick(stock,'005930',dict(last_trade_tick=tick),now_ts=start+200)
    assert len(events)==1 and stock['_initial_quantity_cap_trace']['duplicate_observation_count']==1
    handler._observe_initial_quantity_cap_following_tick(stock,'005930',dict(last_trade_tick=tick),now_ts=start+1201)
    assert '_initial_quantity_cap_trace' not in stock and events[-1][0][-1]=='initial_quantity_cap_capture_finished'
    observer.configure_sink(None)


@pytest.mark.parametrize('route,item,venue,order_route',[
    ('krx_only','005930','KRX','KRX'),
    ('nxt_only','005930_NX','NXT','NXT'),
    ('krx_nxt_integrated','005930_AL','KRX','SOR'),
    ('krx_nxt_integrated','005930_AL','NXT','SOR'),
])
def test_native_quote_route_reaches_live_quantity_capture(monkeypatch,route,item,venue,order_route):
    from src.engine import sniper_state_handlers as handler
    from src.trading.market import quote_consistency
    from src.engine.scalping import position_sizing_allocator as allocator
    from src.tests.test_scalping_position_sizing_allocator import _context
    at=datetime.fromisoformat('2026-10-08T10:00:00+09:00').timestamp()
    context=_context('2026-10-08T10:00:00',venue=venue)
    decision=allocator.resolve_scalping_allocation(context)
    receipt=dict(source_type='0D',item=item,market_route=route,transport_epoch=4,
                 depth_receipt=dict(item=item,market_route=route,transport_epoch=4,observed_epoch=at))
    monkeypatch.setattr(quote_consistency,'ws_quote_source_receipt',lambda *a,**kw:receipt)
    raw=dict(orderbook=dict(asks=[dict(price=100,volume=20)]))
    value=handler._initial_quantity_cap_research_context(context,decision,ws_data=raw,now_ts=at)
    assert value['ask_depth_source']['market_route']==route
    assert value['ask_depth_source']['order_route']==order_route
    assert value['ask_depth_source']['underlying_event_venue_proven'] is (order_route!='SOR')
    receipt['depth_receipt']['item']='005930_NX' if item!='005930_NX' else '005930'
    value=handler._initial_quantity_cap_research_context(context,decision,ws_data=raw,now_ts=at)
    assert 'ask_depth_source' not in value


def test_integrated_quote_is_sor_replay_without_manufacturing_fill_venue():
    trade,path=_research_trade_path();trade.update(quantity_type='KRX_PARENT',comparison_cost_rate=.0023)
    first=path['fills'][0];first['qty']=1
    path['fills'].append({**first,'at':first['at']+timedelta(seconds=30),'qty':3,'venue':'NXT','execution_no':'2'})
    start=path['order_starts'][0];start.update(source='initial_quantity_bundle_order_start_at',total_wait_sec=60,probe_applied=True)
    at=start['at'].timestamp();context=_cap_context(budget=1600,actual_qty=4)
    context['ask_depth_source']=dict(source_type='ws_0D_bound_snapshot',item='005930_AL',market_route='krx_nxt_integrated',observed_epoch=at,transport_epoch=4,levels=[dict(price_krw=99,quantity=20),dict(price_krw=100,quantity=20)])
    source=dict(context=context,attempt_id='a',plan_sha256='b'*64,following_ticks=[dict(attempt_id='a',plan_sha256='b'*64,depth_item='005930_AL',item='005930_AL',market_route='krx_nxt_integrated',transport_epoch='4',observed_epoch=at+40,price_krw=99,quantity=20)])
    path['decisions'][0]['fields'].update(entry_submit_attempt_id='a',entry_execution_sizing_plan_sha256='b'*64)
    value=execution_case(trade,path,source,mode='parent_5stage',shape='two_leg_0_1tick',horizon=60)
    assert value['status']=='paired' and value['modeled_filled_qty']==4
    assert [row['venue'] for row in path['fills']]==['KRX','NXT']
    source['following_ticks'][0]['market_route']='nxt_only'
    value=execution_case(trade,path,source,mode='parent_5stage',shape='two_leg_0_1tick',horizon=60)
    assert value['status']=='partial_unfilled' and value['modeled_filled_qty']==1


def test_capture_terminal_queue_gap_is_preserved_in_source_features(tmp_path):
    day='2026-10-08';_quality(tmp_path,day)
    trades,_=policy.completed_trade_fact_census(day,data_dir=tmp_path,fact_rows=[actual_fact()],entry_on_or_after='2026-09-29')
    directory=tmp_path/'pipeline_events';directory.mkdir()
    event=_event(1,'initial_quantity_cap_capture_finished',day+'T09:51:00+09:00',entry_submit_attempt_id='a',entry_execution_sizing_plan_sha256='b'*64,capture_queue_rejected_count=7,capture_queued_count=20,observation_coverage='sampled_last_trade_tick')
    event['stock_code']='005930'
    (directory/f'pipeline_events_{day}.jsonl').write_text(json.dumps(event)+'\n')
    paths=policy.join_post_fill_paths(trades,data_dir=tmp_path)
    value=paths[trades[0]['trade_id']]['capture_receipts'][0]['fields']
    assert value['capture_queue_rejected_count']==7
    assert value['observation_coverage']=='sampled_last_trade_tick'


def test_quantity_fact_validator_never_decodes_oversized_legacy_timeline(monkeypatch,tmp_path):
    from src.engine import log_archive_service as archive
    from src.engine import strategy_position_performance_report as fact
    from src.engine.lifecycle.holding_window_generation import MAX_PROJECTION_BYTES
    monkeypatch.setattr(archive,'MONITOR_SNAPSHOT_DIR',tmp_path)
    monkeypatch.setattr(fact,'_saved_fact_generation_issue',lambda *a,**k:pytest.fail('unbounded snapshot decode'))
    path=tmp_path/'trade_review_2026-09-30.json'
    with path.open('wb') as handle:handle.truncate(MAX_PROJECTION_BYTES+1)
    assert policy._quantity_fact_generation_issue('2026-09-30')=='trade_review_snapshot_missing'
    with path.with_suffix('.completed_projection.json').open('wb') as handle:handle.truncate(MAX_PROJECTION_BYTES+1)
    assert policy._quantity_fact_generation_issue('2026-09-30')=='fact_snapshot_requires_bounded_native_projection'


def test_quantity_reservation_uses_shared_slots_and_verified_nested_owner(tmp_path):
    from src.engine.lifecycle import research_admission as mod
    r=mod.acquire(tmp_path,'initial_entry_quantity_refresh','2026-10-08')
    assert len(r.handles)==2
    try:
        assert mod.acquire(tmp_path,'main_trailing_all_scope','2026-10-08') is None
        with r.worker(),mod.direct_job(tmp_path,'initial_entry_quantity_refresh','2026-10-08',timeout=0):pass
        with r.worker(),pytest.raises(ValueError,match='identity_invalid'):
            with mod.direct_job(tmp_path,'pre_submit_delay','2026-10-08',timeout=0):pass
    finally:r.close()
    r=mod.acquire(tmp_path,'pre_submit_delay','2026-10-08');assert len(r.handles)==2;r.close()


def _positive_joint_fixture(root):
    parent,parent_path=parent_fixture(root);sha=policy._file_sha256(parent_path)
    facts=[];pid=[];pipeline=root/'pipeline_events';pipeline.mkdir()
    for di,day in enumerate(('2026-10-05','2026-10-06','2026-10-07')):
        _quality(root,day);events=[];pid.append(dict(entry_date=day,pid=123,verified_at=day+'T08:00:00+09:00'))
        for i in range(20):
            rid=100+di*20+i;start=datetime.fromisoformat(day+'T09:30:00+09:00')+timedelta(minutes=i)
            decision=start-timedelta(seconds=1);first=start+timedelta(seconds=5);exit=start+timedelta(seconds=300)
            facts.append({**actual_fact(rid,day),'buy_price':100,'buy_qty':4,'sell_price':110,'profit_rate':9.75,'realized_pnl_krw':39,'broker_actual_fees_taxes_krw':1,'buy_time':first.isoformat(),'sell_time':exit.isoformat()})
            context=_cap_context(budget=1600,actual_qty=4);context.update(quantity_type='KRX_PARENT',ask_depth_source=dict(source_type='ws_0D_bound_snapshot',observed_epoch=decision.timestamp(),item='005930',market_route='KRX',transport_epoch=4,levels=[dict(price_krw=99,quantity=20),dict(price_krw=100,quantity=20)]))
            base=dict(entry_submit_attempt_id=str(rid),entry_execution_sizing_plan_sha256='b'*64)
            def event(stage,at,**fields):
                v=_event(rid,stage,at.isoformat(),**fields);v['stock_code']='005930';events.append(v)
            event('entry_execution_sizing_plan',decision,**base,entry_execution_sizing_valid=True,effective_venue='KRX',quantity_type='KRX_PARENT',quantity_type_classifier_version='initial_quantity_type_v1',ratio=.25,effective_qty=4,reference_time=decision.isoformat(),position_sizing_policy_status='initial_policy_loaded',position_sizing_policy_sha256=sha,scalping_sizing_position_sizing_policy_sha256=sha,initial_quantity_runtime_pid=123,initial_quantity_cap_research_context=json.dumps(context))
            event('order_leg_sent',start,**base,tag='initial_quantity_leg_0',broker_order_no=str(rid),actual_order_submitted=True,initial_quantity_order_start_at=start.isoformat(),initial_quantity_bundle_total_wait_sec=60,initial_quantity_schedule_sha256='c'*64,initial_quantity_policy_file_sha256=sha,initial_quantity_attempt_id=str(rid),initial_quantity_leg_index=0)
            event('position_rebased_after_fill',first,fill_qty=4,fill_price=100,entry_mode='normal',order_no=str(rid),execution_no='1',actual_execution_venue='KRX',broker_execution_observed_at=first.isoformat())
            event('initial_quantity_cap_following_tick',start+timedelta(seconds=40),**base,cap_tick_observed_epoch=(start+timedelta(seconds=40)).timestamp(),cap_tick_price_krw=99,cap_tick_quantity=20,cap_tick_item='005930',cap_tick_depth_item='005930',cap_tick_market_route='KRX',cap_tick_transport_epoch='4',decision_authority='source_only_cap_fill_research',actual_order_submitted=False)
        (pipeline/f'pipeline_events_{day}.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events))
    receipt=dict(source='verified_daily_preopen_main_pid_env',data_root=str(root.resolve()),first_consumed_date='2026-10-05',policy_file_sha256=sha,actual_pid_consumed=True,policy_content_sha256=parent['policy_content_sha256'],daily_pid_receipts=pid)
    return parent,parent_path,facts,receipt


def test_joint_eligible_shape_publishes_and_isolates_one_bad_binding(monkeypatch,tmp_path):
    from src.engine.scalping.initial_quantity_timeout_research import build_timeout_research
    parent,path,facts,pid=_positive_joint_fixture(tmp_path);cache={}
    report=policy.build_initial_quantity_replay('2026-10-07',data_dir=tmp_path,fact_rows=facts,entry_on_or_after=policy.refresh_window(parent),path_cache=cache)
    timeout=build_timeout_research('2026-10-07',data_dir=tmp_path,fact_rows=facts,entry_on_or_after=policy.refresh_window(parent),path_cache=cache,replay=report)
    monkeypatch.setattr(policy,'_natural_refresh_pid_receipt',lambda *a,**kw:pid)
    from src.engine.scalping.initial_quantity_following_bars import build_following_bar_source
    def fetch(code,day,limit):
        base=datetime.strptime(day,'%Y%m%d').replace(hour=9,minute=30,tzinfo=__import__('zoneinfo').ZoneInfo('Asia/Seoul'))
        candles=[dict(source_timestamp=(base+timedelta(minutes=i)).strftime('%Y%m%d%H%M%S'),저가=99) for i in range(61)]
        return candles,dict(api_id='ka10080',request_code=code,request_base_dt=day)
    following=build_following_bar_source(report,fetch=fetch)
    stage=policy.publish_refresh_quantity_evaluation(report,parent_policy=parent,parent_policy_path=path,output_dir=tmp_path/'refresh',pid_receipt=pid,following_bars=following,terminal_receipt=policy._natural_refresh_terminal_receipt(report),timeout_research=timeout)
    evaluation=json.loads(Path(stage['evaluation_path']).read_bytes())
    assert evaluation['state']=='eligible_source_only'
    assert evaluation['type_decisions']['KRX_PARENT']['selected_shape']!='parent'
    assert stage['following_bar_source_status']=='source_bound'
    assert policy.refresh_quantity_stage_terminal_valid(stage)
    # One identifiable binding loss leaves the remaining 59 trades usable.
    changed=copy.deepcopy(report);changed['trades'][0]['applied_policy_status']='wrong'
    changed['report_content_sha256']=policy._digest({k:v for k,v in changed.items() if k!='report_content_sha256'})
    from src.engine.scalping.initial_quantity_refresh_evaluation import evaluate
    result=evaluate(changed,parent_policy=parent,parent_policy_file_sha256=policy._file_sha256(path),pid_receipt=pid,terminal_receipt=policy._natural_refresh_terminal_receipt(changed))
    assert result['parent_policy_bound_trade_count']==59
    assert result['trade_policy_binding_status']=='partial'


def test_cache_corruption_rebuild_and_incremental_date_scan(tmp_path,monkeypatch):
    _quality(tmp_path,'2026-10-08');pipeline=tmp_path/'pipeline_events';pipeline.mkdir()
    (pipeline/'pipeline_events_2026-10-08.jsonl').write_text('{}\n')
    facts=[actual_fact()]
    policy.build_initial_quantity_replay('2026-10-08',data_dir=tmp_path,fact_rows=facts,entry_on_or_after='2026-09-29')
    index=next((tmp_path/'report/initial_entry_quantity_type_policy/source_features').rglob('index.json'))
    value=json.loads(index.read_bytes());base=Path(value['tree_root'])
    shard=base/value['tree']['path'];shard.write_bytes(shard.read_bytes()+b' ')
    scans=[];original=policy._join_post_fill_paths_uncached
    def count(rows,**kw):scans.extend(r['entry_date'] for r in rows);return original(rows,**kw)
    monkeypatch.setattr(policy,'_join_post_fill_paths_uncached',count)
    policy.build_initial_quantity_replay('2026-10-08',data_dir=tmp_path,fact_rows=facts,entry_on_or_after='2026-09-29')
    assert scans==['2026-10-08'];scans.clear()
    policy.build_initial_quantity_replay('2026-10-08',data_dir=tmp_path,fact_rows=facts,entry_on_or_after='2026-09-29')
    assert scans==[]
    _quality(tmp_path,'2026-10-09');(pipeline/'pipeline_events_2026-10-09.jsonl').write_text('{}\n')
    policy.build_initial_quantity_replay('2026-10-09',data_dir=tmp_path,fact_rows=facts+[actual_fact(2,'2026-10-09')],entry_on_or_after='2026-09-29')
    assert scans==['2026-10-09']


def test_joint_byte_verified_memo_rejects_resealed_changed_outcome(tmp_path):
    from src.engine.scalping.initial_quantity_timeout_research import build_timeout_research,timeout_research_valid
    from src.engine.lifecycle import research_storage as storage
    parent,path,facts,pid=_positive_joint_fixture(tmp_path);cache={}
    report=policy.build_initial_quantity_replay('2026-10-07',data_dir=tmp_path,fact_rows=facts,entry_on_or_after=policy.refresh_window(parent),path_cache=cache)
    timeout=build_timeout_research('2026-10-07',data_dir=tmp_path,fact_rows=facts,entry_on_or_after=policy.refresh_window(parent),path_cache=cache,replay=report)
    assert timeout_research_valid(timeout,replay=report)
    root=Path(timeout['joint_evidence_root'])
    def corrupt():
        for i,item in enumerate(storage.iter_tree(root,timeout['joint_outcomes_ref'])):
            if i==0:item={**item,'outcome':{**item['outcome'],'candidate_net_pnl_krw':999999}}
            yield item
    altered={**timeout,'joint_outcomes_ref':storage.write_tree(root,corrupt())}
    altered['report_content_sha256']=policy._digest({k:v for k,v in altered.items() if k!='report_content_sha256'})
    assert not timeout_research_valid(altered,replay=report)


def test_empty_completed_census_with_open_rows_is_valid_empty(tmp_path):
    parent,path=parent_fixture(tmp_path)
    report=policy.build_initial_quantity_replay('2026-10-08',data_dir=tmp_path,fact_rows=[{**actual_fact(),'status':'OPEN'}],entry_on_or_after=policy.refresh_window(parent))
    result=policy.evaluate_refresh_quantity_candidate(report,parent_policy=parent,parent_policy_file_sha256=policy._file_sha256(path),terminal_receipt=policy._natural_refresh_terminal_receipt(report))
    assert result['economic_sample_status']=='valid_empty'


@pytest.mark.parametrize('fields,reason',[
    ({'capture_queue_rejected_count':'7'},'capture_queue_gap'),
    ({'capture_clock_status':'order_start_source_gap'},'capture_clock_gap'),
    ({'capture_clock_status':'capture_clock_invalid'},'capture_clock_gap'),
    ({'capture_queue_rejected_count':True},'capture_queue_count_invalid'),
    ({'capture_queued_count':-1},'capture_queue_count_invalid'),
    ({'capture_queued_count':'9'*5000},'capture_queue_count_invalid'),
])
def test_capture_loss_excludes_counterfactuals_and_preserves_actual_control(fields,reason):
    trade,path=_research_trade_path();trade.update(quantity_type='KRX_PARENT',comparison_cost_rate=.0023)
    path['order_starts'][0].update(source='initial_quantity_bundle_order_start_at',total_wait_sec=60)
    source=dict(context=_cap_context(budget=1600,actual_qty=4),attempt_id='a',plan_sha256='b'*64,
        capture_receipts=[dict(fields=dict(entry_submit_attempt_id='a',entry_execution_sizing_plan_sha256='b'*64,**fields))])
    assert policy._cap_candidate_trade(trade,source,'cap_10pct',.0023)=={'status':reason}
    # All non-control tuples must be loss, even if their model would fill nothing.
    for mode in ('parent_5stage',*policy._CAP_MODES):
        for shape in policy._SHAPES:
            for horizon in (None,60,1200):
                value=execution_case(trade,path,source,mode=mode,shape=shape,horizon=horizon)
                if (mode,shape,horizon)==('parent_5stage','parent',None):
                    assert value['observation_coverage']=='actual_fills'
                    assert value['modeled_filled_qty']==4
                else:
                    assert value==dict(status='source_gap',reason=reason)
    source['capture_receipts'][0]['fields']['entry_submit_attempt_id']='foreign'
    assert policy._capture_source_issue(source) is None
    source['capture_receipts']=[]
    assert policy._capture_source_issue(source) is None


@pytest.mark.parametrize('end,now',[(True,1),(float('nan'),1),(0,1),(1200,-1)])
def test_capture_invalid_bounds_are_explicit_not_normal_completion(monkeypatch,end,now):
    from src.engine import sniper_state_handlers as handler
    from src.engine.scalping import initial_quantity_cap_observation as observer
    start=1000.;events=[]
    monkeypatch.setattr(observer,'append',lambda **kw:(events.append(kw) or True))
    stock=dict(_initial_quantity_cap_trace=dict(started_at_epoch=start,order_capture_end_epoch=end,
               entry_submit_attempt_id='a',entry_execution_sizing_plan_sha256='b'*64,capture_clock_status='frozen_order_start'))
    handler._observe_initial_quantity_cap_following_tick(stock,'005930',{},now_ts=start+now)
    assert len(events)==1
    assert events[0]['fields']['capture_clock_status']=='capture_clock_invalid'
    json.dumps(events[0],allow_nan=False)
    assert '_initial_quantity_cap_trace' not in stock


@pytest.mark.parametrize('now',[float('nan'),True,0])
def test_capture_invalid_observer_clock_retains_gap_until_real_terminal(monkeypatch,now):
    from src.engine import sniper_state_handlers as handler
    from src.engine.scalping import initial_quantity_cap_observation as observer
    events=[];monkeypatch.setattr(observer,'append',lambda **kw:(events.append(kw) or True))
    stock=dict(_initial_quantity_cap_trace=dict(started_at_epoch=1000.,order_capture_end_epoch=2200.,capture_clock_status='frozen_order_start'))
    handler._observe_initial_quantity_cap_following_tick(stock,'005930',{},now_ts=now)
    assert events==[] and stock['_initial_quantity_cap_trace']['capture_clock_status']=='capture_clock_invalid'
    handler._observe_initial_quantity_cap_following_tick(stock,'005930',{},now_ts=2201.)
    assert events[0]['fields']['capture_clock_status']=='capture_clock_invalid'


def test_oversized_execution_index_rebuilds_without_unbounded_read(tmp_path,monkeypatch):
    from src.engine.scalping import initial_quantity_source_cache as cache
    trade,path=_research_trade_path();trade.update(quantity_type='KRX_PARENT',comparison_cost_rate=.0023)
    path['order_starts'][0].update(source='initial_quantity_bundle_order_start_at',total_wait_sec=60)
    tid=trade['trade_id'];source=dict(context=_cap_context(budget=1600,actual_qty=4),attempt_id='a',plan_sha256='b'*64)
    rows={tid:dict(quantity_type='KRX_PARENT',cap_source=source)}
    grid={'control':dict(mode='parent_5stage',shape='parent',horizon=None,reserve=5)}
    def run():return list(cache.joint_records([trade],{tid:path},rows,grid,data_dir=tmp_path,cost_rate=.0023))
    expected=run();index=next(tmp_path.rglob('index.json'))
    with index.open('wb') as handle:handle.truncate(cache.storage.RECORD_BYTES+1)
    original=Path.read_bytes
    def checked(p):
        if p==index:pytest.fail('unbounded index read')
        return original(p)
    monkeypatch.setattr(Path,'read_bytes',checked)
    assert run()==expected
    assert len(list(index.parent.glob('repair-*')))==1
    assert run()==expected


def test_capture_terminal_refusal_keeps_exact_gap_for_bounded_retry(monkeypatch):
    from src.engine import sniper_state_handlers as handler
    from src.engine.scalping import initial_quantity_cap_observation as observer
    events=[]
    def submit(**kw):
        events.append(kw)
        return len(events)==3
    monkeypatch.setattr(observer,'append',submit)
    stock=dict(_initial_quantity_cap_trace=dict(started_at_epoch=1000.,order_capture_end_epoch=2200.,
        entry_submit_attempt_id='a',entry_execution_sizing_plan_sha256='b'*64,capture_clock_status='frozen_order_start'))
    for now in (2201.,2202.):
        handler._observe_initial_quantity_cap_following_tick(stock,'005930',{},now_ts=now)
        assert stock['_initial_quantity_cap_trace']['capture_terminal_pending'] is True
    handler._observe_initial_quantity_cap_following_tick(stock,'005930',{},now_ts=2203.)
    assert '_initial_quantity_cap_trace' not in stock
    assert [e['fields']['capture_queue_rejected_count'] for e in events]==[0,1,2]
    assert all(e['fields']['entry_submit_attempt_id']=='a' for e in events)


def test_feature_cache_invalidates_transitive_reader_change(tmp_path,monkeypatch):
    from src.engine.scalping import initial_quantity_source_cache as cache
    _quality(tmp_path,'2026-10-08');pipeline=tmp_path/'pipeline_events';pipeline.mkdir()
    (pipeline/'pipeline_events_2026-10-08.jsonl').write_text('{}\n')
    facts=[actual_fact()]
    def run():return policy.build_initial_quantity_replay('2026-10-08',data_dir=tmp_path,fact_rows=facts,entry_on_or_after='2026-09-29')
    expected=run();scans=[];join=policy._join_post_fill_paths_uncached
    def count(rows,**kw):scans.extend(r['entry_date'] for r in rows);return join(rows,**kw)
    monkeypatch.setattr(policy,'_join_post_fill_paths_uncached',count)
    assert run()==expected and scans==[]
    original=Path.read_bytes;reader=Path(cache.__file__).with_name('initial_quantity_cap_observation.py')
    monkeypatch.setattr(Path,'read_bytes',lambda p:original(p)+b'\n# changed reader\n' if p==reader else original(p))
    assert run()==expected and scans==['2026-10-08']
    scans.clear()
    assert run()==expected and scans==[]


def test_index_growth_race_is_bounded_before_decode(tmp_path,monkeypatch):
    from src.engine.scalping import initial_quantity_source_cache as cache
    import os
    index=tmp_path/'index.json'
    with index.open('wb') as handle:handle.truncate(cache.storage.RECORD_BYTES+1)
    original=Path.stat
    def old_size(p,**kw):
        stat=original(p,**kw)
        if p==index:
            parts=list(stat);parts[6]=1
            return os.stat_result(parts)
        return stat
    monkeypatch.setattr(Path,'stat',old_size)
    monkeypatch.setattr(cache.json,'loads',lambda *a,**k:pytest.fail('oversize decode'))
    with pytest.raises(ValueError,match='cache_index_invalid'):cache._read_index(index)


def test_native_capture_loss_is_isolated_before_joint_policy_selection(tmp_path):
    from src.engine.scalping.initial_quantity_timeout_research import build_timeout_research,timeout_research_valid
    from src.engine.scalping.initial_quantity_refresh_evaluation import read_joint_cases
    parent,path,facts,pid=_positive_joint_fixture(tmp_path)
    leaf=tmp_path/'pipeline_events/pipeline_events_2026-10-05.jsonl'
    event=_event(100,'initial_quantity_cap_capture_finished','2026-10-05T09:51:00+09:00',
        entry_submit_attempt_id='100',entry_execution_sizing_plan_sha256='b'*64,
        capture_queue_rejected_count='1',capture_queued_count='20',capture_clock_status='frozen_order_start')
    event['stock_code']='005930'
    with leaf.open('a') as handle:handle.write(json.dumps(event)+'\n')
    shared={}
    report=policy.build_initial_quantity_replay('2026-10-07',data_dir=tmp_path,fact_rows=facts,entry_on_or_after=policy.refresh_window(parent),path_cache=shared)
    timeout=build_timeout_research('2026-10-07',data_dir=tmp_path,fact_rows=facts,entry_on_or_after=policy.refresh_window(parent),path_cache=shared,replay=report)
    assert timeout_research_valid(timeout,replay=report)
    cases=read_joint_cases(timeout)
    affected=next(r for r in report['trades'] if str(r['record_id'])=='100')
    assert all(v['status']=='capture_queue_gap' for v in affected['cap_candidates'].values())
    valid={tid for tid,values in cases.items() if any(v['status']!='source_gap' for key,v in values.items() if key!='parent_5stage:parent:None')}
    assert len(valid)==59 and affected['trade_id'] not in valid
