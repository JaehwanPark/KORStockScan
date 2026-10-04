"""Offline five-level and full-depth hypotheses from retained domain journals."""
from __future__ import annotations

import argparse
from bisect import bisect_left, bisect_right
import itertools
import json
from pathlib import Path
import time

from src.engine.scalping import samsung_pattern_campaign as C
from src.engine.scalping import samsung_session_pattern_research as S
from src.engine.scalping import samsung_opening_regime_research as O

R,E,Q=C.R,C.E,C.Q
FAMILIES=('five_support','five_flip','total_support','total_flip','deep_replenish','deep_depletion')
LEGACY=('book_support','book_flip','book_support','book_flip','bid_replenish','ask_depletion')


def profile(raw):
    three=C.normalized_book(raw)
    if three is None:return None
    bids,asks=raw['bid_levels'],raw['ask_levels']
    five=len(bids)>=5 and len(asks)>=5
    bd,ad=raw.get('bid_depth'),raw.get('ask_depth')
    totals=raw.get('route_depth_totals')
    total=(type(bd) is int and type(ad) is int and bd>=sum(x[2] for x in bids)
        and ad>=sum(x[2] for x in asks) and bd>0 and ad>0
        and isinstance(totals,dict) and totals.get('combined')==dict(bid=bd,ask=ad))
    return dict(three_bid=three['bid_sum'],three_ask=three['ask_sum'],
        five_bid=sum(x[2] for x in bids[:5]) if five else None,
        five_ask=sum(x[2] for x in asks[:5]) if five else None,
        bid_prices=tuple(x[1] for x in bids[:5]) if five else None,
        ask_prices=tuple(x[1] for x in asks[:5]) if five else None,
        total_bid=bd if total else None,total_ask=ad if total else None)


def profiles(cache,records,day,session):
    venue,item=('SOR','005930_AL') if session=='SOR_REGULAR' else S.SESSION_ROUTES[session]
    expected={(q['ep'],q['seq']):q for q in cache['depth']};found={};seen=set()
    needle=f'trade_date={day}/venue={venue}/session={session}/market_depth_stream'
    for name in records:
        if needle not in name or name.endswith('manifest.json'):continue
        path=Path(name)
        opener=E.gzip.open(path,'rt') if path.suffix=='.gz' else path.open()
        with opener as handle:
            for line in handle:
                if '005930' not in line:continue
                raw=json.loads(line)
                if raw.get('symbol')!='005930':continue
                if (raw.get('schema')!='scalp_micro_reversion_market_depth_point_v1'
                    or raw.get('item',raw.get('source_item'))!=item
                    or raw.get('source_item') not in (None,item)
                    or raw.get('venue')!=venue or raw.get('session_bucket')!=session):
                    raise ValueError('profile_exact_route_conflict')
                identity=(raw.get('sequence_epoch'),raw.get('series_sequence'))
                if not all(type(x) is int for x in identity):raise ValueError('profile_sequence_invalid')
                q=expected.get(identity)
                if q is None:raise ValueError('profile_not_in_bound_cache')
                if identity in seen:raise ValueError('profile_duplicate_sequence')
                seen.add(identity)
                if (R.epoch(raw['local_receive_timestamp'])!=q['t'] or
                    any(raw.get(a)!=q[b] for a,b in (('best_bid','bid'),('best_ask','ask'),
                        ('best_bid_qty','bq'),('best_ask_qty','aq')))):
                    raise ValueError('profile_cache_binding_conflict')
                found[identity]=profile(raw) if q['valid'] else None
    if seen!=set(expected):raise ValueError('profile_source_incomplete')
    return found


def augment(cache,frames,books):
    ctx=C.campaign_context(cache);dt=ctx['dt'];depth=cache['depth'];out=[]
    for original in frames:
        f={**original};i=f['quote_index'];q=depth[i];current=books.get((q['ep'],q['seq']))
        p=bisect_right(dt,f['t']-5)-1
        old=books.get((depth[p]['ep'],depth[p]['seq'])) if p>=0 else None
        a=bisect_left(ctx['valid'],p);b=bisect_left(ctx['valid'],i)
        connected=(p>=0 and depth[p]['valid'] and depth[p]['ep']==q['ep']
            and 0<=f['t']-5-dt[p]<=1.5 and a<len(ctx['quote_ends']) and ctx['quote_ends'][a]>=b)
        history=[books.get((depth[k]['ep'],depth[k]['seq'])) for k in range(p,i+1)] if connected else []
        five_ok=bool(current and old and connected and all(x and x['five_bid'] is not None
            and x['five_ask'] is not None and x['five_bid']>0 and x['five_ask']>0 for x in history))
        total_ok=bool(current and old and connected and all(x and x['total_bid'] is not None
            and x['total_ask'] is not None for x in history))
        f['profile']=dict(
            five_ratio=current['five_bid']/current['five_ask'] if current and current['five_ask'] and current['five_bid'] is not None else None,
            old_five_ratio=old['five_bid']/old['five_ask'] if five_ok else None,
            total_ratio=current['total_bid']/current['total_ask'] if current and current['total_ask'] else None,
            old_total_ratio=old['total_bid']/old['total_ask'] if total_ok else None,
            deep_bid_replenishment=current['five_bid']/old['five_bid'] if five_ok
                and all(x['bid_prices']==current['bid_prices'] for x in history) else None,
            deep_ask_depletion=current['five_ask']/old['five_ask'] if five_ok
                and all(x['ask_prices']==current['ask_prices'] for x in history) else None)
        out.append(f)
    return out


def mapped_frame(f,rule):
    p=f['profile'];kind='five' if rule['profile_family'].startswith('five') else 'total'
    return {**f,'depth_ratio':p[kind+'_ratio'],'prior_depth_ratio':p['old_'+kind+'_ratio'],
        'bid_replenishment':p['deep_bid_replenishment'],'ask_depletion':p['deep_ask_depletion']}


def qualify(f,rule):
    return (not rule['phase'] or O.phase_pass(f,rule['phase'])) and C.qualifies(mapped_frame(f,rule),rule)


def select(frames,rule,h):
    out=[];until=float('-inf')
    for f in frames:
        if f['t']>=until and qualify(f,rule):out.append(f);until=f['t']+h+1.5
    return out


def registry(fee,regular):
    groups=[('all',None)] if not regular else [(r,None) for r in C.REGIONS]+[('all',15),('all',30)]
    return [dict(id=f'{family}:{w}:{level}:{region}:phase{phase or 0}:{model}',
        profile_family=family,family=LEGACY[FAMILIES.index(family)],window=w,level=level,
        region=region,phase=phase,room_net=None,cost_pct=C.E.COST if model=='stress' else fee,
        cost_model=model,horizons=[600,1200,1800])
        for family,w,level,(region,phase),model in itertools.product(FAMILIES,(60,180,300),(1,2),groups,('stress','quote_fees'))]


def baseline_key(c):return f"{c['region']}:{c['horizon']}:{c['cost_model']}:phase{c['phase'] or 0}"


def choose(candidates,baseline):
    eligible=[c for c in candidates if c['metric']['binary']>=3 and baseline[baseline_key(c)]['binary']>=3
        and c['metric']['win_rate']>baseline[baseline_key(c)]['win_rate']]
    return max(eligible,key=lambda c:(c['metric']['win_rate'],c['metric']['wilson'],c['metric']['binary'],
        -FAMILIES.index(c['profile_family']),-c['window'],-c['level'],-C.REGIONS.index(c['region']),-c['horizon'])) if eligible else None


def native_bridge(projection,frames,rule):
    masked={d:[mapped_frame(f,rule) if qualify(f,rule) else {**mapped_frame(f,rule),'windows':{}}
        for f in fs] for d,fs in frames.items()}
    return C.native_bridge(projection,masked,rule)


def run(root,regular_source,session_source,output):
    start=time.monotonic();regular,one,_=C.load_manifest(regular_source);session,two,_=C.load_manifest(session_source)
    records={**one,**two}
    for module in (C,S,O,Q,E,R):
        path=Path(module.__file__).resolve();records[str(path)]=R.P.file_sha(path)
    for path in (Path(__file__).resolve(),root/'docs/proposals/samsung-depth-profile-research-plan-2026-10-04.md'):
        records[str(path)]=R.P.file_sha(path)
    projection=R.read(Path(regular['projection']));all_daily={};folds=[];census={};prepared={}
    for scope in ('SOR_REGULAR',*S.SESSIONS):
        by_day={}
        for day in R.DAYS:
            if scope=='SOR_REGULAR':
                source=R.read(Path(regular['files'][day]['path']));cache=E.read_cache(Path(source['cache']['path']));frames=source['frames']
            else:
                cache=E.read_cache(Path(session['files'][scope+'|'+day]['path']));frames=cache['frames']
            books=profiles(cache,records,day,scope);fs=augment(cache,frames,books)
            by_day[day]=(cache,fs)
            census[scope+'|'+day]=dict(frames=len(fs),features={k:sum(f['profile'][k] is not None for f in fs)
                for k in ('five_ratio','old_five_ratio','total_ratio','old_total_ratio','deep_bid_replenishment','deep_ask_depletion')})
        prepared[scope]=by_day
    fee=regular['fee_profiles'][R.DAYS[0]]['cost_pct']
    for gap in (1.5,3.,10.):
      for scope,by_day in prepared.items():
        daily={};bases={};signals={};labels={};contexts={};rules=registry(fee,scope=='SOR_REGULAR')
        for day,(cache,frames) in by_day.items():
            ctx=C.campaign_context(cache,gap);contexts[day]=ctx;memo={};out={};choices={};baseline={}
            def get(f,h,c):
                key=(f['index'],h,c)
                if key not in memo:memo[key]=C.label(ctx,f,h,cost_pct=c)
                return memo[key]
            groups={(r['region'],r['phase'],r['cost_model'],r['cost_pct']) for r in rules}
            for region,phase,model,cost in sorted(groups,key=str):
                subset=[f for f in frames if not phase or O.phase_pass(f,phase)]
                for h in (600,1200,1800):
                    baseline[f'{region}:{h}:{model}:phase{phase or 0}']=[get(f,h,cost) for f in C.select(subset,h,region=region)]
            for rule in rules:
                for h in rule['horizons']:
                    key=rule['id']+f':{h}';fs=select(frames,rule,h);choices[key]=fs
                    out[key]={**rule,'key':key,'horizon':h,'metric':C.metric([get(f,h,rule['cost_pct']) for f in fs])}
            daily[day]=out;bases[day]=baseline;signals[day]=choices;labels[day]=memo
        for phase,model in itertools.product((None,15,30) if scope=='SOR_REGULAR' else (None,),('stress','quote_fees')):
            for train,held in ((R.DAYS[:1],R.DAYS[1]),(R.DAYS[:2],R.DAYS[2])):
                candidates=[]
                for key,c in daily[train[0]].items():
                    if c['phase']!=phase or c['cost_model']!=model:continue
                    ls=[labels[d][(f['index'],c['horizon'],c['cost_pct'])] for d in train for f in signals[d][key]]
                    candidates.append({**c,'metric':C.metric(ls)})
                baseline={k:C.metric([l for d in train for l in bases[d][k]]) for k in bases[train[0]]}
                chosen=choose(candidates,baseline);detail=None
                if chosen:
                    fs=signals[held][chosen['key']];ctx=contexts[held];h=chosen['horizon'];cost=chosen['cost_pct']
                    subset=[f for f in by_day[held][1] if not phase or O.phase_pass(f,phase)]
                    detail=dict(candidate=daily[held][chosen['key']],baseline=C.metric(bases[held][baseline_key(chosen)]),
                        outcomes=[labels[held][(f['index'],h,cost)] for f in fs],
                        latency={str(l):C.metric([C.label(ctx,f,h,latency=l,cost_pct=cost) for f in fs]) for l in (.25,1.)},
                        common_clock=C.common_clock_comparison(ctx,subset,fs,chosen),
                        main_trailing_arm_price=C.metric([C.label(ctx,f,h,target_net=.4,cost_pct=cost) for f in fs]),
                        native_bridge=native_bridge(projection,{d:v[1] for d,v in by_day.items()},chosen) if scope=='SOR_REGULAR' else None)
                folds.append(dict(gap=gap,scope=scope,phase=phase,model=model,train_days=list(train),held_day=held,
                    selected=chosen,held=detail,training_candidates=candidates,training_baselines=baseline))
        all_daily[str(gap)+'|'+scope]=daily
        print('depth profiles',gap,scope,'conditions',len(daily[R.DAYS[0]]),flush=True)
    Q.verify_hashes(records);Q.verify_hashes(regular['preserved'])
    C.write(output/'result.json',dict(records=records,census=census,daily=all_daily,folds=folds,
        additional_hypotheses=1944,observed_gap_models=[1.5,3.,10.],success_preservation_veto=False,
        native_bridge_role='profile_fields_and_phase_applied_original_guard_identity_cost_preserved',
        execution_route_verified=False,elapsed_sec=time.monotonic()-start))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path.cwd());p.add_argument('--regular-source',type=Path,required=True)
    p.add_argument('--session-source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.root.resolve(),a.regular_source.resolve(),a.session_source.resolve(),a.output.resolve())


if __name__=='__main__':main()
