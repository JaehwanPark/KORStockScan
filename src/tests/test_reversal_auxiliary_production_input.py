"""Native registry opt-in preserves incumbent bytes and exact research input."""
import copy
import json
from types import SimpleNamespace

import pytest

from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.scalping import reversal_auxiliary_registry as G
from src.engine.scalping import reversal_auxiliary_production_input as M
from src.engine.scalping import reversal_auxiliary_risk_role_experiment as X
from src.engine.scalping import reversal_auxiliary_wire as W
from src.engine.scalping import reversal_auxiliary_research_wire as OLD_W
from src.tests.test_reversal_extended_policy import FIXTURES


def definitions(fixture=None):
    fixture=fixture or next(iter(FIXTURES.values()))
    event=fixture['event']
    sid=M.C.cell_key(event['symbol'],event['market'],event['confirmation_price'])+'|'+event['venue']
    original=G.definition(M.U.V1.ARMS[1],input_version=M.U.VERSION)
    parent=G.compact_definition(original,research_wire_contract=OLD_W.contract())
    current=G.production_definition(parent,scope_ids=[sid])
    return original,parent,current


@pytest.mark.parametrize('fixture',list(FIXTURES.values()))
def test_exact_production_projection_preserves_native_signals_and_wire(fixture,tmp_path,monkeypatch):
    from src.engine.scalping import reversal_auxiliary_intraday as I
    original,parent,current=definitions(fixture)
    snap=(fixture['event'],fixture['source'])
    before=copy.deepcopy((snap,original,parent))
    baseline=G.production_request(snap,parent)
    projected,prompt,schema=G.production_request(snap,current)
    expected=X.project(baseline[0],expected_contract=X.contract(M.MODE))
    assert projected==expected and projected['signals']==baseline[0]['signals']
    assert prompt==baseline[1] and schema==M.U.response_schema(expected)
    env=G.envelope(projected,current)
    assert env==W.envelope(expected,prompt,schema)
    req=G.request(snap,current)
    assert req['candidate_input']==env['wire_input']
    assert req['candidate']['system_prompt']==env['final_prompt']
    assert req['candidate']['response_schema']==env['wire_schema']
    assert req['candidate']['logical_input_sha256']==P.digest(projected)
    assert req['candidate_input_sha256']==P.digest(env['wire_input'])
    assert req['paired_replay_id']!=G.request(snap,parent)['paired_replay_id']
    assert G.production_request(snap,original)==baseline
    assert (snap,original,parent)==before
    assessment=dict(action='ENTER_NOW',policy_version='continuous_reversal_policy_v6',
        signal_set_hash=P.digest(baseline[0]['signals']))
    monkeypatch.setattr(I,'selected_definition',lambda *args:(current,None))
    result=I.apply_request(tmp_path,{'bundle_sha256':'a'*64},snap,(assessment,*baseline))
    assert result[1:]==(projected,prompt,schema)
    assert result[0]['signal_set_hash']==assessment['signal_set_hash']
    assert result[0]['auxiliary_registry_sha256']==current['registry_sha256']
    assert result[0]['auxiliary_wire_hashes']==env['hashes']
    for action in ('BLOCK','RECHECK'):
        denied=({**assessment,'action':action},*baseline)
        assert I.apply_request(tmp_path,{},snap,denied) is denied
    for registry in original,parent,current:G.register(tmp_path,registry)
    assert G.load(tmp_path,parent['registry_sha256'])==parent
    assert G.load(tmp_path,current['registry_sha256'])==current


@pytest.mark.parametrize('defect',['missing','empty','mode','source','transform','scope','parent','version'])
def test_malformed_registry_fails_even_with_rehashed_identity(defect):
    _,_,value=definitions();bad=copy.deepcopy(value)
    contract=bad['production_input_contract']
    if defect=='missing':bad.pop('production_input_contract')
    if defect=='empty':bad['production_input_contract']={}
    if defect=='mode':contract['mode']='ROLE'
    if defect=='source':contract['source_sha256']='a'*64
    if defect=='transform':contract['transform_sha256']='a'*64
    if defect=='scope':contract['scope_ids']=['other_non_fixed|PRE|LT_20000|KRX']
    if defect=='parent':bad['production_parent_registry_sha256']='invalid'
    if defect=='version':bad['input_version']='continuous_reversal_union_auxiliary_v2'
    bad['registry_sha256']=P.digest({k:v for k,v in bad.items() if k!='registry_sha256'})
    with pytest.raises(ValueError):G.validate(bad)


def test_parent_and_scope_cannot_leak_or_be_silently_replaced(tmp_path):
    original,parent,current=definitions()
    for registry in original,parent,current:G.register(tmp_path,registry)
    G.directory(tmp_path).joinpath(parent['registry_sha256']+'.json').unlink()
    with pytest.raises((ValueError,OSError)):G.load(tmp_path,current['registry_sha256'])
    fixture=next(iter(FIXTURES.values()))
    baseline=G.production_request((fixture['event'],fixture['source']),parent)[0]
    other=copy.deepcopy(baseline);other['common_context']['venue']='NXT'
    with pytest.raises(ValueError,match='scope_mismatch'):
        M.project(other,expected_contract=current['production_input_contract'])
    for scopes in ([],current['production_input_contract']['scope_ids']*2,['invalid']):
        with pytest.raises(ValueError):G.production_definition(parent,scope_ids=scopes)


@pytest.mark.parametrize('defect',['untransformed','changed_value','missing_fact','changed_binding','changed_role'])
def test_wire_and_decode_fail_closed_for_unprojected_or_altered_input(defect):
    _,parent,current=definitions();f=next(iter(FIXTURES.values()));snap=(f['event'],f['source'])
    logical=G.production_request(snap,current)[0]
    bad=copy.deepcopy(logical);setup=bad['entry_setup_evidence_v1']
    fact=next(f for f in setup['context_facts'] if '/observed_target_progress_v1/' in f['id'])
    if defect=='untransformed':bad=G.production_request(snap,parent)[0]
    if defect=='changed_value':fact['value']+=1
    if defect=='missing_fact':setup['context_facts'].remove(fact)
    if defect=='changed_binding':setup['risk_fact_bindings']['OBSERVED_TARGET_PROGRESS_CONCERN'].remove(fact['id'])
    if defect=='changed_role':setup['context_facts'].remove(fact);setup['contradicting_facts'].append(fact)
    with pytest.raises(ValueError):G.envelope(bad,current)
    with pytest.raises(ValueError):G.decode_response({},bad,current)


def test_live_sdk_wire_identity_and_new_numeric_citation(tmp_path,monkeypatch):
    from src.tests.test_ai_engine_openai_transport import _build_engine
    from src.engine import ai_engine_openai as E
    from src.utils import constants
    original,parent,current=definitions()
    for value in original,parent,current:G.register(tmp_path,value)
    f=next(iter(FIXTURES.values()));snap=(f['event'],f['source'])
    logical,prompt,schema=G.production_request(snap,current);env=G.envelope(logical,current)
    fact=next(f for f in logical['entry_setup_evidence_v1']['context_facts'] if '/observed_target_progress_v1/' in f['id'])
    raw=dict(assessed={env['citation_map'][s['ref']]:True for s in logical['signals']},
        screen=dict(verdict='CAUTION',risk='OBSERVED_TARGET_PROGRESS_CONCERN',fact=env['citation_map'][fact['id']]),confidence=55)
    engine=_build_engine();calls=[];captures=[]
    def create(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(output_text=json.dumps(raw),id='production-input-test',status='completed')
    engine.client=SimpleNamespace(responses=SimpleNamespace(create=create))
    monkeypatch.setattr(constants,'DATA_DIR',tmp_path)
    monkeypatch.setattr(E,'capture_ai_request',lambda **kw:captures.append(kw) or {})
    result=engine._call_openai_safe(prompt,json.dumps(logical,ensure_ascii=True,sort_keys=True,separators=(',',':')),
        model_override=current['model'],schema_name=E.ENTRY_RISK_ADJUDICATION_SCHEMA,endpoint_name='analyze_target',transport_mode_override='http',
        metadata_extra={'entry_setup_live_policy_selected_prompt_version':G.binding(current)['prompt_version']},
        response_schema_override=schema,auxiliary_registry_sha256=current['registry_sha256'],replay_context=logical,
        auxiliary_identity_context=dict(policy_version='continuous_reversal_policy_v6',registry_sha256=current['registry_sha256']))
    assert result==raw and len(calls)==1
    sent=calls[0]
    assert sent['instructions']==env['final_prompt']
    assert sent['input']==json.dumps(env['wire_input'],ensure_ascii=True,sort_keys=True,separators=(',',':'))
    assert sent['text']['format']['schema']==env['wire_schema']
    assert sent['text']['format']['name']==W.VERSION and sent['model']=='gpt-5.4-nano'
    assert sent['max_output_tokens']==1024 and sent['reasoning']=={'effort':'none'} and 'temperature' not in sent
    assert G.decode_response(result,logical,current)['contradicting_fact_ids']==[fact['id']]
    meta=engine._consume_last_transport_meta()
    identity=G.validate_identity(meta['entry_auxiliary_policy_identity'])
    assert identity['semantic']['production_input_contract']==current['production_input_contract']
    assert 'allowed_runtime_apply' not in identity['semantic']['production_input_contract']
    baseline,p,_=G.production_request(snap,parent)
    legacy_env=G.envelope(baseline,parent)
    legacy_payload=dict(sent,instructions=legacy_env['final_prompt'],input=json.dumps(legacy_env['wire_input']),
        text=dict(format=dict(schema=legacy_env['wire_schema'])))
    old_identity=G.provider_identity(legacy_payload,dict(policy_version='continuous_reversal_policy_v6',registry_sha256=parent['registry_sha256']))
    assert 'production_input_contract' not in old_identity['semantic']
    assert old_identity['identity_sha256']!=identity['identity_sha256']
    assert captures[0]['metadata']['auxiliary_wire_envelope']['hashes']==env['hashes']


@pytest.mark.parametrize('spread',[0.,.2,.4])
def test_legacy_spread_contract_preserves_exact_research_projection(spread):
    from src.tests.test_reversal_auxiliary_risk_role_experiment import legacy
    logical,_=legacy(spread)
    common=logical['common_context']
    sid=M.C.cell_key(common['symbol'],common['market'],common['confirmation_price'])+'|'+common['venue']
    contract=M.contract([sid])
    transformed=M.project(logical,expected_contract=contract)
    assert transformed==X.project(logical,expected_contract=X.contract(M.MODE))
    assert M.validate_projected(transformed,expected_contract=contract)==transformed
    assert transformed['signals']==logical['signals']


@pytest.mark.parametrize('response_kind',['completed','native_changed_after_response'])
def test_full_live_consumer_retains_native_and_response_guards(tmp_path,monkeypatch,response_kind):
    from src.tests import test_reversal_auxiliary_wire as live
    original,parent,current=definitions()
    G.register(tmp_path,original);G.register(tmp_path,parent)
    monkeypatch.setattr(live,'definitions',lambda:(original,current))
    live.test_full_analyze_target_records_raw_then_decodes(tmp_path,monkeypatch,response_kind)
