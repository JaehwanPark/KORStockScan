import json
import pytest
from pathlib import Path

from src.engine.automation import entry_cancel_wait_tuning as mod


def _unclassified_history(day='2026-09-30'):
    events = [dict(stage='order_leg_sent', emitted_date=day, record_id=i,
                   stock_code='123456', fields=dict(actual_order_submitted=True,
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
    monkeypatch.setattr(mod, 'build_report', lambda _day: report)
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
    monkeypatch.setattr(mod, 'build_report', lambda _day: current)
    assert mod.verify_report(report) == (True,None)
    current['previous_thresholds']['standard'] += 1
    _reseal_reconciliation(current)
    assert mod.verify_report(report)[0] is False


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
