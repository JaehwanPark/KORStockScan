"""Typed, sealed multi-signal risk screening; no detection or order authority."""
from __future__ import annotations

import copy
from datetime import datetime
from src.engine.scalping import continuous_reversal as K
from src.engine.scalping import reversal_path_auxiliary as A
from src.engine.scalping import reversal_path_catalog as C
from src.engine.scalping import reversal_auxiliary_contract as V1
from src.engine.scalping.reversal_auxiliary_phases import ARM_SUFFIXES
from src.engine.scalping.continuous_reversal_postclose import digest

VERSION = 'continuous_reversal_union_auxiliary_v1'
NAMESPACE = 'main_normalized_native_v1'
PROMPT = """Assess the COMMON ENTRY OPPORTUNITY represented by ALL supplied signals.
The machine has independently confirmed every listed typed signal. Do not pick
a winning branch. Return assessed_signal_refs containing every supplied ref.
The objective is net +0.4% within 1800 seconds before net -3%, with cost charged
once. Judge that binary event, not expected PnL, payoff ratio or historical rank.
Rolling features end at the shared confirmation and can include earlier selling
or below-VWAP prices. These alone are not proof that the current signal failed.
Breakout and momentum signals need no synthetic decline, low or FIRST uptick.
Unknown optional context is neutral. Never invent depth, news or future prices.
PASS is common-opportunity risk clearance, not conditional permission for one
branch. Signal validity is rechecked by the machine. Cite only supplied fact IDs.
For PASS use NO_BLOCKING_RISK and cite observed_machine_signal. For VETO/CAUTION
cite the exact supplied risk binding and at least one matching adverse/context
fact. Do not invent a compulsory extra confirmation or fixed feature threshold.
Confidence is diagnostic. Output only the required JSON. No order authority.
"""


def opportunity(event):
    """Explicit stream namespace prevents aliases across independent collectors."""
    return digest([NAMESPACE, str(datetime.fromtimestamp(event['epoch'], K.KST).date()),
                   event['symbol'], event['market'], event['venue'], event['source_item'],
                   event['native_epoch'], event['native_sequence']])


def binding(arm):
    if arm not in V1.ARMS:
        raise ValueError('union_arm_invalid')
    return dict(input_version=VERSION, validator_version=VERSION,
                prompt_version=VERSION + ':' + arm, arm=arm,
                prompt_sha256=digest(PROMPT + ARM_SUFFIXES[arm]),
                response_schema_version=VERSION)


def definition_hash(bid):
    return C.branch(bid).get('definition_sha256', digest(C.definition(bid)))


def production_request(source, arm, *, phase=None, event):
    binding(arm)
    signals = event['branch_signals']
    if not signals or set(signals) != set(source['branch_inputs']):
        raise ValueError('union_signal_source_coverage_invalid')
    common_keys = ('epoch', 'symbol', 'market', 'venue', 'source_item',
                   'native_epoch', 'native_sequence', 'confirmation_price', 'entry_ask')
    common = {k: event[k] for k in common_keys}
    if not A.finite(common['entry_ask']) or common['entry_ask'] <= 0:
        raise ValueError('union_entry_quote_missing')
    projected = []
    contexts, adverse, positives, risks = {}, {}, {}, {}
    for bid in sorted(signals):
        signal = signals[bid]
        if any(signal.get(k) != v for k, v in common.items()):
            raise ValueError('union_same_tick_source_conflict')
        if signal['decision_phase'] != C.branch(bid)['decision_phase']:
            raise ValueError('union_signal_definition_invalid')
        inp, _, _ = A.production_request(source['branch_inputs'][bid], arm,
                                         phase=signal['decision_phase'], event=signal)
        evidence = inp['entry_setup_evidence_v1']
        # Existing typed projectors are allowlists. Never transmit label/rank or
        # arbitrary event metadata. Namespaced facts retain their exact scope.
        ref = bid + ':' + definition_hash(bid)
        projected.append(dict(ref=ref, policy_id=bid, phase=signal['decision_phase'],
            definition_sha256=definition_hash(bid),
            observation_phase=copy.deepcopy(inp['observation_phase']),
            observed_signal=copy.deepcopy(inp.get('observed_signal')),
            facts=copy.deepcopy(evidence['facts']),
            recent_observed_prices=copy.deepcopy(inp.get('recent_observed_prices', []))))
        for field, target in (('positive_facts', positives), ('context_facts', contexts),
                              ('contradicting_facts', adverse)):
            for fact in evidence.get(field, []):
                fid = ref + '/' + fact['id']
                target[fid] = dict(copy.deepcopy(fact), id=fid)
        for code, ids in evidence.get('risk_fact_bindings', {}).items():
            risks.setdefault(code, set()).update(ref + '/' + i for i in ids)
    positives['observed_machine_signal'] = dict(id='observed_machine_signal',
                                               value=len(projected), unit='signal_count')
    common.update(opportunity_key=opportunity(event), as_of=K.iso(event['epoch']),
        objective=dict(net_target_pct=.4, net_soft_stop_pct=-3., horizon_seconds=1800, cost_rate=.0023))
    setup = dict(source_quality='price_and_entry_quote_valid', setup_state='READY',
                 facts=dict(entry_ask=event['entry_ask'], confirmation_price=event['confirmation_price']),
                 positive_facts=list(positives.values()), context_facts=list(contexts.values()),
                 contradicting_facts=list(adverse.values()),
                 risk_fact_bindings={k: sorted(v) for k, v in sorted(risks.items())})
    inp = dict(schema=VERSION, common_context=common, signals=projected,
               observation_phase=dict(stage='UNION', rolling_windows_end='AT_CONFIRMATION'),
               entry_setup_evidence_v1=setup)
    if arm in V1.ARMS[2:]:
        ask = event['entry_ask']
        common['entry_geometry'] = dict(target_price=ask*1.004/.9977,
                                        soft_stop_price=ask*.97/.9977)
    return inp, PROMPT + ARM_SUFFIXES[arm], response_schema(inp)


def response_schema(inp):
    setup=inp['entry_setup_evidence_v1']
    fact_ids=sorted({f['id'] for field in ('positive_facts','context_facts','contradicting_facts') for f in setup[field]})
    refs=[s['ref'] for s in inp['signals']]
    def array(values):
        return dict(type='array', items=dict(type='string', enum=values))
    props = dict(schema=dict(type='string', enum=[VERSION]),
        decision_scope=dict(type='string', enum=['COMMON_OPPORTUNITY']),
        assessed_signal_refs=array(refs), risk_verdict=dict(type='string', enum=['PASS','VETO','CAUTION']),
        risk_codes=array(['NO_BLOCKING_RISK'] + sorted(setup['risk_fact_bindings'])),
        supporting_fact_ids=array(fact_ids), contradicting_fact_ids=array(fact_ids),
        confidence=dict(type='integer', minimum=0, maximum=100))
    schema = dict(type='object', additionalProperties=False, required=list(props), properties=props)
    return schema


def validate_response(response, inp, *, arm, phase=None):
    if arm not in V1.ARMS or (inp or {}).get('schema') != VERSION:
        return ['union_input_contract_invalid']
    fields = {'schema','decision_scope','assessed_signal_refs','risk_verdict','risk_codes',
              'supporting_fact_ids','contradicting_fact_ids','confidence'}
    if not isinstance(response, dict) or set(response) != fields:
        return ['union_response_schema_invalid']
    refs = [s['ref'] for s in inp['signals']]
    if (response['schema'] != VERSION or response['decision_scope'] != 'COMMON_OPPORTUNITY'
            or not isinstance(response['assessed_signal_refs'], list)
            or any(not isinstance(v,str) for v in response['assessed_signal_refs'])
            or sorted(response['assessed_signal_refs']) != sorted(refs)
            or type(response['confidence']) is not int or not 0 <= response['confidence'] <= 100
            or response['risk_verdict'] not in {'PASS','CAUTION','VETO'}):
        return ['union_response_coverage_or_role_invalid']
    setup = inp['entry_setup_evidence_v1']
    facts = {f['id'] for k in ('positive_facts','context_facts','contradicting_facts') for f in setup[k]}
    for field in ('supporting_fact_ids', 'contradicting_fact_ids', 'risk_codes'):
        value = response[field]
        if not isinstance(value, list) or any(not isinstance(v, str) for v in value) or len(value) != len(set(value)):
            return ['union_response_citations_invalid']
    if not set(response['supporting_fact_ids'] + response['contradicting_fact_ids']) <= facts:
        return ['union_response_unknown_fact']
    if response['risk_verdict'] == 'PASS':
        return [] if response['risk_codes'] == ['NO_BLOCKING_RISK'] and 'observed_machine_signal' in response['supporting_fact_ids'] else ['union_pass_support_invalid']
    bindings = setup['risk_fact_bindings']
    return [] if response['risk_codes'] and all(c in bindings and set(response['contradicting_fact_ids']).intersection(bindings[c]) for c in response['risk_codes']) else ['union_nonpass_risk_unbound']
