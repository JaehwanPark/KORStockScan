"""Main stop pure decisions, real producer adapters and committed consumers."""
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import pytest
from src.engine.scalping import main_stop_policy as p
from src.engine.scalping import main_stop_replay as r
from src.engine.automation import main_stop_postclose as post
from src.engine.scalping.position_peak_ledger import PositionPeakRuntimeLedger, position_cycle_id


def test_retired_pyramid_cannot_create_or_replace_a_protect_line():
    from src.engine.sniper_execution_receipts import _apply_scale_in_protection
    before = dict(buy_price=10000, trailing_stop_price=10050, protect_profit_pct=.2,
        soft_stop_micro_grace_started_at=100, soft_stop_micro_grace_extension_used=True)
    retired = dict(before)
    assert _apply_scale_in_protection(retired, 'PYRAMID') is False
    assert retired == before
    average = dict(before)
    assert _apply_scale_in_protection(average, 'AVG_DOWN') is True
    assert average['trailing_stop_price'] == before['trailing_stop_price']
    assert average['protect_profit_pct'] == before['protect_profit_pct']
    assert 'soft_stop_micro_grace_started_at' not in average
    assert average['soft_stop_reset_after_avg_down'] is True
    assert p.protect_line_origin({}) == 'not_applicable_no_active_line'
    assert p.protect_line_origin(dict(before, manual_control_exclusion_blocked=True)) == 'manual_existing'
    assert p.protect_line_origin(dict(before, pyramid_count=1)) == 'legacy_retired'
    assert p.protect_line_origin(before) == 'unverified_existing'


def baseline():
    return p.StopValues(-3.,60,20,8,3,.67,1.,-5.,-4.,-2.,-.3)


def seal(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,sort_keys=True))
    return dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def rows(base=1791766800., record=1):
    value=baseline();stock=dict(id=record,code='005930',strategy='SCALPING',position_tag='SCANNER',buy_price=10000.,buy_qty=10)
    stock['main_stop_policy_pin']=p.pin(position_key=position_cycle_id(stock),role='SCANNER',market='REGULAR',target='2026-10-12',baseline=value)
    for n in range(9):
        bid=9990 if n<2 else 9650 if n<6 else 9580
        yield p.source_row(stock,at=base+n,bid=bid,bid_qty=100,
            decision_profit_pct=round((bid*10*.999-100000-10)/100000*100,2),
            quote=dict(market_route='krx_nxt_integrated',item='005930_AL',transport_epoch=1,observed_epoch=base+n),
            coverage_complete=True,automatic_management_allowed=True,
            runtime_flags=dict(grace_enabled=True,protect_enabled=True,handoff_enabled=False,vote_max_worsen_pct=.8),cost_model=dict(buy_cost_krw=10.,sell_cost_rate=.001,known_at=base-10,source_sha256='a'*64),vote_source=None)


def test_single_grace_clock_hard_priority_and_reset():
    v=baseline();first=p.soft_decision(v,profit_pct=-3.1,now=100)
    assert first.disposition=='defer_until' and first.due_at==160
    assert p.soft_decision(v,profit_pct=-3.1,now=159,touch_at=100).due_at==160
    assert p.soft_decision(v,profit_pct=-3.1,now=160,touch_at=100).disposition=='exit_candidate'
    assert p.soft_decision(v,profit_pct=-2.9,now=150,touch_at=100).touch_at is None
    for now in (101,159):
        assert p.soft_decision(v,profit_pct=-5.,now=now,touch_at=100).rule=='scalp_hard_stop_pct'
    assert p.soft_decision(v,profit_pct=-3.1,now=110,touch_at=100,after_add=True).disposition=='exit_candidate'
    assert p.soft_decision(v,profit_pct=-3.1,now=99,touch_at=100).disposition=='exit_candidate'


def test_safety_manual_protect_emergency_and_preset_grace():
    args=dict(hard_pct=-1.4,emergency_pct=-2.4,protect_pct=None,handoff_enabled=True)
    assert p.safety_decision(profit_pct=-1.5,held_sec=10,preset_grace_sec=20,**args).disposition=='hold'
    assert p.safety_decision(profit_pct=-1.5,held_sec=21,preset_grace_sec=20,**args).disposition=='manual_handoff'
    assert p.safety_decision(profit_pct=-2.5,held_sec=1,preset_grace_sec=20,**args).rule=='scalp_hard_stop_emergency'
    assert p.safety_decision(profit_pct=-5.,manual=True,**args).rule=='manual_custody'
    assert p.safety_decision(profit_pct=-1.5,**{**args,'protect_pct':-.5}).rule=='scalp_protect_profit_stop'


def test_samples_horizon_duplicate_capacity_and_protect():
    v=replace(baseline(),window_sec=30,min_span_sec=25,buffer_pct=0.,protect_exit_floor_pct=-999.)
    samples=[]
    for n in range(41):samples,quality=p.append_sample(samples,at=100+n,price=9900)
    assert samples[0]['ts']==110 and len(samples)==31
    assert p.protect_confirmed(v,samples,now=140,price_line=9950,profit_pct=-1.)[0]
    assert not p.protect_confirmed(v,samples,now=170,price_line=9950,profit_pct=-1.)[0]
    assert p.append_sample(samples,at=140,price=9900)[1]=='duplicate'
    assert p.append_sample(samples,at=141,price=9900,cap=2)[1]=='capacity_censored'


def test_native_capture_causal_replay_and_missing_cost():
    source=list(rows());a=r.replay(source,baseline());b=r.replay(source,replace(baseline(),grace_sec=0))
    assert a['status']==b['status']=='modeled'
    assert b['crossing_at']<a['crossing_at'] and b['modeled_net_krw']>a['modeled_net_krw']
    invalid=[dict(x,cost_model=None) for x in source]
    for x in invalid:x['source_sha256']=p.digest({k:v for k,v in x.items() if k!='source_sha256'})
    assert r.replay(invalid,baseline())['modeled_net_krw'] is None
    assert r.replay(source[3:],baseline())['status']=='censored'


def test_durable_pin_clock_survives_add_and_restart(tmp_path):
    ledger=PositionPeakRuntimeLedger(tmp_path/'peaks.json')
    stock=dict(id=42,code='005930',buy_price=10000.,buy_qty=10)
    ledger.record(stock,peak_price=10000,observed_at=100,reason='fill')
    value=p.pin(position_key=position_cycle_id(stock),role='SCANNER',market='REGULAR',target='2026-10-12',baseline=baseline())
    stock['main_stop_policy_pin']=value
    assert ledger.record_stop_pin(stock,value)
    assert ledger.record_stop_clock(stock,110.)
    stock.update(buy_price=9900,buy_qty=20)
    ledger.record(stock,peak_price=10200,observed_at=120,reason='add')
    restored=PositionPeakRuntimeLedger(tmp_path/'peaks.json').get_for_stock(stock)
    assert restored['main_stop_policy_pin']==value and restored['main_stop_touch_at']==110
    with pytest.raises(ValueError):
        ledger.record_stop_pin(stock,{**value,'pin_sha256':'x'})
    with pytest.raises(ValueError):p.pin_values(value,'target:43:005930')


def publication(tmp_path, *, experiment=False, actual=True):
    p.preload({})
    value=baseline();parents={f'{role}|{market}':value for role in p.ROLES for market in p.MARKETS}
    parent=seal(tmp_path/'parent.json',{'values':asdict(value)})
    snapshot=seal(tmp_path/'snapshot.json',{'date':'2026-10-12'})
    source=tmp_path/'pipeline_events/pipeline_events_2026-10-12.jsonl';source.parent.mkdir(parents=True)
    base=1791766800.
    population=list(rows(base,1))+list(rows(base+100,2))+list(rows(base+1000,3))+list(rows(base+1100,4))
    source.write_text(''.join(json.dumps(dict(stage='main_stop_source',fields={'main_stop_source':row}))+'\n' for row in population))
    contract={}
    if experiment:
        performance=seal(tmp_path/'performance.json',dict(schema='main_stop_performance_v1',status='pass',
            code_sha256=post.code_sha(),scope='runtime_and_postclose',unresolved_findings=[]))
        body=dict(schema='main_stop_experiment_v1',parent_sha256=p.digest(asdict(value)),
            source_sha256=p.digest({str(source):post.byte_generation(source)}),code_sha256=post.code_sha(),
            operator_lock_sha256=p.digest([]),frozen_at=base-100,split_at=base+500,
            min_train=2,min_holdout=2,minimum_paired_ev_krw=0.,allowed_keys=['grace_sec'],embargo_sec=60.,
            max_censoring_ratio=0.,max_standard_error_krw=0.,max_daily_change={'grace_sec':60},performance_receipt=performance)
        body['experiment_sha256']=p.digest(body);contract={'SCANNER|REGULAR':body}
    complete=[dict(id=n,status='COMPLETED',source_date='2026-10-12',main_automatic_management_allowed=True,
        actual_cost_reconciliation=dict(status='actual_cost_reconciled',exact_pnl_krw=-4310.,exact_profit_rate=-4.31,
            receipt_sha256='a'*64,raw_sha256='b'*64)) for n in (1,2,3,4)] if actual else []
    cost=seal(tmp_path/'costs.json',{'rows':complete})
    bundle,report=post.publish(tmp_path,'2026-10-12','2026-10-13',parents=parents,parent_receipt=parent,
        snapshot_receipt=snapshot,source_paths=[source],experiments=contract,completed=complete,economic_sources=dict(files={cost['path']:post.byte_generation(Path(cost['path']))},cost_generations={}))
    return bundle,report,parent,source


def test_actual_producer_publication_loader_pin_and_partial_cells(tmp_path):
    bundle,report,_,_=publication(tmp_path,experiment=True)
    assert bundle['cells']['SCANNER|REGULAR']['status']=='selected'
    assert bundle['cells']['SCANNER|REGULAR']['values']['grace_sec']==0
    assert sum(c['status']=='selected' for c in bundle['cells'].values())==1
    env,receipt=post.handoff(tmp_path,'2026-10-13')
    assert receipt['actual_pid_consumed'] is False
    p.preload(env)
    value=p.pin(position_key='target:44:005930',role='SCANNER',market='REGULAR',target='2026-10-13',baseline=baseline())
    assert p.pin_values(value,'target:44:005930').grace_sec==0
    assert p.pin(position_key='x',role='SCANNER',market='PREMARKET',target='2026-10-13',baseline=baseline())['values']['grace_sec']==60
    p.preload({})


def test_no_cost_no_challenger_and_source_revision_invalidates_handoff(tmp_path):
    bundle,_,parent,_=publication(tmp_path,experiment=True,actual=False)
    assert all(c['status']!='selected' for c in bundle['cells'].values())
    Path(parent['path']).write_text('{}')
    with pytest.raises(ValueError,match='source_changed'):post.handoff(tmp_path,'2026-10-13')


def test_policy_cannot_change_safety_under_carried_status(tmp_path):
    bundle,_,_,_=publication(tmp_path)
    bundle['cells']['SCANNER|REGULAR']['values']['hard_stop_pct']=-6.
    bundle['policy_sha256']=p.digest({k:v for k,v in bundle.items() if k!='policy_sha256'})
    with pytest.raises(ValueError,match='carry_changed'):p.validate_bundle(bundle,'2026-10-13')


def test_stage_and_monitor_uninstalled_vs_committed(tmp_path):
    from src.engine.automation.postclose_summary_handoff import active_stage_names,stage_artifacts,_stage_output_issues
    from src.engine.error_detectors.artifact_freshness import _main_stop_semantics
    from datetime import datetime
    from zoneinfo import ZoneInfo
    now=datetime(2026,10,13,7,tzinfo=ZoneInfo('Asia/Seoul'))
    assert 'main_stop_confirmation' not in active_stage_names('2026-10-08')
    assert 'main_stop_confirmation' in active_stage_names('2026-10-12')
    assert _main_stop_semantics(tmp_path,'2026-10-08',now=now)['status']=='not_installed'
    assert _main_stop_semantics(tmp_path,'2026-10-12',now=now)['expected_overdue']
    publication(tmp_path/'data')
    assert _stage_output_issues(tmp_path/'data/report','2026-10-12','main_stop_confirmation')==[]
    assert _main_stop_semantics(tmp_path,'2026-10-12',now=now)['native_validated']


def test_cost_only_revision_invalidates_native_commit_without_replaying(tmp_path, monkeypatch):
    publication(tmp_path, experiment=True)
    cost=tmp_path/'costs.json'
    raw=json.loads(cost.read_text());raw['rows'][0]['actual_cost_reconciliation']['exact_pnl_krw']=-4400
    cost.write_text(json.dumps(raw))
    monkeypatch.setattr(post,'replay',lambda *a,**k:pytest.fail('monitor must not replay'))
    with pytest.raises(ValueError,match='source_generation_changed'):
        post.read_committed(tmp_path,'2026-10-12')


def test_native_check_avoids_full_raw_hash_in_steady_state(tmp_path,monkeypatch):
    publication(tmp_path)
    original=post.byte_generation
    def bounded_hash(path):
        if 'pipeline_events' in str(path):pytest.fail('steady-state full raw hash')
        return original(path)
    monkeypatch.setattr(post,'byte_generation',bounded_hash)
    assert post.read_committed(tmp_path,'2026-10-12')[1]['opportunity_census']['count']==4


def test_operator_veto_is_not_a_stop_key_successor(tmp_path):
    from src.engine.automation.operator_policy_succession import stop_key_authority
    directory=tmp_path/'threshold_cycle/operator_runtime_env_locks'
    seal(directory/'manual.json',dict(family='main_stop_confirmation',manual_veto=True,
        env_overrides={'KORSTOCKSCAN_SCALP_STOP':-3.}))
    with pytest.raises(ValueError,match='veto'):
        stop_key_authority(tmp_path,'2026-10-13',['soft_stop_pct'])
    with pytest.raises(ValueError,match='subset'):
        stop_key_authority(tmp_path,'2026-10-13',['hard_stop_pct'])


def test_runtime_safety_override_cannot_be_hidden_by_stop_bundle(tmp_path):
    bundle,*_=publication(tmp_path)
    env={'KORSTOCKSCAN_'+p.KEYS[k]:str(v) for k,v in asdict(baseline()).items()}
    p.validate_runtime_environment(bundle,env)
    env['KORSTOCKSCAN_SCALP_HARD_STOP']='-6'
    with pytest.raises(ValueError,match='environment_changed'):
        p.validate_runtime_environment(bundle,env)


def test_stale_quote_and_missing_runtime_flags_are_source_gaps():
    original=list(rows())
    for changes,reason in (({'quote_at':1},'quote_clock_unverified'),
                           ({'grace_enabled':None},'runtime_flags_unobserved')):
        first={**original[0],**changes};first['source_sha256']=p.digest({k:v for k,v in first.items() if k!='source_sha256'})
        outcome=r.replay([first]+original[1:],baseline())
        assert outcome['status']=='source_gap' and outcome['reason']==reason


def test_original_soft_emergency_safety_never_requires_new_ai_votes():
    source=[]
    for row in rows():
        row['holding_ai_required']=True
        row['source_sha256']=p.digest({k:v for k,v in row.items() if k!='source_sha256'})
        source.append(row)
    outcome=r.replay(source,replace(baseline(),grace_sec=0),
        vote_reader=lambda *args:pytest.fail('existing emergency releases VETO'))
    assert outcome['status']=='modeled'


@pytest.mark.parametrize('name',[
    '_holding_strong_trailing_enabled','_build_soft_stop_whipsaw_confirmation_decision',
    '_attempt_stop_line_touch_mandatory_avg_down','_evaluate_late_loss_avg_down_retry',
    '_evaluate_soft_stop_line_touch_avg_down_defer','_defensive_avg_down_unfilled_recheck_decision',
    '_emit_scalp_hard_time_stop_shadow','_emit_same_symbol_soft_stop_cooldown_shadow',
    '_holding_exit_ai_reason_label','_loss_recovery_intercepts_sell',
])
def test_retired_stop_entrypoints_cannot_be_reenabled(name):
    from src.engine import sniper_state_handlers as handlers
    assert not hasattr(handlers,name)


def test_holdout_cannot_choose_an_alternative_train_winner():
    contract=dict(allowed_keys=['grace_sec'],min_train=2,min_holdout=2,minimum_paired_ev_krw=0,
                  max_censoring_ratio=0.,max_standard_error_krw=100.)
    def result(delta,held_bad):
        return dict(train_n=10,train_total=10,train_delta=delta,train_delta_sq=delta*delta,
                    holdout_n=10,holdout_total=10,holdout_delta=10.,holdout_delta_sq=100.,
                    train_safety_regressions=0,holdout_safety_regressions=held_bad)
    # Better training winner fails holdout; do not look back for a runner-up.
    assert r.choose({'grace_sec:0':result(100,1),'grace_sec:15':result(50,0)},contract)==(None,'hold_no_edge')


def test_old_observed_policy_does_not_exclude_current_parent_comparison():
    source=list(rows())
    previous=replace(baseline(),grace_sec=30)
    for row in source:
        row['source_stop_values']=asdict(previous)
        row['parent_values_sha256']=p.digest(asdict(previous))
        row['source_sha256']=p.digest({k:v for k,v in row.items() if k!='source_sha256'})
    assert r.replay(source,baseline())['status']=='modeled'


def test_dependency_mutation_between_hash_and_stat_is_rejected(tmp_path,monkeypatch):
    path=tmp_path/'source';path.write_text('old')
    expected=post.byte_generation(path)
    original=post.byte_generation
    def mutate(value):
        receipt=original(value)
        value.write_text('new')
        return receipt
    monkeypatch.setattr(post,'byte_generation',mutate)
    with pytest.raises(ValueError,match='source_changed'):
        post.verified_dependency_stats({str(path):expected})


def test_restart_without_original_touch_never_gets_new_grace(tmp_path,monkeypatch):
    from src.engine import sniper_state_handlers as handlers
    p.preload({})
    monkeypatch.setattr(handlers,'POSITION_PEAK_LEDGER',PositionPeakRuntimeLedger(tmp_path/'ledger.json'))
    stock=dict(id=8,code='005930',strategy='SCALPING',buy_price=10000.,buy_qty=10,
               buy_time=100.,main_stop_restoring_position=True)
    handlers._main_stop_values(stock,1791766800.)
    assert stock['main_stop_clock_unobserved'] is True
    assert stock['main_stop_policy_pin']['origin']=='effective_legacy_rules'


def test_cost_delta_reuses_position_replay_and_nochange_skips_decode(tmp_path,monkeypatch):
    _,report,parent,source=publication(tmp_path)
    cost=tmp_path/'costs.json';cost.write_text(json.dumps({'revision':2}))
    parents={f'{role}|{market}':baseline() for role in p.ROLES for market in p.MARKETS}
    args=dict(parents=parents,parent_receipt=parent,source_paths=[source],
        snapshot_receipt=report['snapshot_receipt'],economic_sources=dict(files={str(cost):post.byte_generation(cost)},cost_generations={}))
    monkeypatch.setattr(post,'replay',lambda *a,**k:pytest.fail('cost correction replayed price path'))
    monkeypatch.setattr(post,'source_events',lambda *a,**k:pytest.fail('unchanged source file decoded raw'))
    bundle,changed=post.publish(tmp_path,'2026-10-12','2026-10-13',**args)
    assert changed['research_sha256']!=report['research_sha256']
    assert changed['opportunity_census']['count']==4
    monkeypatch.setattr(post,'source_events',lambda *a,**k:pytest.fail('unchanged generation decoded raw'))
    assert post.publish(tmp_path,'2026-10-12','2026-10-13',**args)[0]==bundle


def test_native_loader_receipt_and_pin_are_observed_without_executing_exit(tmp_path):
    bundle,*_=publication(tmp_path)
    env,_=post.handoff(tmp_path,'2026-10-13')
    p.preload(env)
    receipt=p.record_loaded_policy(tmp_path)
    assert receipt and p.record_loaded_policy(tmp_path) is None
    result=post.runtime_consumption(tmp_path,bundle)
    assert result['actual_pid_consumed'] and result['status']=='loader_observed'
    raw=json.loads(receipt.read_text());raw['loaded_cells_sha256']='b'*64
    raw['receipt_sha256']=p.digest({k:v for k,v in raw.items() if k!='receipt_sha256'})
    receipt.write_text(json.dumps(raw))
    with pytest.raises(ValueError,match='loaded_map'):post.runtime_consumption(tmp_path,bundle)
    p.preload({})


def test_manual_registration_does_not_hold_entry_lock_or_duplicate(tmp_path,monkeypatch):
    import threading
    from types import SimpleNamespace
    from src.engine import sniper_state_handlers as h
    started,finish=threading.Event(),threading.Event()
    stock=dict(id=12,code='005930',status='HOLDING',strategy='SCALPING',buy_qty=10)
    calls=[]
    def register(*args,**kwargs):
        calls.append(1);started.set()
        assert finish.wait(3)
        return SimpleNamespace(excluded=False,reason='isolated_failure',source='fixture',code='005930',as_log_fields=lambda:{})
    monkeypatch.setattr(h,'add_manual_control_exclusion_code',register)
    monkeypatch.setattr(h,'_env_or_rule_bool',lambda *a,**k:True)
    monkeypatch.setattr(h,'_is_scalp_simulated_position',lambda *a:False)
    monkeypatch.setattr(h,'_has_active_sell_order_pending',lambda *a:False)
    monkeypatch.setattr(h,'_log_holding_pipeline',lambda *a,**k:None)
    monkeypatch.setattr(h,'log_error',lambda *a:None)
    args=dict(strategy='SCALPING',sell_reason_type='LOSS',exit_rule='scalp_hard_stop_pct',profit_rate=-5.,peak_profit=0.,curr_price=9500,buy_price=10000,now_ts=100.,source_stage='fixture')
    result=[]
    thread=threading.Thread(target=lambda:result.append(h._handoff_hard_stop_to_manual_control_if_enabled(stock,'005930',**args)))
    thread.start()
    try:
        assert started.wait(3)
        assert h.ENTRY_LOCK.acquire(timeout=.2)
        h.ENTRY_LOCK.release()
        assert h._handoff_hard_stop_to_manual_control_if_enabled(stock,'005930',**args)
        assert calls==[1]
    finally:
        finish.set();thread.join(3)
    assert result==[True] and stock['manual_control_hard_stop_handoff_pending']
    assert not stock.get('exit_requested')


@pytest.mark.parametrize('deferred',[False,True])
def test_stop_capture_uses_shared_queue_immutable_envelope_and_drop_marker(monkeypatch,deferred):
    from contextlib import nullcontext
    from concurrent.futures import ThreadPoolExecutor
    from src.utils import pipeline_event_logger as logger
    events=[]
    monkeypatch.setattr(logger,'emit_pipeline_event',lambda *a,**k:events.append((a,k)) or {'structured_append_succeeded':True})
    with ThreadPoolExecutor(max_workers=1) as executor:
        queue=logger.BoundedObservationQueue(executor)
        p.configure_source_sink(queue.submit)
        row=next(rows());row.pop('source_sha256')
        with p.defer_source_capture() if deferred else nullcontext():
            assert p.enqueue_source({'id':1},'005930',row)
            row['bid']=1
        queue.close(timeout=2)
    p.configure_source_sink(None)
    captured=json.loads(events[0][1]['fields']['main_stop_source'])
    assert captured['bid']==9990 and captured['source_sha256']==p.digest({k:v for k,v in captured.items() if k!='source_sha256'})
    assert events[0][1]['observed_at_epoch']==captured['at']
    assert not p.enqueue_source({'id':1},'005930',row)
    source=list(rows());source[1]['capture_rejected_count']=1
    source[1]['source_sha256']=p.digest({k:v for k,v in source[1].items() if k!='source_sha256'})
    assert r.replay(source,baseline())['status']=='censored'


def test_runtime_crossing_and_modeled_cost_are_separate():
    source=list(rows())
    for row in source:
        row['decision_profit_pct']=0.
        row['source_sha256']=p.digest({k:v for k,v in row.items() if k!='source_sha256'})
    assert r.replay(source,replace(baseline(),grace_sec=0))['reason']=='crossing_not_observed'
    source[0]['decision_profit_pct']=None
    source[0]['source_sha256']=p.digest({k:v for k,v in source[0].items() if k!='source_sha256'})
    assert r.replay(source,baseline())['reason']=='runtime_decision_profit_unobserved'


def test_legacy_protection_number_does_not_invent_a_main_generator():
    source=list(rows());source[0]['protect_line']=9800.
    source[0]['source_sha256']=p.digest({k:v for k,v in source[0].items() if k!='source_sha256'})
    assert r.replay(source,baseline())['reason']=='protect_line_producer_unidentified'


def test_partitioned_reference_index_deduplicates_without_copying_raw(tmp_path):
    from src.engine.automation import main_stop_source_index as idx
    from collections import Counter
    source=tmp_path/'raw.jsonl'
    population=list(rows())
    event=lambda row:dict(stage='main_stop_source',fields={'main_stop_source':row})
    source.write_text(''.join(json.dumps(event(row))+'\n' for row in population+population))
    census=Counter();inventory={str(source):post.byte_generation(source)}
    prepared=idx.prepare(tmp_path/'cache',inventory,post.source_events,census)
    assert census['raw']==18
    positions=list()
    for position in idx.positions(prepared,tmp_path/'scratch',census):
        positions.append(list(position.rows()))
    assert positions==[population]
    for path in (tmp_path/'cache').rglob('*.json'):
        raw=path.read_text()
        assert '"cost_model"' not in raw and '"buy_basis_krw"' not in raw
    assert census['deduplicated']==9


def test_vote_new_file_and_same_bytes_replacement_regenerate_native_generation(tmp_path):
    _,report,parent,source=publication(tmp_path)
    args=dict(parents={f'{role}|{market}':baseline() for role in p.ROLES for market in p.MARKETS},
        parent_receipt=parent,source_paths=[source],snapshot_receipt=report['snapshot_receipt'])
    # Discovery of a formerly absent original is part of native invalidation.
    vote=tmp_path/'runtime/holding_path_votes/new.jsonl';vote.parent.mkdir(parents=True);vote.write_text('{}\n')
    with pytest.raises(ValueError,match='vote_source_set_changed'):post.read_committed(tmp_path,'2026-10-12')
    post.publish(tmp_path,'2026-10-12','2026-10-13',**args)
    before=post.read_committed(tmp_path,'2026-10-12')[2]['generation']
    replacement=tmp_path/'copy.jsonl';replacement.write_bytes(source.read_bytes());replacement.replace(source)
    post.publish(tmp_path,'2026-10-12','2026-10-13',**args)
    assert post.read_committed(tmp_path,'2026-10-12')[2]['generation']!=before


def test_performance_evidence_cannot_be_missing_or_changed(tmp_path):
    bundle,*_=publication(tmp_path,experiment=True)
    (tmp_path/'performance.json').write_text('{}')
    with pytest.raises(ValueError,match='performance_gate'):p.validate_bundle(bundle,'2026-10-13')


def test_bounded_reader_rejects_path_replaced_during_read(tmp_path,monkeypatch):
    path=tmp_path/'source.json';path.write_text('{"x":1}')
    original=Path.open
    class Changing:
        def __init__(self,handle):self.handle=handle
        def __enter__(self):self.handle.__enter__();return self
        def __exit__(self,*args):return self.handle.__exit__(*args)
        def fileno(self):return self.handle.fileno()
        def read(self,size):
            raw=self.handle.read(size)
            replacement=tmp_path/'next.json';replacement.write_text('{"x":2}');replacement.replace(path)
            return raw
    def open_path(self,*args,**kwargs):
        handle=original(self,*args,**kwargs)
        return Changing(handle) if self==path and args==('rb',) else handle
    monkeypatch.setattr(Path,'open',open_path)
    with pytest.raises(ValueError,match='changed_during_read'):p.bounded_object(path)


def test_nested_census_shard_change_is_detected_without_raw_replay(tmp_path):
    publication(tmp_path)
    _,report,_,directory=post.read_committed(tmp_path,'2026-10-12')
    dependencies=report['census_dependencies']
    leaf=next(directory/name for name in dependencies if '"rows"' in (directory/name).read_text())
    raw=json.loads(leaf.read_text());raw['rows'][0]['reason']='tampered';leaf.write_text(json.dumps(raw))
    with pytest.raises(ValueError,match='census_shard_generation_changed'):
        post.read_committed(tmp_path,'2026-10-12')


def test_source_discovery_includes_native_late_partition(tmp_path):
    import gzip
    directory=tmp_path/'pipeline_events';directory.mkdir()
    base=directory/'pipeline_events_2026-10-12.jsonl';base.write_text('{}\n')
    late=directory/'pipeline_events_2026-10-12.late.jsonl.gz'
    with gzip.open(late,'wt') as handle:handle.write('{}\n')
    assert post.sources(tmp_path,'2026-10-12')==[base,late]


def test_new_late_source_invalidates_handoff_and_must_enter_new_census(tmp_path):
    _,report,parent,source=publication(tmp_path)
    before=post.read_committed(tmp_path,'2026-10-12')[2]['generation']
    late=source.with_name('pipeline_events_2026-10-12.late.jsonl')
    late.write_text(''.join(json.dumps(dict(stage='main_stop_source',
        fields={'main_stop_source':row}))+'\n' for row in rows(record=5)))
    with pytest.raises(ValueError,match='raw_source_set_changed'):
        post.handoff(tmp_path,'2026-10-13')
    args=dict(parents={f'{r}|{m}':baseline() for r in p.ROLES for m in p.MARKETS},
        parent_receipt=parent,snapshot_receipt=report['snapshot_receipt'])
    with pytest.raises(ValueError,match='source_catalog_not_consumed'):
        post.publish(tmp_path,'2026-10-12','2026-10-13',source_paths=[source],**args)
    post.publish(tmp_path,'2026-10-12','2026-10-13',source_paths=post.sources(tmp_path,'2026-10-12'),**args)
    _,current,pointer,_=post.read_committed(tmp_path,'2026-10-12',verify_full=True)
    assert pointer['generation']!=before
    assert current['opportunity_census']['count']==5
    assert str(late) in current['source_inventory']


def test_budget_interruption_preserves_committed_pointer_and_records_resume(tmp_path,monkeypatch):
    _,report,parent,source=publication(tmp_path)
    pointer=post.committed_path(tmp_path,'2026-10-12');before=pointer.read_bytes()
    monkeypatch.setattr(post,'MAX_RESEARCH_SECONDS',0)
    with pytest.raises(ValueError,match='deadline_exceeded'):
        post.publish(tmp_path,'2026-10-12','2026-10-13',parents={f'{r}|{m}':baseline() for r in p.ROLES for m in p.MARKETS},
            parent_receipt=parent,source_paths=[source],snapshot_receipt=report['snapshot_receipt'])
    assert pointer.read_bytes()==before
    receipt=json.loads((tmp_path/'report/main_stop_confirmation/resume_2026-10-12.json').read_text())
    assert receipt['status']=='incomplete' and receipt['target_policy_published'] is False


def test_historical_parent_values_can_migrate_but_old_code_cannot_load_live(tmp_path,monkeypatch):
    _,*_=publication(tmp_path)
    env,_=post.handoff(tmp_path,'2026-10-13')
    monkeypatch.setattr(p,'implementation_sha',lambda:'e'*64)
    with pytest.raises(ValueError,match='code_generation_changed'):
        p.load_bundle(env[p.ENV_FILE],env[p.ENV_SHA],env[p.ENV_DATE])
    parent=p.load_bundle(env[p.ENV_FILE],env[p.ENV_SHA],env[p.ENV_DATE],require_current_code=False)
    assert parent['cells']['SCANNER|REGULAR']['values']==asdict(baseline())


def test_malformed_durable_pin_keeps_typed_hard_safety(monkeypatch):
    from src.engine import sniper_state_handlers as h
    from types import SimpleNamespace
    p.preload({})
    stock=dict(id=7,code='005930',strategy='SCALPING',buy_price=10000.,buy_qty=10,main_stop_policy_pin={})
    value=h._main_stop_values(stock,1791766800.)
    assert value.hard_stop_pct<value.soft_stop_pct
    assert stock['main_stop_pin_persistence']=='invalid_pin_safety_only'
    assert '_main_stop_source_values' not in stock
    assert p.soft_decision(value,profit_pct=-10.,now=1791766800.).disposition=='exit_candidate'


def test_fast_source_admission_follows_disposition_and_freezes_input():
    calls=[];stock={'id':1,'name':'fixture'};row={'at':100.,'cost_model':{'fee':10}}
    p.configure_source_sink(lambda *a,**k:calls.append((a,k)) or {'status':'queued'})
    try:
        with p.defer_source_capture():
            assert p.enqueue_source(stock,'005930',row)
            row['cost_model']['fee']=999
            assert calls==[]
            with p.defer_source_capture():
                assert calls==[]
        assert len(calls)==1 and json.loads(calls[0][0][-1])['cost_model']['fee']==10
    finally:p.configure_source_sink(None)


def test_fast_source_queue_failure_never_masks_exit_or_original_exception():
    stock={'id':1}
    def fail(*a,**k):raise OSError('writer unavailable')
    p.configure_source_sink(fail)
    try:
        with pytest.raises(RuntimeError,match='original_exit_error'):
            with p.defer_source_capture():
                assert p.enqueue_source(stock,'005930',{'at':100.})
                raise RuntimeError('original_exit_error')
        assert stock['main_stop_source_rejected_count']==1
        assert stock['main_stop_source_gap']=='observation_queue_rejected'
    finally:p.configure_source_sink(None)


def test_fast_source_local_buffer_stays_bounded():
    stock={'id':1}
    with p.defer_source_capture():
        assert p.enqueue_source(stock,'005930',{'at':100.})
        assert p.enqueue_source(stock,'005930',{'at':101.})
        assert not p.enqueue_source(stock,'005930',{'at':102.})


def test_unsealed_observation_vector_refreshes_all_inputs_and_cannot_be_mutated(monkeypatch):
    from src.engine.scalping import trailing_mechanical_policy as policy
    monkeypatch.delenv(policy.VECTOR_SHA_ENV_KEY,raising=False)
    env_key=policy.MARKET_ENV_KEYS['SCALP_TRAILING_START_PCT']['REGULAR']
    monkeypatch.delenv(env_key,raising=False)
    scalar=dict(policy.DEFAULTS)
    first=policy.runtime_policy_vector_snapshot(scalar)
    first[0]['REGULAR']['SCALP_TRAILING_START_PCT']=999
    assert policy.runtime_policy_vector_snapshot(scalar)[0]['REGULAR']['SCALP_TRAILING_START_PCT']==.4
    monkeypatch.setenv(env_key,'.6')
    second=policy.runtime_policy_vector_snapshot(scalar)
    assert second[0]['REGULAR']['SCALP_TRAILING_START_PCT']==.6 and second[3]!=first[3]
    monkeypatch.delenv(env_key)
    scalar['SCALP_TRAILING_START_PCT']=.5
    assert policy.runtime_policy_vector_snapshot(scalar)[0]['REGULAR']['SCALP_TRAILING_START_PCT']==.5
    monkeypatch.setenv(env_key,'bad')
    with pytest.raises(ValueError):policy.runtime_policy_vector_snapshot(scalar)
