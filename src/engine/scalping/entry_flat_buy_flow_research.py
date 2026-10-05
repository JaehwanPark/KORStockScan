"""Unregistered Samsung machine recipe using explicit per-fact counterweights.

Report-only caller surface. No production policy registration or publisher.
The proposed action is separate from the unchanged parent machine action.
"""
from copy import deepcopy

from src.engine.scalping import entry_setup_evidence as E
from src.engine.scalping import entry_strategy_policy as S
from src.engine.scalping.entry_machine_observation import digest, number, SCHEMA

RECIPE = 'samsung_flat_buy_flow_report_v1'
HISTORICAL_SCHEMA = 'samsung_flat_buy_flow_historical_receipt_v1'
ALLOWED_FACTS = {
    'ADVERSE_TAPE': {'supportive_micro_tape_vs_program_net_sell',
                     'program_flow_net_and_delta_sell', 'foreign_institutional_joint_sell'},
    'CONFIRMATION_MISSING': {'trigger_confirmation_missing', 'no_supported_setup'},
}
AUTHORITY = dict(runtime_effect=False, allowed_runtime_apply=False, actual_order_submitted=False,
    policy_selected=False, registered_runtime_policy=False,
    decision_authority='offline_machine_recipe_proposal', metric_role='main_entry_win_rate_selection',
    window_policy='frozen_exact_source_cutoff_and_parent', sample_floor='source_receipt_not_promotion',
    primary_decision_metric='cost_bound_target_before_stop', source_quality_gate='hash_bound_asof_source',
    forbidden_uses=['runtime_apply','policy_publication','order_submission','realized_profit'])


def _valid_receipt(raw, receipt):
    """A self hash alone never substitutes for raw-payload and scope binding."""
    if not isinstance(receipt, dict):
        return False
    window = receipt.get('window')
    source_route = receipt.get('source_route')
    route_items = {'KRX|krx_only': '005930',
                   '_AL|krx_nxt_integrated': '005930_AL'}
    if (not isinstance(window, list) or len(window) != 10
            or any(not isinstance(t, dict) for t in window)
            or not isinstance(source_route, str) or source_route not in route_items
            or receipt.get('source_item') != route_items[source_route]):
        return False
    route = source_route.split('|', 1)[1]
    return bool(isinstance(receipt,dict) and receipt.get('schema') == SCHEMA
        and receipt.get('receipt_sha256') == digest({k:v for k,v in receipt.items() if k!='receipt_sha256'})
        and receipt.get('payload_sha256') == digest({k:v for k,v in raw.items() if k!='entry_machine_observation_receipt'})
        and receipt.get('usable') is True and receipt.get('allowed_runtime_apply') is False
        and receipt.get('runtime_effect') is False
        and number(receipt.get('cutoff')) is not None
        and receipt.get('window_sha256') == digest(receipt.get('window'))
        and receipt.get('scope_ok') is True and receipt.get('clock_ok') is True
        and receipt.get('sequence_ok') is True
        and receipt.get('feature_source') == 'ws_exact_route'
        and len(receipt.get('window') or []) == 10
        and type(receipt.get('transport_epoch')) is int
        and receipt['transport_epoch'] > 0
        and all(type(t.get('route_sequence')) is int for t in receipt['window'])
        and all(a['route_sequence']==b['route_sequence']+1 for a,b in zip(receipt['window'],receipt['window'][1:]))
        and all(number(t.get('received_at_ms')) is not None
                and 0 <= receipt['cutoff']*1000-t['received_at_ms']
                and t.get('item') == receipt.get('source_item')
                and t.get('market_route') == route
                and type(t.get('transport_epoch')) is int
                and t.get('transport_epoch') == receipt.get('transport_epoch')
                for t in receipt['window'])
        and all(a['received_at_ms'] >= b['received_at_ms']
                for a,b in zip(window,window[1:]))
        and receipt['cutoff']*1000-receipt['window'][0]['received_at_ms'] <= 5000
        and all(receipt.get('observed_values',{}).get(k)==(raw.get('features') or {}).get(k)
                for k in ('buy_pressure_10t','net_aggressive_delta_10t','price_change_10t_pct',
                          'curr_vs_micro_vwap_bp','micro_vwap_available'))
        and all(receipt.get(k)==raw.get(k) for k in ('stock_code','effective_venue','session_bucket'))
        and number(receipt.get('cutoff')) is not None
        and number(raw.get('entry_machine_input_as_of')) is not None
        and abs(receipt['cutoff']-raw['entry_machine_input_as_of']) <= .001
        and receipt.get('source_item') in {'005930','005930_AL'})


def valid_receipt(raw, receipt):
    try:
        if isinstance(receipt,dict) and receipt.get('schema') == HISTORICAL_SCHEMA:
            rebuilt=historical_receipt(raw,receipt['archive_window'],
                archive_sha256=receipt['archive_sha256'], window_cutoff=receipt['window_cutoff'])
            return receipt == rebuilt and receipt['usable'] is True
        return _valid_receipt(raw,receipt)
    except (KeyError,TypeError,ValueError,OverflowError):
        return False


def historical_receipt(raw, window, *, archive_sha256, window_cutoff):
    """Explicit cross-collector corroboration; no synthesized Main tick identity."""
    cutoff=number(raw.get('entry_machine_input_as_of'))
    valid_hash=(isinstance(archive_sha256,str) and len(archive_sha256)==64
                and all(c in '0123456789abcdef' for c in archive_sha256))
    valid=bool(cutoff is not None and number(window_cutoff) is not None and window_cutoff<=cutoff
        and (raw.get('entry_candle_context') or {}).get('request_code')=='005930_AL'
        and (raw.get('entry_candle_context') or {}).get('ws_route')=='krx_nxt_integrated'
        and valid_hash and isinstance(window,list) and len(window)==10
        and all(isinstance(r,dict) and r.get('valid') is True and r.get('flow_valid') is True
            and r.get('continuous') is True and number(r.get('t')) is not None and r['t']<=window_cutoff
            and number(r.get('p')) is not None and r['p']>0 and number(r.get('q')) is not None and r['q']>=0
            and r.get('side') in ('BUY','SELL') and type(r.get('ep')) is int and type(r.get('seq')) is int for r in window)
        and len({r['ep'] for r in window})==1
        and all(b['seq']==a['seq']+1 and b['t']>=a['t'] for a,b in zip(window,window[1:]))
        and 0<=cutoff-window[-1]['t']<=5)
    values=None
    if valid:
        buy=sum(r['q'] for r in window if r['side']=='BUY');sell=sum(r['q'] for r in window if r['side']=='SELL')
        if buy+sell>0:
            values=dict(buy_pressure_10t=round(100*buy/(buy+sell),2),net_aggressive_delta_10t=buy-sell,
                price_change_10t_pct=round(100*(window[-1]['p']-window[0]['p'])/window[0]['p'],3))
        valid=bool(values and all(number((raw.get('features') or {}).get(k)) is not None
            and abs(raw['features'][k]-v)<1e-8 for k,v in values.items()))
    body=dict(schema=HISTORICAL_SCHEMA,payload_sha256=digest(raw),cutoff=cutoff,
        window_cutoff=window_cutoff,archive_sha256=archive_sha256,archive_window=deepcopy(window),
        source_scope='005930_AL/SOR/SOR_REGULAR',source_epoch_domain='independent_archive_collector',
        main_epoch_equivalence=False,native_promotion_support=False,observed_values=values,usable=valid,
        runtime_effect=False,allowed_runtime_apply=False,actual_order_submitted=False)
    body['receipt_sha256']=digest(body)
    return body


def evaluate(setup, parent, *, source_receipt=None, admission_mode='augment'):
    """Preserve every parent risk fact; express a different bounded setup.

    Only the frozen flat-buy-flow condition is hypothesized to compensate the
    enumerated soft tape/trigger facts. Liquidity, hard facts, selected micro
    recipes and situation vetoes remain unresolved vetoes to the proposal.
    """
    if admission_mode not in {'augment','replace'}:
        raise ValueError('flat_buy_flow_admission_mode_invalid')
    baseline = E.mechanistic_entry_policy_decision(setup, policy=parent)
    rebuilt, effective, receipt = S.rebuild(setup,parent)
    raw = setup.get('strategy_raw_input') or {}
    f = raw.get('features') or {}
    values = [number(f.get(k)) for k in ('buy_pressure_10t','net_aggressive_delta_10t',
                                        'price_change_10t_pct','curr_vs_micro_vwap_bp')]
    scope = (raw.get('stock_code'),str(raw.get('effective_venue') or '').upper(),
             str(raw.get('session_bucket') or '').upper()) == ('005930','KRX','KRX_REGULAR')
    condition = bool(scope and all(v is not None for v in values)
        and values[0]>=60 and values[1]>0 and values[2]==0 and values[3]<=10
        and f.get('micro_vwap_available') is True
        and f.get('tick_aggressor_pressure_usable') is True
        and f.get('tick_aggressor_trusted_count')==10
        and f.get('tick_context_stale') is False and f.get('quote_stale') is False)
    source = source_receipt or raw.get('entry_machine_observation_receipt') or {}
    source_ok = valid_receipt(raw,source)
    bindings = E.entry_action_counterweight_bindings(rebuilt)['bindings']
    ledger=[]
    for group in bindings:
        for fact in group['risk_fact_ids']:
            existing = bool(group['required_counterweight_fact_ids'])
            proposed = bool(condition and source_ok and fact in ALLOWED_FACTS.get(group['risk_code'],set()))
            ledger.append(dict(risk_code=group['risk_code'],fact_id=fact,
                parent_counterweights=deepcopy(group['required_counterweight_fact_ids']),
                proposed_counterweights=['flat_price_buy_flow'] if proposed and not existing else [],
                resolved=existing or proposed))
    reasons=[]
    if not scope: reasons.append('scope_parent_inherited')
    if not condition: reasons.append('frozen_condition_not_met')
    if not source_ok: reasons.append('exact_observation_receipt_missing_or_invalid')
    if baseline['action']=='BLOCK': reasons.append('parent_block_preserved')
    if rebuilt.get('invalidation_facts'): reasons.append('invalidation_preserved')
    if baseline.get('liquidity_inputs_complete') is not True or baseline.get('liquidity_threshold_pass') is not True:
        reasons.append('parent_liquidity_guard_preserved')
    if receipt['effective_thresholds']['micro_confirmation_recipe'] != 0:
        reasons.append('parent_micro_recipe_preserved')
    if any(not r['resolved'] for r in ledger):reasons.append('unresolved_risk_facts')
    proposed=baseline['action']
    if admission_mode=='replace' and scope and proposed=='ENTER_NOW' and reasons:
        proposed='RECHECK'
    if baseline['action']=='RECHECK' and not reasons:
        proposed='ENTER_NOW'
        # A new family replaces the setup hypothesis; the old local-breakout
        # fact remains visible and is never falsely marked confirmed.
        veto=E._apply_entry_situation_veto({**baseline,'action':proposed},setup,parent)
        proposed=veto['action']
        if proposed!='ENTER_NOW':reasons.append('parent_situation_veto_preserved')
    return dict(**AUTHORITY,recipe=RECIPE,admission_mode=admission_mode,parent_sha256=S.digest(parent),
        original_raw_sha256=setup.get('strategy_raw_sha256'),parent_action=baseline['action'],
        proposed_action=proposed,changed=proposed!=baseline['action'],condition_match=condition,
        source_valid=source_ok,unresolved_reasons=reasons,fact_ledger=ledger,
        proposed_setup_family='FLAT_PRICE_BUY_FLOW' if condition and source_ok else None,
        original_setup_family=rebuilt.get('setup_family'),original_setup_state=rebuilt.get('setup_state'),
        original_local_breakout=deepcopy(rebuilt.get('local_breakout')),
        original_micro_price_response=(rebuilt.get('micro_recovery_observation') or {}).get('price_response'),
        local_breakout_replaced_by_distinct_setup=bool(proposed=='ENTER_NOW' and baseline['action']=='RECHECK'
            and (rebuilt.get('local_breakout') or {}).get('recheck_required')))
