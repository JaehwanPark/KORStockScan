"""Compact runtime codec, SDK boundary, immutable v1 and malformed responses."""
import copy
import json
from types import SimpleNamespace
import pytest
from src.engine.scalping import reversal_auxiliary_registry as G
from src.engine.scalping import reversal_auxiliary_wire as W
from src.engine.scalping import reversal_auxiliary_research_wire as OLD
from src.engine.scalping import reversal_auxiliary_transition as X
from src.engine.scalping import reversal_extended_union as U
from src.engine.scalping import continuous_reversal_postclose as P
from src.tests.test_reversal_extended_policy import FIXTURES


def definitions():
    old=G.definition(U.V1.ARMS[1],input_version=U.VERSION)
    return old,G.compact_definition(old,research_wire_contract=OLD.contract())


@pytest.mark.parametrize('fixture',list(FIXTURES.values()))
def test_wire_parity_and_strict_decode(fixture):
    old,new=definitions();snap=(fixture['event'],fixture['source'])
    logical,prompt,schema=G.production_request(snap,new)
    assert G.production_request(snap,old)==(logical,prompt,schema)
    assert G.binding(new)!=G.binding(old)
    assert new['schema']==G.SCHEMA_V2 and old['schema']==G.SCHEMA
    wire,wire_schema,aliases=W.encode(logical)
    assert (wire,wire_schema,aliases)==OLD.encode(logical)
    raw=dict(assessed={aliases[s['ref']]:True for s in logical['signals']},screen=dict(verdict='PASS',risk='NO_BLOCKING_RISK',fact=aliases['observed_machine_signal']),confidence=50)
    assert W.decode(raw,logical,new['base_arm'])==OLD.decode(raw,logical,old['base_arm'])
    assert G.request(snap,new)['candidate']['system_prompt']==prompt+OLD.SUFFIX
    assert G.request(snap,new)['candidate_input']==wire
    for invalid in [None,{},dict(refusal='refused'),dict(raw,confidence=True),dict(raw,assessed={}),dict(raw,screen=dict(verdict='CAUTION',risk='NO_BLOCKING_RISK',fact='f1'))]:
        with pytest.raises(ValueError):W.decode(invalid,logical,new['base_arm'])
    duplicate=copy.deepcopy(logical)
    duplicate['entry_setup_evidence_v1']['positive_facts']*=2
    with pytest.raises(ValueError,match='identity'):W.encode(duplicate)


def test_live_sdk_exact_contract(tmp_path,monkeypatch):
    from src.tests.test_ai_engine_openai_transport import _build_engine
    from src.engine import ai_engine_openai as E
    from src.utils import constants
    old,new=definitions();G.register(tmp_path,old);G.register(tmp_path,new)
    fixture=next(iter(FIXTURES.values()));snap=(fixture['event'],fixture['source'])
    inp,prompt,schema=G.production_request(snap,new)
    env=G.envelope(inp,new);aliases=env['citation_map']
    raw=dict(assessed={aliases[s['ref']]:True for s in inp['signals']},screen=dict(verdict='PASS',risk='NO_BLOCKING_RISK',fact=aliases['observed_machine_signal']),confidence=55)
    calls=[];captures=[];engine=_build_engine()
    def create(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(output_text=json.dumps(raw),id='test-response',status='completed')
    engine.client=SimpleNamespace(responses=SimpleNamespace(create=create))
    monkeypatch.setattr(constants,'DATA_DIR',tmp_path)
    monkeypatch.setattr(E,'capture_ai_request',lambda **kw: captures.append(kw) or {})
    result=engine._call_openai_safe(prompt,json.dumps(inp,ensure_ascii=True,sort_keys=True,separators=(',',':')),
        model_override=new['model'],schema_name=E.ENTRY_RISK_ADJUDICATION_SCHEMA,endpoint_name='analyze_target',transport_mode_override='http',
        metadata_extra={'entry_setup_live_policy_selected_prompt_version':G.binding(new)['prompt_version']},
        response_schema_override=schema,auxiliary_registry_sha256=new['registry_sha256'],replay_context=inp)
    assert result==raw and len(calls)==1
    sent=calls[0]
    assert sent['instructions']==env['final_prompt'] and sent['input']==json.dumps(env['wire_input'],ensure_ascii=True,sort_keys=True,separators=(',',':'))
    assert sent['model']=='gpt-5.4-nano' and sent['max_output_tokens']==1024 and sent['reasoning']=={'effort':'none'}
    assert sent['text']==dict(format=dict(type='json_schema',name=W.VERSION,strict=True,schema=env['wire_schema']),verbosity='low')
    assert sent['store'] is False and 'temperature' not in sent
    assert captures[0]['replay_context']==inp
    assert captures[0]['metadata']['auxiliary_wire_envelope']['hashes']==env['hashes']
    assert G.decode_response(result,inp,new)['risk_verdict']=='PASS'
    tampered=dict(new,wire_contract={})
    tampered['registry_sha256']=P.digest({k:v for k,v in tampered.items() if k!='registry_sha256'})
    with pytest.raises(ValueError):G.validate(tampered)


@pytest.mark.parametrize('response_kind',['completed','incomplete','truncated','unknown_alias','refusal',
    'native_path','native_expired','native_generation','native_all_invalid','unknown_native','provider_error',
    'unsent_budget','timeout_native_mix','revoked'])
def test_full_analyze_target_records_raw_then_decodes(tmp_path,monkeypatch,response_kind):
    """Controlled native machine source; exercise the real entry/provider consumer."""
    import time
    from dataclasses import replace
    from src.tests.test_ai_engine_openai_transport import _build_engine,_sample_ws_data,_sample_ticks,_sample_candles,_allowed_entry_candle_context
    from src.engine import ai_engine_openai as E
    from src.engine.scalping import continuous_reversal_policy as POLICY,continuous_reversal_policy_v6 as V
    from src.engine.scalping import reversal_auxiliary_intraday as I,reversal_source_diagnostics as D,mechanistic_entry_runtime_policy as N
    from src.engine.scalping.entry_setup_evidence import MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1
    from src.utils import constants
    from src.engine.scalping import ai_decision_trace
    from src.tests.test_ai_decision_trace import _enable
    _enable(monkeypatch,tmp_path)
    old,new=definitions();G.register(tmp_path,old);G.register(tmp_path,new)
    f=next(iter(FIXTURES.values()));snap=(copy.deepcopy(f['event']),copy.deepcopy(f['source']))
    inp,prompt,schema=G.production_request(snap,new);env=G.envelope(inp,new)
    snap[0]['epoch']=time.time()
    a=dict(action='ENTER_NOW',reason='test_native_source',policy_version=V.SCHEMA,auxiliary_arm=new['base_arm'],
        auxiliary_binding=G.binding(new),auxiliary_registry_sha256=new['registry_sha256'],family_sha256='f'*64,
        event=snap[0],signal_id='s'*64,signal_set_hash=P.digest(inp['signals']),opportunity_key='e'*64,
        scope_execution_hash='x'*64,matched_policy_refs=[s['ref'] for s in inp['signals']],cell_key='samsung|REGULAR|ALL',route='SOR',
        auxiliary_wire_contract=env['contract'],auxiliary_wire_hashes=env['hashes'])
    live=dict(enabled=True,status='active_bounded_krx_canary',selected_prompt_version=N.AI_VERSION,
        primary_decision_owner='mechanistic_entry_adjudicator',ai_role='auxiliary_risk_screen_pass_veto_no_promotion',
        mechanistic_threshold_policy=MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1,machine_bundle_sha256='b'*64,
        continuous_reversal=dict(schema=V.SCHEMA,family_sha256='f'*64,machine_cells={},auxiliary_cells={}))
    monkeypatch.setattr(constants,'DATA_DIR',tmp_path)
    monkeypatch.setattr(E,'resolve_live_prompt_policy',lambda **kw:copy.deepcopy(live))
    monkeypatch.setattr(E,'TRADING_RULES',replace(E.TRADING_RULES,OPENAI_ANALYZE_TARGET_PROMPT_VERSION=E.DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION))
    monkeypatch.setattr(POLICY,'assess',lambda *args,**kw:(copy.deepcopy(a),inp,prompt,schema))
    monkeypatch.setattr(D,'validate_claim_with_receipt',lambda *args,**kw:snap)
    monkeypatch.setattr(I,'apply_request',lambda *args:args[-1])
    monkeypatch.setattr(I,'validate_decision',lambda *args,**kw:None)
    monkeypatch.setattr(N,'load_effective',lambda **kw:{'bundle_sha256':'b'*64})
    monkeypatch.setattr(V,'validate_active_claim',lambda *args,**kw:a['matched_policy_refs'])
    engine=_build_engine();calls=[]
    raw=dict(assessed={env['citation_map'][s['ref']]:True for s in inp['signals']},screen=dict(verdict='PASS',risk='NO_BLOCKING_RISK',fact=env['citation_map']['observed_machine_signal']),confidence=55)
    def create(**kwargs):
        calls.append(kwargs)
        if response_kind=='provider_error': raise RuntimeError('provider_transport_failure')
        if response_kind=='timeout_native_mix': raise TimeoutError('offline provider timeout')
        output=json.dumps(raw)
        if response_kind=='truncated':output='{"assessed":'
        if response_kind=='refusal':output=''
        if response_kind=='unknown_alias':output=json.dumps(dict(raw,screen=dict(verdict='PASS',risk='NO_BLOCKING_RISK',fact='unknown')))
        return SimpleNamespace(output_text=output,id='integration-response',status='incomplete' if response_kind=='incomplete' else 'completed')
    engine.client=SimpleNamespace(responses=SimpleNamespace(create=create))
    native_errors={'native_path':'reversal_signal_path_changed',
        'native_expired':'reversal_signal_expired_or_changed',
        'native_generation':'reversal_signal_generation_changed',
        'native_all_invalid':'reversal_all_requested_signals_invalidated',
        'unknown_native':'reversal_unrecognized_parser_fault'}
    if response_kind in native_errors:
        def reject(*args,**kw):raise ValueError(native_errors[response_kind])
        monkeypatch.setattr(V,'validate_active_claim',reject)
        engine.consecutive_failures=1
    elif response_kind=='unsent_budget':
        engine.consecutive_failures=1
        def reject(*args,**kw):raise E.OpenAIHTTPWallClockDeadlineError('unsent queue budget',future_cancelled=True)
        monkeypatch.setattr(engine,'_create_openai_response_with_deadline',reject)
    elif response_kind=='revoked':
        engine.consecutive_failures=1
        def reject(*args,**kw):raise ValueError('auxiliary_decision_generation_revoked')
        monkeypatch.setattr(I,'validate_decision',reject)
    sequence=['timeout','native','native','timeout','native'];step=[0]
    if response_kind=='timeout_native_mix':
        def mixed(*args,**kw):
            if sequence[step[0]]=='native':raise ValueError('reversal_signal_path_changed')
            return a['matched_policy_refs']
        monkeypatch.setattr(V,'validate_active_claim',mixed)
    count=4 if response_kind=='unknown_native' else 5 if response_kind in native_errors or response_kind in {'provider_error','unsent_budget','timeout_native_mix','revoked'} else 1
    for index in range(count):
        step[0]=index
        snap[0]['epoch']=time.time()
        if response_kind in {'provider_error','unsent_budget','timeout_native_mix'}:
            a['opportunity_key']=P.digest(['independent_test_point',index])
            a['signal_id']=P.digest(['independent_test_signal',index])
        result=engine.analyze_target('test',_sample_ws_data(),_sample_ticks(),_sample_candles(),strategy='SCALPING',prompt_profile='watching',
            candle_context=_allowed_entry_candle_context(),reversal_signal_claim={'snapshot':snap,'token':'native-test'})
    if response_kind in {'unsent_budget','timeout_native_mix','revoked'}:
        assert result['action']!='BUY' and not engine.ai_disabled
        assert engine.consecutive_failures==(2 if response_kind=='timeout_native_mix' else 1)
        # Two provider failures retain the existing two-key retry allowance;
        # the three intervening native rejects neither increment nor reset it.
        assert len(calls)==(4 if response_kind=='timeout_native_mix' else 0)
        if response_kind=='unsent_budget':
            assert result['provider_adapter_entered'] and not result['provider_sdk_started']
            assert result['provider_called'] is False
            records=list((tmp_path/'runtime/initial_quantity/operating_opportunities').glob('*.json'))
            assert len(records)==5 and all(json.loads(p.read_text())['state']=='transmission_uncertain' for p in records)
        return
    if response_kind in native_errors or response_kind=='provider_error':
        assert len(calls)==(5 if response_kind=='provider_error' else 0) and result['action']!='BUY'
        if response_kind in native_errors and response_kind!='unknown_native':
            assert engine.consecutive_failures==1 and not engine.ai_disabled
            assert result['provider_called'] is False
            assert result['reason']==native_errors[response_kind]
            assert result['evaluation_attempt_id']
        else:
            assert engine.consecutive_failures==5 and engine.ai_disabled
        return
    assert len(calls)==1,result
    assert result['provider_sdk_started'] and result['provider_response_received']
    assert result['provider_physical_transmission']=='response_confirmed'
    request_rows=[json.loads(line) for path in (tmp_path/'ai_decision_requests').glob('*.jsonl') for line in path.read_text().splitlines()]
    assert len(request_rows)==1
    assert request_rows[0]['continuous_reversal_request_binding']['binding_status']=='matched'
    assert calls[0]['instructions']==env['final_prompt']
    receipts=list((I.root(tmp_path)/'responses').glob('*.json'))
    if response_kind!='completed':
        assert not receipts and result['action']!='BUY',result
        native=json.loads((tmp_path/'runtime/initial_quantity/operating_opportunities'/('e'*64+'.json')).read_text())
        assert native['state']=='response_received' and native['history'][-1]['binding']['provider_receipt']['openai_response_id']=='integration-response'
        return
    assert len(receipts)==1,result
    receipt=I.read(receipts[0]);assert receipt['decoded_response']['risk_verdict']=='PASS'
    native=json.loads((tmp_path/'runtime/initial_quantity/operating_opportunities'/('e'*64+'.json')).read_text())
    response=next(h['binding'] for h in native['history'] if h['state']=='response_received')
    assert response['response']==raw and response['provider_receipt']['openai_response_id']=='integration-response'
    assert result['entry_ai_risk_verdict']=='PASS' and result['action']=='BUY',result
