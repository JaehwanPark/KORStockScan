"""Bounded, offline Samsung absorption differential study on sealed captures.

Five predeclared filters. Unknown extra conditions inherit the absorption action.
No optimization grid, acquisition, publication, execution or realized PnL claims.
"""
from bisect import bisect_right
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from statistics import mean, median
import argparse
import gzip
import json
import math

from src.engine.scalping import entry_strategy_policy as S
from src.engine.scalping import entry_admission_analysis as H
from src.engine.scalping import entry_flat_buy_flow_research as F
from src.engine.scalping import entry_first_signal_exit_research as E
from src.engine.scalping import entry_observation_recipe_policy as R
from src.engine.scalping import samsung_absorption_acceptance_research as A

IDS = ('H1', 'H2', 'H3', 'H4', 'H12')
AUTHORITY = dict(runtime_effect=False, allowed_runtime_apply=False, actual_order_submitted=False,
    policy_selected=False, provider_calls=0, pristine_holdout=False,
    metric_role='cost_bound_price_path_diagnostic', realized_profit_claimed=False)


def number(value):
    return float(value) if type(value) in (int,float) and math.isfinite(value) else None


def timestamp(value):
    try:
        stamp = datetime.fromisoformat(value)
        return stamp.timestamp() if stamp.tzinfo is not None else None
    except (ValueError,TypeError):
        return None


def h1(raw, receipt):
    if not F.valid_receipt(raw, receipt):
        return None, 'original_tick_receipt_invalid'
    window = receipt.get('archive_window')
    if not window:
        # Do not infer quantity or aggressor side from summary pressure.
        return None, 'per_trade_quantity_and_direction_unavailable'
    buys = [number(r.get('q')) for r in window if r.get('side') == 'BUY']
    if not buys or any(q is None or q < 0 for q in buys) or sum(buys) <= 0:
        return None, 'positive_trusted_buy_quantity_missing'
    ratio = max(buys) / sum(buys)
    return ratio <= .5, dict(max_buy_share=ratio, receipt_sha256=receipt['receipt_sha256'])


def h2(raw, receipt, previous):
    if not previous or not F.valid_receipt(raw, receipt):
        return None, 'preceding_capture_missing'
    old, old_receipt = previous
    if not F.valid_receipt(old, old_receipt):
        return None, 'preceding_capture_receipt_invalid'
    def epoch_key(proof):
        window=proof.get('archive_window')
        if window:return ('archive',window[-1]['ep'])
        if proof.get('window'):return ('main',proof.get('transport_epoch'))
        return None
    if epoch_key(receipt) is None or epoch_key(receipt) != epoch_key(old_receipt):
        return None, 'capture_epoch_not_comparable'
    elapsed = raw['entry_machine_input_as_of'] - old['entry_machine_input_as_of']
    if not 0 < elapsed <= 5:
        return None, 'preceding_capture_outside_original_tick_ttl'
    current = number(raw.get('features',{}).get('buy_pressure_10t'))
    before = number(old.get('features',{}).get('buy_pressure_10t'))
    if current is None or before is None:
        return None, 'pressure_missing'
    return before < 60 <= current, dict(previous_pressure=before,current_pressure=current,elapsed_sec=elapsed)


def h3(raw, receipt, depth, times):
    cutoff = number(raw.get('entry_machine_input_as_of'))
    if cutoff is None or not F.valid_receipt(raw,receipt):
        return None,'original_clock_or_tick_receipt_invalid'
    window = receipt.get('archive_window')
    if not window:
        return None,'archive_epoch_unavailable'
    i=bisect_right(times,cutoff)
    if i < 2:
        return None,'preceding_quote_missing'
    old,cur=depth[i-2:i]
    start=number((raw.get('mechanistic_micro_window') or {}).get('feature',{}).get('window_started_at_ms'))
    if start is None or not start/1000 <= old['t'] < cur['t'] <= cutoff:
        return None,'preceding_quote_not_bound_to_original_micro_window'
    ttl=number((raw.get('mechanistic_micro_window') or {}).get('market_data_health',{}).get('quote_max_age_ms'))
    if ttl is None or ttl <= 0:
        return None,'original_quote_ttl_missing'
    if (not 0 < cur['t']-old['t'] <= ttl/1000 or not 0 <= cutoff-cur['t'] <= ttl/1000
        or not old.get('valid') or not cur.get('valid') or not cur.get('continuous')
        or old['ep'] != cur['ep'] or cur['ep'] != window[-1]['ep'] or cur['seq'] != old['seq']+1):
        return None,'quote_clock_epoch_or_sequence_gap'
    quote=raw.get('quote') or {}
    if (number(quote.get('best_bid')) != cur['bid'] or number(quote.get('best_ask')) != cur['ask']):
        return None,'archive_current_quote_not_matching_original'
    if any(q['bid'] <= 0 or q['ask'] <= q['bid'] for q in (old,cur)):
        return None,'locked_or_inverted_quote_diagnostic_only'
    return cur['bid'] >= old['bid'] and cur['ask']-cur['bid'] <= old['ask']-old['bid'], dict(
        previous_bid=old['bid'],bid=cur['bid'],previous_spread=old['ask']-old['bid'],
        spread=cur['ask']-cur['bid'],source_epoch=cur['ep'],source_times=[old['t'],cur['t']])


def h4(raw, cost):
    body = (raw.get('entry_candle_context') or {}).get('strategy_completed_bars') or {}
    payload = body.get('body') or {}
    available = timestamp(payload.get('observed_at'))
    cutoff = number(raw.get('entry_machine_input_as_of'))
    if (body.get('sha256') != S.digest(payload) or available is None or cutoff is None
        or available > cutoff or cost is None or cost < 0):
        return None,'asof_completed_bar_receipt_or_cost_missing'
    bars=payload.get('bars') or []
    if len(bars)<5:
        return None,'five_prior_completed_bars_missing'
    selected=bars[-5:];times=[timestamp(b.get('dt')) for b in selected]
    if (any(t is None for t in times) or any(b.get('forming') is not False for b in selected)
        or any(b.get('partial_volume') is not False for b in selected)
        or any(b-a != 60 for a,b in zip(times,times[1:]))
        or times[-1]+60 > available or not 0 <= cutoff-(times[-1]+60) < 60):
        return None,'bar_completion_availability_or_continuity_invalid'
    lows=[number(b.get('l')) for b in selected];highs=[number(b.get('h')) for b in selected]
    if any(x is None or x <= 0 for x in lows+highs) or any(h<l for h,l in zip(highs,lows)):
        return None,'bar_price_invalid'
    value=(max(highs)/min(lows)-1)*100
    return value >= cost+.1,dict(past_range_pct=value,required_pct=cost+.1,available_at=available,
                               bar_end_at=times[-1]+60)


def filtered_action(action, condition):
    if condition not in (True,False,None) or type(condition) not in (bool,type(None)):
        raise ValueError('condition_must_be_boolean_or_unknown')
    return 'RECHECK' if action == 'ENTER_NOW' and condition is False else action


def outcome(row):
    path=row['path'];status=path.get('status');net=number(path.get('net_pct'))
    if status in {'target','stop'}:
        return status
    if status=='timeout' and net is not None:
        return 'complete_timeout_positive' if net>0 else 'complete_timeout_negative' if net<0 else 'complete_timeout_zero'
    return 'source_or_price_gap:' + str(status)


def distribution(values):
    valid=[x for x in values if number(x) is not None]
    return dict(count=len(valid),missing=len(values)-len(valid),minimum=min(valid) if valid else None,
        median=median(valid) if valid else None,maximum=max(valid) if valid else None)


def compare_variants(rows):
    result={}
    for scope,population in [('all_origins',rows),('fixed_watch',[r for r in rows if A.fixed_watch(r)])]:
        scope_result={}
        for key in ('baseline','absorption')+IDS:
            changed=[{**r,'candidate_action':r['parent_action'] if key=='baseline' else r['absorption_action']
                      if key=='absorption' else filtered_action(r['absorption_action'],r['conditions'][key])} for r in population]
            events=E.observed_action_runs(changed,key_function=A._key)
            selected=R.replay(E.mask_first_signals(changed,events),'candidate_action')
            metrics=A.metrics(selected)
            metrics['outcome_counts']=dict(Counter(outcome(r) for r in selected))
            metrics['complete_path_count']=sum(v['complete_path_count'] for v in metrics['by_date'].values())
            metrics['selected_ids']=[r['trace'] for r in selected]
            metrics['source_observation_count']=len(population)
            metrics['unknown_inherited_signal_count']=sum(r['absorption_action']=='ENTER_NOW' and r['conditions'].get(key) is None for r in population) if key in IDS else 0
            metrics['known_condition_count']=sum(r['conditions'].get(key) is not None for r in population) if key in IDS else None
            metrics['path_net_distribution']=distribution([r['path'].get('net_pct') for r in selected])
            complete=[r['path']['net_pct'] for r in selected if number(r['path'].get('net_pct')) is not None]
            metrics['mean_price_cf_diagnostic']=mean(complete) if complete else None
            scope_result[key]=metrics
        result[scope]=scope_result
    return result


def recommend(comparisons):
    results={}
    for scope,arms in comparisons.items():
        eligible=[];details={}
        for key in IDS:
            candidate=arms[key]; metric='positive_path_rate_pct'
            support=candidate['metric_date_support'][metric]
            comparable=(len(support)>=2 and candidate['complete_path_count']>=3 and all(
                arms[a]['metric_date_support'][metric]==support and arms[a]['complete_path_count']>=3 for a in ('baseline','absorption')))
            value=candidate['date_equal_metrics'][metric]
            improved=(comparable and value is not None and all(value-arms[a]['date_equal_metrics'][metric]>1e-9 for a in ('baseline','absorption')))
            details[key]=dict(comparable=comparable,improves_both_controls=bool(improved),
                source_identifiable=candidate['known_condition_count']>0,
                outcome='improves' if improved else 'no_improvement' if comparable else 'not_identifiable')
            if improved and candidate['known_condition_count']>0:eligible.append(key)
        # Predeclared simplicity/order, never an adaptive combination search.
        selected=next((k for k in IDS if k in eligible),None)
        results[scope]=dict(status='recommend_register_for_forward' if selected else
            'no_improvement' if any(v['comparable'] for v in details.values()) else 'not_identifiable',
            candidate_id=selected, hypotheses=details)
    return dict(**AUTHORITY,primary_metric='date_equal_complete_path_positive_rate',scopes=results,
        selection_limit=1, recommended_candidate=results['all_origins']['candidate_id'] or results['fixed_watch']['candidate_id'],
        future_validation_required=True, discovery_dates=['2026-09-29','2026-09-30','2026-10-02'])


def paired_events(rows, originals, price_index):
    def key(row):
        native=row.get('native_provenance')
        watch=tuple(native[4:]) if isinstance(native,list) and len(native)==7 else ('watch_identity_unavailable',row.get('source_lane'))
        return A._key(row)+(row['archive_epoch'],)+watch
    events=E.observed_action_runs(rows,key_function=key)
    by_trace={r['trace']:r for r in rows};result=[]
    for event in events:
        first=event['first_by_arm'];entry=dict(event_id=event['event_id'],first_by_arm=first,
            watch_identity_status='unavailable' if 'watch_identity_unavailable' in event['key'] else 'observed',
            preceding_gap_sec=event['preceding_gap_sec'],max_internal_observation_gap_sec=event['max_internal_observation_gap_sec'],
            status='paired' if len(first)==2 else 'one_arm_only', same_absolute_end=None)
        if len(first)==2:
            old,new=(by_trace[first[k]] for k in ('parent_action','candidate_action'))
            entry['entry_time_delta_sec']=E.epoch(new)-E.epoch(old)
            end=min(E.epoch(old),E.epoch(new))+3600
            diagnostics={}
            for arm,row in [('baseline',old),('absorption',new)]:
                raw=originals[row['trace']];bars=price_index.get((row['day'],'005930','KRX','KRX_REGULAR',row['outcome_request_code']),[])
                duration=end-E.epoch(row)
                clock=H.capture_clock(raw)
                close=clock.replace(hour=15,minute=30,second=0,microsecond=0).timestamp()
                from src.engine.scalping.ai_action_outcome_calibration import _full_entry_cost_pct
                cost=_full_entry_cost_pct(raw['comparison'].get('entry_cost_contract'),source_date=row['day'])
                if duration<=0 or end>close or cost is None or cost!=raw['comparison'].get('conservative_execution_cost_pct'):
                    diagnostics[arm]=dict(status='endpoint_cost_or_session_invalid',endpoint_net_pct=None)
                    continue
                tail=[b for b in bars if E.epoch(row)<b['t']<=end]
                if (not tail or end-tail[-1]['t']>90 or tail[0]['t']-E.epoch(row)>90
                    or any(b['t']-a['t']>90 for a,b in zip(tail,tail[1:]))):
                    diagnostics[arm]=dict(status='endpoint_missing',endpoint_net_pct=None);continue
                quote=raw['setup_evidence']['strategy_raw_input']['quote']
                diagnostics[arm]=dict(status='observed',endpoint_net_pct=(tail[-1]['close']/quote['best_ask']-1)*100-cost,
                    entry_at=E.epoch(row),terminal_at=tail[-1]['t'],price_role='endpoint_diagnostic_does_not_replace_barriers')
            entry['same_absolute_end']=dict(at=end,arms=diagnostics)
        result.append(entry)
    return result


def run(request_path, observation_path, output):
    from src.engine.scalping.entry_policy_hypothesis_research import stream_array
    from src.engine.scalping.ai_action_outcome_calibration import _full_entry_cost_pct
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    request=json.loads(Path(request_path).read_text());source=json.loads(Path(observation_path).read_text())
    seals={str(Path(request_path).resolve()):H.file_sha(request_path),str(Path(observation_path).resolve()):H.file_sha(observation_path),
           str(Path(__file__).resolve()):H.file_sha(__file__)}
    originals={};proofs={};archives={}
    for item in request['files']:
        path=Path(item['path'])
        if H.file_sha(path)!=item['sha256']:raise ValueError('research_source_changed:'+str(path))
        seals[str(path)]=item['sha256']
        if item['role']=='capture':
            for row in stream_array(path):
                if row.get('stock_code')=='005930':
                    trace=row['decision_trace_id']
                    if trace in originals:raise ValueError('duplicate_source_trace')
                    originals[trace]=row
        elif item['role']=='samsung_receipt':
            proofs={r['trace']:r['source_receipt'] for r in json.loads(path.read_text())}
        elif 'locked-source/' in str(path):
            with gzip.open(path,'rt') as f:data=json.load(f)
            archives[data['day']]=data
    rows=[];previous={}
    for observation in sorted((r for r in source['observations'] if r['group']=='samsung'),key=lambda r:(r['ts'],r['trace'])):
        row=deepcopy(observation);original=originals[row['trace']];raw=original['setup_evidence']['strategy_raw_input'];proof=proofs[row['trace']]
        if (S.digest(raw)!=row['raw_sha256']
            or F.valid_receipt(raw,proof) is not row['evaluator_receipt']['source_valid']):
            raise ValueError('research_original_binding_invalid')
        H.capture_clock(original)
        archive=archives[row['day']]
        # The original receipt seals this independent collector; epoch domains
        # are never relabelled as the Main runtime epoch.
        if proof['archive_sha256'] != next(i['sha256'] for i in request['files'] if 'locked-source/'+row['day'] in i['path']):
            raise ValueError('research_archive_receipt_hash_invalid')
        ep=proof['archive_window'][-1]['ep'] if proof.get('archive_window') else None;key=(row['day'],row['outcome_request_code'],ep)
        depth=archive['depth'];times=[q['t'] for q in depth]
        cost=_full_entry_cost_pct(original['comparison'].get('entry_cost_contract'),source_date=row['day'])
        conditions={'H1':h1(raw,proof),'H2':h2(raw,proof,previous.get(key)),
                    'H3':h3(raw,proof,depth,times),'H4':h4(raw,cost)}
        values={k:v[0] for k,v in conditions.items()}
        values['H12']=None if values['H1'] is None or values['H2'] is None else values['H1'] and values['H2']
        row.update(conditions=values,condition_evidence={k:v[1] for k,v in conditions.items()},
                   absorption_action=row['candidate_action'],archive_epoch=ep)
        features=raw.get('features') or {};quote=raw.get('quote') or {}
        row['features']={k:features.get(k) for k in ('buy_pressure_10t','net_aggressive_delta_10t','tick_aggressor_trusted_count',
            'price_change_10t_pct','curr_vs_micro_vwap_bp','spread_bp','distance_from_day_high_pct')}
        row['environment']={}
        snapshot=raw.get('ai_market_snapshot_v1') or {}
        for name in ('program','investor'):
            context=(snapshot.get('sources') or {}).get(name) or {}
            observed=timestamp(context.get('observed_at'));ttl=number(context.get('freshness_limit_ms'))
            fresh=(context.get('quality')=='fresh' and observed is not None and ttl is not None
                and 0 <= (raw['entry_machine_input_as_of']-observed)*1000 <= ttl
                and context.get('market_route')==(raw.get('entry_candle_context') or {}).get('ws_route'))
            row['environment'][name]=dict(eligible=fresh,quality=context.get('quality'),
                source=context.get('source'),missing_reason=context.get('missing_reason'),
                value=context.get('value') if fresh else None)
        row['features'].update(best_bid=quote.get('best_bid'),best_ask=quote.get('best_ask'),cost_pct=cost,
            stop_distance_pct=original.get('outcome_stop_distance_pct'))
        row['absorption_receipt_valid']=F.valid_receipt(raw,proof)
        rows.append(row);previous[key]=(raw,proof)
    if len(rows)!=519 or len({r['trace'] for r in rows})!=519:raise ValueError('research_frozen_population_changed')
    comparisons=compare_variants(rows);recommendation=recommend(comparisons)
    census={scope:{day:{action:dict(Counter(outcome(r) for r in population if r['day']==day and r['parent_action']==action))
        for action in ('ENTER_NOW','BLOCK','RECHECK')} for day in sorted({r['day'] for r in population})}
        for scope,population in [('all_origins',rows),('fixed_watch',[r for r in rows if A.fixed_watch(r)])]}
    differences={day:{label:{key:distribution([r['features'][key] for r in rows if r['day']==day and outcome(r)==label])
        for key in rows[0]['features']} for label in sorted({outcome(r) for r in rows if r['day']==day})}
        for day in sorted({r['day'] for r in rows})}
    environments={day:{label:{name:dict(eligible_count=sum(r['environment'][name]['eligible'] for r in rows if r['day']==day and outcome(r)==label),
        source_states=dict(Counter(str(r['environment'][name]['quality']) for r in rows if r['day']==day and outcome(r)==label)),
        values=[r['environment'][name]['value'] for r in rows if r['day']==day and outcome(r)==label and r['environment'][name]['eligible']])
        for name in ('program','investor')} for label in sorted({outcome(r) for r in rows if r['day']==day})}
        for day in sorted({r['day'] for r in rows})}
    registry={key:dict(classification='new_conditional_application',conditions=dict(Counter(str(r['conditions'][key]) for r in rows)),
        on_absorption_enter=dict(Counter(str(r['conditions'][key]) for r in rows if r['absorption_action']=='ENTER_NOW')),
        unknown_reasons=dict(Counter(str(r['condition_evidence'].get(key)) for r in rows if r['conditions'][key] is None))) for key in IDS}
    registry['H4']['prior_distinction']='Prior research used 900-second range and fixed 0.33%; this uses original 5 completed bars and original cost + 0.1%.'
    # Data root is explicitly inferred from the sealed canonical price path.
    price_path=next(Path(i['path']) for i in request['files'] if 'machine_completed_price_source_' in i['path'])
    data_root=price_path.parents[2]
    index,price_sources,_=H.price_index(data_root,sorted({r['day'] for r in rows}))
    paired=paired_events(rows,originals,index)
    sensitivity={day:recommend(compare_variants([r for r in rows if r['day']!=day])) for day in sorted({r['day'] for r in rows})}
    outputs={'source-manifest':dict(seals=seals,rows=len(rows),fixed_watch=sum(A.fixed_watch(r) for r in rows),
        original_native_count=sum(r['native_provenance'] is not None for r in rows),
        unique_native_count=len({tuple(r['native_provenance']) for r in rows if r['native_provenance'] is not None}),
        absorption_exact_tick_receipt_counts=dict(Counter(str(r['absorption_receipt_valid']) for r in rows)),
        source_clock_coverage={day:dict(first=min(r['ts'] for r in rows if r['day']==day),last=max(r['ts'] for r in rows if r['day']==day)) for day in sorted({r['day'] for r in rows})},
        source_dates=sorted({r['day'] for r in rows}),
        historical_compressed_bytes_recovered=False),
        'hypothesis-registry':registry,'outcome-census':census,'feature-differences':dict(numeric=differences,environment=environments),
        'paired-events':dict(events=paired,counts=dict(Counter(r['status'] for r in paired))),
        'comparisons':dict(arms=comparisons,leave_one_date_out=sensitivity,not_independent_holdouts=True),
        'recommendation':recommendation,'observations':dict(rows=rows),
        'validation':dict(input_hashes_unchanged=all(H.file_sha(p)==sha for p,sha in seals.items()),
            rows=519,scope_guard=True,maximum_policies=7,variants=list(IDS),outcome_not_used_for_conditions=True,
            unknown_inherits_absorption=True,raw_and_receipt_binding=True)}
    for name,value in outputs.items():A.write(output/(name+'.json'),dict(**AUTHORITY,result=value))
    return recommendation



def candidate_kernels():
    from src.engine.scalping import samsung_policy_compatibility as compatibility
    return {**A.kernels(), Path(__file__).name:H.file_sha(__file__),
            Path(compatibility.__file__).name:H.file_sha(compatibility.__file__)}


def freeze_candidate(recommendation, evidence, base_frozen):
    if recommendation.get('recommended_candidate') != 'H2':
        raise ValueError('only_reviewed_H2_forward_adapter_registered')
    return A.seal(dict(schema='samsung_absorption_differential_frozen_v1',**AUTHORITY,
        candidate_id='absorption_p60_v10_H2', rule='previous_valid_same_epoch_pressure_lt60_then_ge60_within_5s',
        unknown_action='absorption_action', known_fail_action='RECHECK',
        parent_policy=base_frozen['parent_policy'],parent_sha256=base_frozen['parent_sha256'],
        base_frozen_sha256=S.digest(base_frozen), kernel_manifest=candidate_kernels(),
        recommendation_scope='all_origins', fixed_watch_improvement_observed=False,
        later_source_after_date='2026-10-05',pristine_holdout_dates=[],
        primary_metric='date_equal_complete_path_positive_rate',
        evidence=[dict(path=str(Path(p).resolve()),sha256=H.file_sha(p)) for p in evidence]))


def prepare_forward(root, day, frozen, base_frozen):
    from src.engine.scalping.entry_policy_hypothesis_research import stream_array
    if (frozen != A.seal(frozen) or frozen.get('schema') != 'samsung_absorption_differential_frozen_v1'
        or frozen.get('candidate_id') != 'absorption_p60_v10_H2'
        or frozen.get('rule') != 'previous_valid_same_epoch_pressure_lt60_then_ge60_within_5s'
        or frozen.get('unknown_action') != 'absorption_action' or frozen.get('known_fail_action') != 'RECHECK'
        or frozen.get('kernel_manifest') != candidate_kernels()
        or frozen.get('base_frozen_sha256') != S.digest(base_frozen)
        or day <= frozen['later_source_after_date']
        or any(H.file_sha(v['path']) != v['sha256'] for v in frozen['evidence'])):
        raise ValueError('samsung_H2_frozen_or_date_changed')
    intake=A.prepare(root,day,base_frozen)
    if intake['status'] != 'evaluated':
        return A.seal(dict(**AUTHORITY,status=intake['status'],candidate_id=frozen['candidate_id'],
            frozen_sha256=frozen['artifact_content_sha256'],base_intake=intake))
    capture=next(Path(p) for p in intake['source_seals'] if 'machine_observation_projection_' in p)
    originals={r['decision_trace_id']:r for r in stream_array(capture) if r.get('stock_code')=='005930'}
    rows=[];previous={}
    for item in sorted(intake['observations'],key=lambda r:(r['ts'],r['trace'])):
        raw=originals[item['trace']]['setup_evidence']['strategy_raw_input']
        proof=raw.get('entry_machine_observation_receipt') or {}
        key=(item['day'],item['outcome_request_code'],proof.get('transport_epoch'))
        condition,receipt=h2(raw,proof,previous.get(key))
        rows.append(dict(item,absorption_action=item['candidate_action'],conditions={'H2':condition},condition_evidence=receipt,
            candidate_action=filtered_action(item['candidate_action'],condition)))
        previous[key]=(raw,proof)
    arms={}
    for key in ('parent_action','absorption_action','candidate_action'):
        modified=[dict(r,candidate_action=r[key]) for r in rows]
        events=E.observed_action_runs(modified,key_function=A._key)
        arms[key]=A.metrics(R.replay(E.mask_first_signals(modified,events),'candidate_action'))
    if H.file_sha(capture)!=intake['source_seals'][str(capture)]:raise ValueError('samsung_H2_source_changed')
    return A.seal(dict(**AUTHORITY,status='evaluated',candidate_id=frozen['candidate_id'],day=day,
        frozen_sha256=frozen['artifact_content_sha256'],source_seals=intake['source_seals'],exclusions=intake['exclusions'],
        conditions=dict(Counter(str(r['conditions']['H2']) for r in rows)),rows=rows,comparison=arms,
        candidate_reselection=False,policy_publication=False))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request',type=Path);parser.add_argument('--observations',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--forward-frozen',type=Path);parser.add_argument('--base-frozen',type=Path)
    parser.add_argument('--date');parser.add_argument('--root',type=Path,default=Path.cwd())
    args=parser.parse_args()
    if args.forward_frozen:
        if not args.base_frozen or not args.date or args.request or args.observations:
            parser.error('--forward-frozen requires --base-frozen and --date only')
        result=prepare_forward(args.root,args.date,json.loads(args.forward_frozen.read_text()),json.loads(args.base_frozen.read_text()))
        A.write(args.output,result);print(json.dumps(dict(status=result['status'],output=str(args.output))))
    else:
        if not args.request or not args.observations or args.base_frozen or args.date:
            parser.error('historical research requires --request and --observations')
        print(json.dumps(run(args.request,args.observations,args.output)))


if __name__=='__main__':main()
