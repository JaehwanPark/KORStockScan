"""Automatic producer provenance, normal consumer and exact-source failures."""
import gzip
import json
from pathlib import Path
from collections import Counter
import pytest
from src.engine.automation import main_trailing_source_assembler as source
from src.engine.automation import main_trailing_all_scope_research as research
from src.engine.automation import main_trailing_research_handoff as handoff
from src.engine.scalping.pre_submit_delay_initial_policy import digest
from src.engine.scalping.ai_decision_trace import _json_bytes
from src.engine.scalping.trailing_mechanical_policy import baseline_receipt
from src.engine.automation.runtime_policy_bootstrap import _digest_json
from src.tests.test_micro_reversion_symbol_master import _master_payload
from src.engine.lifecycle import research_storage as storage


DAY='2026-10-08'
TARGET='2026-10-12'


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value))


def fixture(root):
    master=root/'report/micro_reversion_economic_reference/micro_reversion_symbol_master_2026-08-25.json'
    write(master,_master_payload())
    parent=dict(target_date=DAY,scalp_trailing_mechanical_policy_receipt=baseline_receipt({},source='operator_directed_m1_baseline'))
    parent['manifest_sha256']=_digest_json(parent)
    write(root/'runtime/policy_bootstrap'/f'runtime_policy_bootstrap_{DAY}.json',parent)
    event=dict(at=DAY+'T09:00:00+09:00',source_item='005930',native_epoch=1)
    row=dict(schema='mechanistic_entry_observation_v1',bundle_sha256='a'*64,
        captured_at=DAY+'T09:00:00.100+09:00',source=dict(assessment=dict(action='ENTER_NOW',event=event,
            canonical_opportunity_id='original-canonical')),label_context=dict(evaluation_attempt_id='native-1',stock_code='005930'))
    row['machine_observation_sha256']=__import__('hashlib').sha256(_json_bytes(row)).hexdigest()
    native=root/'ai_decision_payloads'/f'ai_decision_payloads_{DAY}.jsonl'
    native.parent.mkdir(parents=True);native.write_text(json.dumps(row)+'\n')
    trace=dict(schema='ai_decision_trace_v1',decision_stage='entry_screen',decision_ts=DAY+'T09:00:01+09:00',
        stock_code='005930',evaluation_attempt_id='native-1',decision_trace_id='trace-1',source_event_stage='machine_enter',
        entry_mechanistic_action='ENTER_NOW',entry_ai_risk_verdict='PASS',provider_called=True,
        decision_evaluation_status='evaluated',result_source='live',prompt_version='frozen',entry_ai_component_sha256='b'*64,
        market_data_route='KRX',session_bucket='REGULAR',machine_bundle_sha256='a'*64,
        machine_observation_sha256=row['machine_observation_sha256'])
    path=root/'ai_decision_trace'/f'ai_decision_trace_{DAY}.jsonl'
    path.parent.mkdir(parents=True);path.write_text(json.dumps(trace)+'\n')
    return path,native


def test_automatic_native_binding_warm_reuse_and_new_file_invalidation(tmp_path,monkeypatch):
    root=tmp_path/'source';path,native=fixture(root);assembly=tmp_path/'assembly';out=tmp_path/'research'
    manifest=source.assemble(root,assembly,source_date=DAY,target_date=TARGET,start_date=DAY)
    payload=research._sealed(manifest)
    assert payload['population_ids_ref']['count']==1
    assert payload['assembly_census']['source_gaps']['native_canonical_identity_recovered']==1
    original=source._native_index
    monkeypatch.setattr(source,'_native_index',lambda *a,**k:pytest.fail('unchanged source decoded again'))
    assert source.assemble(root,assembly,source_date=DAY,target_date=TARGET,start_date=DAY)==manifest
    result=research.run(manifest,input_root=assembly,output_root=out,dry_run=False)
    assert result['status']=='complete'
    assert result['common_population_evaluation']['common_ids_ref']['count']==0
    report_path=out/f'research_{DAY}.json'
    assert handoff.verify_report(report_path,target_date=TARGET)[0]==result
    # A new invalid exact-date receipt changes inventory as well as valid rows.
    write(root/'runtime/mechanistic_entry_policy/decisions'/DAY/'pid'/'new.json',{})
    with pytest.raises(ValueError,match='inventory_changed'):
        handoff.verify_report(report_path,target_date=TARGET)
    monkeypatch.setattr(source,'_native_index',original)
    source.assemble(root,assembly,source_date=DAY,target_date=TARGET,start_date=DAY)
    assert research._sealed(manifest)['assembly_input_generation_sha256']!=payload['assembly_input_generation_sha256']


def _issued_trailing_receipt(root, monkeypatch):
    from datetime import datetime
    from src.engine.scalping import trailing_entry_research_source as bridge
    from src.engine.scalping import entry_execution_sizing_plan as sizing
    from src.tests.test_entry_execution_sizing_plan import _priced, _receipt
    trace, native=fixture(root)
    from src.engine.scalping import ai_decision_trace as capture
    monkeypatch.setenv('KORSTOCKSCAN_AI_DECISION_TRACE_ENABLED','true')
    monkeypatch.setattr(capture,'DATA_DIR',root)
    monkeypatch.setattr(capture,'_now',lambda:datetime.fromisoformat(DAY+'T09:00:00.100+09:00'))
    native.unlink()  # Replace only this test's handwritten bootstrap row.
    result=capture.capture_machine_observation(
        exact_payload=dict(stock_code='005930',evaluation_attempt_id='native-1',best_ask=102),
        setup_evidence={},assessment=dict(action='ENTER_NOW',canonical_opportunity_id='original-canonical',
            event=dict(at=DAY+'T09:00:00+09:00',source_item='005930',native_epoch=1,entry_ask=102)),bundle_sha256='a'*64)
    assert result['machine_capture_status']=='captured'
    original=json.loads(native.read_text())
    trace_row=json.loads(trace.read_text())
    trace_row['machine_observation_sha256']=result['machine_observation_sha256']
    trace.write_text(json.dumps(trace_row)+'\n')
    known=datetime.fromisoformat(DAY+'T09:00:01.200+09:00').timestamp()
    action=_receipt(evaluation_attempt_id='native-1',machine_observation_sha256=original['machine_observation_sha256'],
                    machine_bundle_sha256='a'*64)
    monkeypatch.setattr(sizing,'runtime_entry_execution_sizing_policy',lambda:(None,'disabled_baseline'))
    monkeypatch.setattr(sizing,'runtime_mechanistic_entry_price_policy',lambda:({},'disabled_baseline'))
    # The actual price owner emits str(epoch); native depth retains int(epoch).
    orders=[{**_priced(dict(qty=2,price=102)), 'entry_price_epoch':'1', 'entry_price_captured_at':known}]
    _,fields=sizing.compose_entry_execution_sizing_plan(orders,expected_total_qty=2,action_receipt=action,
        quantity_policy_version='baseline',split_policy_version='baseline')
    receipt=bridge.capture(symbol='005930',position_key='record:7',action_receipt=action,sizing_fields=fields,
        cap_context={'ask_depth_source':dict(observed_epoch=known-.1,item='005930',market_route='KRX',
            transport_epoch=1,source_type='ws_0D_bound_snapshot',levels=[dict(price_krw=102,quantity=10)])},
        cost_model=dict(buy_cost_krw=0,sell_cost_rate=.0023,source_sha256='c'*64,
            known_at=DAY+'T09:00:01.100+09:00',actual_broker_cost=False),entry_context=None,known_at=known)
    assert receipt.get('status')!='source_gap',receipt
    return receipt,known,native


def _emit_trailing_source(root, monkeypatch, receipt, known, *, forward=True, holding_fault=None):
    from src.utils import pipeline_event_logger as logger
    from src.engine.scalping.universal_trailing_replay import quote_source_digest
    from src.tests.test_main_all_scope_trailing import quote
    monkeypatch.setattr(logger,'DATA_DIR',root)
    monkeypatch.setattr(logger,'log_info',lambda *a,**kw:None)
    monkeypatch.setattr(logger,'_get_producer_compactor',lambda:None)
    monkeypatch.setattr(logger,'threshold_family_for_stage',lambda *a:None)
    plan=logger.emit_pipeline_event('ENTRY_PIPELINE','TEST','005930','entry_execution_sizing_plan',
        fields={'trailing_entry_plan_receipt':json.dumps(receipt)},observed_at_epoch=known)
    assert plan['structured_append_succeeded'] is True
    if forward:
        from src.engine.scalping.trailing_entry_research_source import install, holding_link
        event=quote(1,DAY+'T09:00:01.300',qty=2)
        event=json.loads(json.dumps(event).replace('123456','005930'))
        event['quote_snapshot_sha256']=digest(event['ws_data'])
        event['sell_execution_plan']['quote_source_sha256']=event['quote_snapshot_sha256']
        event['sell_execution_plan']['quantity']=2
        event['source_sha256']=quote_source_digest(event)
        stock={'buy_time':known+.01}
        install(stock,receipt)
        link=holding_link(stock,position_key='record:7',buy_fill_identity='e'*64,known_at=event['known_at'])
        if holding_fault and link:
            if holding_fault=='missing':link=None
            else:
                if holding_fault=='position':link['position_key']='record:8'
                if holding_fault=='pre_plan':link['first_buy_at']=known-1
                if holding_fault=='future_buy':link['first_buy_at']=known+1
                link['sha256']=digest({k:v for k,v in link.items() if k!='sha256'})
        result=logger.emit_pipeline_event('HOLDING_PIPELINE','TEST','005930','scalp_trailing_input_transition',
            fields={'trailing_entry_plan_receipt_sha256':receipt['receipt_sha256'],
                    'trailing_entry_plan_holding_link':json.dumps(link),
                    'universal_trailing_quote':json.dumps(event)},observed_at_epoch=known+.1)
        assert result['structured_append_succeeded'] is True


def _read_trailing_source(root, known):
    import sqlite3
    db=sqlite3.connect(':memory:');sources={};gaps=Counter()
    try:
        source._native_index(root,[DAY],sources,gaps,db)
        source._entry_plan_index(root,[DAY],sources,gaps,db)
        rows=[]
        for position,events in source._trace_rows(root,[DAY],sources,gaps,db=db,as_of=known+2):
            rows.append((position,list(events)))
        return rows,gaps
    finally:
        db.close()


def test_runtime_plan_serializer_native_join_and_observed_forward_path(tmp_path,monkeypatch):
    root=tmp_path/'source'
    receipt,known,native=_issued_trailing_receipt(root,monkeypatch)
    before=native.read_bytes()
    _emit_trailing_source(root,monkeypatch,receipt,known)
    rows,gaps=_read_trailing_source(root,known)
    assert len(rows)==1
    position,events=rows[0]
    assert position['entry_plan_source_status']=='bound_visible_depth_model'
    assert position['qty']==2 and position['buy_basis_krw']==204
    assert position['entry_reference_ask']==102
    assert position['entry_reference_role']=='native_entry_ask_price_path_only'
    assert position['entry_at']==known and position['entry_at']>position['auxiliary_completed_at']
    assert position['cost_model']['known_at_original']==DAY+'T09:00:01.100+09:00'
    assert position['entry_depth_verified'] is True and len(events)==1
    assert position['operating_ai_required'] is True  # Never fabricate an AI-free original.
    assert native.read_bytes()==before
    assert not gaps.get('trailing_plan_source_invalid')


@pytest.mark.parametrize('damage',['hash','future_cost','wrong_route','conditional','depth','missing_forward','different_attempt',
    'future_price','stale_price','bool_epoch','ambiguous_epoch','wrong_price','unknown_order_type',
    'price_owner','price_source_hash','price_leg_id','malformed_depth'])
def test_runtime_plan_missing_or_conflicting_inputs_never_invent_entry_or_path(tmp_path,monkeypatch,damage):
    root=tmp_path/'source'
    receipt,known,_=_issued_trailing_receipt(root,monkeypatch)
    from src.engine.scalping.entry_execution_sizing_plan import _content_sha256
    if damage=='future_cost':receipt['cost_model']['known_at']=known+10
    elif damage=='wrong_route':receipt['ask_depth_source']['market_route']='NXT'
    elif damage=='conditional':
        receipt['execution_plan']['legs'][0]['execution_phase']='after_verified_probe_fill'
        receipt['execution_plan_sha256']=_content_sha256(receipt['execution_plan'])
    elif damage=='depth':receipt['ask_depth_source']['levels'][0]['quantity']=1
    elif damage=='malformed_depth':receipt['ask_depth_source']=['bad']
    elif damage=='different_attempt':
        receipt['evaluation_attempt_id']='other'
        receipt['execution_plan']['action_receipt_id']='other'
        receipt['execution_plan_sha256']=_content_sha256(receipt['execution_plan'])
    elif damage in {'future_price','stale_price','bool_epoch','ambiguous_epoch','wrong_price','unknown_order_type',
                    'price_owner','price_source_hash','price_leg_id'}:
        price=receipt['execution_plan']['price_candidates'][0]
        if damage=='future_price':price['captured_at']=known+3600
        elif damage=='stale_price':price['captured_at']=known-3600
        elif damage=='bool_epoch':
            price['epoch']=True;receipt['ask_depth_source']['transport_epoch']=True
        elif damage=='ambiguous_epoch':price['epoch']='01'
        elif damage=='wrong_price':price['numeric_price']+=1
        elif damage=='unknown_order_type':price['order_type_code']='INVALID'
        elif damage=='price_owner':price['source']='other_owner'
        elif damage=='price_source_hash':price['source_receipt_sha256']='f'*64
        elif damage=='price_leg_id':price['price_leg_id']='other_leg'
        receipt['execution_plan_sha256']=_content_sha256(receipt['execution_plan'])
    receipt['receipt_sha256']=digest({k:v for k,v in receipt.items() if k!='receipt_sha256'})
    if damage=='hash':receipt['receipt_sha256']='f'*64
    _emit_trailing_source(root,monkeypatch,receipt,known,forward=damage!='missing_forward')
    rows,gaps=_read_trailing_source(root,known)
    assert len(rows)==1
    position,events=rows[0]
    if damage=='missing_forward':
        assert position['entry_depth_verified'] is True
        assert events==[] and gaps['trailing_plan_bound_forward_path_unobserved']==1
    else:
        assert position['entry_depth_verified'] is False and events==[]
        assert position['entry_plan_source_status']!='bound_visible_depth_model'


@pytest.mark.parametrize('fault',['missing','position','pre_plan','future_buy'])
def test_runtime_plan_forward_path_requires_same_position_and_initial_buy(tmp_path,monkeypatch,fault):
    root=tmp_path/'source';receipt,known,_=_issued_trailing_receipt(root,monkeypatch)
    _emit_trailing_source(root,monkeypatch,receipt,known,holding_fault=fault)
    rows,gaps=_read_trailing_source(root,known)
    assert rows[0][0]['entry_depth_verified'] is True
    assert rows[0][1]==[dict(kind='SOURCE_GAP',known_at=None)]
    assert gaps['trailing_plan_forward_holding_link_invalid']==1


@pytest.mark.parametrize('fault',['reentry','add','missing_buy','old_buy','different_position'])
def test_runtime_plan_diagnostic_pointer_cannot_cross_holding_generations(tmp_path,monkeypatch,fault):
    from src.engine.scalping import trailing_entry_research_source as bridge
    receipt,known,_=_issued_trailing_receipt(tmp_path/'source',monkeypatch)
    stock={'buy_time':known+.01};bridge.install(stock,receipt)
    assert bridge.holding_link(stock,position_key='record:7',buy_fill_identity='e'*64,known_at=known+.1)
    generation='e'*64;position='record:7'
    if fault=='reentry':stock['buy_time']=known+.05
    if fault=='add':generation='f'*64
    if fault=='missing_buy':stock.pop('buy_time')
    if fault=='old_buy':stock['buy_time']=known-1
    if fault=='different_position':position='record:8'
    assert bridge.holding_link(stock,position_key=position,buy_fill_identity=generation,known_at=known+.1) is None
    assert '_trailing_entry_plan_receipt_sha256' not in stock
    assert '_trailing_entry_plan_binding' not in stock
    bridge.install(stock,receipt);bridge.clear(stock)
    assert bridge.holding_link(stock,position_key='record:7',buy_fill_identity='e'*64,known_at=known+.1) is None


def test_conflicting_native_or_clock_after_cutoff_is_excluded(tmp_path):
    root=tmp_path/'source';path,native=fixture(root)
    original=json.loads(native.read_text());other={**original,'label_context':{**original['label_context'],'evaluation_attempt_id':'other'}}
    # An invalid hash cannot supply a replacement native binding.
    native.write_text(json.dumps(other)+'\n')
    manifest=source.assemble(root,tmp_path/'bad',source_date=DAY,target_date=TARGET,start_date=DAY)
    value=research._sealed(manifest)
    assert value['population_ids_ref']['count']==0
    assert value['assembly_census']['source_gaps']['native_canonical_identity_missing']==1
    native.write_text(json.dumps(original)+'\n')
    cutoff=__import__('datetime').datetime.fromisoformat(DAY+'T09:00:00.500+09:00').timestamp()
    manifest=source.assemble(root,tmp_path/'early',source_date=DAY,target_date=TARGET,start_date=DAY,as_of=cutoff)
    assert research._sealed(manifest)['population_ids_ref']['count']==0


def test_plain_gzip_alias_conflict_cannot_be_ignored(tmp_path):
    root=tmp_path/'source';path,native=fixture(root)
    compressed=path.with_suffix('.jsonl.gz')
    with gzip.open(compressed,'wb') as handle:handle.write(path.read_bytes())
    assert source.select_stream(root,'ai_decision_trace',DAY,{})==path
    with gzip.open(compressed,'wb') as handle:handle.write(b'{}\n')
    with pytest.raises(ValueError,match='plain_gzip_conflict'):
        source.assemble(root,tmp_path/'bad',source_date=DAY,target_date=TARGET,start_date=DAY)


def test_holding_extension_is_verified_even_when_parent_values_carry(tmp_path):
    root=tmp_path/'source';fixture(root);assembly=tmp_path/'assembly';out=tmp_path/'research'
    manifest=source.assemble(root,assembly,source_date=DAY,target_date=TARGET,start_date=DAY)
    result=research.run(manifest,input_root=assembly,output_root=out,dry_run=False)
    path=out/f'research_{DAY}.json'
    extension=dict(report_path=str(path),report_generation=source.byte_generation(path),status=result['status'],
        input_window_generation_sha256=result['input_window_generation_sha256'],initial_policy_sha256=result['initial_policy']['policy_sha256'],
        scope_count=result['scope']['scope_count'],allowed_runtime_apply=False)
    assert handoff.verify_extension({'date':DAY,'all_scope_trailing_research':extension},target_date=TARGET)==result
    extension['initial_policy_sha256']='c'*64
    with pytest.raises(ValueError,match='extension_binding'):
        handoff.verify_extension({'date':DAY,'all_scope_trailing_research':extension},target_date=TARGET)


def test_alphanumeric_verified_scope_remains_research_only():
    from src.engine.scalping.main_exit_scope import build_scope,validate_scope
    result=build_scope([dict(code='0123A0',known_at=1,tradable=None)],as_of=2,universe_source_sha256='a'*64)
    validate_scope(result)
    assert result['scope_count']==8 and result['allowed_runtime_apply'] is False


@pytest.mark.parametrize('boundary',[1,2,3,4])
def test_real_initial_publication_interruption_never_accepts_mixed_receipts(tmp_path,monkeypatch,boundary):
    root=tmp_path/'source';fixture(root);assembly=tmp_path/'assembly';out=tmp_path/'research'
    manifest=source.assemble(root,assembly,source_date=DAY,target_date=TARGET,start_date=DAY)
    result=research.run(manifest,input_root=assembly,output_root=out,dry_run=False)
    original=handoff._atomic;calls=[]
    def stop(path,value):
        original(path,value);calls.append(path)
        if len(calls)==boundary:raise RuntimeError('interrupted')
    monkeypatch.setattr(handoff,'_atomic',stop)
    with pytest.raises(RuntimeError):handoff.publish_initial(root,out/f'research_{DAY}.json',target_date=TARGET)
    if boundary<4:
        with pytest.raises((ValueError,OSError)):
            handoff.verify_initial(root,result['initial_policy'],target_date=TARGET,
                parent_sha256=result['initial_policy']['parent_sha256'])
    else:
        assert handoff.verify_initial(root,result['initial_policy'],target_date=TARGET,
            parent_sha256=result['initial_policy']['parent_sha256'])['target_date']==TARGET


def test_immutable_source_successors_preserve_prior_manifest(tmp_path):
    root=tmp_path/'source';fixture(root);base=tmp_path/'assembly'
    first=source.assemble(root,base,source_date=DAY,target_date=TARGET,start_date=DAY,immutable=True)
    original=first.read_bytes()
    assert source.assemble(root,base,source_date=DAY,target_date=TARGET,start_date=DAY,immutable=True)==first
    write(root/'runtime/mechanistic_entry_policy/decisions'/DAY/'pid'/'new.json',{})
    successor=source.assemble(root,base,source_date=DAY,target_date=TARGET,start_date=DAY,immutable=True)
    assert successor!=first and first.read_bytes()==original


def test_retained_original_projection_flows_from_native_metadata_to_completed_population(tmp_path,monkeypatch):
    from src.tests.test_holding_window_generation import _retained_original_window
    from src.engine.lifecycle.holding_window_generation import capture_window
    root=tmp_path/'source';day,raw,fact=_retained_original_window(root,monkeypatch)
    write(root/'report/micro_reversion_economic_reference/micro_reversion_symbol_master_2026-08-25.json',_master_payload())
    parent=dict(target_date=day,scalp_trailing_mechanical_policy_receipt=baseline_receipt({},source='operator_directed_m1_baseline'))
    parent['manifest_sha256']=_digest_json(parent)
    write(root/'runtime/policy_bootstrap'/f'runtime_policy_bootstrap_{day}.json',parent)
    sidecar=raw.with_suffix('.completed_projection.json')
    originals={p:p.read_bytes() for p in (raw,sidecar)}
    monkeypatch.setattr(fact,'_legacy_original_stream',lambda *a:pytest.fail('original canonical validation repeated'))
    dependency=capture_window(root,[day])['dependencies'][day]
    assert dependency['status']=='observed'
    source_refs={}
    cohort=list(source.large_completed_sources(root,raw,day,tmp_path/'direct',dependency,sources=source_refs))
    assert len(cohort)==1
    trade,position,events=cohort[0]
    assert position['position_key']=='49013' and position['owner']=='main'
    assert position['actual_cost_reconciliation']=={'status':'cost_source_unavailable'}
    assert position['entry_at'] is None and position['qty'] is None
    assert list(events)==[]  # No missing original quote, fill or cost is invented.
    assert any('/legacy_sources/' in name for name in source_refs)
    assert any(name.endswith(f'strategy_position_fact_sync_{day}.status.json') for name in source_refs)
    manifest=source.assemble(root,tmp_path/'assembly',source_date=day,target_date='2026-10-01',start_date=day)
    value=research._sealed(manifest)
    positions=[]
    for part in storage.iter_tree(manifest.parent,value['partitions_ref']):
        positions.extend(research._sealed(manifest.parent/part['path'])['positions'])
    actual=[p for p in positions if p['evidence_kind']=='actual_completed']
    assert [p['position_key'] for p in actual]==['49013']
    assert value['assembly_census']['source_gaps'].get('completed_snapshot_source_gap',0)==0
    assert actual[0]['actual_cost_reconciliation']['status']=='cost_source_unavailable'
    assert actual[0]['entry_at'] is None and actual[0]['automatic_management_allowed'] is False
    assert not Path(str(sidecar)+'.dependencies.json').exists()
    assert {p:p.read_bytes() for p in originals}==originals
    with pytest.raises(ValueError,match='cost_generation_changed'):
        list(source.large_completed_sources(root,raw,day,tmp_path/'bad-cost',
            {**dependency,'cost_generation':{**dependency['cost_generation'],'count':1}}))


def test_large_original_without_retained_native_proof_remains_an_identifiable_gap(tmp_path,monkeypatch):
    from src.tests.test_strategy_position_performance_report import _legacy_unreceipted_original
    from src.engine.lifecycle.holding_window_generation import capture_window
    root=tmp_path/'source';day,raw=_legacy_unreceipted_original(root,monkeypatch)
    dependency=capture_window(root,[day])['dependencies'][day]
    assert dependency['status']=='source_gap'
    with pytest.raises(ValueError,match='legacy_metadata_required'):
        list(source.large_completed_sources(root,raw,day,tmp_path/'output',dependency))


def test_retained_raw_original_manifest_reaches_unchanged_completed_custody(tmp_path,monkeypatch):
    from src.tests.test_strategy_position_performance_report import (
        _legacy_raw_original,_write_legacy_status,report_mod)
    root=tmp_path/'source';day,raw=_legacy_raw_original(root,monkeypatch)
    value=report_mod._load_completion_fact_projection(day,raw);_write_legacy_status(day,value)
    write(root/'report/micro_reversion_economic_reference/micro_reversion_symbol_master_2026-08-25.json',_master_payload())
    parent=dict(target_date=day,scalp_trailing_mechanical_policy_receipt=baseline_receipt({},source='operator_directed_m1_baseline'))
    parent['manifest_sha256']=_digest_json(parent)
    write(root/'runtime/policy_bootstrap'/f'runtime_policy_bootstrap_{day}.json',parent)
    manifest=source.assemble(root,tmp_path/'assembly',source_date=day,target_date='2026-09-30',start_date=day)
    report=research._sealed(manifest);positions=[]
    for part in storage.iter_tree(manifest.parent,report['partitions_ref']):
        positions.extend(research._sealed(manifest.parent/part['path'])['positions'])
    actual=[p for p in positions if p['evidence_kind']=='actual_completed']
    assert [p['position_key'] for p in actual]==['48376']
    assert actual[0]['source_reference']['path']==str(raw)
    assert actual[0]['actual_cost_reconciliation']['status']=='cost_source_unavailable'
    assert actual[0]['automatic_management_allowed'] is False
    assert actual[0]['entry_at'] is None and actual[0]['qty'] is None
    assert report['assembly_census']['source_gaps'].get('completed_snapshot_source_gap',0)==0
    sources=list(storage.iter_tree(manifest.parent,report['source_generations_ref']))
    assert any('postclose_exit.json' in row['path'] for row in sources)
    assert not raw.with_suffix('.completed_projection.json').exists()


@pytest.mark.parametrize('have_sidecar',[False,True])
def test_bare_gzip_native_empty_is_consumed_as_empty_without_missing_original_inode(tmp_path,have_sidecar):
    from src.tests.test_holding_window_generation import _archived_empty_original
    root=tmp_path/'source';raw,physical,sidecar,original_manifest,_=_archived_empty_original(root,day=DAY)
    if not have_sidecar:sidecar.unlink()
    write(root/'report/micro_reversion_economic_reference/micro_reversion_symbol_master_2026-08-25.json',_master_payload())
    parent=dict(target_date=DAY,scalp_trailing_mechanical_policy_receipt=baseline_receipt({},source='operator_directed_m1_baseline'))
    parent['manifest_sha256']=_digest_json(parent)
    write(root/'runtime/policy_bootstrap'/f'runtime_policy_bootstrap_{DAY}.json',parent)
    manifest=source.assemble(root,tmp_path/'assembly',source_date=DAY,target_date=TARGET,start_date=DAY)
    report=research._sealed(manifest)
    assert report['population_ids_ref']['count']==0
    assert report['assembly_census']['source_gaps'].get('completed_snapshot_unverified',0)==0
    assert report['assembly_census']['source_gaps'].get('completed_snapshot_source_gap',0)==0
    consumed=list(storage.iter_tree(manifest.parent,report['source_generations_ref']))
    assert any(row['path']==str(physical) for row in consumed)
    assert any(row['path']==str(original_manifest) for row in consumed)
    assert not raw.exists() and not Path(str(physical)+'.archive_receipt.json').exists()


def _original_partial_calendar_source(root,day,*,holding_events=0):
    from src.tests.test_holding_window_generation import _archived_empty_original
    raw,physical,sidecar,_,value=_archived_empty_original(root,day=day,legacy=True)
    sidecar.unlink();value['meta']['snapshot_profile']='intraday_light'
    value['meta']['completion_event_unresolved_id_count']=0
    value['metrics'].update(total_trades=0,completed_trades=0,entered_rows=0,open_trades=0,
        open_scalp_position_projection_count=0,full_fill_events=0,partial_fill_events=0,carry_completed_rows=0,
        holding_events=holding_events)
    value['sections'].update(completed_trades=[],open_trades=[])
    # The original observed prefix remains distinct from any later trace data.
    value['meta']['trailing_event_source_receipts']=[dict(path='original-prefix-only',size_bytes=3058,logical_sha256='a'*64)]
    physical.write_bytes(gzip.compress(json.dumps(value).encode(),mtime=0))
    return raw,physical,value


@pytest.mark.parametrize('day,trading,holding_events',[('2026-10-05',False,0),('2026-10-09',False,2),
    ('2026-10-11',False,0),('2026-10-01',True,0)])
def test_partial_nontrading_calendar_diagnostic_never_upgrades_raw_census(tmp_path,monkeypatch,day,trading,holding_events):
    from src.utils import market_day
    from src.engine.lifecycle.holding_window_generation import capture_window
    monkeypatch.setattr(market_day,'get_krx_trading_day_status',lambda _: (trading,'trading_day' if trading else 'holiday:fixture'))
    root=tmp_path/'source';raw,physical,value=_original_partial_calendar_source(root,day,holding_events=holding_events)
    original=physical.read_bytes();prior=capture_window(root,[day])
    write(root/'report/micro_reversion_economic_reference/micro_reversion_symbol_master_2026-08-25.json',_master_payload())
    parent=dict(target_date=day,scalp_trailing_mechanical_policy_receipt=baseline_receipt({},source='operator_directed_m1_baseline'))
    parent['manifest_sha256']=_digest_json(parent)
    write(root/'runtime/policy_bootstrap'/f'runtime_policy_bootstrap_{day}.json',parent)
    manifest=source.assemble(root,tmp_path/'assembly',source_date=day,target_date='2026-10-12',start_date=day)
    report=research._sealed(manifest);census=report['assembly_census']
    assert census['source_gaps']['completed_snapshot_unverified']==1
    assert report['population_ids_ref']['count']==0
    diagnostics=census['publication_due_diagnostics']
    if trading:assert diagnostics==[]
    else:
        assert len(diagnostics)==1
        row=diagnostics[0]
        assert row['publication_status']=='not_due' and row['native_postclose_valid_empty'] is False
        assert row['source_gap_preserved'] is True
        assert row['original_holding_event_count']==holding_events
        assert row['original_snapshot_profile']=='intraday_light'
        assert row['original_window_status']==prior['dependencies'][day]['status']
        assert row['original_source_receipts']==value['meta']['trailing_event_source_receipts']
        assert row['original_metrics']==value['metrics']
    assert capture_window(root,[day])==prior and physical.read_bytes()==original
    assert not raw.exists() and not Path(str(physical)+'.archive_receipt.json').exists()


@pytest.mark.parametrize('mutation',['nonzero_entry','nonzero_open','missing_count','nonzero_fill','nonempty_rows','count_bool'])
def test_nontrading_partial_unknown_or_nonzero_observations_remain_source_gaps(tmp_path,monkeypatch,mutation):
    from src.utils import market_day
    monkeypatch.setattr(market_day,'get_krx_trading_day_status',lambda _: (False,'weekend'))
    root=tmp_path/'source';day='2026-10-11';_,physical,value=_original_partial_calendar_source(root,day)
    if mutation=='nonzero_entry':value['metrics']['entered_rows']=1
    elif mutation=='nonzero_open':value['metrics']['open_trades']=1
    elif mutation=='missing_count':value['metrics'].pop('open_trades')
    elif mutation=='nonzero_fill':value['metrics']['full_fill_events']=1
    elif mutation=='nonempty_rows':value['sections']['completed_trade_projection']=[dict(id=7)]
    elif mutation=='count_bool':value['metrics']['canonical_completed_trades']=False
    physical.write_bytes(gzip.compress(json.dumps(value).encode(),mtime=0))
    diagnostic=source.partial_publication_calendar_diagnostic(root,day)
    assert diagnostic['publication_status']=='not_due'
    assert diagnostic['zero_trade_observations'] is False
    assert diagnostic['source_gap_preserved'] is True


@pytest.mark.parametrize('mutation',[
    'plain_fifo','gzip_fifo','plain_symlink','gzip_symlink','parent_symlink',
    'physical_oversize','decoded_oversize','crc','isize','truncated','duplicate_key','decode_race'])
def test_calendar_diagnostic_rejects_unsafe_intake_before_unbounded_hash(tmp_path,monkeypatch,mutation):
    import os
    from src.utils import market_day
    monkeypatch.setattr(market_day,'get_krx_trading_day_status',lambda _: (False,'weekend'))
    root=tmp_path/'source';day='2026-10-11'
    raw,physical,value=_original_partial_calendar_source(root,day)
    original=physical.read_bytes()
    if mutation=='plain_fifo':os.mkfifo(raw)
    elif mutation=='gzip_fifo':physical.unlink();os.mkfifo(physical)
    elif mutation=='plain_symlink':raw.symlink_to(physical)
    elif mutation=='gzip_symlink':
        saved=physical.with_name('saved.gz');physical.rename(saved);physical.symlink_to(saved)
    elif mutation=='parent_symlink':
        actual=physical.parent.with_name('actual_snapshots');physical.parent.rename(actual)
        physical.parent.symlink_to(actual,target_is_directory=True)
    elif mutation=='physical_oversize':
        with physical.open('wb') as handle:handle.truncate(4*1024*1024+1)
    elif mutation=='decoded_oversize':
        physical.write_bytes(gzip.compress(b' '* (4*1024*1024+1),mtime=0))
    elif mutation in ('crc','isize'):
        corrupt=bytearray(original);corrupt[-8 if mutation=='crc' else -4]^=1
        physical.write_bytes(corrupt)
    elif mutation=='truncated':physical.write_bytes(original[:-1])
    elif mutation=='duplicate_key':
        physical.write_bytes(gzip.compress(b'{"date":"2026-10-11",'+json.dumps(value).encode()[1:],mtime=0))
    elif mutation=='decode_race':
        original_loads=source.json.loads
        def changed(*args,**kwargs):
            result=original_loads(*args,**kwargs)
            physical.write_bytes(original+b'changed')
            return result
        monkeypatch.setattr(source.json,'loads',changed)
    original_generation=source.byte_generation
    def forbid_source_hash(path):
        assert Path(path) not in (raw,physical),'calendar intake must precede full source hashing'
        return original_generation(path)
    monkeypatch.setattr(source,'byte_generation',forbid_source_hash)
    monkeypatch.setattr(source,'read',lambda _:pytest.fail('calendar diagnostic used the general full-hash reader'))
    assert source.partial_publication_calendar_diagnostic(root,day) is None


def test_calendar_diagnostic_rejects_regular_file_replaced_by_fifo_before_open(tmp_path,monkeypatch):
    import os
    from src.utils import market_day
    monkeypatch.setattr(market_day,'get_krx_trading_day_status',lambda _: (False,'weekend'))
    root=tmp_path/'source';day='2026-10-11'
    _,physical,_=_original_partial_calendar_source(root,day)
    original_open=os.open
    def raced(path,flags,*args,**kwargs):
        if Path(path)==physical:
            assert flags & os.O_NONBLOCK and flags & os.O_NOFOLLOW
            physical.unlink();os.mkfifo(physical)
        return original_open(path,flags,*args,**kwargs)
    monkeypatch.setattr(os,'open',raced)
    assert source.partial_publication_calendar_diagnostic(root,day) is None


@pytest.mark.parametrize('compressed',[False,True])
def test_calendar_diagnostic_generation_hashes_exact_bounded_original_bytes(tmp_path,monkeypatch,compressed):
    import hashlib
    from src.utils import market_day
    monkeypatch.setattr(market_day,'get_krx_trading_day_status',lambda _: (False,'holiday:fixture'))
    root=tmp_path/'source';day='2026-10-09'
    raw,physical,value=_original_partial_calendar_source(root,day,holding_events=2)
    if not compressed:
        raw.write_bytes(gzip.decompress(physical.read_bytes()));physical.unlink();physical=raw
    original=physical.read_bytes()
    result=source.partial_publication_calendar_diagnostic(root,day)
    assert result['source_generation']==dict(path=physical.name,size=len(original),sha256=hashlib.sha256(original).hexdigest())
    assert result['original_holding_event_count']==2
    assert result['original_source_receipts']==value['meta']['trailing_event_source_receipts']
    assert result['source_gap_preserved'] is True and result['native_postclose_valid_empty'] is False
    assert physical.read_bytes()==original


def test_plain_original_with_unproven_bare_sidecar_archive_is_an_identified_gap(tmp_path):
    from src.tests.test_holding_window_generation import _old_empty_projection
    root=tmp_path/'source';fixture(root)
    raw,sidecar,_=_old_empty_projection(root,DAY)
    archived=Path(str(sidecar)+'.gz');archived.write_bytes(gzip.compress(sidecar.read_bytes(),mtime=0));sidecar.unlink()
    manifest=source.assemble(root,tmp_path/'assembly',source_date=DAY,target_date=TARGET,start_date=DAY)
    report=research._sealed(manifest)
    assert report['assembly_census']['source_gaps']['completed_snapshot_source_gap']==1
    assert archived.exists() and raw.exists()
    assert not Path(str(archived)+'.archive_receipt.json').exists()
