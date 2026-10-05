from copy import deepcopy
import pytest
from src.engine.scalping import entry_pullback_buy_flow_research as R


def case(monkeypatch, *, action='RECHECK', fact='trigger_confirmation_missing',
         code='CONFIRMATION_MISSING', disposition='RECHECKABLE'):
    raw=dict(stock_code='000660', effective_venue='KRX', session_bucket='krx_regular',
        features=dict(buy_pressure_10t=65, net_aggressive_delta_10t=10,
            curr_vs_micro_vwap_bp=-5, tick_aggressor_trusted_count=10,
            tick_aggressor_pressure_usable=True, tick_context_stale=False,
            quote_stale=False, micro_vwap_available=True))
    setup=dict(strategy_raw_input=raw, strategy_raw_sha256=R.S.digest(raw),
        source_quality=dict(status='fresh_consistent'),
        local_breakout=dict(recheck_required=True))
    decision=dict(action=action, reason='original', liquidity_inputs_complete=True,
        liquidity_threshold_pass=True, core_comparison=dict(risk_assessments=[
            dict(fact_id=fact, risk_code=code, disposition=disposition)]))
    monkeypatch.setattr(R.E,'mechanistic_entry_policy_decision',lambda *a,**kw:deepcopy(decision))
    monkeypatch.setattr(R.E,'_apply_entry_situation_veto',lambda d,*a:d)
    return setup,decision


def test_distinct_setup_does_not_fabricate_old_breakout(monkeypatch):
    setup,_=case(monkeypatch);before=deepcopy(setup)
    result=R.evaluate(setup,{})
    assert result['proposed_action']=='ENTER_NOW'
    assert result['original_local_breakout']['recheck_required'] is True
    assert result['fact_ledger'][0]['original']['fact_id']=='trigger_confirmation_missing'
    assert setup==before and result['allowed_runtime_apply'] is False


@pytest.mark.parametrize('code,fact,disposition',[
    ('ADVERSE_TAPE','supportive_micro_tape_vs_program_net_sell','RECHECKABLE'),
    ('LIQUIDITY_FRAGILE','liquidity_adverse','RECHECKABLE'),
    ('CONFIRMATION_MISSING','unknown_confirmation','RECHECKABLE'),
    ('CONFIRMATION_MISSING','trigger_confirmation_missing','BLOCK')])
def test_only_named_soft_confirmations_can_resolve(monkeypatch,code,fact,disposition):
    setup,_=case(monkeypatch,code=code,fact=fact,disposition=disposition)
    assert R.evaluate(setup,{})['proposed_action']=='RECHECK'


@pytest.mark.parametrize('guard',['BLOCK','liquidity','source','invalidation','micro','situation'])
def test_parent_guards_survive(monkeypatch,guard):
    setup,decision=case(monkeypatch)
    if guard=='BLOCK':decision['action']='BLOCK'
    elif guard=='liquidity':decision['liquidity_threshold_pass']=False
    elif guard=='source':setup['source_quality']['status']='missing'
    elif guard=='invalidation':setup['invalidation_facts']=['hard_source']
    elif guard=='micro':decision['strategy_selection']=dict(effective_thresholds=dict(micro_confirmation_recipe=1))
    elif guard=='situation':monkeypatch.setattr(R.E,'_apply_entry_situation_veto',lambda d,*a:{**d,'action':'BLOCK'})
    assert R.evaluate(setup,{})['proposed_action']!='ENTER_NOW'


def test_existing_enter_can_be_removed_without_success_retention(monkeypatch):
    setup,_=case(monkeypatch,action='ENTER_NOW',disposition='COMPENSATED')
    setup['strategy_raw_input']['features']['buy_pressure_10t']=50
    setup['strategy_raw_sha256']=R.S.digest(setup['strategy_raw_input'])
    assert R.evaluate(setup,{})['proposed_action']=='RECHECK'


@pytest.mark.parametrize('field,value',[('stock_code','005930'),('session_bucket','NXT_AFTERMARKET'),('effective_venue','NXT')])
def test_other_scopes_inherit_parent(monkeypatch,field,value):
    setup,_=case(monkeypatch,action='ENTER_NOW')
    setup['strategy_raw_input'][field]=value
    setup['strategy_raw_sha256']=R.S.digest(setup['strategy_raw_input'])
    assert R.evaluate(setup,{})['proposed_action']=='ENTER_NOW'


def test_invalid_raw_and_live_policy_are_rejected(monkeypatch):
    setup,_=case(monkeypatch);setup['strategy_raw_input']['features']['buy_pressure_10t']=99
    with pytest.raises(ValueError,match='raw_capture_invalid'):R.evaluate(setup,{})
    assert R.E.validate_mechanistic_entry_threshold_policy(R.AUTHORITY)
