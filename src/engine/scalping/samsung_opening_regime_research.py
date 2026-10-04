"""Offline opening hypotheses with strictly past retained preopen references."""
from __future__ import annotations

import argparse
from datetime import datetime
import itertools
from pathlib import Path
import time
from zoneinfo import ZoneInfo

from src.engine.scalping import samsung_pattern_campaign as C

R,E,Q = C.R,C.E,C.Q
ANCHORS = ('none','below_preopen_close','above_preopen_close','above_preopen_high')


def preopen_anchor(cache):
    rows = [r for r in cache['rows'] if r['valid']]
    if not rows: return None
    return dict(day=cache['day'],close=rows[-1]['p'],high=max(r['p'] for r in rows),
        source_max_at=rows[-1]['t'],close_epoch=rows[-1]['ep'],close_sequence=rows[-1]['seq'],
        observations=len(rows),route='005930_AL|SOR|SOR_PREMARKET',
        basis='observed_trade_extrema_not_official_ohlc_or_fill')


def phase_pass(f, minutes):
    d=datetime.fromtimestamp(f['t'],ZoneInfo('Asia/Seoul'))
    return d.hour==9 and d.minute<minutes


def qualify(f, rule, anchor):
    if not phase_pass(f,rule['opening_minutes']) or not C.qualifies(f,rule): return False
    kind=rule['anchor']
    if kind=='none':return True
    if (anchor is None or anchor['source_max_at']>=f['t'] or anchor['day']!=
        datetime.fromtimestamp(f['t'],ZoneInfo('Asia/Seoul')).date().isoformat()): return False
    if kind=='below_preopen_close':return f['ask']<=anchor['close']
    if kind=='above_preopen_close':return f['bid']>=anchor['close']
    if kind=='above_preopen_high':return f['bid']>=anchor['high']
    raise ValueError('unknown_preopen_anchor')


def registry(fee):
    base=[r for r in C.rules(fee) if r['region']=='all' and r['stage'] in ('micro','book','fees_micro','fees_book')]
    return [{**r,'id':r['id']+f':opening{m}:{a}','opening_minutes':m,'anchor':a}
        for r,m,a in itertools.product(base,(15,30),ANCHORS)]


def select(frames, rule, anchor, horizon):
    until=float('-inf');out=[]
    for f in frames:
        if f['t']>=until and qualify(f,rule,anchor):
            out.append(f);until=f['t']+horizon+1.5
    return out


def native_bridge(projection, frames_by_day, rule, anchors):
    # Keep every original timestamp, including nonqualifying frames, so the last
    # valid old signal cannot be carried across a later failed opening gate.
    masked={d:[f if qualify(f,rule,anchors[d]) else {**f,'windows':{}} for f in fs]
        for d,fs in frames_by_day.items()}
    return C.native_bridge(projection,masked,rule)


def run(root, regular_source, session_source, output, max_quote_gap=1.5):
    started=time.monotonic()
    regular,one,sha1=C.load_manifest(regular_source)
    session,two,sha2=C.load_manifest(session_source)
    plan=root/'docs/proposals/samsung-opening-regime-research-plan-2026-10-04.md'
    seals={**one,**two,str(Path(__file__).resolve()):R.P.file_sha(Path(__file__)),str(plan):R.P.file_sha(plan)}
    projection=R.read(Path(regular['projection']));frames_by_day={};contexts={};anchors={};daily={};signals={};outcomes={};bases={}
    fee=regular['fee_profiles'][R.DAYS[0]]['cost_pct'];rules=registry(fee)
    for day in R.DAYS:
        prepared=R.read(Path(regular['files'][day]['path']));frames=prepared['frames'];frames_by_day[day]=frames
        ctx=C.campaign_context(E.read_cache(Path(prepared['cache']['path'])),max_quote_gap);contexts[day]=ctx
        before=E.read_cache(Path(session['files']['SOR_PREMARKET|'+day]['path']))
        anchor=preopen_anchor(before);anchors[day]=anchor
        if anchor and anchor['day']!=day:raise ValueError('preopen_anchor_date_conflict')
        memo={};result={};choices={};baseline={}
        def get(f,h,c):
            key=(f['index'],h,c)
            if key not in memo:memo[key]=C.label(ctx,f,h,cost_pct=c)
            return memo[key]
        for minutes,h,model in itertools.product((15,30),(600,1200,1800),('stress','quote_fees')):
            cost=E.COST if model=='stress' else fee
            fs=C.select([f for f in frames if phase_pass(f,minutes)],h)
            baseline[f'{minutes}:{h}:{model}']=[get(f,h,cost) for f in fs]
        for rule in rules:
            for h in rule['horizons']:
                key=rule['id']+f':{h}'
                fs=select(frames,rule,anchor,h)
                choices[key]=fs;result[key]=dict(**rule,key=key,horizon=h,metric=C.metric([get(f,h,rule['cost_pct']) for f in fs]))
        daily[day]=result;signals[day]=choices;outcomes[day]=memo;bases[day]=baseline
        print(day,'opening_rules',len(result),'outcomes',len(memo),flush=True)
    folds=[]
    for model in ('stress','quote_fees'):
        for train,held in [(R.DAYS[:1],R.DAYS[1]),(R.DAYS[:2],R.DAYS[2])]:
            candidates=[]
            for key,r in daily[train[0]].items():
                if r['cost_model']!=model:continue
                labels=[outcomes[d][(f['index'],r['horizon'],r['cost_pct'])] for d in train for f in signals[d][key]]
                candidates.append({**r,'metric':C.metric(labels)})
            baseline={k:C.metric([o for d in train for o in bases[d][k]]) for k in bases[train[0]]}
            eligible=[r for r in candidates if r['metric']['binary']>=3
                and baseline[f"{r['opening_minutes']}:{r['horizon']}:{model}"]['binary']>=3
                and r['metric']['win_rate']>baseline[f"{r['opening_minutes']}:{r['horizon']}:{model}"]['win_rate']]
            chosen=max(eligible,key=lambda r:(r['metric']['win_rate'],r['metric']['wilson'],r['metric']['binary'],
                -C.FAMILIES.index(r['family']),-r['window'],-r['level'],-r['opening_minutes'],-ANCHORS.index(r['anchor']),-r['horizon'])) if eligible else None
            detail=None
            if chosen:
                key=chosen['key'];fs=signals[held][key];h=chosen['horizon'];cost=chosen['cost_pct'];ctx=contexts[held]
                subset=[f for f in frames_by_day[held] if phase_pass(f,chosen['opening_minutes'])]
                detail=dict(candidate=daily[held][key],baseline=C.metric(bases[held][f"{chosen['opening_minutes']}:{h}:{model}"]),
                    outcomes=[outcomes[held][(f['index'],h,cost)] for f in fs],
                    latency={str(l):C.metric([C.label(ctx,f,h,latency=l,cost_pct=cost) for f in fs]) for l in (.25,1.)},
                    common_clock=C.common_clock_comparison(ctx,subset,fs,chosen),
                    main_trailing_arm_price=C.metric([C.label(ctx,f,h,target_net=.4,cost_pct=cost) for f in fs]),
                    native_bridge=native_bridge(projection,frames_by_day,chosen,anchors),
                    neighbors=[r for r in daily[held].values() if r['family']==chosen['family']
                        and r['opening_minutes']==chosen['opening_minutes'] and r['anchor']==chosen['anchor']
                        and r['cost_model']==model and r['horizon']==h])
            folds.append(dict(model=model,train_days=list(train),held_day=held,selected=chosen,held=detail,
                training_baselines=baseline,training_candidates=candidates))
    Q.verify_hashes(seals);Q.verify_hashes(regular['preserved']);Q.verify_hashes(session['preserved'])
    C.write(output/'result.json',dict(records=seals,regular_source_sha256=sha1,session_source_sha256=sha2,
        daily=daily,folds=folds,anchors=anchors,hypothesis_count=sum(len(r['horizons']) for r in rules),
        max_observed_quote_gap_sec=max_quote_gap,quote_gap_sensitivity=max_quote_gap!=1.5,
        success_preservation_veto=False,execution_route_verified=False,elapsed_sec=time.monotonic()-started,
        native_bridge_role='opening_and_anchor_gates_included_canonical_frames_unchanged'))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path.cwd())
    parser.add_argument('--regular-source',type=Path,required=True)
    parser.add_argument('--session-source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--max-observed-quote-gap',type=float,choices=(1.5,3.,10.),default=1.5)
    a=parser.parse_args();run(a.root.resolve(),a.regular_source.resolve(),a.session_source.resolve(),a.output.resolve(),a.max_observed_quote_gap)


if __name__=='__main__':main()
