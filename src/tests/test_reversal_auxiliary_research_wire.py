"""Lossless wire identifiers and strict reconstruction, without API calls."""
import copy
import pytest
from src.engine.scalping import reversal_auxiliary_research_wire as W
from src.engine.scalping import reversal_auxiliary_registry as G
from src.engine.scalping import reversal_auxiliary_tuning as T
from src.engine.scalping import reversal_extended_union as U
from src.tests.test_reversal_extended_policy import FIXTURES


@pytest.mark.parametrize('fixture',list(FIXTURES.values()))
def test_roundtrip_preserves_facts_and_every_signal(fixture):
    registry=G.definition(U.V1.ARMS[1],input_version=U.VERSION)
    snapshot=(fixture['event'],fixture['source'])
    req=G.request(snapshot,registry);inp=req['candidate_input']
    wire,schema,aliases=W.encode(inp)
    reverse={v:k for k,v in aliases.items()}
    def undo(v):
        if isinstance(v,str):return reverse.get(v,v)
        if isinstance(v,list):return [undo(x) for x in v]
        if isinstance(v,dict):return {k:undo(x) for k,x in v.items() if k!='citation_name'}
        return v
    assert undo(wire)==inp
    checked={aliases[s['ref']]:True for s in inp['signals']}
    raw=dict(assessed=checked,screen=dict(verdict='PASS',risk='NO_BLOCKING_RISK',fact=aliases['observed_machine_signal']),confidence=61)
    result=dict(candidate_response=raw,provider_attempt_receipt=dict(raw_output_sha256='raw'),provider_provenance=dict(response_id='real-test'))
    original=copy.deepcopy(result)
    compact=W.request(req,inp,W.contract())
    from src.engine.scalping.ai_decision_quality import execute_openai_prompt_v2_candidate
    projected=execute_openai_prompt_v2_candidate(compact,_request_projection_only=True)['provider_request_projection']
    assert projected['max_output_tokens']==1024
    decoded,errors=T.response_projection(result,compact,inp,registry)
    assert errors==[] and decoded['risk_verdict']=='PASS' and result==original
    assert set(decoded['assessed_signal_refs'])=={s['ref'] for s in inp['signals']}
    for risk,ids in inp['entry_setup_evidence_v1']['risk_fact_bindings'].items():
        if not ids:continue
        raw['screen']=dict(verdict='CAUTION',risk=risk,fact=aliases[ids[0]])
        assert U.validate_response(W.decode(raw,inp,registry['base_arm']),inp,arm=registry['base_arm'])==[]
    raw['screen']=dict(verdict='CAUTION',risk='NO_BLOCKING_RISK',fact=aliases['observed_machine_signal'])
    with pytest.raises(ValueError,match='decoded_invalid'):W.decode(raw,inp,registry['base_arm'])
    raw['assessed'].clear()
    with pytest.raises(ValueError,match='signal_coverage'):W.decode(raw,inp,registry['base_arm'])
    with pytest.raises(ValueError,match='contract_changed'):W.request(req,inp,dict(version='old'))


def test_malformed_refusal_and_invented_facts_never_decode_to_pass():
    fixture=next(iter(FIXTURES.values()));arm=U.V1.ARMS[0]
    inp,_,_=U.production_request(fixture['source'],arm,event=fixture['event'])
    _,_,ids=W.encode(inp)
    raw=dict(assessed={ids[s['ref']]:True for s in inp['signals']},screen=dict(verdict='PASS',risk='NO_BLOCKING_RISK',fact='invented'),confidence=50)
    for value in (None,{},dict(refusal='refused'),raw):
        with pytest.raises(ValueError):W.decode(value,inp,arm)
    raw['screen']['fact']=ids['observed_machine_signal'];raw['screen']['risk']=[]
    with pytest.raises(ValueError):W.decode(raw,inp,arm)
