"""Typed signal facts and fixed auxiliary arms without invented reversal facts."""
from __future__ import annotations
import copy
import math
from src.engine.scalping import reversal_auxiliary_phases as OLD
from src.engine.scalping import reversal_auxiliary_contract as V1
from src.engine.scalping.continuous_reversal_branches import FIRST, CONFIRMED
from src.engine.scalping.continuous_reversal_postclose import digest

VERSION = 'continuous_path_auxiliary_v1'
PHASES = frozenset({'MOMENTUM_CROSS','MOMENTUM_HOLD','HIGH_BREAKOUT',
                    'RETEST_RECLAIM_FIRST','RETEST_RECLAIM_PEAK'})
FEATURES = ('confirmation_price','entry_ask','spread_pct','drawdown_5m_pct',
            'volume_ratio_60s','return_60s_pct','session_return_pct','vs_vwap_60s_pct',
            'buy_pressure_10t','buy_pressure_30s','return_10t_pct')
PROOF_FIELDS = frozenset({'epoch','price','threshold','return_60s_pct','previous_condition','prior_high',
                         'low','peak','reclaim','minimum_price','touch_epoch','touch_price'})
PROMPT = '''Assess the supplied machine-observed signal at its actual confirmation ask.
Judge net +0.4% within 1800 seconds before net -3%, with cost 0.23% once.
Judge event likelihood, never expected PnL, payoff ratio or a desired PASS quota.
The signal_kind and observed_signal identify what actually occurred: momentum
cross, held momentum, prior high breakout, or low retest followed by reclaim.
Do not describe a momentum or breakout signal as a decline and first uptick.
All rolling features end AT_CONFIRMATION. Context may mix observations before
and through the signal. Selling or below-VWAP context alone is not evidence
of a failed signal after confirmation. Preserve adverse values and assess the
current small-target opportunity. Optional unknown context is neutral.
Do not demand another confirmation or invent future prices, depth, news or
source gaps. This auxiliary screen has no order authority. Confidence is
diagnostic. The runtime retains all quote, account, order and safety guards.
Return only the six-field JSON. PASS uses ["NO_BLOCKING_RISK"] and cites
observed_machine_signal. CAUTION/VETO cites an exact supplied fact binding
for each risk code. Context concerns do not assert later invalidation.
'''


def finite(value):
    return type(value) in (int,float) and math.isfinite(value)


def project_signal(event):
    return {k:v for k,v in event['signal_proof'].items() if k in PROOF_FIELDS}


def validate_input_signal(inp,event):
    from src.engine.scalping.continuous_reversal import iso
    validate_signal(event)
    if (inp.get('schema')!=VERSION or inp.get('observed_signal')!=project_signal(event)
            or inp.get('signal_kind')!=event['decision_phase'] or inp.get('source_item')!=event['source_item']
            or inp.get('as_of')!=iso(event['epoch'])
            or inp.get('observation_phase')!=dict(stage=event['decision_phase'],rolling_windows_end='AT_CONFIRMATION',post_trigger_observations='OBSERVED_THROUGH_CONFIRMATION')):
        raise ValueError('path_auxiliary_signal_input_conflict')
    f=event['branch_features'];facts=inp['entry_setup_evidence_v1']['facts']
    expected=dict(confirmation_price=event['confirmation_price'],entry_ask=event['entry_ask'],
        spread_pct=event['spread_pct'],drawdown_5m_pct=event['drawdown_5m_pct'],volume_ratio_60s=event['volume_ratio_60s'],
        return_60s_pct=f['ret'],session_return_pct=f['session'],vs_vwap_60s_pct=f['vwap'],buy_pressure_10t=f['buy10'])
    if any(facts.get(k)!=v for k,v in expected.items()):raise ValueError('path_auxiliary_feature_input_conflict')


def validate_signal(event):
    phase=event.get('decision_phase');p=event.get('signal_proof') or {}
    if phase not in PHASES or event.get('signal_kind')!=phase:
        raise ValueError('path_signal_phase_invalid')
    if any(not finite(event.get(k)) for k in ('epoch','confirmation_price')) or event['confirmation_price']<=0:
        raise ValueError('path_signal_price_clock_invalid')
    if any(not finite(p.get(k)) for k in ('epoch','price','native_epoch','native_sequence')) or p['price']<=0:
        raise ValueError('path_root_proof_invalid')
    if not (p['epoch']<=event['epoch'] and p['native_epoch']==event['native_epoch'] and p['native_sequence']<=event['native_sequence']):
        raise ValueError('path_signal_timeline_invalid')
    if phase in {'MOMENTUM_CROSS','MOMENTUM_HOLD','HIGH_BREAKOUT'}:
        if p.get('previous_condition') is not False:
            raise ValueError('path_signal_known_cross_missing')
        if phase=='HIGH_BREAKOUT':
            valid=finite(p.get('prior_high')) and p['price']>p['prior_high']
        else:
            valid=finite(p.get('threshold')) and finite(p.get('return_60s_pct')) and p['return_60s_pct']>=p['threshold']
        if phase=='MOMENTUM_HOLD':
            valid=valid and event['epoch']-p['epoch']>=1 and finite(p.get('minimum_price')) and p['minimum_price']>=p['price'] and event['confirmation_price']>=p['price']
        else:
            valid=valid and event['epoch']==p['epoch'] and event['native_sequence']==p['native_sequence'] and event['confirmation_price']==p['price']
    else:
        valid=(all(finite(p.get(k)) for k in ('low','peak','reclaim','minimum_price','touch_epoch','touch_sequence','touch_price'))
            and p['low']>0 and p['price']>p['low'] and p['peak']>p['low']
            and p['reclaim']==(p['peak'] if phase=='RETEST_RECLAIM_PEAK' else p['price'])
            and p['epoch']<=p['touch_epoch']<=event['epoch']<=p['epoch']+120
            and p['native_sequence']<p['touch_sequence']<event['native_sequence']
            and p['minimum_price']>=p['low']*.998 and p['touch_price']<=p['low']
            and event['confirmation_price']>=p['reclaim'])
    if not valid:raise ValueError('path_signal_proof_invalid')


def prompt(phase,arm):
    if phase in {FIRST,CONFIRMED}:return OLD.prompt(phase,arm)
    if phase not in PHASES or arm not in V1.ARMS:raise ValueError('path_auxiliary_phase_unsupported')
    return PROMPT+'Signal kind: '+phase+'.\n'+OLD.ARM_SUFFIXES[arm]


def binding(phase,arm):
    if phase in {FIRST,CONFIRMED}:return OLD.binding(phase,arm)
    return dict(phase=phase,arm=arm,prompt_version=VERSION+':'+phase+':'+arm,
        prompt_sha256=digest(prompt(phase,arm)),input_version=VERSION,
        response_schema_version='entry_setup_risk_adjudication_v1',validator_version=VERSION,
        feature_version='continuous_path_prefix_v1',fact_definition_sha256=digest([FEATURES,PROMPT,phase]))


def production_request(source,arm,*,phase=FIRST,event=None):
    if phase in {FIRST,CONFIRMED}:return OLD.production_request(source,arm,phase=phase,event=event)
    validate_signal(event)
    if phase!=event['decision_phase'] or source.get('signal_kind')!=phase or source.get('signal_proof')!=event['signal_proof']:
        raise ValueError('path_auxiliary_source_signal_conflict')
    facts={k:copy.deepcopy(source['facts'][k]) for k in FEATURES}
    if any(v is not None and not finite(v) for v in facts.values()):raise ValueError('path_feature_invalid')
    if any(not finite(facts[k]) or facts[k]<=0 for k in ('confirmation_price','entry_ask')) or facts['spread_pct'] is None or facts['spread_pct']<0:
        raise ValueError('path_essential_quote_invalid')
    if facts['confirmation_price']!=event['confirmation_price'] or facts['entry_ask']!=event['entry_ask']:
        raise ValueError('path_quote_signal_conflict')
    positive=[dict(id='observed_machine_signal',value=event['confirmation_price'],unit='price')]
    contexts=[];adverse=[];bindings={}
    for feature,fid,threshold,op in (
        ('buy_pressure_10t','recent_sell_pressure',50,'lt'),('return_60s_pct','negative_short_momentum',0,'lt'),
        ('vs_vwap_60s_pct','below_recent_vwap',0,'lt'),('volume_ratio_60s','volume_not_expanding',1,'lt')):
        value=facts[feature]
        if value is not None and value<threshold:contexts.append(dict(id=fid,value=value,unit='percent' if feature!='volume_ratio_60s' else 'ratio'))
    if contexts:bindings['EARLY_SIGNAL_FRAGILE']=[f['id'] for f in contexts]
    if facts['spread_pct']>0:
        adverse.append(dict(id='observed_spread',value=facts['spread_pct'],unit='percent'))
        bindings['ENTRY_SPREAD_CONCERN']=['observed_spread']
    if arm==V1.ARMS[0]:adverse+=contexts;contexts=[]
    prices=[{k:p[k] for k in ('age_sec','price','qty','side')} for p in source['recent_observed_prices']]
    if any(not finite(p['age_sec']) or p['age_sec']<0 or not finite(p['price']) or p['price']<=0 or p['side'] not in {'BUY','SELL','UNKNOWN'} or (p['qty'] is not None and (not finite(p['qty']) or p['qty']<0)) for p in prices):
        raise ValueError('path_recent_observation_invalid')
    inp={k:copy.deepcopy(source[k]) for k in ('market','venue','source_item','symbol_group','price_band','as_of')}
    proof=project_signal(event)
    inp.update(schema=VERSION,context='Machine-observed signal; auxiliary only, no order authority.',
        objective=dict(net_target_pct=.4,net_soft_stop_pct=-3.,horizon_seconds=1800,cost_rate=.0023),
        signal_kind=phase,observed_signal=proof,
        observation_phase=dict(stage=phase,rolling_windows_end='AT_CONFIRMATION',post_trigger_observations='OBSERVED_THROUGH_CONFIRMATION'),
        mechanistic_entry_assessment=dict(action='ENTER_NOW',machine_signal_confirmed=True,signal_kind=phase,basis='observed_native_signal'),
        entry_setup_evidence_v1=dict(setup_state='READY',source_quality='price_and_entry_quote_valid',facts=facts,
            positive_facts=positive,context_facts=contexts,contradicting_facts=adverse,risk_fact_bindings=bindings,
            optional_missing=[k for k,v in facts.items() if v is None]),recent_observed_prices=prices,
        runtime_effect=False,allowed_runtime_apply=False,actual_order_submitted=False)
    if arm in V1.ARMS[2:]:
        ask,trade=facts['entry_ask'],facts['confirmation_price']
        inp['entry_geometry']=dict(target_price=ask*1.004/.9977,soft_stop_price=ask*.97/.9977,
            ask_premium_to_trade_pct=100*(ask/trade-1),target_gap_from_trade_pct=100*(ask*1.004/.9977/trade-1))
    schema=V1.response_schema(inp,complete_source_only=arm==V1.ARMS[-1]);schema['properties']['risk_codes']['minItems']=1
    return inp,prompt(phase,arm),schema


def validate_response(response,inp,*,arm,phase):
    if phase in {FIRST,CONFIRMED}:return OLD.validate_response(response,inp,arm=arm,phase=phase)
    if phase not in PHASES or inp.get('signal_kind')!=phase or inp.get('observation_phase',{}).get('stage')!=phase:return ['path_response_phase_mismatch']
    # The six-field shape and non-PASS bindings are unchanged. Only the
    # support fact is typed; no invented first uptick is injected for validation.
    schema=V1.response_schema(inp,complete_source_only=arm==V1.ARMS[-1])
    if not isinstance(response,dict) or set(response)!=set(schema['required']):return ['response_schema_invalid']
    for key,rule in schema['properties'].items():
        v=response[key]
        if rule['type']=='string' and v not in rule['enum']:return ['response_schema_invalid']
        if rule['type']=='integer' and (type(v) is not int or not 0<=v<=100):return ['response_schema_invalid']
        if rule['type']=='array' and (not isinstance(v,list) or any(x not in rule['items'].get('enum',[]) for x in v)):return ['response_schema_invalid']
    if response['risk_verdict']=='PASS':
        return [] if response['risk_codes']==['NO_BLOCKING_RISK'] and 'observed_machine_signal' in response['supporting_fact_ids'] else ['path_pass_support_invalid']
    if response['risk_verdict']=='INSUFFICIENT':return ['essential_source_gap_not_supplied']
    bindings=inp['entry_setup_evidence_v1']['risk_fact_bindings'];contrary=set(response['contradicting_fact_ids'])
    return [] if response['risk_codes'] and all(c in bindings and contrary.intersection(bindings[c]) for c in response['risk_codes']) else ['nonpass_risk_unbound']
