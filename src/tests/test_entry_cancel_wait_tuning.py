import json
import pytest
from pathlib import Path

from src.engine.automation import entry_cancel_wait_tuning as mod


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
    state=dict(parents=[],source_counts={'2026-09-17':0},
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
    monkeypatch.setattr(mod,'_current_sources',lambda d:([],[],[],dict(projection={'status':'ready'},
        registry={'status':'verified'},actual_outcomes={'status':'missing'},source_quality={'tuning_input_allowed':True})))
    monkeypatch.setattr(summary,'verify_summary_handoff',lambda *a,**k:{'issues':[]})
    payload=mod.write_report('2026-09-18')
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
