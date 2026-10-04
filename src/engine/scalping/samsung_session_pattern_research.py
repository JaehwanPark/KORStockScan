"""Offline session-separated reuse of retained Samsung local domain records."""
from __future__ import annotations

import argparse
from collections import Counter
import itertools
import json
from pathlib import Path
import time

from src.engine.scalping import samsung_pattern_campaign as C

R, E, Q = C.R, C.E, C.Q
SESSION_ROUTES = {'SOR_PREMARKET':('SOR','005930_AL'),
    'SOR_AFTERMARKET':('SOR','005930_AL'), 'NXT_PREMARKET':('NXT','005930_NX'),
    'NXT_REGULAR_OVERLAP':('NXT','005930_NX')}
SESSIONS = tuple(SESSION_ROUTES)


def partition(root, day, session, records):
    result = {}; books = {}; stats = {}
    venue,item = SESSION_ROUTES[session]
    base = root/f'data/observations/scalp_micro_reversion_forward/trade_date={day}/venue={venue}/session={session}'
    for kind,stem in [('trade','market_stream'),('depth','market_depth_stream')]:
        meta = base/(stem+'.manifest.json')
        if not meta.exists():
            # Known zero/absent observation partition is diagnostic missing,
            # never zero economics or a source-certified no-entry policy.
            result['rows' if kind=='trade' else 'depth'] = []
            stats[kind] = dict(count=0,valid=0,first=None,last=None,status='source_partition_missing')
            continue
        records[str(meta)] = R.P.file_sha(meta)
        manifest = json.loads(meta.read_text()); rows = []; seen = set(); previous = {}; rejected = Counter()
        schema = 'scalp_micro_reversion_market_stream_point_v3' if kind=='trade' else 'scalp_micro_reversion_market_depth_point_v1'
        if (manifest.get('schema')!='scalp_micro_reversion_market_path_manifest_v1'
            or manifest.get('row_schema')!=schema or not isinstance(manifest.get('shards'),list)):
            raise ValueError('session_manifest_contract_invalid')
        for shard in manifest['shards']:
            path = (base/shard['file']).resolve()
            if path.parent!=base.resolve() or not path.exists(): raise ValueError('shard_missing_or_outside_partition')
            records[str(path)] = R.P.file_sha(path)
            opener = E.gzip.open(path,'rt') if path.suffix=='.gz' else path.open()
            with opener as stream:
                for line in stream:
                    if '005930' not in line: continue
                    r = json.loads(line)
                    if r.get('symbol')!='005930': continue
                    if (r.get('schema')!=schema or r.get('source_item',r.get('item'))!=item
                        or r.get('item') not in (None,item)
                        or r.get('venue')!=venue or r.get('session_bucket')!=session):
                        rejected['schema_or_exact_route'] += 1; continue
                    t,ex = R.epoch(r['local_receive_timestamp']),R.epoch(r['exchange_timestamp'])
                    ep,seq = r['sequence_epoch'],r['series_sequence']
                    if type(ep) is not int or type(seq) is not int or seq<1 or r['local_receive_timestamp'][:10]!=day:
                        raise ValueError('session_sequence_or_date_invalid')
                    identity = (ep,seq)
                    if identity in seen: raise ValueError('session_duplicate_sequence')
                    seen.add(identity); old = previous.get(ep); previous[ep]=(seq,t)
                    continuous = old is None or (seq==old[0]+1 and t>=old[1])
                    clock = 0<=t-ex<=5
                    row = dict(t=t,ex=ex,ep=ep,seq=seq,continuous=continuous)
                    if kind=='trade':
                        p,q,side = r.get('trade_price'),r.get('trade_qty'),r.get('aggressor_side')
                        valid = clock and r.get('path_consumer_eligible') is True and r.get('path_order_status')=='accept' and R.finite(p) and p>0
                        row.update(p=p,q=q,side=side,valid=bool(valid),
                            flow_valid=bool(valid and R.finite(q) and q>0 and side in ('BUY','SELL')))
                    else:
                        bid,ask = r.get('best_bid'),r.get('best_ask')
                        valid = clock and R.finite(bid) and R.finite(ask) and 0<bid<=ask
                        row.update(bid=bid,ask=ask,bq=r.get('best_bid_qty'),aq=r.get('best_ask_qty'),valid=bool(valid))
                        books[identity] = C.normalized_book(r) if valid else None
                    rows.append(row)
            Q.verify_hashes({str(path):records[str(path)]})
        Q.verify_hashes({str(meta):records[str(meta)]})
        rows.sort(key=lambda r:(r['t'],r['ep'],r['seq']))
        result['rows' if kind=='trade' else 'depth'] = rows
        stats[kind] = dict(count=len(rows),valid=sum(r['valid'] for r in rows),
            first=rows[0]['t'] if rows else None,last=rows[-1]['t'] if rows else None,rejected=dict(rejected))
    return result,books,stats


def prepare(root, output):
    records = {}
    for module in (C,Q,E,R):
        p = Path(module.__file__).resolve(); records[str(p)] = R.P.file_sha(p)
    records[str(Path(__file__).resolve())] = R.P.file_sha(Path(__file__))
    plan = root/'docs/proposals/samsung-pattern-campaign-plan-2026-10-04.md'
    records[str(plan)] = R.P.file_sha(plan)
    continuity_plan=root/'docs/proposals/samsung-quote-continuity-sensitivity-research-plan-2026-10-04.md'
    records[str(continuity_plan)] = R.P.file_sha(continuity_plan)
    parent = root/'tmp/samsung-quote-recovery-research-20261004/locked-source/manifest.json'
    existing = R.read(parent)
    records.update({**existing['kernel_manifest'],**existing['source_manifest'],str(parent):R.P.file_sha(parent)})
    profiles,fee = C.fee_profiles(root,records)
    files = {}; census = {}
    for session,day in itertools.product(SESSIONS,R.DAYS):
        cache,books,stats = partition(root,day,session,records)
        frames = C.feature_rows(cache,books)
        path = output/f'{session}-{day}.json.gz'
        Q.write_cache(path,dict(day=day,session=session,rows=cache['rows'],depth=cache['depth'],frames=frames))
        key = session+'|'+day
        files[key] = dict(path=str(path),sha256=R.P.file_sha(path),session=session,day=day)
        census[key] = dict(**stats,features=len(frames),book_valid=sum(b is not None for b in books.values()))
        print(session,day,'trades',len(cache['rows']),'depth',len(cache['depth']),'frames',len(frames),flush=True)
    Q.verify_hashes(records)
    preserved = {str(root/k):v for k,v in R.read(root/'tmp/samsung-continuous-recovery-research-20261003/preserved-artifacts.json').items()}
    Q.verify_hashes(preserved)
    C.write(output/'manifest.json',dict(records=records,files=files,census=census,fee_profiles=profiles,
        rules=[r for r in C.rules(fee) if r['region']=='all'],preserved=preserved,
        sessions=list(SESSIONS),session_join_forbidden=True))


def run(source, output, max_quote_gap=1.5):
    started = time.monotonic(); manifest,seals,source_sha = C.load_manifest(source)
    all_results = {}; folds = []
    for session in SESSIONS:
        daily = {}; baselines = {}; outcomes = {}; contexts = {}; signals = {}; frames_by_day = {}
        for day in R.DAYS:
            cache = E.read_cache(Path(manifest['files'][session+'|'+day]['path']))
            ctx = C.campaign_context(cache,max_quote_gap); contexts[day] = ctx; frames = cache['frames']
            frames_by_day[day] = frames
            memo = {}; results = {}; bases = {}; choices = {}
            def get(f,h,c):
                key = (f['index'],h,c)
                if key not in memo: memo[key] = C.label(ctx,f,h,cost_pct=c)
                return memo[key]
            for h,model in itertools.product(C.HORIZONS,('stress','quote_fees')):
                cost = E.COST if model=='stress' else manifest['fee_profiles'][day]['cost_pct']
                bases[f'all:{h}:{model}'] = [get(f,h,cost) for f in C.select(frames,h)]
            for rule in manifest['rules']:
                for h in rule['horizons']:
                    key = rule['id']+f':{h}'
                    fs = C.select(frames,h,rule)
                    results[key] = dict(**rule,key=key,horizon=h,metric=C.metric([get(f,h,rule['cost_pct']) for f in fs]))
                    choices[key] = fs
            daily[day]=results; baselines[day]=bases; outcomes[day]=memo; signals[day]=choices
            print(session,day,'rules',len(results),'outcomes',len(memo),flush=True)
        for stage in ('micro','cycle','book','fees_micro','fees_cycle','fees_book'):
            for train,held in [(R.DAYS[:1],R.DAYS[1]),(R.DAYS[:2],R.DAYS[2])]:
                candidates = []
                for key,c in daily[train[0]].items():
                    if c['stage']!=stage: continue
                    labels = [outcomes[d][(f['index'],c['horizon'],c['cost_pct'])] for d in train for f in signals[d][key]]
                    candidates.append({**c,'metric':C.metric(labels)})
                bases = {k:C.metric([o for d in train for o in baselines[d][k]]) for k in baselines[train[0]]}
                chosen = C.choose(candidates,bases); detail = None
                if chosen:
                    fs = signals[held][chosen['key']]; ctx = contexts[held]
                    detail = dict(candidate=daily[held][chosen['key']],baseline=C.metric(baselines[held][C.baseline_key(chosen)]),
                        outcomes=[outcomes[held][(f['index'],chosen['horizon'],chosen['cost_pct'])] for f in fs],
                        latency={str(l):C.metric([C.label(ctx,f,chosen['horizon'],latency=l,cost_pct=chosen['cost_pct']) for f in fs]) for l in (.25,1.)},
                        main_trailing_arm_price=C.metric([C.label(ctx,f,chosen['horizon'],target_net=.4,cost_pct=chosen['cost_pct']) for f in fs]),
                        common_clock=C.common_clock_comparison(ctx,frames_by_day[held],fs,chosen))
                folds.append(dict(session=session,stage=stage,train_days=list(train),held_day=held,
                    selected=chosen,held=detail,training_baselines=bases,training_candidates=candidates))
        all_results[session] = dict(daily=daily,baselines={d:{k:C.metric(v) for k,v in b.items()} for d,b in baselines.items()})
    Q.verify_hashes(seals); Q.verify_hashes(manifest['preserved'])
    C.write(output/'result.json',dict(source_manifest_sha256=source_sha,folds=folds,
        results=all_results,census=manifest['census'],session_join_forbidden=True,
        hypotheses_per_session=sum(len(r['horizons']) for r in manifest['rules']),
        max_observed_quote_gap_sec=max_quote_gap,quote_gap_sensitivity=max_quote_gap!=1.5,
        native_promotion_support=False,execution_route_verified=False,elapsed_sec=time.monotonic()-started))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('prepare','run'))
    parser.add_argument('--root',type=Path,default=Path.cwd())
    parser.add_argument('--source',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--max-observed-quote-gap',type=float,choices=(1.5,3.,10.),default=1.5)
    args = parser.parse_args()
    if args.mode=='prepare': prepare(args.root.resolve(),args.output.resolve())
    else:
        if args.source is None: parser.error('--source is required for run')
        run(args.source.resolve(),args.output.resolve(),args.max_observed_quote_gap)


if __name__=='__main__': main()
