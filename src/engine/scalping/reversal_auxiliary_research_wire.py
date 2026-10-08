"""Offline union-response transport experiment, with reversible citation IDs.

Owned by scalping research. This is not registered for runtime publication.
Raw provider payloads remain intact; decoding never supplies a missing answer.
"""
from __future__ import annotations

import copy
from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.scalping import reversal_extended_union as U

VERSION = 'auxiliary_compact_citations_v1'
SUFFIX = """
Transport format: signal and fact IDs are lossless short aliases. Fact names
retain their original meaning. Apply the same risk assessment above. Instead
of the long response arrays, return the compact schema supplied with this call.
Set every assessed signal check to true only after considering that signal.
Return one screen: PASS with NO_BLOCKING_RISK and the observed_machine_signal
fact, or CAUTION/VETO with the most material supplied risk and a fact bound to
that risk. A schema option or risk binding is a citation vocabulary, not proof
that the risk exists. Choose the verdict from the supplied facts. Confidence
remains diagnostic. No extra prose. No order authority.
"""


def contract():
    return dict(version=VERSION, source_sha256=P.file_hash(__file__))


def object_schema(properties):
    return dict(type='object', properties=properties, required=list(properties), additionalProperties=False)


def enum(values):
    return dict(type='string', enum=list(values))


def encode(inp):
    if inp.get('schema') != U.VERSION or not inp.get('signals'):
        raise ValueError('compact_wire_input_invalid')
    setup = inp['entry_setup_evidence_v1']
    refs = [s['ref'] for s in inp['signals']]
    facts = sorted({f['id'] for k in ('positive_facts','context_facts','contradicting_facts') for f in setup[k]})
    if len(set(refs)) != len(refs) or 'observed_machine_signal' not in facts:
        raise ValueError('compact_wire_identity_invalid')
    aliases = {v:'s'+str(i+1) for i,v in enumerate(refs)}
    aliases.update({v:'f'+str(i+1) for i,v in enumerate(facts)})
    def replace(value):
        if isinstance(value,str): return aliases.get(value,value)
        if isinstance(value,list): return [replace(v) for v in value]
        if isinstance(value,dict): return {k:replace(v) for k,v in value.items()}
        return value
    wire = replace(inp)
    for field in ('positive_facts','context_facts','contradicting_facts'):
        for original, transformed in zip(setup[field],wire['entry_setup_evidence_v1'][field]):
            transformed['citation_name'] = original['id'].rsplit('/',1)[-1]
    variants = [object_schema(dict(verdict=enum(['PASS']), risk=enum(['NO_BLOCKING_RISK']),
                                   fact=enum([aliases['observed_machine_signal']])))]
    for risk, ids in sorted(setup['risk_fact_bindings'].items()):
        if not ids: continue
        if not set(ids) <= set(facts): raise ValueError('compact_wire_risk_binding_invalid')
        variants.append(object_schema(dict(verdict=enum(['CAUTION','VETO']), risk=enum([risk]),
                                            fact=enum([aliases[i] for i in sorted(set(ids))]))))
    schema = object_schema(dict(
        assessed=object_schema({aliases[r]:dict(type='boolean',enum=[True]) for r in refs}),
        screen=dict(anyOf=variants), confidence=dict(type='integer',minimum=0,maximum=100)))
    return wire, schema, aliases


def request(req, logical_input, expected_contract):
    if expected_contract != contract(): raise ValueError('compact_wire_contract_changed')
    wire, schema, aliases = encode(logical_input)
    result = copy.deepcopy(req)
    result['candidate_input'] = wire
    result['candidate_input_sha256'] = P.digest(wire)
    result['candidate'].update(system_prompt=req['candidate']['system_prompt']+SUFFIX,
        response_schema=schema,schema_name=VERSION,max_output_tokens=1024,
        response_schema_sha256=P.digest(schema),response_schema_instance_sha256=P.digest(schema),
        compact_wire_contract=expected_contract,logical_input_sha256=P.digest(logical_input),
        citation_map_sha256=P.digest(aliases))
    result['candidate'].pop('contract_sha256',None)
    result['paired_replay_id'] = P.digest([req['paired_replay_id'],VERSION,
        {k:result[k] for k in ('candidate_input','candidate','control','stage')}])
    return result


def decode(raw, inp, arm):
    _, _, aliases = encode(inp)
    inverse = {v:k for k,v in aliases.items()}
    signals = {aliases[s['ref']] for s in inp['signals']}
    if (not isinstance(raw,dict) or set(raw) != {'assessed','screen','confidence'}
            or not isinstance(raw['assessed'],dict) or set(raw['assessed']) != signals
            or any(v is not True for v in raw['assessed'].values())):
        raise ValueError('compact_wire_signal_coverage_invalid')
    screen = raw['screen']
    if (not isinstance(screen,dict) or set(screen) != {'verdict','risk','fact'}
            or any(not isinstance(v,str) for v in screen.values())):
        raise ValueError('compact_wire_screen_invalid')
    if not isinstance(screen['fact'],str) or screen['fact'] not in inverse:
        raise ValueError('compact_wire_fact_unknown')
    fact = inverse[screen['fact']]
    passed = screen['verdict'] == 'PASS'
    response = dict(schema=U.VERSION,decision_scope='COMMON_OPPORTUNITY',
        assessed_signal_refs=[inverse[s] for s in raw['assessed']],risk_verdict=screen['verdict'],
        risk_codes=[screen['risk']], supporting_fact_ids=[fact] if passed else [],
        contradicting_fact_ids=[] if passed else [fact],confidence=raw['confidence'])
    errors = U.validate_response(response,inp,arm=arm)
    if errors: raise ValueError('compact_wire_decoded_invalid:'+','.join(errors))
    return response


def response(record_result, req, logical_input, arm):
    raw = record_result.get('candidate_response')
    cfg = req['candidate'].get('compact_wire_contract')
    if not cfg: return raw
    if cfg != contract() or req['candidate'].get('logical_input_sha256') != P.digest(logical_input):
        raise ValueError('compact_wire_contract_changed')
    # Keep provider receipts and parsed wire response unmodified. Evaluation
    # recomputes this projection from the stored wire payload every time.
    return decode(raw,logical_input,arm)
