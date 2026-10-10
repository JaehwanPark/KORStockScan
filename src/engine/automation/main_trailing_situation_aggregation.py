"""External registered-type research using the single global purged split.

The grid and numeric candidates are fixed before holdout. No runtime authority
is added; qualified cells still require the existing family selector.
"""
from datetime import datetime
import json
import math
from zoneinfo import ZoneInfo

from src.engine.lifecycle import research_storage as storage
from src.engine.scalping.pre_submit_delay_initial_policy import digest, number
from src.engine.scalping.trailing_situation_policy import (
    TYPES, START_MARKETS, validate_classifier, pin_context, validate_pin,
)
from src.engine.scalping.trailing_mechanical_policy import classifier_hash, normalize_values
from src.engine.scalping.trailing_threshold_policy import market_type_at


def research(partitions, *, grid, candidates, parent_values, parent_classifier_parameters,
             evaluation, output_root):
    if not grid:
        return {'schema':'main_trailing_situation_research_v1','status':'grid_not_registered',
                'classifier':None,'cells':{},'allowed_runtime_apply':False}
    if not isinstance(grid,list) or not 1<=len(grid)<=16:
        raise ValueError('trailing_situation_registered_grid_budget_invalid')
    grid=[validate_classifier(dict(g)) for g in grid]
    if any(g['trained_through']!=0 for g in grid) or len({g['classifier_sha256'] for g in grid})!=len(grid):
        raise ValueError('trailing_situation_grid_invalid')
    parent_m1=classifier_hash(parent_classifier_parameters)
    eligible={'incumbent':{m:normalize_values(parent_values[m]) for m in START_MARKETS}}
    rejected=[]
    for name,item in candidates.items():
        config=item.get('classifier_parameters') if 'market_values' in item else None
        if classifier_hash(config)!=parent_m1: rejected.append(name);continue
        values=item.get('market_values',item)
        eligible[name]={m:normalize_values(values[m]) for m in START_MARKETS}
    strata=evaluation.get('strata') or {}
    training_kind=next((kind for kind in ('actual_completed','actual_entry_alternative_exit','enter_pass_opportunity_cf')
        if ((strata.get(kind) or {}).get('train_ids_ref') or {}).get('count')),None)
    if training_kind is None:
        return {'schema':'main_trailing_situation_research_v1','status':'hold_sample_or_source',
                'classifier':None,'grid_sha256':digest(grid),'cells':{},'allowed_runtime_apply':False}
    with storage.index(output_root) as db:
        for part in partitions():
            for identity,context in part['population_context'].items():
                value={'context':context,'outcomes':{n:part['minimal_results'][identity][part['candidate_aliases'][n]]
                    for n in eligible}}
                value=storage.compact_outcomes(output_root,value)
                storage.put(db,identity,value,content_sha=digest(storage.logical_value(value)))
        db.execute('CREATE TABLE membership(id TEXT PRIMARY KEY,evidence TEXT,split TEXT,market TEXT,kind TEXT) WITHOUT ROWID')
        db.execute('CREATE TABLE outcomes(id TEXT,candidate TEXT,body TEXT,PRIMARY KEY(id,candidate)) WITHOUT ROWID')
        from src.engine.lifecycle.research_input_budget import Claim
        for identity,value,_ in storage.records(db):
            with Claim(4096*len(eligible)):
                value=storage.expand_outcomes(output_root,value)
                for name,body in value['outcomes'].items():
                    db.execute('INSERT INTO outcomes VALUES (?,?,?)',(identity,name,storage.encoded(body).decode()))
        for evidence,cohort in strata.items():
            for split in ('train','holdout'):
                for identity in storage.iter_tree(output_root,cohort[split+'_ids_ref']):
                    row=db.execute('SELECT body FROM records WHERE id=? AND conflicted=0',(identity,)).fetchone()
                    if row is None: raise ValueError('trailing_situation_population_generation_invalid')
                    context=json.loads(row[0])['context']
                    db.execute('INSERT INTO membership VALUES (?,?,?,?,?)',
                        (identity,evidence,split,market_type_at(context['entry_at']),'BASE'))
        db.execute('CREATE INDEX cell_membership ON membership(evidence,split,market,kind,id)')
        def classify(config,evidence,split):
            for identity,body in db.execute('SELECT m.id,r.body FROM membership m JOIN records r ON r.id=m.id '
                'WHERE m.evidence=? AND m.split=? ORDER BY m.id',(evidence,split)):
                context=json.loads(body)['context']
                pin=pin_context(context.get('entry_context'),position_key=identity,entry_at=context['entry_at'],classifier=config)
                db.execute('UPDATE membership SET kind=? WHERE id=?',(pin['situation_type'],identity))
        def stats(evidence,split,market,kind,name,config=None):
            where=(evidence,split,market,kind)
            def values():
                for identity,body,candidate_body,parent_body in db.execute(
                    'SELECT m.id,r.body,o.body,p.body FROM membership m JOIN records r ON r.id=m.id '
                    'JOIN outcomes o ON o.id=m.id AND o.candidate=? '
                    'JOIN outcomes p ON p.id=m.id AND p.candidate="incumbent" '
                    'WHERE m.evidence=? AND m.split=? AND m.market=? AND m.kind=? ORDER BY m.id',(name,*where)):
                    context=json.loads(body)['context'];amount=number(context['buy_basis_krw'])
                    if amount is None or amount<=0: raise ValueError('trailing_situation_notional_unverified')
                    candidate,base=json.loads(candidate_body),json.loads(parent_body)
                    reference=max(base['modeled_net_pnl_krw'],candidate['actual_pnl_krw']) if evidence=='actual_completed' else base['modeled_net_pnl_krw']
                    delta=candidate['modeled_net_pnl_krw']-reference
                    stress=(candidate['slippage_net_pnl_krw'][2]-reference)/amount*100
                    clock=number(context.get('completion_at')) if evidence=='actual_completed' else context['entry_at']
                    day=datetime.fromtimestamp(clock,ZoneInfo('Asia/Seoul')).date().isoformat() if clock is not None else None
                    compatible=(context.get('operating_ai_required') is False or
                        (config is not None and context.get('operating_ai_required') is True
                        and validate_pin(context.get('situation_pin'),identity)
                        and context['situation_pin']['classifier_sha256']==config['classifier_sha256']
                        and context['situation_pin']['situation_type']==kind))
                    yield identity,delta,amount,stress,day,compatible
            n=db.execute('SELECT count(*) FROM membership WHERE evidence=? AND split=? AND market=? AND kind=?',where).fetchone()[0]
            total=math.fsum(d for _,d,_,_,_,_ in values());notional=math.fsum(a for _,_,a,_,_,_ in values())
            days={};compatible=True;clock_n=0
            for _,_,_,stress,day,ok in values():
                compatible=compatible and ok
                if day is not None:
                    # fsum per day is delegated to another streaming pass below.
                    days[day]=days.get(day,0)+1;clock_n+=1
            worst_day=min((math.fsum(s for _,_,_,s,d,_ in values() if d==day)/count for day,count in days.items()),default=None)
            adverse=storage.write_tree(output_root,(i for i,d,_,_,_,_ in values() if d<0))
            return dict(n=n,equal_weight_avg_profit_pct=math.fsum(d/a*100 for _,d,a,_,_,_ in values())/n if n else None,
                notional_weighted_ev_pct=100*total/notional if notional else None,paired_delta_net_krw=total if n else None,
                worst_slippage_delta_net_krw=math.fsum(s*a/100 for _,_,a,s,_,_ in values()) if n else None,
                worst_paired_delta_pct=min((d/a*100 for _,d,a,_,_,_ in values()),default=None),worsened_ids_ref=adverse,
                worst_slippage_ev_pct=math.fsum(s for _,_,_,s,_,_ in values())/n if n else None,
                worst_slippage_min_day_ev_pct=worst_day,verified_days=sorted(days),completion_clock_verified=n==clock_n),compatible
        scores,trained={},{}
        for config in grid:
            classify(config,training_kind,'train');selection={};score=0.
            for market in START_MARKETS:
                allowed=[name for name,values in eligible.items() if all(values[m]==eligible['incumbent'][m] for m in START_MARKETS if m!=market)]
                for kind in TYPES:
                    metrics={name:stats(training_kind,'train',market,kind,name)[0] for name in allowed}
                    winner=min(allowed,key=lambda name:(-(metrics[name]['equal_weight_avg_profit_pct'] or 0),name)) if kind!='BASE' else 'incumbent'
                    if (metrics[winner]['equal_weight_avg_profit_pct'] or 0)<=0: winner='incumbent'
                    selection[market+'|'+kind]=winner;score+=max(0.,metrics[winner]['paired_delta_net_krw'] or 0)
            scores[config['classifier_sha256']]=score;trained[config['classifier_sha256']]=selection
        winning=min(scores,key=lambda sha:(-scores[sha],sha));hypothesis=next(g for g in grid if g['classifier_sha256']==winning)
        trained_through=max(json.loads(body)['context']['observation_end_at'] for body, in db.execute(
            "SELECT r.body FROM records r JOIN membership m ON r.id=m.id WHERE m.evidence=? AND m.split='train'",(training_kind,)))
        frozen={**hypothesis,'trained_through':trained_through};frozen['classifier_sha256']=digest({k:v for k,v in frozen.items() if k!='classifier_sha256'})
        cells={}
        for evidence in strata:
            classify(hypothesis,evidence,'train');classify(frozen,evidence,'holdout')
            for market in START_MARKETS:
                for kind in TYPES:
                    key=market+'|'+kind;winner=trained[winning][key]
                    tr,tr_ok=stats(evidence,'train',market,kind,winner,frozen)
                    ho,ho_ok=stats(evidence,'holdout',market,kind,winner,frozen)
                    compatible=tr_ok and ho_ok
                    qualified=(evidence=='actual_completed' and winner!='incumbent'
                        and len(set(tr['verified_days']+ho['verified_days']))>=7 and tr['n']>=30 and ho['n']>=10
                        and len(ho['verified_days'])>=2 and tr['completion_clock_verified'] and ho['completion_clock_verified']
                        and all((v or 0)>0 for v in (tr['equal_weight_avg_profit_pct'],ho['equal_weight_avg_profit_pct'],ho['worst_slippage_ev_pct'],ho['worst_slippage_min_day_ev_pct']))
                        and not tr['worsened_ids_ref']['count'] and not ho['worsened_ids_ref']['count'] and compatible)
                    cells[evidence+'|'+key]={'train_selected_candidate':winner,'train':tr,'holdout':ho,
                        'candidate_values':eligible[winner][market],'effective_initial_values':eligible['incumbent'][market],
                        'disposition':'research_candidate_requires_existing_selector_review' if qualified else 'parent_carry',
                        'parent_values':eligible['incumbent'][market],'holdout_reselected':False,
                        'operating_ai_type_input_compatible':compatible,'training_evidence_kind':training_kind,'allowed_runtime_apply':False}
        # Freeze the single market from training, before holdout eligibility.
        # A failed holdout cannot redirect the canary to a different market.
        train_market_scores={market:math.fsum(max(0.,stats(training_kind,'train',market,kind,
            trained[winning][market+'|'+kind])[0]['paired_delta_net_krw'] or 0.) for kind in TYPES)
            for market in START_MARKETS}
        train_market=min(train_market_scores,key=lambda m:(-train_market_scores[m],m))
        body=dict(schema='main_trailing_situation_research_v1',storage_schema='main_trailing_sharded_situation_v2',
            status='research_complete',classifier=frozen,grid_sha256=digest(grid),train_grid_scores=scores,
            train_winner_hypothesis_sha256=winning,cells=cells,fixed_m1_classifier_sha256=parent_m1,
            train_selected_market=train_market,train_market_scores=train_market_scores,
            rejected_m1_candidates=rejected,input_common_ids_sha256=evaluation['common_ids_ref']['logical_sha256'],allowed_runtime_apply=False)
        return {**body,'artifact_sha256':digest(body)}
