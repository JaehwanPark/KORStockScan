import json
import pytest
from pathlib import Path

from src.engine.automation import entry_cancel_wait_tuning as mod


@pytest.fixture
def terminal_cancel_pair(monkeypatch):
    from src.engine.pipeline_event_summary import execution_projection_identity
    monkeypatch.setenv('KORSTOCKSCAN_BROKER_ACCOUNT_KEY','terminal-test-account')
    day='2026-10-22'
    terminal=dict(event='ORDER_TERMINAL',state='ORDER_TERMINAL',event_hash='a'*64,
        account_key='terminal-test-account',
        intent_id='intent',symbol='123456',owner_type='main_scalping',
        owner_id='main_scalping:7',position_id='main_scalping:7',side='BUY',action='NEW',
        order_date=day,broker_order_no='order',quantity=1,filled_qty=1,
        observed_at_kst=day+'T09:00:00+09:00')
    fields=dict(orig_ord_no='order',entry_split_initial_entry_seed='large frozen source'*100,
                cancel_reason='entry_split_probe_timeout')
    requested=dict(stage='entry_order_cancel_requested',emitted_date=day,emitted_at=day+'T09:01:00',
                   pipeline='ENTRY_PIPELINE',stock_code='123456',record_id=7,fields=fields)
    failed={**requested,'stage':'entry_order_cancel_failed','emitted_at':day+'T09:01:01',
            'fields':{**fields,'cancel_response':'failed','cancel_message':'owner_registry_cancel_original_not_open'}}
    for row in (requested,failed):row['execution_source_event_sha256']=execution_projection_identity(row)
    return [requested,failed],[terminal]


@pytest.mark.parametrize('damage',[None,'partial','boolean_fill','account','owner','date','clock','message','unpaired'])
def test_terminal_cancel_diagnostics_preserve_original_identities_without_raw_duplication(terminal_cancel_pair,damage):
    import copy
    rows,registry=copy.deepcopy(terminal_cancel_pair)
    if damage=='partial':registry[0]['filled_qty']=0
    elif damage=='boolean_fill':registry[0]['filled_qty']=True
    elif damage=='account':registry[0]['account_key']='other-account'
    elif damage=='owner':registry[0]['owner_id']='main_scalping:other'
    elif damage=='date':registry[0]['order_date']='2026-10-21'
    elif damage=='clock':registry[0]['observed_at_kst']='2026-10-22T09:02:00+09:00'
    elif damage=='message':rows[1]['fields']['cancel_message']='broker_failure'
    elif damage=='unpaired':rows=rows[:1]
    kept,diagnostics=mod._partition_terminal_cancel_diagnostics(iter(rows),registry)
    if damage:
        assert kept==rows and diagnostics=={}
    else:
        assert kept==[]
        groups=diagnostics['2026-10-22']
        assert {sha for group in groups for sha in group['event_sha256s']}=={mod._digest(r) for r in rows}
        assert {sha for group in groups for sha in group['execution_sha256s']}=={r['execution_source_event_sha256'] for r in rows}
        assert len(json.dumps(diagnostics))<len(json.dumps(rows))
        mod._validate_terminal_cancel_diagnostics(groups,'2026-10-22',registry=registry)


@pytest.mark.parametrize('damage',[None,'new_loss','identity','terminal','partial','pair','generation'])
def test_terminal_diagnostics_reconcile_the_real_native_census(tmp_path,monkeypatch,terminal_cancel_pair,damage):
    import copy
    from src.engine.pipeline_event_summary import CANCEL_WAIT_SUMMARY_STAGES,IDENTITY_CONTRACT,IDENTITY_MODULUS
    from src.engine.scalping import entry_split_order_plan as entry
    rows,registry=copy.deepcopy(terminal_cancel_pair);day='2026-10-22'
    summary=tmp_path/'pipeline_event_summaries'/f'pipeline_event_producer_summary_{day}.jsonl'
    summary.parent.mkdir()
    stages=CANCEL_WAIT_SUMMARY_STAGES|{'order_leg_sent'}
    summary.write_text(''.join(json.dumps(dict(target_date=day,stage=stage,
        identity_contract=IDENTITY_CONTRACT,execution_projection_identity_contract='lossless_execution_projection_v1',
        event_count=sum(r['stage']==stage for r in rows),
        execution_projection_hash_sum=format(sum(int(r['execution_source_event_sha256'],16) for r in rows if r['stage']==stage)%IDENTITY_MODULUS,'064x')))+'\n' for stage in stages))
    manifest=dict(target_date=day,identity_contract=IDENTITY_CONTRACT,summary_stages=sorted(stages),
                  summary_storage_size_bytes=summary.stat().st_size)
    summary.with_name(f'pipeline_event_producer_summary_manifest_{day}.json').write_text(json.dumps(manifest))
    census=entry._execution_projection_census(day,rows,stages=stages,data_root=tmp_path)
    assert census['status']=='ready'
    kept,diagnostics=mod._partition_terminal_cancel_diagnostics(rows,registry);groups=diagnostics[day]
    if damage=='new_loss':census['native_census_projection']['expected_stage_counts'][rows[0]['stage']]+=1
    elif damage=='identity':groups[0]['execution_sha256s'][0]='f'*64
    elif damage=='terminal':registry[0]['event_hash']='f'*64
    elif damage=='partial':registry[0]['filled_qty']=0
    elif damage=='pair':groups.pop()
    elif damage=='generation':summary.write_text('{}\n')
    if damage in {'terminal','partial','pair','generation'}:
        with pytest.raises(ValueError):
            mod._validate_terminal_cancel_diagnostics(groups,day,registry=registry)
            mod._projected_census_matches(tmp_path,day,kept,manifest,census['native_census_projection'],groups)
    else:
        actual=mod._projected_census_matches(tmp_path,day,kept,manifest,census['native_census_projection'],groups)
        assert actual is (damage is None)
        if damage is None:
            binding=mod._source_binding(dict(status='ready',retained_event_count=2,producer_census=census),
                dict(status='verified'),diagnostics=groups)
            state=dict(through_date=day,parents=[],source_events=[],source_counts={},actual_outcomes=[],
                model_rows=[],submission_reconciliation=dict(by_date={day:dict(source_binding=binding)}))
            state['sha256']=mod._digest(state)
            directory=tmp_path/'report/entry_cancel_wait_tuning';directory.mkdir(parents=True)
            from src.engine.scalping.entry_cancel_wait_runtime import ECONOMIC_SCHEMA
            payload=dict(date=day,generated_at=day+'T20:00:00+09:00',economic_schema=ECONOMIC_SCHEMA,economic_state=state)
            payload['proof_sha256']=mod._digest({k:v for k,v in payload.items() if k!='generated_at'})
            report_path=directory/f'entry_cancel_wait_tuning_{day}.json'
            report_path.write_text(json.dumps(payload))
            import hashlib
            report_path.with_suffix('.reuse-contract.json').write_text(json.dumps(dict(
                artifact_sha256=hashlib.sha256(report_path.read_bytes()).hexdigest(),
                report_proof_sha256=payload['proof_sha256'],as_of=payload['generated_at'],
                terminal_cancel_diagnostics_sha256=mod._diagnostic_projection_digest(payload))))
            monkeypatch.setattr(mod,'DATA_DIR',tmp_path);monkeypatch.setattr(mod,'REPORT_DIR',directory)
            monkeypatch.setattr(entry,'_execution_registry_snapshot',lambda:(registry,dict(status='verified')))
            monkeypatch.setattr(entry,'_bounded_execution_projection',lambda *_a,**_k:pytest.fail('unchanged large source rescan'))
            rebuilt=mod._previous_state('2026-10-23')
            assert rebuilt['_verified_source_bindings'][day]==binding
            assert rebuilt['source_events']==[]
            groups[0]['event_sha256s'][0]='f'*64
            state['sha256']=mod._digest({k:v for k,v in state.items() if k!='sha256'})
            payload['proof_sha256']=mod._digest({k:v for k,v in payload.items() if k not in {'generated_at','proof_sha256'}})
            report_path.write_text(json.dumps(payload))
            with pytest.raises(ValueError,match='diagnostic_publication_changed'):
                mod._previous_state('2026-10-23')


def _unclassified_history(day='2026-09-30'):
    events = [dict(stage='order_leg_sent', emitted_date=day, record_id=i,
                   pipeline='ENTRY_PIPELINE',stock_code='123456', fields=dict(actual_order_submitted=True,
                   broker_order_no=f'B{i}', buy_account_key='acct-a'))
              for i in (1, 2)]
    state = dict(through_date=day, parents=[], source_counts={}, source_events=events,
                 actual_outcomes=[], model_rows=[], consumed_holdouts=[])
    state['sha256'] = mod._digest(state)
    return state


def _empty_reconciliation_report(tmp_path, monkeypatch, predecessor=None, *, streamed=False):
    from src.engine.scalping import entry_split_order_plan as entry
    monkeypatch.setattr(entry, '_bounded_execution_projection', lambda *_a, **_k: ([], {'status':'ready'}))
    monkeypatch.setattr(mod, 'REPORT_DIR', tmp_path)
    monkeypatch.setattr(mod, '_incumbent', lambda _day: (
        dict(mod.DEFAULT_THRESHOLDS), {'previous_scope_overrides': []}))
    monkeypatch.setattr(mod, '_previous_state', lambda _day: predecessor or {})
    monkeypatch.setattr(mod, '_current_sources', lambda _day: (
        entry._ExecutionProjectionRows([]) if streamed else [], [], [], dict(projection={'status': 'ready'}, registry={'status': 'verified'},
                        actual_outcomes={'status': 'missing'},
                        source_quality={'tuning_input_allowed': True})))
    return mod.build_report('2026-10-02')


def test_streamed_projection_preserves_cancel_history(tmp_path,monkeypatch):
    report=_empty_reconciliation_report(tmp_path,monkeypatch,_unclassified_history(),streamed=True)
    assert report['submission_census']['zero_is_verified'] is True
    assert report['historical_reconciliation']['unclassified_submission_count']==2
    assert report['economic_tuning_input_allowed'] is False


def test_current_empty_does_not_erase_historical_unclassified_submissions(tmp_path, monkeypatch):
    report = _empty_reconciliation_report(tmp_path, monkeypatch, _unclassified_history())
    assert report['submission_census']['zero_is_verified'] is True
    assert report['submission_census']['unresolved_prior_custody_count'] is None
    assert report['historical_reconciliation']['unclassified_submission_count'] == 2
    assert report['historical_reconciliation']['zero_is_verified'] is False
    assert report['economic_evaluation']['status'] == 'source_gap'
    assert report['economic_tuning_input_allowed'] is False


def test_predecessor_event_only_date_is_revalidated(tmp_path, monkeypatch):
    from src.engine.scalping import entry_split_order_plan as entry
    from src.engine.scalping.entry_cancel_wait_runtime import ECONOMIC_SCHEMA
    state = _unclassified_history()
    monkeypatch.setattr(mod, 'REPORT_DIR', tmp_path)
    monkeypatch.setattr(entry, '_execution_registry_snapshot', lambda: ([], {'status': 'verified'}))
    calls = []
    def original(day, **kwargs):
        calls.append(day)
        return [], {'status': 'ready'}
    monkeypatch.setattr(entry, '_bounded_execution_projection', original)
    (tmp_path/'entry_cancel_wait_tuning_2026-09-30.json').write_text(json.dumps(
        dict(economic_schema=ECONOMIC_SCHEMA, economic_state=state)))
    with pytest.raises(ValueError, match='original_projection_changed'):
        mod._previous_state('2026-10-02')
    assert calls == ['2026-09-30']


def test_hold_preserves_thresholds_without_samples(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path / "reports")
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    payload = mod.build_report("2026-06-12")
    assert payload["recommended_thresholds"] == mod.DEFAULT_THRESHOLDS
    assert payload["enabled"] is True
    assert payload["automatic_off_allowed"] is False
    assert payload["evidence_summary"]["state"] == "missing_source_hold"
    assert all(item["calibration_state"] == "hold_sample" for item in payload["profiles"].values())




def test_registry_only_attempt_cannot_be_verified_zero():
    registry=[{'intent_id':'lost','owner_type':'main_scalping','side':'BUY','action':'NEW',
        'order_date':'2026-09-17','client_intent_id':'main:1:ENTRY_BUY:1','state':'INTENT_AMBIGUOUS'}]
    parents,unclassified=mod._parents('2026-09-17',[],registry)
    assert not parents and unclassified==1


@pytest.mark.parametrize('state,order,filled,expected', [
    ('INTENT_REJECTED','',0,0), ('INTENT_AMBIGUOUS','',0,1),
    ('INTENT_RESERVED','',0,1), ('INTENT_REJECTED','000123',0,1),
    ('INTENT_REJECTED','',1,1), ('ORDER_TERMINAL','000123',0,1)])
def test_rejected_reservation_is_preserved_separately_from_submitted_orders(state,order,filled,expected):
    row=dict(intent_id='rejected',owner_type='main_scalping',owner_id='main_scalping:1',
        side='BUY',action='NEW',order_date='2026-10-16',client_intent_id='main:1:ENTRY_BUY:1',
        state=state,broker_order_no=order,filled_qty=filled,fill_amount=filled*100,
        reason='original_entry_deadline_expired')
    details={};parents,unknown=mod._parents('2026-10-16',[],[row],details=details)
    assert parents==[] and unknown==expected
    assert details['rejected_without_order_intent_ids']==(['rejected'] if not expected else [])
    unresolved=mod._unresolved_prior_custody('2026-10-19',[row],[],[])
    assert ('rejected' in unresolved) is bool(expected)
    assert row['reason']=='original_entry_deadline_expired'


def test_rejected_reservation_cannot_hide_a_native_submission_or_fill():
    row=dict(intent_id='rejected',owner_type='main_scalping',owner_id='main_scalping:1',
        side='BUY',action='NEW',order_date='2026-10-16',state='INTENT_REJECTED')
    event=dict(stage='order_leg_sent',emitted_date='2026-10-16',record_id=1,
        fields=dict(actual_order_submitted=True,broker_order_no='000123',owner_registry_intent_id='rejected'))
    with pytest.raises(ValueError,match='rejected_intent_submission_source_conflict'):
        mod._parents('2026-10-16',[event],[row])
    fill={**row,'event':'FILL_RECORDED','filled_qty':1,'fill_amount':100}
    _,unknown=mod._parents('2026-10-16',[],[row,fill])
    assert unknown==1


def test_residual_receipt_classifies_native_order_without_timeout_tuning_authority():
    from datetime import datetime
    from types import SimpleNamespace
    from src.engine.scalping import entry_cancel_wait_runtime as runtime
    day='2026-10-15';at=datetime.fromisoformat(day+'T10:00:00+09:00').timestamp()
    stock=dict(id=42,code='403870',entry_split_probe_bundle_id='original-probe',
        entry_split_probe_requested_qty=21)
    owner=SimpleNamespace(owner_type='main_scalping',owner_id='main_scalping:42',client_intent_id='original-residual-client')
    stock['entry_split_probe_submit_source']=runtime.probe_submit_source(stock,
        parent_id='original-attempt',account_key='acct-a',owner_context=owner,planned_qty=21,source_date=day)
    fields=runtime.residual_submission_fields(stock,{'tag':'residual-1'},owner_context=owner,
        account_key='acct-a',intent_id='I1',order_no='B1',qty=8,price=10000,route='KRX',now_ts=at)
    fields.update(actual_order_submitted=True,broker_order_no='B1',submitted_qty=8,broker_route='KRX')
    event=dict(stage='order_leg_sent',emitted_date=day,record_id=42,stock_code='403870',fields=fields)
    registry=[dict(event='ORDER_BOUND',intent_id='I1',owner_type='main_scalping',owner_id=owner.owner_id,
        client_intent_id=owner.client_intent_id,account_key='acct-a',order_date=day,broker_order_no='B1',
        side='BUY',action='NEW',quantity=8,filled_qty=0,symbol='403870',route='KRX',state='ORDER_BOUND')]
    parents,unknown=mod._parents(day,[event],registry)
    assert unknown==0 and len(parents)==1
    assert parents[0]['economic_eligible'] is False
    assert parents[0]['incumbent_timeout_sec'] is None
    assert parents[0]['timeout_owner']=='entry_split_probe_residual_runtime'
    assert not next(iter(parents[0]['children'].values()))['terminal_reconciled']
    # Valid-looking new metadata cannot relabel another owner's native order.
    registry[0]['client_intent_id']='another-generation'
    with pytest.raises(ValueError,match='residual_submission_source_identity_invalid'):
        mod._parents(day,[event],registry)


def test_projected_real_submit_without_context_or_owner_cannot_be_verified_zero():
    event=dict(stage='order_leg_sent',emitted_date='2026-09-22',fields=dict(
        actual_order_submitted='True',broker_order_no='0022991'))
    parents,unclassified=mod._parents('2026-09-22',[event],[])
    assert not parents and unclassified==1
    registry=[dict(intent_id='main-1',owner_type='main_scalping',side='BUY',action='NEW',
        order_date='2026-09-22',broker_order_no='0022991',client_intent_id='main:ENTRY_BUY:1')]
    assert mod._parents('2026-09-22',[event],registry)[1]==1
    event['fields']['actual_order_submitted']='False'
    assert mod._parents('2026-09-22',[event],[])[1]==0
    failed=dict(stage='entry_cancel_wait_submission',emitted_date='2026-09-22',
        fields=dict(actual_order_submitted='False',entry_cancel_wait_submission_context='invalid'))
    assert mod._parents('2026-09-22',[failed],[])[1]==0


def test_cancel_wait_parent_requires_same_submit_owner_account_and_explicit_parent(monkeypatch):
    day = '2026-09-28'
    context = dict(source_date=day, parent_id=None, child_id='probe',
        requested_qty=2, stock_code='123456', broker_route='SOR',
        actual_timeout_sec=90, wait_profile='standard', submitted_price=10000,
        frozen_at=day+'T09:00:00+09:00', seed={})
    context['sha256'] = mod._digest(context)
    submit = dict(stage='entry_cancel_wait_submission', emitted_date=day,
        record_id=42, stock_code='123456', fields=dict(
            actual_order_submitted=True, broker_order_no='B1',
            owner_registry_intent_id='I1',
            entry_cancel_wait_submission_context=json.dumps(context)))
    sent = dict(stage='order_leg_sent', emitted_date=day, record_id=42,
        stock_code='123456', fields=dict(actual_order_submitted=True,
            broker_order_no='B1', buy_parent_id='attempt-42',
            buy_child_id='attempt-42:B1', owner_registry_intent_id='I1',
            buy_owner_type='main_scalping', buy_owner_id='main_scalping:42',
            buy_account_key='acct-a', broker_route='SOR', submitted_qty=2))
    registry = [dict(intent_id='I1', owner_type='main_scalping', side='BUY',
        action='NEW', account_key='acct-a', owner_id='main_scalping:42',
        order_date=day, broker_order_no='B1', quantity=2, symbol='123456',
        route='SOR', state='ORDER_BOUND')]
    parents, unknown = mod._parents(day, [submit, sent], registry)
    assert unknown == 0 and [p['parent_id'] for p in parents] == ['attempt-42']
    sent['fields']['buy_account_key'] = 'acct-b'
    with pytest.raises(ValueError, match='submission_owner'):
        mod._parents(day, [submit, sent], registry)
    sent['fields']['buy_account_key'] = 'acct-a'
    sent['fields'].update(owner_registry_intent_id='',
        buy_registry_mode='single_owner_unregistered',
        buy_owner_policy_date=day, buy_owner_policy_selected=False,
        buy_owner_policy_coexistence=False,
        buy_owner_policy_reason='exact_date_policy_missing_legacy_exclusion_retained',
        buy_owner_policy_hash='')
    submit['fields']['owner_registry_intent_id'] = ''
    sent['timestamp'] = day + 'T09:00:00+09:00'
    parents, unknown = mod._parents(day, [submit, sent], [])
    assert unknown == 0 and parents[0]['parent_id'] == 'attempt-42'
    assert list(parents[0]['children'].values())[0]['intent_id'] is None
    assert list(parents[0]['children'].values())[0]['terminal_reconciled'] is False


def _sequential_first_fixture():
    from src.engine.scalping.initial_quantity_timeout import build_bundle_timeout_schedule
    day = '2026-09-28'
    schedule = build_bundle_timeout_schedule(
        quantity_type='KRX_PARENT', policy_sha256='a' * 64,
        decision_at=day+'T08:59:00+09:00',
        order_start_at=day+'T09:00:00+09:00', total_wait_sec=120,
        leg_count=2, cancel_confirm_reserve_sec=5)
    context = dict(schema='entry_cancel_wait_submitted_paired_v2',
        source_date=day, frozen_at=day+'T09:00:01+09:00',
        parent_id='attempt-42', bundle_attempt_id='evaluation-42',
        child_id='initial_quantity_0', stock_code='123456',
        requested_qty=2, plan_total_qty=5, submitted_price=10000,
        broker_route='SOR', session_bucket='KRX_REGULAR',
        owner_type='main_scalping', owner_id='main_scalping:42',
        owner_client_intent_id='client-42',
        timeout_owner='initial_quantity_bundle_timeout_schedule',
        initial_quantity_schedule=schedule, actual_timeout_sec=None,
        candidate_timeout_secs=[], economic_eligible=False, observation_only=True)
    context['sha256'] = mod._digest(context)
    sent = dict(stage='order_leg_sent', emitted_date=day, record_id=42,
        stock_code='123456', fields=dict(actual_order_submitted=True,
            broker_order_no='B1', buy_parent_id='attempt-42',
            buy_child_id='attempt-42:B1', owner_registry_intent_id='I1',
            buy_owner_type='main_scalping', buy_owner_id='main_scalping:42',
            buy_owner_client_intent_id='client-42', buy_account_key='acct-a',
            broker_route='SOR', market_session_bucket='KRX_REGULAR',
            submitted_qty=2, entry_split_submitted_price=10000,
            entry_split_submitted_at=day+'T09:00:02+09:00',
            tag='initial_quantity_0', initial_quantity_leg_index=0,
            initial_quantity_attempt_id='evaluation-42',
            initial_quantity_requested_qty=5,
            initial_quantity_schedule_sha256=schedule['schedule_sha256'],
            initial_quantity_policy_file_sha256='a' * 64,
            cancel_wait_timeout_owner='initial_quantity_bundle_timeout_schedule',
            entry_cancel_wait_submission_context=json.dumps(context)))
    registry = [dict(intent_id='I1', owner_type='main_scalping', side='BUY',
        action='NEW', account_key='acct-a', owner_id='main_scalping:42',
        client_intent_id='client-42',
        order_date=day, broker_order_no='B1', quantity=2,
        symbol='123456', route='SOR', state='ORDER_BOUND')]
    return day, context, sent, registry


def test_sequential_first_leg_is_source_only_parent_not_unclassified():
    day, context, sent, registry = _sequential_first_fixture()
    parents, unknown = mod._parents(day, [sent], registry)
    assert unknown == 0
    assert len(parents) == 1
    assert parents[0]['timeout_owner'] == 'initial_quantity_bundle_timeout_schedule'
    assert parents[0]['economic_eligible'] is False
    assert parents[0]['children']['I1']['quantity'] == 2
    duplicate = {**sent, 'stage': 'entry_cancel_wait_submission'}
    parents, unknown = mod._parents(day, [sent, duplicate], registry)
    assert unknown == 0 and len(parents) == 1
    assert len(parents[0]['children']) == 1
    changed = json.loads(json.dumps(sent))
    changed['fields']['initial_quantity_schedule_sha256'] = 'b' * 64
    with pytest.raises(ValueError, match='sequential_schedule'):
        mod._parents(day, [changed], registry)


@pytest.mark.parametrize('fault',[None,'account','symbol','owner','date','unknown_parent','operation','ambiguous_parent'])
def test_reprice_scope_requires_native_parent_and_preserves_custody(fault):
    day,_,sent,registry=_sequential_first_fixture()
    sent['fields'].update(broker_order_no='00010',buy_child_id='attempt-42:00010')
    registry[0]['broker_order_no']='00010'
    reprice={**registry[0],'intent_id':'R1','broker_order_no':'00011',
        'client_intent_id':'main_scalping:42:42:ENTRY_REPRICE_BUY:00010:'+'c'*32}
    if fault in {'account','symbol','owner','date'}:
        field={'account':'account_key','symbol':'symbol','owner':'owner_id','date':'order_date'}[fault]
        reprice[field]={'account':'other','symbol':'654321','owner':'main_scalping:43','date':'2026-09-29'}[fault]
    elif fault=='unknown_parent':reprice['client_intent_id']=reprice['client_intent_id'].replace('00010:','00099:')
    elif fault=='operation':reprice['client_intent_id']=reprice['client_intent_id'].replace('ENTRY_REPRICE_BUY','ENTRY_BUY')
    elif fault=='ambiguous_parent':registry.append({**registry[0],'intent_id':'duplicate'})
    details={};parents,unknown=mod._parents(day,[sent],[*registry,reprice],details=details)
    if fault:
        assert details['excluded_reprice_order_sources']==[]
        if fault!='date':assert unknown>0
        return
    assert unknown==0 and len(parents)==1
    proof=details['excluded_reprice_order_sources'][0]
    assert proof['intent_id']=='R1' and proof['root_submission_intent_id']=='I1'
    assert proof['parent_broker_order_no']=='00010' and proof['economic_eligible'] is False
    assert proof['terminal_or_cost_inferred'] is False
    # Scope classification cannot reconcile a real order or its costs.
    assert mod._unresolved_prior_custody('2026-10-19',[*registry,reprice],parents,[])==['I1','R1']
    chained={**reprice,'intent_id':'R2','broker_order_no':'00012',
        'client_intent_id':'main_scalping:42:42:ENTRY_REPRICE_BUY:00011:'+'d'*32}
    details={};_,unknown=mod._parents(day,[sent],[*registry,reprice,chained],details=details)
    assert unknown==0
    assert {x['root_submission_intent_id'] for x in details['excluded_reprice_order_sources']}=={'I1'}


def test_sequential_first_uncertain_attempt_stays_out_of_submitted_parents():
    day, context, sent, registry = _sequential_first_fixture()
    uncertain = dict(stage='entry_cancel_wait_submission',
        emitted_date=day, record_id=42, stock_code='123456',
        fields=dict(actual_order_submitted=False,
            dispatch_disposition='response_uncertain', broker_call_attempted=True,
            entry_cancel_wait_submission_context=json.dumps(context),
            cancel_wait_timeout_owner='initial_quantity_bundle_timeout_schedule'))
    unresolved_registry = [{**registry[0], 'broker_order_no': None,
                            'state': 'INTENT_AMBIGUOUS'}]
    details = {}
    parents, unknown = mod._parents(
        day, [uncertain, uncertain], unresolved_registry, details=details)
    assert parents == [] and unknown == 1
    assert details['response_uncertain_attempt_count'] == 1
    assert details['unresolved_uncertain_attempt_count'] == 1
    details = {}
    parents, unknown = mod._parents(day, [uncertain, sent], registry, details=details)
    assert unknown == 0 and len(parents) == 1
    assert details['resolved_uncertain_attempt_count'] == 1


def test_sequential_first_source_only_is_excluded_from_cancel_wait_replay():
    day, _, sent, registry = _sequential_first_fixture()
    parents, unknown = mod._parents(day, [sent], registry)
    assert unknown == 0
    assert mod._replay_parents(parents, [], [], {}) == ([], [], {})


def test_sequential_first_partial_fill_and_cancel_pending_keep_null_cost():
    day, _, sent, registry = _sequential_first_fixture()
    fill = dict(intent_id='I1', owner_type='main_scalping', side='BUY',
        action='NEW', event='FILL_RECORDED', filled_qty=1, execution_no='E1')
    parents, unknown = mod._parents(day, [sent], registry+[fill])
    assert unknown == 0
    child = parents[0]['children']['I1']
    assert child['terminal_state'] == 'partial_open'
    assert child['filled_qty'] == 1 and child['cost_krw'] is None
    cancel = dict(intent_id='C1', account_key='acct-a',
        order_date=day, owner_id='main_scalping:42', side='BUY',
        action='CANCEL', original_order_no='B1', state='INTENT_RESERVED')
    parents, unknown = mod._parents(day, [sent], registry+[fill,cancel])
    assert unknown == 0
    assert parents[0]['children']['I1']['terminal_state'] == 'cancel_pending'
    closed = dict(intent_id='C1', side='BUY', action='CANCEL',
                  state='ORDER_TERMINAL')
    parents, unknown = mod._parents(day, [sent], registry+[fill,cancel,closed])
    assert unknown == 0
    assert parents[0]['children']['I1']['terminal_state'] == 'partial_open'


def test_sequential_first_report_counts_real_submit_without_economic_authority(
    monkeypatch, tmp_path,
):
    day, _, sent, registry = _sequential_first_fixture()
    monkeypatch.setattr(mod, 'REPORT_DIR', tmp_path)
    monkeypatch.setattr(mod, '_incumbent', lambda _day: (
        dict(mod.DEFAULT_THRESHOLDS), {'path': None}))
    monkeypatch.setattr(mod, '_previous_state', lambda _day: {})
    monkeypatch.setattr(mod, '_current_sources', lambda _day: (
        [sent], registry, [], {'projection': {'status': 'ready'},
        'registry': {'status': 'verified'},
        'actual_outcomes': {'status': 'missing'},
        'source_quality': {'tuning_input_allowed': True}}))
    report = mod.build_report(day)
    assert report['submission_census']['submitted_parent_count'] == 1
    assert report['submission_census']['economic_parent_count'] == 0
    assert report['submission_census']['excluded_sequential_timeout_owner_count'] == 1
    assert report['submission_census']['zero_is_verified'] is False
    assert report['evidence_summary']['state'] == 'source_only_sequential_excluded'
    assert report['economic_tuning_input_allowed'] is False
    assert report['recommended_thresholds'] == mod.DEFAULT_THRESHOLDS

    fill = {**registry[0], 'event': 'FILL_RECORDED',
            'filled_qty': 2, 'execution_no': 'E1'}
    terminal = {**registry[0], 'event': 'ORDER_TERMINAL',
                'state': 'ORDER_TERMINAL', 'filled_qty': 2}
    proof = {key: terminal[key] for key in (
        'intent_id','account_key','order_date','broker_order_no','owner_type',
        'owner_id','symbol','side','action','route','quantity','filled_qty')}
    proof.update(schema='order_owner_terminal_reconciliation_v1',
                 receipt_sha256='f'*64)
    receipt = dict(intent_id='I1', account_key='acct-a',
                   event='TERMINAL_RECONCILIATION_RECORDED',
                   terminal_reconciliation=proof)
    monkeypatch.setattr(mod, '_current_sources', lambda _day: (
        [sent], registry+[fill, terminal, receipt], [],
        {'projection': {'status': 'ready'},
         'registry': {'status': 'verified'},
         'actual_outcomes': {'status': 'missing'},
         'source_quality': {'tuning_input_allowed': True}}))
    refreshed = mod.build_report(day)
    child = refreshed['economic_state']['parents'][0]['children']['I1']
    assert child['terminal_reconciled'] is True
    assert child['terminal_state'] == 'full_terminal'
    monkeypatch.setattr(mod, '_previous_state',
                        lambda _day: report['economic_state'])
    monkeypatch.setattr(mod, '_current_sources', lambda _day: (
        [], registry+[fill, terminal, receipt], [],
        {'projection': {'status': 'ready'},
         'registry': {'status': 'verified'},
         'actual_outcomes': {'status': 'missing'},
         'source_quality': {'tuning_input_allowed': True}}))
    resumed = mod.build_report('2026-09-29')
    child = resumed['economic_state']['parents'][0]['children']['I1']
    assert child['terminal_reconciled'] is True
    assert child['terminal_state'] == 'full_terminal'


def test_sequential_first_terminal_requires_exact_registry_proof():
    day, _, sent, registry = _sequential_first_fixture()
    fill = {**registry[0], 'event': 'FILL_RECORDED',
            'filled_qty': 2, 'execution_no': 'E1'}
    terminal = {**registry[0], 'event': 'ORDER_TERMINAL',
                'state': 'ORDER_TERMINAL', 'filled_qty': 2}
    proof = {key: terminal[key] for key in (
        'intent_id','account_key','order_date','broker_order_no','owner_type',
        'owner_id','symbol','side','action','route','quantity','filled_qty')}
    proof.update(schema='order_owner_terminal_reconciliation_v1',
                 receipt_sha256='f'*64)
    receipt = {'intent_id': 'I1', 'account_key': 'acct-a',
               'event': 'TERMINAL_RECONCILIATION_RECORDED',
               'terminal_reconciliation': proof}
    parents, unknown = mod._parents(day, [sent], registry+[fill,terminal,receipt])
    assert unknown == 0
    assert parents[0]['children']['I1']['terminal_state'] == 'full_terminal'
    broken = {**receipt, 'terminal_reconciliation': {
        **proof, 'broker_order_no': 'OTHER'}}
    parents, unknown = mod._parents(day, [sent], registry+[fill,terminal,broken])
    assert unknown == 0
    assert parents[0]['children']['I1']['terminal_state'] == 'terminal_unverified'


def test_sequential_first_context_freezes_before_broker_call():
    import ast
    from datetime import datetime
    from types import SimpleNamespace
    from src.engine import sniper_state_handlers as handlers
    from src.engine.scalping.entry_cancel_wait_runtime import (
        sequential_first_submission_fields,
    )

    day, expected, sent, _ = _sequential_first_fixture()
    fields = sequential_first_submission_fields(
        {'code': '123456', 'market_session_bucket': 'KRX_REGULAR'},
        {'tag': 'initial_quantity_0'},
        intent={'schedule': expected['initial_quantity_schedule'],
                'attempt_id': 'evaluation-42', 'requested_qty': 5},
        owner_context=SimpleNamespace(owner_type='main_scalping',
            owner_id='main_scalping:42', client_intent_id='client-42'),
        parent_id='attempt-42', qty=2, price=10000, route='SOR',
        now_ts=datetime.fromisoformat(day+'T09:00:01+09:00').timestamp())
    context = json.loads(fields['entry_cancel_wait_submission_context'])
    assert context == expected
    assert fields['cancel_wait_timeout_owner'] == (
        'initial_quantity_bundle_timeout_schedule')
    tree = ast.parse(Path(handlers.__file__).read_text())
    owner = next(node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and node.name == '_submit_watching_triggered_entry')
    calls = [node for node in ast.walk(owner) if isinstance(node, ast.Call)]
    first_intent = min(node.lineno for node in calls
        if isinstance(node.func, ast.Name)
        and node.func.id == '_initial_quantity_prepare_first_submit')
    freeze = min(node.lineno for node in calls
        if isinstance(node.func, ast.Name)
        and node.func.id == 'sequential_first_submission_fields')
    broker = min(node.lineno for node in calls
        if isinstance(node.func, ast.Attribute)
        and node.func.attr == 'send_buy_order')
    assert first_intent < freeze < broker
    assert sent['fields']['initial_quantity_schedule_sha256'] == context[
        'initial_quantity_schedule']['schedule_sha256']


def test_runtime_submission_log_merges_response_without_losing_dispatch_truth():
    import ast
    from pathlib import Path
    from src.engine import sniper_state_handlers as handlers
    from src.engine.scalping.entry_cancel_wait_runtime import submission_response_fields

    tree=ast.parse(Path(handlers.__file__).read_text())
    call=next(node for node in ast.walk(tree) if isinstance(node,ast.Call)
        and isinstance(node.func,ast.Name) and node.func.id=='_log_entry_pipeline'
        and len(node.args)>=3 and isinstance(node.args[2],ast.Constant)
        and node.args[2].value=='entry_cancel_wait_submission')
    captured=[]
    env={**vars(handlers),'stock':{},'code':'041190',
         'submission_response_fields':submission_response_fields,
         'wait_submission':{'actual_order_submitted':False,
                            'entry_cancel_wait_submission_context':'frozen-context'},
         'res':{'return_code':'0','ord_no':'0022991'},
         '_log_entry_pipeline':lambda *args,**fields:captured.append(fields)}
    eval(compile(ast.Expression(call),'<actual-cancel-wait-log-call>','eval'),env)
    assert captured==[{'actual_order_submitted':True,
                       'entry_cancel_wait_submission_context':'frozen-context',
                       'broker_order_no':'0022991','broker_return_code':'0',
                       'owner_registry_intent_id':'','dispatch_disposition':'accepted'}]


def test_prior_custody_cannot_supply_a_zero_profit_day():
    journal=[dict(intent_id='held',owner_type='main_scalping',side='BUY',action='NEW',
        order_date='2026-09-17',state='ORDER_TERMINAL',terminal_reconciliation=True,filled_qty=1)]
    assert mod._unresolved_prior_custody('2026-09-18',journal,[],[])==['held']
    journal[0]['filled_qty']=0
    # A truthy flag / cancel ACK is not an owner-issued terminal receipt.
    assert mod._unresolved_prior_custody('2026-09-18',journal,[],[])==['held']
    journal[0].update(account_key='acct', broker_order_no='B1', owner_id='main_scalping:1',
        symbol='123456', route='SOR', quantity=1)
    proof={key:journal[0][key] for key in ('intent_id','account_key','order_date','broker_order_no',
        'owner_type','owner_id','symbol','side','action','route','quantity','filled_qty')}
    proof.update(schema='order_owner_terminal_reconciliation_v1', receipt_sha256='a'*64)
    journal[0]['terminal_reconciliation']=proof
    assert mod._unresolved_prior_custody('2026-09-18',journal,[],[])==[]


def test_incumbent_uses_runtime_manifest_not_verifier_receipt(tmp_path,monkeypatch):
    monkeypatch.setattr(mod,'DATA_DIR',tmp_path)
    directory=tmp_path/'runtime/policy_bootstrap';directory.mkdir(parents=True)
    (directory/'runtime_policy_bootstrap_2026-09-17.json').write_text(json.dumps(dict(target_date='2026-09-17',
        env_overrides={'KORSTOCKSCAN_SCALPING_ENTRY_TIMEOUT_SEC':'90'})))
    (directory/'runtime_policy_bootstrap_verify_2026-09-17.json').write_text(json.dumps(dict(target_date='2026-09-17',status='pass')))
    values,receipt=mod._incumbent('2026-09-17')
    assert values['standard']==90
    assert Path(receipt['path']).name=='runtime_policy_bootstrap_2026-09-17.json'


def test_actual_cancel_state_model_requires_independent_clock_holdout():
    rows=[]
    for day in ('2026-09-07','2026-09-08'):
        for i in range(10):
            rows.append(dict(parent_id=f'{day}:{i}',source_date=day,completion_date=day,
                scope=['KRX','KRX_REGULAR','KRX','standard'],fill_class='no_fill',complete=True,
                model_identity='model',net_error_pct=0.,cancel_ack_delay_sec=1.,late_fill_window_sec=2.,
                capital_error_minutes=0.,reserve_error_minutes=0.))
    model=mod._fit_model(rows,'model')
    assert model['validated'] is True and model['supported_states']==['no_fill']
    assert model['available_after_date']=='2026-09-08'
    rows[-1]['late_fill_window_sec']=3.
    assert mod._fit_model(rows,'model')['validated'] is False


def test_predecessor_self_reseal_cannot_replace_original_events(tmp_path,monkeypatch):
    from src.engine.scalping import entry_split_order_plan as entry
    from src.engine.scalping.entry_cancel_wait_runtime import ECONOMIC_SCHEMA
    monkeypatch.setattr(mod,'REPORT_DIR',tmp_path)
    monkeypatch.setattr(entry,'_execution_registry_snapshot',lambda:([],{'status':'verified'}))
    monkeypatch.setattr(entry,'_bounded_execution_projection',lambda *a,**k:([],{'status':'ready'}))
    state=dict(through_date='2026-09-17',parents=[],source_counts={'2026-09-17':0},
        source_events=[dict(emitted_date='2026-09-17',stage='entry_cancel_wait_submission',fields={})])
    state['sha256']=mod._digest(state)
    (tmp_path/'entry_cancel_wait_tuning_2026-09-17.json').write_text(json.dumps(dict(economic_schema=ECONOMIC_SCHEMA,economic_state=state)))
    with pytest.raises(ValueError,match='original_projection_changed'):
        mod._previous_state('2026-09-18')


def test_last_summary_semantics_cannot_reuse_a_generation_pass(tmp_path,monkeypatch):
    from src.engine.automation import postclose_summary_handoff as summary
    root=tmp_path/'data';root.mkdir()
    monkeypatch.setattr(mod,'DATA_DIR',root)
    monkeypatch.setattr(mod,'REPORT_DIR',root/'report/entry_cancel_wait_tuning')
    monkeypatch.setattr(mod,'_current_sources',lambda d:([],[],[],dict(projection={'status':'ready','retained_event_count':0},
        registry={'status':'verified'},actual_outcomes={'status':'missing'},source_quality={'tuning_input_allowed':True})))
    monkeypatch.setattr(summary,'verify_summary_handoff',lambda *a,**k:{'issues':[]})
    payload=mod.write_report('2026-09-18')
    summary_path=root/'report/runtime_approval_summary/runtime_approval_summary_2026-09-18.json'
    summary_path.parent.mkdir(parents=True,exist_ok=True)
    summary_path.write_text(json.dumps(dict(sources={'entry_cancel_wait':{'economic_evidence':{'cancel_wait_reconciliation':mod.validated_reconciliation_view(payload)}}})))
    pp=mod.REPORT_DIR/'entry_cancel_wait_policy_2026-09-18.json';policy=json.loads(pp.read_text())
    view=mod.handoff_view(payload,policy,pp)
    tower=root/'report/tuning_performance_control_tower/tuning_performance_control_tower_2026-09-18.json'
    tower.parent.mkdir(parents=True);tower.write_text(json.dumps({'entry_cancel_wait_economic_tuning':view}))
    checklist=tmp_path/'docs/checklists/2026-09-21-stage2-todo-checklist.md'
    checklist.parent.mkdir(parents=True);checklist.write_text(mod.checklist_handoff(view))
    assert mod.verify_handoff('2026-09-18')['status']=='PASS'
    view['policy_disposition']='validated_scope_candidate'
    tower.write_text(json.dumps({'entry_cancel_wait_economic_tuning':view}))
    assert 'cancel_wait_last_consumer_semantics_or_generation_invalid' in mod.verify_handoff('2026-09-18')['issues']


def test_deterministic_ev_applies_daily_step(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path / "reports")
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    event_dir = tmp_path / "pipeline_events"
    event_dir.mkdir()
    rows = []
    for idx in range(5):
        for timeout, ev in ((60, -1.0), (90, 1.0)):
            rows.append(
                {
                    "stage": "entry_cancel_wait_counterfactual_completed",
                    "fields": {
                        "runtime_family": "entry_cancel_wait_runtime",
                        "wait_profile": "standard",
                        "timeout_sec": timeout,
                        "counterfactual_ev_pct": ev,
                    },
                }
            )
    (event_dir / "pipeline_events_2026-06-12.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
    )
    payload = mod.build_report("2026-06-12")
    assert payload["recommended_thresholds"]["standard"] == 90
    assert payload["profiles"]["standard"]["calibration_state"] == "adjust"
    assert payload["evidence_summary"]["state"] == "candidate_ready"
    assert payload["evidence_summary"]["threshold_change_supported"] is True
    assert payload["evidence_summary"]["completed_candidate_count"] == 10


def test_invalid_rows_hold_previous_thresholds(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path / "reports")
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    event_dir = tmp_path / "pipeline_events"
    event_dir.mkdir()
    rows = []
    for _idx in range(5):
        rows.append(
            {
                "stage": "entry_cancel_wait_counterfactual_completed",
                "fields": {
                    "runtime_family": "entry_cancel_wait_runtime",
                    "wait_profile": "standard",
                    "timeout_sec": 90,
                    "counterfactual_ev_pct": 1.0,
                },
            }
        )
    rows.append(
        {
            "stage": "entry_cancel_wait_counterfactual_completed",
            "fields": {
                "runtime_family": "entry_cancel_wait_runtime",
                "wait_profile": "unknown",
                "timeout_sec": 90,
                "counterfactual_ev_pct": 1.0,
            },
        }
    )
    (event_dir / "pipeline_events_2026-06-12.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
    )

    payload = mod.build_report("2026-06-12")

    assert payload["source_quality_status"] == "warning"
    assert payload["recommended_thresholds"] == mod.DEFAULT_THRESHOLDS
    assert payload["profiles"]["standard"]["calibration_state"] == (
        "hold_source_quality"
    )
    assert payload["evidence_summary"] == {
        "state": "invalid_rows_warning",
        "registered_count": 0,
        "completed_candidate_count": 5,
        "threshold_change_supported": False,
        "carry_forward_applied": True,
    }


def test_touch_mark_proxy_is_retained_but_cannot_tune_current_policy(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path / "reports")
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    event_dir = tmp_path / "pipeline_events"
    event_dir.mkdir()
    row = {"stage": "entry_cancel_wait_counterfactual_completed", "fields": {
        "runtime_family": "entry_cancel_wait_runtime", "wait_profile": "standard",
        "timeout_sec": 90, "counterfactual_ev_pct": 10.0}}
    (event_dir / "pipeline_events_2026-09-17.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for _ in range(5)), encoding="utf-8")
    payload = mod.build_report("2026-09-17")
    assert payload["diagnostic_proxy_row_count"] is None
    assert payload["economic_tuning_input_allowed"] is False
    assert payload["evidence_summary"]["state"] == "source_gap"
    assert payload["recommended_thresholds"] == mod.DEFAULT_THRESHOLDS
    assert payload["enabled"] is True
    assert payload["automatic_off_allowed"] is False


def _reconciliation_fixture(tmp_path, monkeypatch, *, unknown_history=False):
    """Real producer/policy bytes, bounded fake sources, no runtime writes."""
    from src.engine.scalping import entry_split_order_plan as entry
    data = tmp_path/'data'
    directory = data/'report/entry_cancel_wait_tuning'
    directory.mkdir(parents=True, exist_ok=True)
    registry = data/'runtime/order_owner_registry.jsonl'
    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_text('')
    registry.with_suffix('.jsonl.lock').touch()
    from src.engine.pipeline_event_summary import (CANCEL_WAIT_SUMMARY_STAGES,
        IDENTITY_CONTRACT, IDENTITY_MODULUS, execution_projection_identity)
    predecessor = _unclassified_history() if unknown_history else {}
    for event in predecessor.get('source_events', []):
        event['execution_source_event_sha256'] = execution_projection_identity(event)
    if predecessor:
        predecessor['sha256'] = mod._digest({k:v for k,v in predecessor.items() if k != 'sha256'})
    manifests = {}
    contract = {'status':'verified', 'tail_hash':'0'*64}
    for day in ('2026-09-29','2026-09-30','2026-10-01','2026-10-02'):
        path = data/'pipeline_event_summaries'/f'pipeline_event_producer_summary_manifest_{day}.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        events = [e for e in predecessor.get('source_events', []) if e['emitted_date'] == day]
        census = path.with_name(f'pipeline_event_producer_summary_{day}.jsonl')
        census.write_text(''.join(json.dumps(dict(target_date=day, stage=stage,
            identity_contract=IDENTITY_CONTRACT, execution_projection_identity_contract='lossless_execution_projection_v1',
            event_count=sum(e['stage'] == stage for e in events),
            execution_projection_hash_sum=format(sum(int(e['execution_source_event_sha256'],16)
                for e in events if e['stage'] == stage) % IDENTITY_MODULUS, '064x')))+'\n'
            for stage in CANCEL_WAIT_SUMMARY_STAGES | {'order_leg_sent'}))
        manifests[day] = dict(target_date=day, generation=1, identity_contract=IDENTITY_CONTRACT,
            summary_stages=sorted(CANCEL_WAIT_SUMMARY_STAGES | {'order_leg_sent'}),
            summary_storage_size_bytes=census.stat().st_size)
        path.write_text(json.dumps(manifests[day]))
    def projection(day, **_kwargs):
        events = [e for e in predecessor.get('source_events', []) if e['emitted_date'] == day]
        return events, dict(status='ready', retained_event_count=len(events),
            producer_census={'manifest_sha256':entry._canonical_sha256(manifests[day])})
    if predecessor:
        predecessor['_verified_source_bindings'] = {'2026-09-30':mod._source_binding(projection('2026-09-30')[1], contract)}
    monkeypatch.setattr(entry, '_bounded_execution_projection', projection)
    monkeypatch.setattr(mod, 'DATA_DIR', data)
    monkeypatch.setattr(mod, 'REPORT_DIR', directory)
    monkeypatch.setattr(mod, '_previous_state', lambda _day: predecessor)
    monkeypatch.setattr(mod, '_incumbent', lambda _day: (dict(mod.DEFAULT_THRESHOLDS), {'previous_scope_overrides':[]}))
    monkeypatch.setattr(mod, '_current_sources', lambda day: ([], [], [], dict(
        projection=projection(day)[1], registry=contract, actual_outcomes={'status':'missing'},
        source_quality={'tuning_input_allowed':True})))
    report = mod.build_report('2026-10-02')
    monkeypatch.setattr(mod, 'build_report', lambda _day, **_kwargs: report)
    policy, policy_path = mod.prepare_policy(report, '2026-10-06', publication_date='2026-10-02')
    report_path = directory/'entry_cancel_wait_tuning_2026-10-02.json'
    report_path.write_text(json.dumps(report))
    return report, policy, report_path, policy_path


def _reseal_reconciliation(report):
    state = report['economic_state']
    state['sha256'] = mod._digest({k:v for k,v in state.items() if k != 'sha256'})
    report['proof_sha256'] = mod._digest({k:v for k,v in report.items() if k not in ('generated_at','proof_sha256')})


@pytest.mark.parametrize('unknown', [False, True])
def test_shared_view_accepts_verified_empty_and_documented_history_gap(tmp_path, monkeypatch, unknown):
    report, policy, _, _ = _reconciliation_fixture(tmp_path, monkeypatch, unknown_history=unknown)
    view = mod.validated_reconciliation_view(report, policy, data_root=tmp_path/'data')
    assert view['findings'] == []
    assert view['status'] == 'incumbent_carry'
    assert view['daily_zero_is_verified'] is True
    assert view['unresolved_prior_custody_count'] is (None if unknown else 0)
    assert view['historical_state'] == ('source_gap' if unknown else 'verified_empty')
    assert report['economic_evaluation']['delta_ev_pct'] is None


def test_shared_view_validates_gzip_census_and_invalidates_cache_on_alias_conflict(tmp_path, monkeypatch):
    import gzip
    report, policy, _, _ = _reconciliation_fixture(tmp_path, monkeypatch)
    data=tmp_path/'data'
    paths=list((data/'pipeline_event_summaries').glob('*.jsonl'))
    for path in paths:
        path.with_name(path.name+'.gz').write_bytes(gzip.compress(path.read_bytes()))
        path.unlink()
    first=mod.validated_reconciliation_view(report, policy, data_root=data)
    assert first['findings']==[] and first['status']=='incumbent_carry'
    # A conflicting plain alias must not reuse the previous gzip-only PASS.
    path=paths[0]
    path.write_text('{"stage":"conflicting"}\n')
    revised=mod.validated_reconciliation_view(report, policy, data_root=data)
    assert revised['status']=='source_invalid'


def test_native_census_projection_keeps_semantics_without_redecoding_full_sources(tmp_path, monkeypatch):
    from src.engine.scalping import entry_split_order_plan as entry
    from src.engine.pipeline_event_summary import CANCEL_WAIT_SUMMARY_STAGES
    report,policy,_,_=_reconciliation_fixture(tmp_path,monkeypatch)
    data=tmp_path/'data'
    for day,row in report['economic_state']['submission_reconciliation']['by_date'].items():
        if not row['coverage_verified']:continue
        census=entry._execution_projection_census(day,[],stages=CANCEL_WAIT_SUMMARY_STAGES|{'order_leg_sent'},data_root=data)
        assert census['status']=='ready'
        row['source_binding']['native_census_projection']=census['native_census_projection']
    _reseal_reconciliation(report)
    policy['source_report_proof_sha256']=report['proof_sha256']
    # This test intentionally omits policy: the receipt is source observation,
    # never a way to approve a policy whose original report hash changed.
    monkeypatch.setattr(entry,'_execution_projection_census',lambda *a,**k:pytest.fail('duplicate full census read'))
    view=mod.validated_reconciliation_view(report,data_root=data)
    assert view['status']=='incumbent_carry' and view['findings']==[]
    path=data/'pipeline_event_summaries/pipeline_event_producer_summary_2026-10-02.jsonl'
    path.write_text(path.read_text()+'{}\n')
    assert mod.validated_reconciliation_view(report,data_root=data)['status']=='source_invalid'


@pytest.mark.parametrize('mutation,reason', [
    ('false_zero','cancel_wait_false_historical_zero'),
    ('erase_unknown','cancel_wait_false_historical_zero'),
    ('bool_count','cancel_wait_false_daily_zero'),
    ('missing_date','cancel_wait_history_source_binding_missing'),
    ('fake_ev','cancel_wait_empty_economics_fabricated'),
])
def test_resealed_report_cannot_hide_semantic_defects(tmp_path, monkeypatch, mutation, reason):
    report, _, _, _ = _reconciliation_fixture(tmp_path, monkeypatch, unknown_history=True)
    if mutation == 'false_zero':
        report['historical_reconciliation']['zero_is_verified'] = True
        report['historical_reconciliation']['unresolved_prior_custody_count'] = 0
    elif mutation == 'erase_unknown':
        row = report['economic_state']['submission_reconciliation']['by_date']['2026-09-30']
        row['unclassified_identities'] = []
        row['unclassified_submission_count'] = 0
    elif mutation == 'bool_count':
        report['submission_census']['submitted_parent_count'] = False
    elif mutation == 'missing_date':
        del report['economic_state']['submission_reconciliation']['by_date']['2026-09-30']
    else:
        report['economic_evaluation']['delta_ev_pct'] = 0
    _reseal_reconciliation(report)
    assert reason in mod.validated_reconciliation_view(report)['findings']
    assert mod.verify_report(report, recompute=False)[0] is False


def test_shared_view_reports_stale_manifest_without_replay(tmp_path, monkeypatch):
    report, policy, _, _ = _reconciliation_fixture(tmp_path, monkeypatch)
    manifest = tmp_path/'data/pipeline_event_summaries/pipeline_event_producer_summary_manifest_2026-10-02.json'
    manifest.write_text(json.dumps({'target_date':'2026-10-02','generation':2}))
    monkeypatch.setattr(mod, 'build_report', lambda *_args: pytest.fail('monitor replay'))
    assert 'cancel_wait_stale_source_generation' in mod.validated_reconciliation_view(
        report, policy, data_root=tmp_path/'data')['findings']


def test_source_only_prior_child_is_pending_even_without_registry():
    details = {}
    parent = dict(source_date='2026-09-30', parent_id='p', children={
        'source-only':dict(terminal_reconciled=False, fills=[])})
    assert mod._unresolved_prior_custody('2026-10-02', [], [parent], [], details=details) == ['source-only']
    assert details == dict(known_open_order_count=0, terminal_unverified_count=1, filled_cost_unresolved_count=0)


def test_predecessor_isolates_failed_date_without_discarding_verified_date(tmp_path, monkeypatch):
    from src.engine.scalping import entry_split_order_plan as entry
    from src.engine.scalping.entry_cancel_wait_runtime import ECONOMIC_SCHEMA
    original_previous = mod._previous_state
    monkeypatch.setattr(mod, 'REPORT_DIR', tmp_path)
    state = _unclassified_history()
    state['source_counts']['2026-09-29'] = 0
    state['sha256'] = mod._digest({k:v for k,v in state.items() if k != 'sha256'})
    path = tmp_path/'entry_cancel_wait_tuning_2026-09-30.json'
    path.write_text(json.dumps(dict(date='2026-09-30', economic_schema=ECONOMIC_SCHEMA, economic_state=state)))
    calls = []
    def projected(day, **_kwargs):
        calls.append(day)
        return [], dict(status='ready',retained_event_count=0)
    monkeypatch.setattr(entry, '_bounded_execution_projection', projected)
    monkeypatch.setattr(entry, '_execution_registry_snapshot', lambda: ([],{'status':'verified','tail_hash':'0'*64}))
    rebuilt = original_previous('2026-10-02')
    assert calls == ['2026-09-29','2026-09-30']
    assert rebuilt['source_counts'] == {'2026-09-29':0}
    assert rebuilt['_verified_source_bindings']['2026-09-29']['status'] == 'ready'
    assert len(rebuilt['_quarantined_sources']['2026-09-30']['excluded_source_event_sha256s']) == 2
    assert rebuilt['source_events'] == []


def _append_registry_event(path, *, owner_type='widget', day='2026-10-02'):
    import hashlib
    from src.trading.order.owner_custody_registry import OrderOwnerRegistry, REGISTRY_SCHEMA
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    previous = rows[-1]['event_hash'] if rows else '0'*64
    event = dict(schema=REGISTRY_SCHEMA, previous_hash=previous, intent_id='append-1',
        owner_type=owner_type, side='BUY', action='NEW', order_date=day, state='ORDER_BOUND',
        broker_order_no='OTHER1')
    event['event_hash'] = hashlib.sha256(previous.encode()+OrderOwnerRegistry._canonical(event)).hexdigest()
    with path.open('a') as handle:
        handle.write(json.dumps(event)+'\n')
    return event['event_hash']


@pytest.mark.parametrize('owner,expected', [('widget',False), ('main_scalping',True)])
def test_registry_append_uses_ancestry_and_relevant_owner(tmp_path, monkeypatch, owner, expected):
    report, policy, _, _ = _reconciliation_fixture(tmp_path, monkeypatch)
    _append_registry_event(tmp_path/'data/runtime/order_owner_registry.jsonl', owner_type=owner)
    view = mod.validated_reconciliation_view(report, policy, data_root=tmp_path/'data')
    assert ('cancel_wait_stale_registry_generation' in view['findings']) is expected
    if not expected:
        assert view['findings'] == []


def test_incumbent_revalidation_accepts_only_unrelated_registry_append(tmp_path, monkeypatch):
    report, _, _, _ = _reconciliation_fixture(tmp_path, monkeypatch)
    tail = _append_registry_event(tmp_path/'data/runtime/order_owner_registry.jsonl')
    current = json.loads(json.dumps(report))
    current['source_contract']['registry']['tail_hash'] = tail
    for row in current['economic_state']['submission_reconciliation']['by_date'].values():
        row['source_binding']['registry_tail_hash'] = tail
    current['input_fingerprint'] = 'b'*64
    current['preflight_fingerprint'] = 'c'*64
    _reseal_reconciliation(current)
    monkeypatch.setattr(mod, 'build_report', lambda _day, **_kwargs: current)
    assert mod.verify_report(report) == (True,None)
    current['previous_thresholds']['standard'] += 1
    _reseal_reconciliation(current)
    assert mod.verify_report(report)[0] is False


def test_native_generation_revalidation_freezes_only_the_artifact_clock(tmp_path, monkeypatch):
    from datetime import datetime, timedelta
    native_build = mod.build_report
    report, _, _, _ = _reconciliation_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(mod, 'build_report', native_build)
    class LaterClock(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime.now(tz) + timedelta(hours=1)
    monkeypatch.setattr(mod, 'datetime', LaterClock)
    assert mod.verify_report(report) == (True, None)
    frozen = mod.build_report(report['date'], artifact_as_of=report['generated_at'])
    assert frozen['generated_at'] == report['generated_at']
    assert frozen['policy_generation']['as_of'] == report['policy_generation']['as_of']
    assert frozen['proof_sha256'] == report['proof_sha256']
    incumbent = mod._incumbent
    def changed_incumbent(day):
        thresholds, source = incumbent(day)
        return {**thresholds, 'standard': thresholds['standard'] + 1}, source
    monkeypatch.setattr(mod, '_incumbent', changed_incumbent)
    assert mod.verify_report(report) == (False, 'cancel_wait_source_or_metric_revalidation_failed')


def test_external_sealed_census_rejects_coherently_resealed_empty_history(tmp_path, monkeypatch):
    report, _, _, _ = _reconciliation_fixture(tmp_path, monkeypatch, unknown_history=True)
    state = report['economic_state']
    state['source_events'] = []
    state['source_counts']['2026-09-30'] = 0
    row = state['submission_reconciliation']['by_date']['2026-09-30']
    row.update(unclassified_identities=[],unclassified_submission_count=0,source_event_sha256s=[],blocker=None)
    row['source_binding']['retained_event_count'] = 0
    history = report['historical_reconciliation']
    history.update(unclassified_submission_count=0, coverage_verified=True, zero_is_verified=True,
        unresolved_prior_custody_count=0, status='verified_empty',blocker=None)
    report['submission_census']['unresolved_prior_custody_count'] = 0
    report['economic_evaluation']['status'] = 'no_submitted_orders'
    report['evidence_summary'].update(state='no_submitted_orders',historical_state='verified_empty')
    _reseal_reconciliation(report)
    assert 'cancel_wait_history_source_binding_missing' in mod.validated_reconciliation_view(
        report, data_root=tmp_path/'data')['findings']


def test_failed_parent_parse_counts_unique_actual_submissions():
    day = '2026-09-30'
    sent = _unclassified_history(day)['source_events']
    duplicate_submission = {**sent[0], 'stage':'entry_cancel_wait_submission',
        'fields':{**sent[0]['fields'], 'entry_cancel_wait_submission_context':'invalid'}}
    failed = dict(stage='entry_cancel_wait_submission',emitted_date=day,record_id=3,
        fields={'actual_order_submitted':False,'entry_cancel_wait_submission_context':'invalid'})
    assert len(mod._unclassified_source_identities(day,sent+[duplicate_submission,failed])) == 2


def test_semantic_cache_avoids_repeated_metadata_reads_and_invalidates_append(tmp_path,monkeypatch):
    report, policy, _, _ = _reconciliation_fixture(tmp_path,monkeypatch)
    mod._RECONCILIATION_VIEW_CACHE.clear()
    calls = []
    original = mod._sealed_census_matches
    def census(*args, **kwargs):
        calls.append(args[1])
        return original(*args, **kwargs)
    monkeypatch.setattr(mod,'_sealed_census_matches',census)
    first = mod.validated_reconciliation_view(report,policy,data_root=tmp_path/'data')
    count = len(calls)
    assert count > 0
    assert mod.validated_reconciliation_view(report,policy,data_root=tmp_path/'data') == first
    assert len(calls) == count
    _append_registry_event(tmp_path/'data/runtime/order_owner_registry.jsonl')
    assert mod.validated_reconciliation_view(report,policy,data_root=tmp_path/'data')['findings'] == []
    assert len(calls) > count


def test_semantic_aggregate_budget_holds_before_census_read(tmp_path,monkeypatch):
    report, policy, _, _ = _reconciliation_fixture(tmp_path,monkeypatch)
    monkeypatch.setattr(mod,'MAX_RECONCILIATION_METADATA_BYTES',1)
    monkeypatch.setattr(mod,'_sealed_census_matches',lambda *_a: pytest.fail('budget overread'))
    result = mod.validated_reconciliation_view(report,policy,data_root=tmp_path/'data')
    assert result['status'] == 'unobservable'
    assert result['reason'] == 'bounded_reconciliation_metadata_required'
    assert result['findings'] == []


def test_metadata_budget_cannot_suppress_known_false_historical_zero(tmp_path,monkeypatch):
    report, _, _, _ = _reconciliation_fixture(tmp_path,monkeypatch,unknown_history=True)
    report['historical_reconciliation']['zero_is_verified'] = True
    _reseal_reconciliation(report)
    monkeypatch.setattr(mod,'MAX_RECONCILIATION_METADATA_BYTES',1)
    view = mod.validated_reconciliation_view(report,data_root=tmp_path/'data')
    assert view['status'] == 'source_invalid'
    assert 'cancel_wait_false_historical_zero' in view['findings']


def test_candidate_projection_requires_existing_model_and_holdout_evidence(tmp_path,monkeypatch):
    report, _, _, _ = _reconciliation_fixture(tmp_path,monkeypatch)
    report['economic_tuning_input_allowed'] = True
    report['economic_evaluation']['status'] = 'economic_improvement_validated'
    report['evidence_summary'].update(state='economic_improvement_validated',threshold_change_supported=True,carry_forward_applied=False)
    _reseal_reconciliation(report)
    assert 'cancel_wait_selected_without_economic_evidence' in mod.validated_reconciliation_view(report)['findings']
    # A complete contract remains admissible; the repair adds no new floor.
    metrics = dict(paired_count=1,eligible=True,delta_ev_pct=.1,mean_day_delta_krw=100,
        delta_ev_lower_bound_pct=.05,day_delta_lower_bound_krw=50)
    selected = dict(scope=['standard'],holdout_date='2026-10-02',
        training={**metrics,'verification_dates':['2026-10-01']},
        holdout={**metrics,'verification_dates':['2026-10-02']})
    from src.engine.scalping.entry_cancel_wait_runtime import SELECTION_RULE
    report['economic_evaluation'].update(metrics,selected=selected,selection_rule_version=SELECTION_RULE)
    report['model_validation'].update(validated=True,actual_sample_count=20,scope=['standard'],available_after_date='2026-09-30')
    report['submission_census']['economic_parent_count'] = 1
    assert mod._candidate_evidence_valid(report) is True
    selected['training']['verification_dates'] = ['2026-10-02']
    assert mod._candidate_evidence_valid(report) is False


@pytest.mark.parametrize('invalid_path', ['symlink','oversize'])
def test_latest_untrusted_predecessor_is_not_silently_skipped(tmp_path,monkeypatch,invalid_path):
    monkeypatch.setattr(mod,'REPORT_DIR',tmp_path)
    path = tmp_path/'entry_cancel_wait_tuning_2026-09-30.json'
    if invalid_path == 'symlink':
        target = tmp_path/'outside.json'; target.write_text('{}')
        path.symlink_to(target)
    else:
        with path.open('wb') as handle:
            handle.truncate(mod.MAX_RECONCILIATION_METADATA_BYTES + 1)
    with pytest.raises(ValueError,match='predecessor_path_or_size_invalid'):
        mod._previous_state('2026-10-02')


@pytest.mark.parametrize('queued', [False, True])
@pytest.mark.parametrize('owner,quantity,expected',[(None,0,'verified_empty'),('episode',5,'verified_empty'),('main_scalping',5,'known_open')])
def test_native_custody_checkpoint_qualifies_main_and_retired_independently(tmp_path,monkeypatch,owner,quantity,expected,queued):
    import hashlib
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from src.engine.scalping import main_custody_checkpoint as checkpoint
    from src.trading.order import owner_custody_registry as custody
    data=tmp_path/'data';path=data/'runtime/order_owner_registry.jsonl';path.parent.mkdir(parents=True)
    rows=[]
    if owner:
        row=dict(schema=custody.REGISTRY_SCHEMA,event='FILL_RECORDED',intent_id='buy1',account_key='fixture',owner_type=owner,
            symbol='123456',position_id='position1',side='BUY',action='NEW',state='ORDER_TERMINAL',filled_qty=quantity,previous_hash='0'*64)
        row['event_hash']=hashlib.sha256(('0'*64).encode()+custody.OrderOwnerRegistry._canonical(row)).hexdigest();rows=[row]
    path.write_text(''.join(json.dumps(r)+'\n' for r in rows));path.with_suffix('.jsonl.lock').touch()
    registry=custody.OrderOwnerRegistry(path)
    monkeypatch.setattr(checkpoint,'DATA_DIR',data);monkeypatch.setattr(custody,'broker_account_key',lambda:'fixture')
    monkeypatch.setattr(custody,'default_order_owner_registry',lambda:registry)
    snapshot=dict(captured_at=datetime(2026,10,2,15,31,tzinfo=ZoneInfo('Asia/Seoul')).timestamp(),successful_exchanges={'KRX','NXT'},
        inventory_rows_valid=True,open_order_rows_valid=True,open_orders_request_succeeded=True,unverified_open_order_codes=set(),
        inventory_by_code={'123456':dict(qty=quantity)} if owner else {},open_qty_by_code={})
    if queued:
        from concurrent.futures import ThreadPoolExecutor
        from src.utils.pipeline_event_logger import BoundedObservationQueue
        with ThreadPoolExecutor(max_workers=1) as executor:
            queue = BoundedObservationQueue(executor)
            monkeypatch.setattr(checkpoint, '_SOURCE_SINK', queue.submit)
            assert checkpoint.enqueue(snapshot, query_generation=checkpoint.journal_generation()) == 'queued'
            assert queue.close(timeout=2)
        assert queue.snapshot()['completed'] == 1
        assert queue.snapshot()['append_confirmed'] == 1
        assert queue.snapshot()['append_unobservable'] == 0
        assert queue.snapshot()['unavailable'] == queue.snapshot()['failed'] == 0
        native = json.loads((data/'runtime/main_custody_checkpoints/2026-10-02.json').read_text())
    else:
        native=checkpoint.publish(snapshot,query_generation=checkpoint.journal_generation())
    ledger={'2026-09-30':dict(coverage_verified=False,unclassified_identities=['historical-missing']),
        '2026-10-02':dict(coverage_verified=True,unclassified_identities=[])}
    result=checkpoint.view(native,registry.verified_events_snapshot(),ledger,day='2026-10-02',current_generation=checkpoint.journal_generation())
    assert result['status']==expected
    assert native['historical_terminal_or_profit_inferred'] is False
    assert (data/'runtime/main_custody_checkpoints'/f"2026-10-02.{native['sha256']}.json").exists()
    bad=json.loads(json.dumps(native));bad['registry_tail_hash']='f'*64;bad['sha256']=checkpoint.digest({k:v for k,v in bad.items() if k!='sha256'})
    assert checkpoint.view(bad,rows,ledger,day='2026-10-02',current_generation=checkpoint.journal_generation())['status']=='unknown'


def test_custody_capture_is_bounded_queued_and_never_writes_synchronously(tmp_path,monkeypatch):
    from src.engine.scalping import main_custody_checkpoint as checkpoint
    saved=[]
    monkeypatch.setattr(checkpoint,'_SOURCE_SINK',lambda *a,**kw:saved.append((a,kw)) or {'status':'queued'})
    snapshot={'inventory_by_code':{'123456':{'qty':1}}, 'successful_exchanges': {'NXT','KRX'},
              'unverified_open_order_codes': {'123456'}}
    def forbidden(*a,**kw):raise AssertionError('synchronous source write')
    monkeypatch.setattr(checkpoint,'publish',forbidden)
    assert checkpoint.enqueue(snapshot,query_generation=[1,2,3,4])=='queued'
    snapshot['inventory_by_code']['123456']['qty']=10
    snapshot['successful_exchanges'].clear()
    snapshot['unverified_open_order_codes'].clear()
    assert saved[0][0][1]['inventory_by_code']['123456']['qty']==1
    assert saved[0][0][1]['successful_exchanges']==['KRX','NXT']
    assert saved[0][0][1]['unverified_open_order_codes']==['123456']
    json.dumps(saved[0][0][1], allow_nan=False)
    monkeypatch.setattr(checkpoint,'_SOURCE_SINK',lambda *a,**kw:{'status':'rejected'})
    assert checkpoint.enqueue(snapshot,query_generation=[1,2,3,4])=='source_gap'


@pytest.mark.parametrize('fault', ['none','late_terminal','wrong_identity','source_gap','open_order'])
def test_current_checkpoint_does_not_require_pre_checkpoint_research_dispatch(tmp_path, monkeypatch, fault):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from src.engine.scalping import main_custody_checkpoint as checkpoint
    from src.trading.order import owner_custody_registry as custody
    data=tmp_path/'data';path=data/'runtime/order_owner_registry.jsonl';path.parent.mkdir(parents=True)
    day='2026-10-16';rows=[];previous='0'*64
    common=dict(schema=custody.REGISTRY_SCHEMA,intent_id='residual-1',account_key='fixture',
        owner_type='main_scalping',owner_id='main_scalping:42',symbol='123456',position_id='p1',
        side='BUY',action='NEW',order_date=day,quantity=2,filled_qty=0,broker_order_no='B1')
    for event,clock in [('ORDER_BOUND','10:00:00'),('ORDER_TERMINAL','16:00:00' if fault=='late_terminal' else '10:01:00')]:
        row={**common,'event':event,'state':event,'observed_at_kst':day+'T'+clock+'+09:00','previous_hash':previous}
        row['event_hash']=__import__('hashlib').sha256(previous.encode()+custody.OrderOwnerRegistry._canonical(row)).hexdigest()
        previous=row['event_hash'];rows.append(row)
    path.write_text(''.join(json.dumps(r)+'\n' for r in rows));path.with_suffix('.jsonl.lock').touch()
    registry=custody.OrderOwnerRegistry(path)
    monkeypatch.setattr(checkpoint,'DATA_DIR',data);monkeypatch.setattr(custody,'broker_account_key',lambda:'fixture')
    monkeypatch.setattr(custody,'default_order_owner_registry',lambda:registry)
    snapshot=dict(captured_at=datetime(2026,10,16,15,31,tzinfo=ZoneInfo('Asia/Seoul')).timestamp(),
        successful_exchanges={'KRX','NXT'},inventory_rows_valid=True,open_order_rows_valid=True,
        open_orders_request_succeeded=True,unverified_open_order_codes=set(),inventory_by_code={},
        open_qty_by_code={'123456':{'BUY':2}} if fault=='open_order' else {})
    native=checkpoint.publish(snapshot,query_generation=checkpoint.journal_generation())
    unknown=checkpoint.digest(['order',day,'42','fixture','different' if fault=='wrong_identity' else 'B1'])
    ledger={day:dict(coverage_verified=fault!='source_gap',unclassified_identities=[unknown])}
    result=checkpoint.view(native,registry.verified_events_snapshot(),ledger,day=day,
                           current_generation=checkpoint.journal_generation())
    assert result['status']==('verified_empty' if fault=='none' else 'unknown')
    if fault=='none':
        assert result['checkpoint_superseded_historical_dispatch_count']==1
        assert result['historical_terminal_or_profit_inferred'] is False
        assert ledger[day]['unclassified_identities']==[unknown]


def test_complete_future_population_can_select_while_history_gap_is_preserved():
    scope=['KRX','KRX_REGULAR','KRX','standard']
    actual=[]
    for day in ('2026-09-30','2026-10-01'):
        for i in range(10):
            actual.append(dict(parent_id=f'actual:{day}:{i}',source_date=day,completion_date=day,
                scope=scope,fill_class='full' if i%2 else 'no_fill',complete=True,model_identity='fixture-model',
                net_error_pct=0.,cancel_ack_delay_sec=1.,late_fill_window_sec=1.,capital_error_minutes=0.,reserve_error_minutes=0.))
    model=mod._fit_model(actual,'fixture-model');assert model['validated']
    rows=[]
    for day in ('2026-10-02','2026-10-05'):
        arms={str(t):dict(status='completed_source_only',net_pnl_krw=100. if t==90 else 0.,stress_net_pnl_krw=90. if t==90 else 0.,
            capital_krw_minutes=1000.,reserve_krw_minutes=1000.,modeled_filled_qty=1 if t==90 else 0,
            modeled_exit_at=day+'T10:02:00+09:00',behavior_sha256=str(t)) for t in (30,60,90)}
        rows.append(dict(parent_id='cf:'+day,source_date=day,scope=scope,fill_class='no_fill',requested_qty=1,
            notional_krw=1000.,budget_krw=10000.,incumbent_timeout_sec=60,submitted_at=day+'T10:00:00+09:00',arms=arms))
    ledger={'2026-09-29':dict(coverage_verified=False,unclassified_identities=['original-missing']),
        **{r['source_date']:dict(coverage_verified=True,unclassified_identities=[]) for r in rows}}
    result=mod._economic_research(rows+[dict(parent_id='bad',source_date='2026-09-29')],model,
        {'2026-09-29':1,'2026-10-02':1,'2026-10-05':1},ledger)
    assert result['status']=='economic_improvement_validated'
    assert result['selected']['timeout_sec']==90 and result['delta_ev_pct']>0
    assert ledger['2026-09-29']['coverage_verified'] is False
    rows[-1]['arms']['90']['net_pnl_krw']=-100.
    assert mod._economic_research(rows,model,{'2026-10-02':1,'2026-10-05':1},ledger)['status']=='holdout_rejected'


def _lost_original_fixture(tmp_path, monkeypatch, *, predecessor_day='2026-10-15'):
    """A sealed dated source plus a later explicitly lossy quarantine."""
    from collections import Counter
    from src.engine.scalping import entry_split_order_plan as entry
    from src.engine.scalping.entry_cancel_wait_runtime import ECONOMIC_SCHEMA
    from src.engine.pipeline_event_summary import execution_projection_identity
    import hashlib
    directory=tmp_path/'data/report/entry_cancel_wait_tuning'
    directory.mkdir(parents=True,exist_ok=True)
    monkeypatch.setattr(mod,'REPORT_DIR',directory)
    events=_unclassified_history()['source_events']
    for event in events:
        event['pipeline']='ENTRY_PIPELINE'
        event['execution_source_event_sha256']=execution_projection_identity(event)
    counts=dict(Counter(e['stage'] for e in events))
    source_path=tmp_path/'data/threshold_cycle/date=2026-09-30/family=entry_price_execution_quality/part-native.jsonl'
    source_path.parent.mkdir(parents=True,exist_ok=True)
    source_path.write_text(''.join(json.dumps(e)+'\n' for e in events))
    projection=dict(status='ready',retained_event_count=len(events),full_population_coverage_verified=True,
        projection_contract=entry.EXECUTION_MODEL_CONTRACT,
        coverage_scope='declared_execution_stage_producer_census',
        producer_census=dict(status='ready',expected_stage_counts=counts,observed_stage_counts=counts,
            missing_identity_count=0,identity_conservation_holds=True,manifest_sha256='a'*64),
        sources=[dict(path=str(source_path),sha256=hashlib.sha256(source_path.read_bytes()).hexdigest())])
    state=_unclassified_history();state['source_events']=events
    # Recovery must not import any old economic/model row.
    state['model_rows']=[dict(parent_id='old_model',source_date='2026-09-30',complete=True)]
    state['actual_outcomes']=[dict(plan_sha256='old_cost',completion_date='2026-09-30',net_pnl_krw=99)]
    state['sha256']=mod._digest({k:v for k,v in state.items() if k!='sha256'})
    original=dict(date='2026-09-30',economic_schema=ECONOMIC_SCHEMA,runtime_family=mod.RUNTIME_FAMILY,
        policy_version=mod.POLICY_VERSION,runtime_effect=False,allowed_runtime_apply=True,
        economic_state=state,source_contract=dict(projection=projection,
            registry=dict(status='verified',tail_hash='0'*64),source_quality=dict(tuning_input_allowed=True)))
    original['proof_sha256']=mod._digest(original)
    original_path=directory/'entry_cancel_wait_tuning_2026-09-30.json'
    original_path.write_text(json.dumps(original))
    reason='cancel_wait_predecessor_original_projection_changed:2026-09-30'
    quarantine=dict(reason=reason,excluded_source_event_sha256s=[],
        artifact_path=str(directory/'entry_cancel_wait_tuning_2026-10-14.json'),artifact_sha256='b'*64)
    previous=dict(through_date=predecessor_day,parents=[],source_counts={'2026-09-29':0},source_events=[],
        actual_outcomes=[],model_rows=[],consumed_holdouts=[],submission_reconciliation=dict(
            by_date={'2026-09-29':{},'2026-09-30':dict(coverage_verified=False,
                source_binding=dict(status='source_gap',reason=reason),source_event_sha256s=[],excluded_source_event_sha256s=[],
                parent_identities=[],classified_parent_count=0,unclassified_identities=[],unclassified_submission_count=0)},
            quarantined_sources={'2026-09-30':quarantine}))
    previous_path=directory/f'entry_cancel_wait_tuning_{predecessor_day}.json'
    def write_previous():
        previous['sha256']=mod._digest({k:v for k,v in previous.items() if k!='sha256'})
        value=dict(date=predecessor_day,economic_schema=ECONOMIC_SCHEMA,economic_state=previous,
            runtime_family=mod.RUNTIME_FAMILY,policy_version=mod.POLICY_VERSION)
        value['proof_sha256']=mod._digest(value)
        previous_path.write_text(json.dumps(value))
    write_previous()
    native=json.loads(json.dumps(projection));calls=[]
    def project(day,**kwargs):
        calls.append(day)
        return (json.loads(json.dumps(events)),json.loads(json.dumps(native))) if day=='2026-09-30' else ([],dict(status='ready',retained_event_count=0))
    monkeypatch.setattr(entry,'_bounded_execution_projection',project)
    monkeypatch.setattr(entry,'_execution_registry_snapshot',lambda:([],dict(status='verified',tail_hash='0'*64)))
    return dict(events=events,original=original,original_path=original_path,previous=previous,
        previous_path=previous_path,write_previous=write_previous,native=native,calls=calls)


def test_lost_quarantine_recovers_native_events_without_economics_or_false_empty(tmp_path,monkeypatch):
    fixture=_lost_original_fixture(tmp_path,monkeypatch)
    original_bytes=fixture['original_path'].read_bytes();previous_bytes=fixture['previous_path'].read_bytes()
    reads=[];reader=mod._bounded_semantic_json
    monkeypatch.setattr(mod,'_bounded_semantic_json',lambda p:(reads.append(p) or reader(p)))
    rebuilt=mod._previous_state('2026-10-16')
    assert fixture['calls']==['2026-09-29','2026-09-30']
    assert reads.count(fixture['original_path'])==1 and reads.count(fixture['previous_path'])==1
    assert rebuilt['source_events']==fixture['events'] and rebuilt['parents']==[]
    assert '2026-09-30' not in rebuilt['source_counts']
    assert rebuilt['actual_outcomes']==[] and rebuilt['model_rows']==[]
    assert rebuilt['_quarantined_sources']=={}
    proof=rebuilt['_recovered_sources']['2026-09-30']
    assert proof['prior_quarantine']==fixture['previous']['submission_reconciliation']['quarantined_sources']['2026-09-30']
    assert proof['imported_economics'] is False and proof['terminal_or_cost_completion_inferred'] is False
    ledger,history=mod._reconcile_history('2026-10-16',rebuilt['source_events'],[],[],[],
        dict(projection=dict(status='ready',retained_event_count=0),registry=dict(status='verified'),source_quality=dict(tuning_input_allowed=True)),rebuilt,{})
    assert ledger['recovered_sources']['2026-09-30']==proof
    assert ledger['by_date']['2026-09-30']['unclassified_submission_count']==2
    assert history['status']=='source_gap' and history['zero_is_verified'] is False
    assert fixture['original_path'].read_bytes()==original_bytes and fixture['previous_path'].read_bytes()==previous_bytes


@pytest.mark.parametrize('fault',['not_quarantined','verified_empty','known_nonempty','missing_original','altered_report',
    'wrong_date','unknown_schema','retired_family','native_event','native_manifest','native_source','native_census','source_quality',
    'native_contract','missing_manifest','boolean_census','missing_registry_tail'])
def test_original_recovery_rejects_unproven_or_conflicting_ancestry(tmp_path,monkeypatch,fault):
    fixture=_lost_original_fixture(tmp_path,monkeypatch)
    previous=fixture['previous'];row=previous['submission_reconciliation']['by_date']['2026-09-30']
    original=fixture['original']
    if fault=='not_quarantined':previous['submission_reconciliation']['quarantined_sources']={}
    elif fault=='verified_empty':row.update(coverage_verified=True,source_binding=dict(status='ready',retained_event_count=0))
    elif fault=='known_nonempty':row['excluded_source_event_sha256s']=['f'*64]
    elif fault=='missing_original':fixture['original_path'].unlink()
    elif fault=='altered_report':original['runtime_effect']=True
    elif fault=='wrong_date':original['date']='2026-09-29'
    elif fault=='unknown_schema':original['economic_schema']='unknown'
    elif fault=='retired_family':original['runtime_family']='episode'
    elif fault=='native_event':fixture['events'][0]['record_id']='changed'
    elif fault=='native_manifest':fixture['native']['producer_census']['manifest_sha256']='f'*64
    elif fault=='native_source':fixture['native']['sources'][0]['sha256']='f'*64
    elif fault=='native_census':fixture['native']['producer_census']['identity_conservation_holds']=False
    elif fault=='native_contract':fixture['native']['projection_contract']='unknown'
    elif fault=='missing_manifest':fixture['native']['producer_census']['manifest_sha256']=None
    elif fault=='boolean_census':fixture['native']['producer_census']['observed_stage_counts']['order_leg_sent']=True
    elif fault=='missing_registry_tail':original['source_contract']['registry']['tail_hash']=None
    else:original['source_contract']['source_quality']['tuning_input_allowed']=False
    if fault not in {'missing_original','altered_report'}:
        original['proof_sha256']=mod._digest({k:v for k,v in original.items() if k!='proof_sha256'})
        fixture['original_path'].write_text(json.dumps(original))
    elif fault=='altered_report':fixture['original_path'].write_text(json.dumps(original))
    fixture['write_previous']()
    rebuilt=mod._previous_state('2026-10-16')
    assert rebuilt['source_events']==[] and rebuilt['_recovered_sources']=={}
    assert rebuilt['_verified_source_bindings']['2026-09-30']['status']=='source_gap'
    assert '2026-09-30' in rebuilt['_quarantined_sources']


def test_recovered_native_source_accepts_gzip_alias_and_retains_ancestry(tmp_path,monkeypatch):
    fixture=_lost_original_fixture(tmp_path,monkeypatch)
    fixture['native']['sources'][0]['path'] += '.gz'
    rebuilt=mod._previous_state('2026-10-16')
    proof=rebuilt['_recovered_sources']['2026-09-30']
    carry=json.loads(json.dumps(rebuilt))
    for key in list(carry):
        if key.startswith('_'):carry.pop(key)
    carry['through_date']='2026-10-16'
    carry['submission_reconciliation']['by_date']['2026-09-30']=dict(
        source_event_sha256s=proof['source_event_sha256s'],source_binding=rebuilt['_verified_source_bindings']['2026-09-30'])
    carry['submission_reconciliation']['recovered_sources']=rebuilt['_recovered_sources']
    carry['submission_reconciliation']['quarantined_sources']={}
    carry['sha256']=mod._digest({k:v for k,v in carry.items() if k!='sha256'})
    from src.engine.scalping.entry_cancel_wait_runtime import ECONOMIC_SCHEMA
    next_report=dict(date='2026-10-16',economic_schema=ECONOMIC_SCHEMA,economic_state=carry)
    next_report['proof_sha256']=mod._digest(next_report)
    (mod.REPORT_DIR/'entry_cancel_wait_tuning_2026-10-16.json').write_text(json.dumps(next_report))
    subsequent=mod._previous_state('2026-10-17')
    assert subsequent['_recovered_sources']==rebuilt['_recovered_sources']
    assert subsequent['source_events']==rebuilt['source_events'] and subsequent['model_rows']==[]
    fixture['original_path'].write_text(fixture['original_path'].read_text()+' ')
    rejected=mod._previous_state('2026-10-17')
    assert rejected['_recovered_sources']=={} and rejected['source_events']==[]


def _recovered_view_fixture(tmp_path,monkeypatch):
    fixture=_lost_original_fixture(tmp_path,monkeypatch,predecessor_day='2026-10-01')
    report,_,_,_=_reconciliation_fixture(tmp_path,monkeypatch,unknown_history=True)
    events=[e for e in report['economic_state']['source_events'] if e['emitted_date']=='2026-09-30']
    assert events==fixture['events']
    manifest=report['economic_state']['submission_reconciliation']['by_date']['2026-09-30']['source_binding']['producer_manifest_sha256']
    fixture['original']['source_contract']['projection']['producer_census']['manifest_sha256']=manifest
    fixture['native']['producer_census']['manifest_sha256']=manifest
    fixture['original']['proof_sha256']=mod._digest({k:v for k,v in fixture['original'].items() if k!='proof_sha256'})
    fixture['original_path'].write_text(json.dumps(fixture['original']))
    previous,previous_sha=mod._bounded_semantic_json(fixture['previous_path'])
    recovery=mod._recover_lost_original('2026-09-30',previous['economic_state'],events,
        fixture['native'],[],dict(status='verified',tail_hash='0'*64),fixture['previous_path'],previous_sha,previous)
    report['economic_state']['submission_reconciliation']['recovered_sources']={'2026-09-30':recovery}
    _reseal_reconciliation(report)
    mod._RECONCILIATION_VIEW_CACHE.clear()
    return fixture,report


@pytest.mark.parametrize('which',['original','predecessor'])
def test_recovery_view_binds_both_original_and_quarantined_predecessor_cache_generations(tmp_path,monkeypatch,which):
    fixture,report=_recovered_view_fixture(tmp_path,monkeypatch)
    data=tmp_path/'data'
    view=mod.validated_reconciliation_view(report,data_root=data)
    assert view['findings']==[] and view['status']=='incumbent_carry'
    assert view['recovered_source_dates']==['2026-09-30']
    assert view['historical_state']=='source_gap' and view['historical_zero_is_verified'] is False
    # Whitespace preserves semantic self-hashes, but is a new original artifact.
    path=fixture['original_path' if which=='original' else 'previous_path']
    path.write_text(path.read_text()+' ')
    changed=mod.validated_reconciliation_view(report,data_root=data)
    assert changed['status']=='source_invalid' and changed['findings']


@pytest.mark.parametrize('mutation',['false_quarantine','false_parent_hash','new_parent','source_event','import_economics','future_parent'])
def test_recovery_view_rejects_self_resealed_false_recovery_claims(tmp_path,monkeypatch,mutation):
    fixture,report=_recovered_view_fixture(tmp_path,monkeypatch)
    receipt=report['economic_state']['submission_reconciliation']['recovered_sources']['2026-09-30']
    if mutation=='false_quarantine':
        parent=json.loads(fixture['previous_path'].read_bytes())
        parent['economic_state']['submission_reconciliation']['by_date']['2026-09-30']['coverage_verified']=True
        _reseal_reconciliation(parent)
        fixture['previous_path'].write_text(json.dumps(parent))
        import hashlib
        receipt['predecessor_artifact_sha256']=hashlib.sha256(fixture['previous_path'].read_bytes()).hexdigest()
    elif mutation=='false_parent_hash':receipt['predecessor_artifact_sha256']='f'*64
    elif mutation=='new_parent':receipt['predecessor_artifact_path']=str(fixture['previous_path'].with_name('entry_cancel_wait_tuning_2026-09-29.json'))
    elif mutation=='source_event':receipt['source_event_sha256s']=['f'*64]
    elif mutation=='import_economics':receipt['imported_economics']=True
    else:receipt['predecessor_artifact_path']=str(fixture['previous_path'].with_name('entry_cancel_wait_tuning_2026-10-02.json'))
    receipt['sha256']=mod._digest({k:v for k,v in receipt.items() if k!='sha256'})
    _reseal_reconciliation(report)
    assert mod.validated_reconciliation_view(report,data_root=tmp_path/'data')['status']=='source_invalid'


def test_recovery_view_detects_late_ancestry_change_after_semantic_read(tmp_path,monkeypatch):
    fixture,report=_recovered_view_fixture(tmp_path,monkeypatch)
    reader=mod._bounded_semantic_json
    changed=False
    def read(path):
        nonlocal changed
        result=reader(path)
        if path==fixture['previous_path'] and not changed:
            changed=True
            path.write_text(path.read_text()+' ')
        return result
    view=mod.validated_reconciliation_view(report,data_root=tmp_path/'data',read_object=read)
    assert view['status']=='unobservable' and view['reason']=='semantic_generation_changed_during_read'


@pytest.mark.parametrize('kind',['fifo','symlink','oversize'])
def test_recovery_receipt_reader_rejects_nonregular_or_unbounded_sources(tmp_path,kind):
    import os
    path=tmp_path/'receipt.json'
    if kind=='fifo':os.mkfifo(path)
    elif kind=='symlink':
        target=tmp_path/'target.json';target.write_text('{}');path.symlink_to(target)
    else:
        with path.open('wb') as handle:handle.truncate(mod.MAX_RECONCILIATION_METADATA_BYTES+1)
    with pytest.raises(ValueError,match='artifact_path_or_size_invalid'):
        mod._bounded_semantic_json(path)


def test_recovery_cache_hit_rechecks_original_generation_before_return(tmp_path,monkeypatch):
    fixture,report=_recovered_view_fixture(tmp_path,monkeypatch)
    assert mod.validated_reconciliation_view(report,data_root=tmp_path/'data')['findings']==[]
    original=mod._reconciliation_metadata_generation;calls=0
    def generation(*args):
        nonlocal calls
        result=original(*args);calls+=1
        if calls==1:
            fixture['original_path'].write_text(fixture['original_path'].read_text()+' ')
        return result
    monkeypatch.setattr(mod,'_reconciliation_metadata_generation',generation)
    view=mod.validated_reconciliation_view(report,data_root=tmp_path/'data')
    assert view['status']=='unobservable' and view['reason']=='semantic_generation_changed_during_read'
