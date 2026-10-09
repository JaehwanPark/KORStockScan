"""Bounded v6 research snapshots using unchanged sources and changed-scope replay.

No provider or runtime mutation. Unchanged branch definitions reuse their native
point census; changed memberships run the current FSM over the original prefix.
Only a hash-selected reservoir is materialized in the existing shared store.
"""
from __future__ import annotations
import copy
import gzip
import json
from collections import Counter,defaultdict
from pathlib import Path
from src.engine.ai import offline_comparison_store as S
from src.engine.scalping import continuous_reversal as K
from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.scalping import reversal_auxiliary_research as Q
from src.engine.scalping import reversal_extended_catalog as C
from src.engine.scalping import reversal_extended_state as R
from src.engine.scalping import reversal_extended_runtime as LIVE
from src.engine.scalping import reversal_extended_union as U
from src.engine.scalping import continuous_reversal_operating_postclose as O


def unchanged_scopes(old_manifest,new_manifest):
    result=set()
    for sid,ids in new_manifest['scopes'].items():
        if set(ids)!=set(old_manifest['scopes'].get(sid,[])):continue
        if all(C.branch(b)==C.OLD.branch(b) for b in ids):result.add(sid)
    return result


def select(pool,point,snapshot,*,seed,limit):
    key=point['opportunity_key'];rank=P.digest([seed,key]);bucket=pool[point['scope']]
    if key in bucket:return
    if len(bucket)<limit or rank<max(v[0] for v in bucket.values()):
        bucket[key]=(rank,copy.deepcopy(point),snapshot)
        if len(bucket)>limit:bucket.pop(max(bucket,key=lambda k:bucket[k][0]))


def build(data_root,parent,machine,*,seed,excluded,per_scope=6):
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    from src.engine.scalping import continuous_reversal_policy_v6 as V
    if not isinstance(seed,str) or not seed or type(per_scope) is not int or not 1<=per_scope<=10:
        raise ValueError('research_reservoir_config_invalid')
    if machine['artifact_content_sha256']!=P.seal(machine)['artifact_content_sha256']:
        raise ValueError('research_population_source_changed')
    if parent['continuous_reversal']['schema']!=V.SCHEMA:raise ValueError('research_v6_parent_required')
    manifest=parent['continuous_reversal']['operating_manifest']
    same=unchanged_scopes(machine['operating_manifest'],manifest)
    changed=set(manifest['scopes'])-same
    pool=defaultdict(dict);census=defaultdict(Counter);receipts=[];conflicts=set(machine.get('quarantined_conflicts',[]))
    seen={};excluded=set(excluded)
    with S.Store(data_root,readonly=True) as store:
        for number,part in enumerate(machine['partitions']):
            records=store.get(part['records_object'])
            if P.digest(records)!=part['records_sha256']:raise ValueError('research_partition_changed')
            old={p['opportunity_key']:p for p in records}
            for p in records:
                if p['scope'] not in same:continue
                key=p['opportunity_key'];fingerprint=P.digest(p)
                if key in seen:
                    if seen[key]!=fingerprint:conflicts.add(key)
                    continue
                seen[key]=fingerprint;census[p['scope']]['all_points']+=1
                census[p['scope']][p['outcome']['status']]+=1
                if key in excluded or key in conflicts:continue
                if p['outcome']['status'] not in {'WIN','FAIL_STOP','FAIL_TIMEOUT'}:continue
                # Object is loaded only if this point enters the reservoir.
                select(pool,p,None,seed=seed,limit=per_scope)
            rec=part['normalized_source'];market=K.market_bucket(rec['session']);route=rec['venue']
            affected=[s for s in changed if s.split('|')[1]==market and s.split('|')[-1]==route]
            if not affected:continue
            with N.source_anchor(data_root):path=N.source_path(rec['path'])
            if P.file_hash(path)!=rec['sha256']:raise ValueError('research_normalized_source_changed')
            receipts.append(dict(path=str(path.resolve()),sha256=rec['sha256']))
            raw=json.loads(gzip.decompress(path.read_bytes()))['symbols']
            for symbol,source_rows in sorted(raw.items()):
                keys=[C.cell_key(symbol,market,1)] if C.group(symbol)=='samsung' else [f'{C.group(symbol)}|{market}|{b}' for b in C.BANDS]
                sids=[key+'|'+route for key in keys]
                if not set(sids)&changed:continue
                from src.trading.market.session_contract import market_source_partition_venue as _explicit_item_venue
                for item in sorted({r[9] for r in source_rows if isinstance(r[9],str) and r[9].split('_',1)[0]==symbol and _explicit_item_venue(r[9])==route}):
                    rows=[r[:] for r in source_rows]
                    for row in rows:
                        if row[9]!=item:row[8]=0
                    ids=sorted({bid for sid in sids for bid in manifest['scopes'][sid]})
                    state=R.State(branch_ids=ids,registry_sha256=C.SHA256,session_anchor=next((r for r in rows if r[8]),None),offline=True)
                    times=[r[0] for r in rows];_,ends,valid=K.segments(rows)
                    tree=K.Tree([r[3] if r[8] else None for r in rows])
                    for index,row in enumerate(rows):
                        ready=state.observe(row,symbol=symbol,venue=route,session=rec['session'])
                        sid=C.cell_key(symbol,market,row[3] or 1)+'|'+route
                        if ready and sid in changed:
                            event=ready[0]['event'];key=U.opportunity(event)
                            hits=set(event['branch_signals'])&set(manifest['scopes'][sid])
                            if hits and key not in seen:
                                seen[key]='replayed';label=K.label(rows,times,tree,ends,valid,index,event['entry_ask'])
                                previous=old.get(key)
                                if label['status']=='UNRESOLVED' and previous and previous['outcome'].get('source')=='same_item_completed_bar_backfill':
                                    old_event=store.get(previous['snapshot_obj'])[0]
                                    if all(old_event.get(k)==event.get(k) for k in ('entry_ask','epoch','source_item','native_epoch','native_sequence')):
                                        label=copy.deepcopy(previous['outcome']);census[sid]['reused_exact_bar_label']+=1
                                census[sid]['all_points']+=1;census[sid][label['status']]+=1
                                if key not in excluded and key not in conflicts and label['status'] in {'WIN','FAIL_STOP','FAIL_TIMEOUT'}:
                                    rank=P.digest([seed,key]);bucket=pool[sid]
                                    if len(bucket)<per_scope or rank<max(v[0] for v in bucket.values()):
                                        snapshot=O.subset(LIVE.snapshot(state,ready[0]),manifest['scopes'][sid])
                                        p=dict(opportunity_key=key,scope=sid,day=rec['day'],symbol=symbol,outcome=label)
                                        select(pool,p,snapshot,seed=seed,limit=per_scope)
                        state.ready.clear()
            print(json.dumps(dict(partition=number+1,total=len(machine['partitions']),points=sum(v['all_points'] for v in census.values()),retained=sum(map(len,pool.values())))),flush=True)
        # Freeze exact native snapshots only for the selected, bounded reservoir.
        materialized=[]
        for sid,bucket in pool.items():
            for key,(_,p,snapshot) in bucket.items():
                if key in conflicts:continue
                if snapshot is None:
                    snapshot=copy.deepcopy(store.get(p['snapshot_obj']))
                    # v6 changed the envelope registry, while these scope roots
                    # and their exact definitions are identical. Source facts,
                    # signals, times and labels remain untouched.
                    before=P.digest(U.production_request(snapshot[1],U.V1.ARMS[1],event=snapshot[0]))
                    snapshot[0]['registry_sha256']=C.SHA256
                    assert before==P.digest(U.production_request(snapshot[1],U.V1.ARMS[1],event=snapshot[0]))
                materialized.append((p,snapshot))
    with S.Store(data_root) as store:
        points=[]
        for p,snapshot in materialized:points.append(dict(p,snapshot_obj=store.put(snapshot)))
        obj=store.put(points)
    code={Path(m.__file__).name:P.file_hash(m.__file__) for m in V.contract_modules()}
    result=P.seal(dict(schema=O.SCHEMA,source_date=machine['source_date'],policy_schema=V.SCHEMA,
        parent_bundle_sha256=parent['bundle_sha256'],operating_manifest=manifest,execution_code_sha256=P.digest(code),
        source_parent_machine_sha256=machine['artifact_content_sha256'],source_receipts=receipts,
        partitions=[dict(records_object=obj,records_sha256=P.digest(points),points=len(points))],
        population='all_source_partitions_with_bounded_hash_reservoir',selection=dict(seed=seed,per_scope=per_scope),
        eligible_census={k:dict(v) for k,v in census.items()},unchanged_scopes=sorted(same),replayed_scopes=sorted(changed),
        quarantined_conflicts=sorted(conflicts),development_keys=sorted(excluded),**P.AUTH))
    return result
