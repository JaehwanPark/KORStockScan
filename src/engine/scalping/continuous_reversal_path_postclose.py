"""Registered route-isolated replay and durable uncapped auxiliary comparison.

Partitions and requests are streamed. SQLite owns exact request reservations;
uncertain attempts require reconciliation and never silently call twice.
"""
from __future__ import annotations
import argparse
import copy
import concurrent.futures
import fcntl
import gzip
import json
import math
import os
import sqlite3
import time
import hashlib
import inspect
import tempfile
import threading
from collections import Counter, defaultdict
from datetime import datetime
from fractions import Fraction
from pathlib import Path
from src.engine.scalping import continuous_reversal as K
from src.engine.scalping import continuous_reversal_branches as B
from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.scalping import reversal_path_catalog as C
from src.engine.scalping import reversal_path_runtime as R
from src.engine.scalping import continuous_reversal_policy_v4 as V3
from src.engine.scalping import reversal_path_auxiliary as A
from src.engine.scalping import reversal_auxiliary_contract as V1

SCHEMA = 'continuous_reversal_path_postclose_v1'
_RUNS = {}
_BARS = {}


def directory(data_root, day):
    base=Path(data_root)/'report/continuous_reversal_registered/v4'/day
    key=str(base.resolve())
    if key not in _RUNS:
        receipt=json.loads((base/'current-run.json').read_text())
        if receipt['artifact_content_sha256']!=P.seal(receipt)['artifact_content_sha256']:
            raise ValueError('path_run_receipt_changed')
        _RUNS[key]=receipt['run_sha256']
    return base/_RUNS[key]


def begin_run(data_root,day,publication,parent_bundle,source):
    base=Path(data_root)/'report/continuous_reversal_registered/v4'/day
    code={Path(m.__file__).name:P.file_hash(m.__file__) for m in (K,B,C,R,A,V3,__import__(__name__,fromlist=['*']))}
    bar_key=str(Path(data_root).resolve()),day
    frozen=[]
    def sink(original,content):
        h=hashlib.sha256(content).hexdigest();target=base/'.bar-staging'/h
        if not target.exists():
            target.parent.mkdir(parents=True,exist_ok=True)
            fd,name=tempfile.mkstemp(dir=target.parent,prefix='.bar-')
            try:
                with os.fdopen(fd,'wb') as handle:handle.write(content);handle.flush();os.fsync(handle.fileno())
                os.replace(name,target)
            finally:
                if Path(name).exists():Path(name).unlink()
        if P.file_hash(target)!=h:raise ValueError('path_bar_custody_changed')
        return target
    bars={}
    for date in sorted({r['day'] for r in source['normalized_sources']['partitions']}):
        bars[date]=P.completed_bars(data_root,date,snapshot_sink=sink)
        frozen.extend(bars[date][1])
    _BARS[bar_key]=bars
    history=applied_census_raw(data_root,day)
    contract=dict(source_date=day,publication_date=publication,effective_date=publication,
        applied_census_sha256=P.digest(history),completed_bar_receipts=[r['sha256'] for r in frozen],
        parent_bundle_sha256=parent_bundle['bundle_sha256'],
        registry_sha256=C.SHA256,code=code,label=C.LABEL,source_manifest_sha256=source['artifact_content_sha256'],
        normalized_sources=source['normalized_sources'])
    run=P.digest(contract);_RUNS[str(base.resolve())]=run
    code_receipts=[]
    for m in (K,B,C,R,A,V3,__import__(__name__,fromlist=['*'])):
        path=base/run/'code'/Path(m.__file__).name;path.parent.mkdir(parents=True,exist_ok=True)
        original=Path(m.__file__);h=code[original.name]
        if P.file_hash(original)!=h:raise ValueError('path_run_code_changed_before_freeze')
        if not path.exists():
            with original.open('rb') as src,path.open('xb') as dst:
                import shutil
                shutil.copyfileobj(src,dst);dst.flush();os.fsync(dst.fileno())
        if P.file_hash(path)!=h:raise ValueError('path_run_code_snapshot_changed')
        code_receipts.append(dict(path=str(path.resolve()),sha256=h))
    for values,records in bars.values():
        for record in records:
            old=Path(record['path']);target=base/run/'frozen'/('bars-'+record['sha256']+'.json');target.parent.mkdir(parents=True,exist_ok=True)
            if not target.exists():os.link(old,target)
            if P.file_hash(target)!=record['sha256']:raise ValueError('path_run_bar_changed')
            record['path']=str(target.resolve())
    receipt=P.seal(dict(schema=SCHEMA,run_sha256=run,contract=contract,code_receipts=code_receipts,**P.AUTH))
    P.write(base/run/'run-contract.json',receipt);P.write(base/'current-run.json',receipt)
    return run


def applied_census_raw(data_root,day):
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    return [dict(path=str(p.resolve()),sha256=P.file_hash(p)) for p in sorted((N.root(Path(data_root))/'consumed'/day).rglob('*.json'))]


def active(data_root, day):
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    bundle = N.load_effective(data_root=Path(data_root),target_date=day)
    return bundle if (bundle or {}).get('continuous_reversal',{}).get('schema') == V3.SCHEMA else None


def freeze_registration(data_root, day, research):
    """Copy minimal research custody into immutable, content-addressed sources."""
    out = directory(data_root,day)/'registered-sources'; out.mkdir(parents=True,exist_ok=True)
    records = []
    for name in ('research.py','typed_rank.py','handoff.py','path_handoff.py','manifest.json','validation.json','proposed-path-registration-batch.json','proposed-type-registration-batch.json'):
        src = Path(research)/name
        if not src.is_file():
            raise ValueError('registered_research_source_missing:'+name)
        h = P.file_hash(src); dst = out/(h+'-'+name)
        if not dst.exists():
            dst.write_bytes(src.read_bytes())
        if P.file_hash(dst) != h:
            raise ValueError('registered_research_snapshot_changed')
        records.append(dict(name=name,path=str(dst.resolve()),sha256=h))
    value = P.seal(dict(schema=SCHEMA,source_date=day,registry_manifest=C.MANIFEST,
                        registry_sha256=C.SHA256,source_receipts=records,**P.AUTH))
    P.write(out/('registration-'+value['artifact_content_sha256']+'.json'),value)
    return value


def applied_census(data_root, day):
    """Native consumption proves application; prepared candidates are separate."""
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    rows = []; prepared = []; roots = N.root(Path(data_root))
    seen=set()
    for path in sorted((roots/'consumed'/day).rglob('*.json')):
        r = N._read(path)
        if (r.get('actual_pid_consumed') is not True or r.get('receipt_sha256') != P.digest({k:v for k,v in r.items() if k!='receipt_sha256'})):
            rows.append(dict(path=str(path),status='invalid_consumption_receipt')); continue
        identity=(r['bundle_sha256'],r.get('pid_identity',{}).get('start_ticks'))
        if identity in seen:continue
        seen.add(identity)
        gen = roots/'generations'/(r['bundle_sha256']+'.json')
        if not gen.is_file():
            rows.append(dict(path=str(path),status='historical_definition_missing')); continue
        bundle = N._read(gen); N.validate(bundle,target_date=bundle['target_date'])
        family = bundle.get('continuous_reversal') or {}
        try:
            machine,_ = V3.migrate(family)
            status = 'consumed_definition_available'
        except (ValueError,KeyError):
            machine = None; status = 'historical_definition_missing'
        frozen=directory(data_root,day)/'frozen'/('consumed-'+r['receipt_sha256']+'.json')
        N._atomic_write_json(frozen,r)
        rows.append(dict(path=str(frozen.resolve()),native_path=str(path.resolve()),sha256=P.file_hash(frozen),status=status,
                         definition_path=str(gen.resolve()),definition_sha256=P.file_hash(gen),
                         family_sha256=family.get('family_sha256'),bundle_sha256=r['bundle_sha256'],
                         release_commit=r.get('release_commit'),observed_at=r['observed_at'],
                         machine_cells=machine,applied_window_observed='unobservable_without_exact_stream_mapping',
                         cumulative_fixed_definition_replay='available' if machine else 'historical_definition_missing'))
    used = {r.get('bundle_sha256') for r in rows}
    for path in (roots/'candidates').glob('policy_*.json'):
        r = N._read(path)
        if r.get('bundle_sha256') not in used:
            prepared.append(dict(path=str(path.resolve()),bundle_sha256=r.get('bundle_sha256'),status='prepared_not_consumed'))
    return dict(consumed_versions=rows,prepared_versions=prepared,collector_live_mapping='not_observed')


def replay(rows, *, symbol, venue, session, bars=None, new_only=False):
    """Features see the prefix only; labels run after all signals are frozen."""
    ids = [i for i in C.MANIFEST['definitions'] if C.applicable(i,C.cell_key(symbol,session,rows[0][3] or 1),venue)]
    # General type definitions depend on anchor price bands, not the first price.
    ids = list(dict.fromkeys(ids+[i for i in C.MANIFEST['definitions'] for b in C.BANDS
                    if C.applicable(i, f'{C.group(symbol)}|{K.market_bucket(session)}|{b}',venue)])) if C.group(symbol) != 'samsung' else ids
    if new_only:ids=[bid for bid in ids if bid in C.NEW_DEFINITIONS]
    if not ids:return [],{}
    anchor = next((r for r in rows if r[8]), None)
    state = R.State(branch_ids=ids,session_anchor=anchor,offline=True); points=[]
    for index,row in enumerate(rows):
        for ready in state.observe(row,symbol=symbol,venue=venue,session=session):
            e = ready['event']; signals=e['branch_signals']
            base = {k:v for k,v in e.items() if k not in ('branch_signals','anchor_lineage','branch_features') and not k.startswith('_')}
            p = dict(event=base, entry_index=index, branch_hits=list(signals),
                     confirmed_signals=copy.deepcopy(signals),path_inputs=copy.deepcopy(ready.get('path_inputs',{})),
                     anchor_lineage=e['anchor_lineage'], canonical_id=e['canonical_opportunity_id'])
            if base['decision_phase']==B.CONFIRMED:
                first=next((s for s in signals.values() if s['decision_phase']==B.FIRST),None)
                if first:p['first_signal']=first
            # FIRST and CONFIRMED share one actual ask/label at this tick.
            if any(s['entry_ask'] != base['entry_ask'] for s in signals.values()):
                raise ValueError('registered_same_tick_ask_conflict')
            points.append(p)
        # Offline labeling consumes each observation immediately. Live ready
        # capacity must never become a retrospective population sample cap.
        state.ready.clear()
    times=[r[0] for r in rows]; _,ends,valid=K.segments(rows)
    tree=K.Tree([r[3] if r[8] else None for r in rows])
    for p in points:
        e=p['event']; outcome=K.label(rows,times,tree,ends,valid,p['entry_index'],e['entry_ask'])
        if outcome['status']=='UNRESOLVED' and e['entry_ask'] is not None and bars:
            supplement=bars.label(e['epoch'],e['entry_ask'],1800)
            if supplement['status']!='UNRESOLVED':outcome={**supplement,'source':'same_item_completed_bar_backfill'}
        p['outcome']=outcome
    return points,dict(state.counts)


def population(data_root,day,*,source=None):
    source=source or P.ensure_population(data_root,day)
    if source['artifact_content_sha256']!=P.seal(source)['artifact_content_sha256']:
        raise ValueError('registered_source_manifest_invalid')
    out=directory(data_root,day);partitions=[]
    run_receipt=json.loads((out/'run-contract.json').read_text());receipts=run_receipt['code_receipts']+[dict(path=str((out/'run-contract.json').resolve()),sha256=P.file_hash(out/'run-contract.json'))]
    records=source['normalized_sources']['partitions']; dates=sorted({r['day'] for r in records})
    def snapshot_sink(original,content):
        h=hashlib.sha256(content).hexdigest();dst=out/'frozen'/('bars-'+h+'.json');dst.parent.mkdir(parents=True,exist_ok=True)
        if dst.exists():
            if P.file_hash(dst)!=h:raise ValueError('registered_bar_snapshot_changed')
            return dst
        fd,tmp=tempfile.mkstemp(dir=dst.parent,prefix='.bars-')
        try:
            with os.fdopen(fd,'wb') as handle:handle.write(content);handle.flush();os.fsync(handle.fileno())
            try:os.link(tmp,dst)
            except FileExistsError:
                if P.file_hash(dst)!=h:raise ValueError('registered_bar_snapshot_changed')
        finally:os.unlink(tmp)
        return dst
    bars=_BARS.get((str(Path(data_root).resolve()),day)) or {d:P.completed_bars(data_root,d,snapshot_sink=snapshot_sink) for d in dates}
    previous={}
    if source.get('base_population'):
        origin=source['base_population']
        if P.file_hash(origin['path'])!=origin['sha256']:raise ValueError('path_base_population_changed')
        base=json.loads(Path(origin['path']).read_text())
        if (base.get('artifact_content_sha256')!=P.seal(base)['artifact_content_sha256']
                or base.get('registry_sha256')!=C.OLD.SHA256):
            raise ValueError('path_base_population_invalid')
        previous={P.digest(p['normalized_source']):p for p in base['partitions']}
        receipts.extend(base['source_receipts']);receipts.append(origin)
    for d,(_,rs) in bars.items():
        for rec in rs:
            dst=out/'frozen'/('bars-'+rec['sha256']+'.json'); dst.parent.mkdir(parents=True,exist_ok=True)
            if not dst.exists():dst.write_bytes(Path(rec['path']).read_bytes())
            if P.file_hash(dst)!=rec['sha256']:raise ValueError('registered_bar_snapshot_changed')
            receipts.append(dict(path=str(dst.resolve()),sha256=rec['sha256']))
    for rec in records:
        market=K.market_bucket(rec['session'])
        if rec['venue'] not in C.ROUTES.get(market,()):continue
        if P.file_hash(rec['path'])!=rec['sha256']:raise ValueError('registered_source_changed')
        code={Path(m.__file__).name:P.file_hash(m.__file__) for m in (K,B,C,R,P)}
        code['registered_replay_functions_sha256']=P.digest([inspect.getsource(replay),inspect.getsource(population)])
        old=previous.get(P.digest(rec))
        fingerprint=P.digest([C.SHA256,code,rec,bars[rec['day']][1],C.LABEL,old])
        dst=out/'partitions'/(fingerprint+'.jsonl.gz'); meta=dst.with_suffix('.receipt.json'); dst.parent.mkdir(parents=True,exist_ok=True)
        if not dst.exists() or not meta.exists():
            for cached in sorted(out.parent.glob('*/partitions/'+dst.name)):
                cached_meta=cached.with_suffix('.receipt.json')
                if cached==dst or not cached_meta.exists():continue
                record=json.loads(cached_meta.read_text())
                if record.get('fingerprint')!=fingerprint or P.file_hash(cached)!=record.get('sha256'):continue
                if not dst.exists():os.link(cached,dst)
                if not meta.exists():os.link(cached_meta,meta)
                break
        if not dst.exists() or not meta.exists():
            raw=json.loads(gzip.decompress(Path(rec['path']).read_bytes()))['symbols']; census=Counter(); n=0
            tmp=dst.with_suffix('.partial')
            old_points={}
            if old:
                if P.file_hash(old['path'])!=old['sha256']:raise ValueError('path_base_partition_changed')
                with gzip.open(old['path'],'rt') as stream:
                    for line in stream:
                        point=json.loads(line);old_points[point['canonical_id']]=point
                census.update(old['census'])
            with gzip.open(tmp,'wt') as handle:
                from src.engine.scalping.micro_reversion.forward_collector import _explicit_item_venue
                for symbol,rows in sorted(raw.items()):
                    items={r[9] for r in rows if isinstance(r[9],str) and r[9].split('_',1)[0]==symbol and _explicit_item_venue(r[9])==rec['venue']}
                    for item in sorted(items):
                        strict=[r[:] for r in rows]
                        for r in strict:
                            if r[9]!=item:r[8]=0
                        supplement=bars[rec['day']][0].get((rec['day'],item))
                        if supplement and rec.get('cutoff_epoch') is not None:
                            supplement=K.Bars([r for r in supplement.rows if r['t']+60 <= rec['cutoff_epoch']])
                        prior_points=[p for p in old_points.values() if p['event']['symbol']==symbol and p['event']['source_item']==item]
                        if prior_points:
                            times=[r[0] for r in strict];_,ends,valid=K.segments(strict)
                            tree=K.Tree([r[3] if r[8] else None for r in strict])
                            for point in prior_points:
                                e=point['event'];outcome=K.label(strict,times,tree,ends,valid,point['entry_index'],e['entry_ask'])
                                if outcome['status']=='UNRESOLVED' and e['entry_ask'] is not None and supplement:
                                    enriched=supplement.label(e['epoch'],e['entry_ask'],1800)
                                    if enriched['status']!='UNRESOLVED':outcome={**enriched,'source':'same_item_completed_bar_backfill'}
                                point['outcome']=outcome
                        points,counts=replay(strict,symbol=symbol,venue=rec['venue'],session=rec['session'],bars=supplement,new_only=bool(old))
                        census.update(counts)
                        for point in points:
                            prior=old_points.pop(point['canonical_id'],None)
                            if prior:
                                if prior['entry_index']!=point['entry_index'] or prior['event']['entry_ask']!=point['event']['entry_ask']:
                                    raise ValueError('path_base_identity_conflict')
                                point['branch_hits']=list(dict.fromkeys(prior['branch_hits']+point['branch_hits']))
                                point['confirmed_signals']=dict(prior.get('confirmed_signals',{}),**point['confirmed_signals'])
                                if prior.get('first_signal'):point['first_signal']=prior['first_signal']
                                for bid in prior['branch_hits']:
                                    if bid not in point['confirmed_signals']:
                                        first=prior.get('first_signal') or prior['event']
                                        if C.branch(bid)['decision_phase']!=B.FIRST or first['decision_phase']!=B.FIRST:
                                            raise ValueError('path_base_branch_signal_missing')
                                        point['confirmed_signals'][bid]=copy.deepcopy(first)
                                point['anchor_lineage']=dict(prior.get('anchor_lineage',{}),**point['anchor_lineage'])
                                # Reused branches retain their frozen prefix/outcome.
                                if prior['outcome']!=point['outcome']:
                                    raise ValueError('path_same_prefix_label_conflict')
                            handle.write(json.dumps(point,ensure_ascii=True,allow_nan=False,separators=(',',':'))+'\n'); n+=1
                for point in sorted(old_points.values(),key=lambda p:p['canonical_id']):
                    handle.write(json.dumps(point,ensure_ascii=True,allow_nan=False,separators=(',',':'))+'\n');n+=1
            os.replace(tmp,dst)
            P.write(meta,dict(fingerprint=fingerprint,sha256=P.file_hash(dst),points=n,census=dict(census),normalized_source=rec))
            print('registered replay',rec['day'],rec['venue'],rec['session'],n,flush=True)
        value=json.loads(meta.read_text())
        if value['fingerprint']!=fingerprint or P.file_hash(dst)!=value['sha256']:raise ValueError('registered_partition_cache_changed')
        partitions.append(dict(path=str(dst.resolve()),**value)); receipts.append(dict(path=rec['path'],sha256=rec['sha256']))
        receipts.append(dict(path=str(dst.resolve()),sha256=value['sha256']))
    report=P.seal(dict(schema=SCHEMA,source_date=day,status='completed',source_manifest_sha256=source['artifact_content_sha256'],
                       registry_sha256=C.SHA256,partitions=partitions,source_receipts=receipts,**P.AUTH))
    path=out/'frozen'/('population-'+report['artifact_content_sha256']+'.json');P.write(path,report)
    return report,path


def iter_points(population):
    for part in population['partitions']:
        if P.file_hash(part['path'])!=part['sha256']:raise ValueError('registered_partition_changed')
        with gzip.open(part['path'],'rt') as handle:
            for line in handle:yield json.loads(line)


def unique_points(population, census):
    """Deduplicate identical observations and quarantine conflicting identities."""
    identities={};conflicts=set()
    for point in iter_points(population):
        identity=point['canonical_id'];signature=P.digest(point)
        if identity in identities:
            census['duplicate_rows']=census.get('duplicate_rows',0)+1
            if identities[identity]!=signature:conflicts.add(identity)
        else:identities[identity]=signature
    census['quarantined_identities']=sorted(conflicts)
    seen=set()
    for point in iter_points(population):
        identity=point['canonical_id']
        if identity in conflicts or identity in seen:continue
        seen.add(identity);yield point


def registration_receipts(data_root, day):
    """Bind the exact registered evidence to issued policies, outside live tmp."""
    out=Path(data_root)/'report/continuous_reversal_registered/v4';matches=[]
    for path in out.glob('????-??-??/*/registered-sources/registration-*.json'):
        if not '2026-06-05'<=path.parent.parent.parent.name<=day:continue
        value=json.loads(path.read_text())
        if value.get('registry_sha256')!=C.SHA256:continue
        if value.get('artifact_content_sha256')!=P.seal(value)['artifact_content_sha256']:
            raise ValueError('registered_registration_receipt_invalid')
        records=value['source_receipts']
        if any(P.file_hash(r['path'])!=r['sha256'] for r in records):
            raise ValueError('registered_registration_source_changed')
        matches.append((value['artifact_content_sha256'],records+[dict(path=str(path.resolve()),sha256=P.file_hash(path))]))
    if not matches:return []
    if len({P.digest([(r.get('name'),r['sha256']) for r in records[:-1]]) for _,records in matches})>1:
        raise ValueError('registered_registration_source_ambiguous')
    return sorted(matches)[0][1]


def metric(counter):
    return dict(wins=counter['WIN'],resolved=sum(counter[x] for x in ('WIN','FAIL_STOP','FAIL_TIMEOUT')),
                excluded=counter['UNRESOLVED'],counts=dict(counter))


def source_quality(data_root, day, population):
    """Count identifiable row exclusions; missing native items are not empty."""
    key=P.digest([population['artifact_content_sha256'],inspect.getsource(source_quality)])
    path=directory(data_root,day)/'frozen'/('row-quality-'+key+'.json')
    if path.exists():
        value=json.loads(path.read_text())
        if value['artifact_content_sha256']!=P.seal(value)['artifact_content_sha256']:
            raise ValueError('registered_row_quality_changed')
        return value,path
    from src.engine.scalping.micro_reversion.forward_collector import _explicit_item_venue
    scopes=defaultdict(Counter);partitions=[];total=Counter()
    for part in population['partitions']:
        rec=part['normalized_source'];raw=json.loads(gzip.decompress(Path(rec['path']).read_bytes()))['symbols'];counts=Counter()
        for symbol,rows in raw.items():
            for row in rows:
                local=Counter(total_rows=1)
                valid_price=type(row[3]) in (int,float) and math.isfinite(row[3]) and row[3]>0
                item=row[9];native_item=isinstance(item,str) and item.split('_',1)[0]==symbol and _explicit_item_venue(item)==rec['venue']
                if not native_item:local['source_item_excluded_rows']+=1
                if not row[8] or not valid_price:local['path_ineligible_rows']+=1
                if row[8] and valid_price and native_item:
                    local['native_eligible_rows']+=1
                    if not K.good_quote(row):local['entry_quote_unavailable_rows']+=1
                counts.update(local)
                if valid_price:scopes[C.cell_key(symbol,rec['session'],row[3])+'|'+rec['venue']].update(local)
        partitions.append(dict(day=rec['day'],venue=rec['venue'],session=rec['session'],counts=dict(counts)));total.update(counts)
    value=P.seal(dict(schema=SCHEMA,source_date=day,status='completed',population_sha256=population['artifact_content_sha256'],
        row_exclusion=True,totals=dict(total),partitions=partitions,scope_counts={k:dict(v) for k,v in scopes.items()},**P.AUTH))
    P.write(path,value);return value,path


def select(candidates, incumbent):
    eligible=[c for c in candidates if c['metrics']['resolved']]
    if not eligible:return None
    return max(eligible,key=lambda c:(Fraction(c['metrics']['wins'],c['metrics']['resolved']),c['payload_sha256']==incumbent['payload_sha256'],-candidates.index(c)))


def machine_report(data_root,day,publication,parent_bundle,*,source=None,publish_outputs=True):
    source=source or P.ensure_population(data_root,day)
    begin_run(data_root,day,publication,parent_bundle,source)
    old,aux=V3.migrate(parent_bundle['continuous_reversal']); value,path=population(data_root,day,source=source)
    quality,quality_path=source_quality(data_root,day,value)
    history=applied_census(data_root,day); catalogs={}; counts={}; branch_counts={}; duplicate_census={}
    for key in C.cells():
        for route in old[key]['routes']:
            portfolios=list(C.PORTFOLIOS[key][route]); seen={tuple(p['branch_ids']) for p in portfolios}
            additions=[old[key]['routes'][route]['payload']]
            additions += [r['machine_cells'][key]['routes'][route]['payload'] for r in history['consumed_versions'] if r.get('machine_cells')]
            for payload in additions:
                ids=tuple(b['branch_id'] for b in payload['branches'])
                if ids not in seen:
                    portfolios.append(dict(portfolio_id=P.digest(ids),branch_ids=list(ids),origin='actual_applied_or_incumbent'));seen.add(ids)
            catalogs[key,route]=portfolios; counts[key,route]={p['portfolio_id']:Counter() for p in portfolios}
            branch_counts[key,route]=defaultdict(Counter)
    for point in unique_points(value,duplicate_census):
        e=point['event']; identity=point['canonical_id']; scope=C.cell_key(e['symbol'],e['market'],e['confirmation_price']),e['venue']
        status=point['outcome']['status']; hits=set(point['branch_hits'])
        for b in hits:branch_counts[scope][b][status]+=1
        for p in catalogs[scope]:
            if hits.intersection(p['branch_ids']):counts[scope][p['portfolio_id']][status]+=1
    cells=[];selected_scopes={}
    for key in sorted(C.cells(),key=lambda k:'|REGULAR|' not in k):
        cell=dict(key=key,routes={})
        for route,parent in old[key]['routes'].items():
            candidates=[]
            for p in catalogs[key,route]:
                payload=B.payload([C.branch(i) for i in p['branch_ids']]);m=metric(counts[key,route][p['portfolio_id']])
                candidates.append(dict(**p,payload=payload,payload_sha256=P.digest(payload),metrics=m,
                    status='eligible' if m['resolved'] else 'no_resolved_sample' if m['excluded'] else 'valid_empty'))
            winner=select(candidates,parent)
            if winner:
                payload=winner['payload']; bm={b['branch_id']:metric(branch_counts[key,route][b['branch_id']]) for b in payload['branches']}
                local={b:m if m['resolved'] else None for b,m in bm.items()}
                selected=dict(payload=payload,payload_sha256=P.digest(payload),local_metrics=winner['metrics'],branch_metrics=local,
                    status='machine_selected_auxiliary_pending',carry_source=None,candidates=candidates,
                    incumbent_not_comparable=not next(c['metrics']['resolved'] for c in candidates if c['payload_sha256']==parent['payload_sha256']))
            else:
                g,market,band=key.split('|');regular=f'{g}|REGULAR|{band}'
                choices=([selected_scopes.get((regular,route)),old[regular]['routes'].get(route)] if market!='REGULAR' else [])+[parent]
                compatible=[]
                for choice in choices:
                    if not choice:continue
                    try:C.validate_payload(choice['payload'],key,route)
                    except ValueError:continue
                    compatible.append(choice)
                if not compatible:raise ValueError('applicable_parent_missing:'+key+':'+route)
                selected=copy.deepcopy(compatible[0]);selected.update(candidates=candidates,status='carry_no_resolved_sample',local_metrics=None)
                selected['priority_metrics']={b['branch_id']:selected['branch_metrics'].get(b['branch_id']) or selected.get('priority_metrics',{}).get(b['branch_id']) for b in selected['payload']['branches']}
                selected['branch_metrics']={b['branch_id']:None for b in selected['payload']['branches']}
                selected['carry_source']=dict(family_sha256=parent_bundle['continuous_reversal']['family_sha256'],
                    cell_key=regular if compatible[0] is not parent else key,parent_payload_sha256=selected['payload_sha256'],reason='no_local_resolved_sample_compatible_regular_then_verified_previous')
            qc=quality['scope_counts'].get(key+'|'+route,{})
            selected['scope_source_status']='source_gap_no_eligible_native_item_rows' if qc.get('total_rows') and not qc.get('native_eligible_rows') else 'eligible_native_rows' if qc.get('native_eligible_rows') else 'no_observations'
            if selected['scope_source_status'].startswith('source_gap') and selected['local_metrics'] is None:
                selected['status']='carry_source_gap'
                for candidate in selected['candidates']:
                    if candidate['status']=='valid_empty':candidate['status']='source_gap_not_comparable'
            cell['routes'][route]=selected
            selected_scopes[key,route]=selected
        cells.append(cell)
    history_receipts=[record for r in history['consumed_versions'] if r.get('sha256') for record in
        (dict(path=r['path'],sha256=r['sha256']),dict(path=r['definition_path'],sha256=r['definition_sha256']))]
    source_path=directory(data_root,day)/'frozen/source-manifest.json'
    P.write(source_path,source)
    report=P.seal(dict(schema=SCHEMA,source_date=day,target_date=day,publication_date=publication,status='completed',
        report_scope='main_mechanistic_entry',cells=cells,baseline_cells=list(old.values()),baseline_auxiliary_cells=list(aux.values()),
        parent_bundle_sha256=parent_bundle['bundle_sha256'],source_manifest_sha256=value['source_manifest_sha256'],
        population_path=str(path.resolve()),source_receipts=value['source_receipts']+[dict(path=str(source_path.resolve()),sha256=P.file_hash(source_path)),dict(path=str(path.resolve()),sha256=P.file_hash(path)),dict(path=str(quality_path.resolve()),sha256=P.file_hash(quality_path))]+registration_receipts(data_root,day)+history_receipts,
        source_row_exclusions=quality['totals'],
        label_contract=C.LABEL,selection_basis='cumulative_raw_win_fraction',registry_sha256=C.SHA256,
        applied_history=history,duplicate_census=duplicate_census,**P.AUTH))
    P.write(directory(data_root,day)/'machine-comparison.json',report)
    if publish_outputs:
        P.write(P.directory(data_root,day)/'machine.json',report)
        standard=Path(data_root)/'report/ai_decision_action_outcome_calibration'
        P.write(standard/f'winrate_policy_{day}.json',report)
        P.write(standard/f'winrate_policy_terminal_{day}.json',P.seal(dict(schema=SCHEMA,source_date=day,target_date=day,status='completed',
            selection_basis=report['selection_basis'],report_sha256=report['artifact_content_sha256'],disposition='continuous_reversal_selected',
            policy_sha256=P.digest(cells),staged=dict(status='machine_component_prepared'),**P.AUTH)))
    return report


def request(point,arm):
    inp,prompt,schema=A.production_request(point['input'],arm,phase=point['phase'],event=point['event'])
    from src.engine.scalping.ai_decision_quality import _sha256
    req=dict(paired_replay_parent_id=point['event_id'],micro_reversion_replay_arm=arm,
        offline_provider_attempt_number=1,stage='entry',candidate_input=inp,candidate_input_sha256=_sha256(inp),
        control=dict(provider='openai',model='gpt-5.4-nano'),
        candidate=dict(provider='openai',model='gpt-5.4-nano',prompt_version=A.binding(point['phase'],arm)['prompt_version'],
            system_prompt=prompt,response_schema=schema,response_schema_sha256=_sha256(schema),
            schema_name='entry_setup_risk_adjudication_v1',max_output_tokens=512,reasoning_effort='none'),**P.AUTH)
    # Comparison owner/event/branch is excluded. Exact bytes plus generation
    # settings own transport reuse. The event timeline is already in the input.
    body={k:req[k] for k in ('candidate_input','candidate','control','stage')}
    identity=P.digest([point.get('canonical_id',point['event_id']),point['phase'],body])
    req['paired_replay_id']=identity
    return req


def import_exact_cache(data_root,day,db):
    paths=P.result_paths(data_root,day)+sorted((Path(data_root)/'report/continuous_reversal_v2').glob('????-??-??/provider-results.jsonl'))
    paths=[p for p in paths if '2026-06-05'<=p.parent.name<=day]
    machine=json.loads((directory(data_root,day)/'machine-comparison.json').read_text())
    receipts={}
    for cell in machine['baseline_auxiliary_cells']:
        for route in cell['routes'].values():
            for policy in route['payload']['branch_policies'].values():
                rs=policy.get('actual_response_evidence') or []
                for record in [rs] if isinstance(rs,dict) else rs:receipts[record['path']]=record['sha256']
    for name,h in receipts.items():
        path=Path(name)
        if P.file_hash(path)!=h:raise ValueError('path_exact_export_changed')
        paths.append(path)
    count=0
    for original in dict.fromkeys(paths):
        h=P.file_hash(original);path=directory(data_root,day)/'frozen'/('import-'+h+('.jsonl.gz' if original.suffix=='.gz' else '.jsonl'))
        if not path.exists():
            with original.open('rb') as src,path.open('xb') as dst:
                import shutil
                shutil.copyfileobj(src,dst);dst.flush();os.fsync(dst.fileno())
        if P.file_hash(path)!=h:raise ValueError('path_exact_import_changed')
        opener=gzip.open if path.suffix=='.gz' else open
        with opener(path,'rt') as handle:
            for line in handle:
                r=json.loads(line);req=r.get('request');result=r.get('result') or {}
                if not req or not result.get('provider_provenance',{}).get('response_id'):continue
                try:
                    d,venue,session,symbol,epoch,sequence=req['paired_replay_parent_id'].split(':')
                    inp=req['candidate_input'];phase=inp['observation_phase']['stage']
                    canonical=P.digest([d,symbol,K.market_bucket(session),venue,inp['source_item'],int(epoch),int(sequence)])
                    body={k:req[k] for k in ('candidate_input','candidate','control','stage')}
                    identity=P.digest([canonical,phase,body]);req=copy.deepcopy(req);req['paired_replay_id']=identity
                    errors=A.validate_response(result['candidate_response'],inp,arm=req['micro_reversion_replay_arm'],phase=phase)
                except (ValueError,KeyError,TypeError):continue
                record=dict(result=result,validation_errors=errors,source_record_path=str(path.resolve()))
                old=db.execute('SELECT result FROM requests WHERE identity=?',(identity,)).fetchone()
                if old and old[0] and json.loads(old[0]).get('result') != result:raise ValueError('registered_exact_response_conflict')
                db.execute("INSERT OR IGNORE INTO requests(identity,request,state,result) VALUES (?,?,'completed',?)",(identity,json.dumps(req,ensure_ascii=True),json.dumps(record,ensure_ascii=True)))
                if old and not old[0]:
                    db.execute("UPDATE requests SET state='completed',result=? WHERE identity=?",(json.dumps(record,ensure_ascii=True),identity))
                count+=1
    db.commit();return count


def provider_lock_path(data_root):
    return Path(data_root)/'report/continuous_reversal_registered/v4/provider-worker.lock'


def connect_ledger(data_root, *, provider_lock_held=False):
    path=Path(data_root)/'report/continuous_reversal_registered/v4/request-ledger.sqlite3';path.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(path,timeout=30)
    db.execute('PRAGMA journal_mode=WAL');db.execute('PRAGMA synchronous=FULL')
    db.execute('PRAGMA cache_size=-65536')
    wanted={'owners_generation_identity','owners_point_cover','requests_state_identity','requests_priority','requests_outcome_cover'}
    existing={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='index'")}
    migration=not wanted.issubset(existing)
    schema_lock=None
    if migration and not provider_lock_held:
        schema_lock=provider_lock_path(data_root).open('a')
        try:fcntl.flock(schema_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            schema_lock.close();db.close();raise ValueError('registered_ledger_migration_provider_worker_active')
    try:
        db.execute('CREATE TABLE IF NOT EXISTS requests(identity TEXT PRIMARY KEY, request TEXT NOT NULL, state TEXT NOT NULL, result TEXT, reserved_at TEXT)')
        if 'priority' not in {r[1] for r in db.execute('PRAGMA table_info(requests)')}:
            db.execute('ALTER TABLE requests ADD COLUMN priority INTEGER NOT NULL DEFAULT 0')
        db.execute('CREATE TABLE IF NOT EXISTS owners(generation TEXT, comparison TEXT, opportunity TEXT, arm TEXT, identity TEXT, outcome TEXT, PRIMARY KEY(generation,comparison,opportunity,arm))')
        db.execute('CREATE INDEX IF NOT EXISTS owners_generation_identity ON owners(generation,identity)')
        db.execute('CREATE INDEX IF NOT EXISTS owners_point_cover ON owners(generation,comparison,opportunity,arm,identity)')
        db.execute('CREATE INDEX IF NOT EXISTS requests_state_identity ON requests(state,identity)')
        db.execute('CREATE INDEX IF NOT EXISTS requests_priority ON requests(state,priority DESC,identity)')
        db.execute('CREATE INDEX IF NOT EXISTS requests_outcome_cover ON requests(identity,state,result)')
        db.commit()
    except Exception:
        db.close();raise
    finally:
        if schema_lock:schema_lock.close()
    return db


def reconcile_journal(db, path):
    """Restore exact durable responses without making another provider call."""
    if not path.exists():return 0
    restored=0
    with path.open('rb+') as handle:
        safe_offset=0
        for line in handle:
            if not line.endswith(b'\n'):
                # Keep crash evidence before removing the unusable append tail.
                tail=path.with_name(path.name+'.partial-'+hashlib.sha256(line).hexdigest())
                with tail.open('wb') as saved:
                    saved.write(line);saved.flush();os.fsync(saved.fileno())
                handle.truncate(safe_offset);handle.flush();os.fsync(handle.fileno());break
            safe_offset=handle.tell()
            row=json.loads(line);identity=row['request_identity'];req=row['request'];record=row['record']
            old=db.execute('SELECT request,state,result FROM requests WHERE identity=?',(identity,)).fetchone()
            if not old or req.get('paired_replay_id')!=identity or json.loads(old[0])!=req:
                raise ValueError('registered_response_journal_request_conflict')
            if old[2] and json.loads(old[2]).get('result')!=record.get('result'):
                raise ValueError('registered_response_journal_result_conflict')
            if old[1] in {'completed','failed'}:continue
            state='completed' if (record.get('result') or {}).get('provider_provenance',{}).get('response_id') else 'failed'
            db.execute('UPDATE requests SET state=?,result=? WHERE identity=?',(state,json.dumps(record,ensure_ascii=True),identity));restored+=1
    db.commit();return restored


def ledger_states(db, generation):
    return dict(db.execute("SELECT r.state,count(*) FROM requests r INDEXED BY requests_state_identity WHERE EXISTS(SELECT 1 FROM owners o INDEXED BY owners_generation_identity WHERE o.generation=? AND o.identity=r.identity) GROUP BY r.state",(generation,)))


def prepare_inputs(data_root,day,machine):
    root=provider_lock_path(data_root);root.parent.mkdir(parents=True,exist_ok=True)
    with root.open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        return _prepare_inputs(data_root,day,machine)


def eligible_population_points(machine, population):
    """Declare owners from frozen population, independently of input creation."""
    winner={c['key']:c for c in machine['cells']}
    baseline={c['key']:c for c in machine['baseline_cells']}
    applied=[('consumed:'+r['family_sha256'],r['machine_cells'])
             for r in machine['applied_history']['consumed_versions'] if r.get('machine_cells')]
    quarantined=set(machine.get('duplicate_census',{}).get('quarantined_identities',[]));seen=set()
    for part in population['partitions']:
        with gzip.open(part['path'],'rt') as handle:
            for line in handle:
                point=json.loads(line);e=point['event'];identity=point['canonical_id']
                if identity in quarantined or identity in seen:continue
                seen.add(identity)
                if point['outcome']['status']=='UNRESOLVED':continue
                key=C.cell_key(e['symbol'],e['market'],e['confirmation_price']);route=e['venue'];owners={}
                for label,cells in [('selected',winner),('applied_baseline',baseline),*applied]:
                    cell=cells[key]['routes'][route]
                    hits=[b['branch_id'] for b in cell['payload']['branches'] if b['branch_id'] in point['branch_hits']]
                    if hits:owners.setdefault(V3.primary(cell,hits),[]).append(label)
                for bid,labels in owners.items():
                    branch=C.branch(bid)
                    comparison='|'.join((key,route,bid,branch.get('definition_sha256',P.digest(C.definition(bid))),branch['decision_phase']))
                    yield dict(comparison=comparison,canonical_id=identity,branch_id=bid,
                               owners=labels,outcome=point['outcome'])


def input_owner_census(points):
    counts=Counter();identities=hashlib.sha256();digests=[]
    for point in points:
        counts[point['comparison']]+=1
        identity=[point[k] for k in ('comparison','canonical_id','branch_id','owners','outcome')]
        digests.append(P.digest(identity))
    # Grouping input reconstruction must not change the declared owner set.
    # Only small identity digests are sorted, never raw points or request BLOBs.
    for digest in sorted(digests):identities.update((digest+'\n').encode('ascii'))
    return dict(comparisons=dict(counts),eligible_points=sum(counts.values()),
                owners_sha256=identities.hexdigest(),expected_requests=5*sum(counts.values()))


def grouped_partition_points(part, out):
    """Disk grouping for merged/interleaved sources; one feature array at a time."""
    with tempfile.TemporaryDirectory(prefix='.input-group-',dir=out) as temporary:
        db=sqlite3.connect(str(Path(temporary)/'points.sqlite3'))
        try:
            db.execute('CREATE TABLE points(symbol TEXT,item TEXT,ordinal INTEGER,body TEXT,PRIMARY KEY(symbol,item,ordinal)) WITHOUT ROWID')
            with gzip.open(part['path'],'rt') as handle:
                for ordinal,line in enumerate(handle):
                    point=json.loads(line);event=point['event']
                    db.execute('INSERT INTO points VALUES (?,?,?,?)',(event['symbol'],event['source_item'],ordinal,line))
            db.commit()
            for body, in db.execute('SELECT body FROM points ORDER BY symbol,item,ordinal'):
                yield json.loads(body)
        finally:db.close()


def input_generation():
    return P.digest(dict(code={Path(m.__file__).name:P.file_hash(m.__file__)
        for m in (K,B,A,V1,__import__(__name__,fromlist=['*']))},
        typed_input_version=A.VERSION,phase_bindings=C.PHASES))


def _prepare_inputs(data_root,day,machine):
    """No point/date cap. Reconstruct only selected and actual baseline paths."""
    value=json.loads(Path(machine['population_path']).read_text());winner={c['key']:c for c in machine['cells']};baseline={c['key']:c for c in machine['baseline_cells']}
    out=directory(data_root,day);input_gen=input_generation()
    path=out/'frozen'/('inputs-'+machine['artifact_content_sha256']+'-'+input_gen+'.jsonl.gz')
    code_receipts=[]
    for module in (K,B,A,V1,__import__(__name__,fromlist=['*'])):
        origin=Path(module.__file__);h=P.file_hash(origin);target=out/'code'/('input-'+h+'-'+origin.name)
        target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():
            with origin.open('rb') as src,target.open('xb') as dst:
                import shutil
                shutil.copyfileobj(src,dst);dst.flush();os.fsync(dst.fileno())
        if P.file_hash(target)!=h:raise ValueError('path_input_code_snapshot_changed')
        code_receipts.append(dict(path=str(target.resolve()),sha256=h))
    universe=P.seal(dict(schema=SCHEMA,machine_report_sha256=machine['artifact_content_sha256'],
        population_sha256=P.file_hash(machine['population_path']),
        input_generation_sha256=input_gen,source_receipts=code_receipts,
        **input_owner_census(eligible_population_points(machine,value)),**P.AUTH))
    # This independent declaration commits before any input or ledger write.
    P.write(out/'frozen'/('universe-'+machine['artifact_content_sha256']+'.json'),universe)
    if not path.exists():
        tmp=path.with_suffix('.partial');tmp.parent.mkdir(parents=True,exist_ok=True)
        quarantined=set(machine.get('duplicate_census',{}).get('quarantined_identities',[]));seen=set()
        with gzip.open(tmp,'wt') as handle:
            for part in value['partitions']:
                rec=part['normalized_source'];raw=json.loads(gzip.decompress(Path(rec['path']).read_bytes()))['symbols'];features={}
                for p in grouped_partition_points(part,out):
                    e=p['event']
                    if p['canonical_id'] in quarantined or p['canonical_id'] in seen:continue
                    seen.add(p['canonical_id'])
                    if p['outcome']['status']=='UNRESOLVED':continue
                    key=C.cell_key(e['symbol'],e['market'],e['confirmation_price']);route=e['venue'];owners={}
                    applied=[('consumed:'+r['family_sha256'],r['machine_cells']) for r in machine['applied_history']['consumed_versions'] if r.get('machine_cells')]
                    for label,cells in [('selected',winner),('applied_baseline',baseline),*applied]:
                        cell=cells[key]['routes'][route];hits=[b['branch_id'] for b in cell['payload']['branches'] if b['branch_id'] in p['branch_hits']]
                        if not hits:continue
                        bid=V3.primary(cell,hits); owners.setdefault(bid,[]).append(label)
                    if not owners:continue
                    fk=e['symbol'],e['source_item']
                    if fk not in features:
                        # Partitions are symbol ordered. Retain only one
                        # symbol/item projection, not every full array.
                        features.clear()
                        rows=[r[:] for r in raw[e['symbol']]]
                        for r in rows:
                            if r[9]!=e['source_item']:r[8]=0
                        features[fk]=(rows,K.build_features(rows))
                    rows,fs=features[fk];i=p['entry_index']
                    for bid,labels in owners.items():
                        signal=copy.deepcopy(p['confirmed_signals'].get(bid) or p.get('first_signal') or dict(e,decision_phase=B.FIRST))
                        if bid in p.get('path_inputs',{}):
                            inp=copy.deepcopy(p['path_inputs'][bid])
                        else:
                            values={k:float(v[i]) if math.isfinite(v[i]) else None for k,v in fs.items()}
                            values.update({k:signal[k] for k in K.INPUT_FEATURES[4:]})
                            signal['entry_index']=i
                            inp=K.make_input(signal,rows,values)
                        point=dict(event_id=signal['event_id'],event=signal,input=inp,phase=C.branch(bid)['decision_phase'],outcome=p['outcome'],
                                   comparison='|'.join((key,route,bid,C.branch(bid).get('definition_sha256',P.digest(C.definition(bid))),C.branch(bid)['decision_phase'])),
                                   canonical_id=p['canonical_id'],branch_id=bid,owners=labels)
                        handle.write(json.dumps(point,ensure_ascii=True,allow_nan=False,separators=(',',':'))+'\n')
                print('registered inputs',rec['day'],rec['venue'],rec['session'],flush=True)
        with tmp.open('rb') as durable:os.fsync(durable.fileno())
        if input_generation()!=input_gen:raise ValueError('path_input_producer_changed')
        os.replace(tmp,path)
    with gzip.open(path,'rt') as handle:
        actual=input_owner_census(json.loads(line) for line in handle)
    if any(actual[k]!=universe[k] for k in actual):
        raise ValueError('path_expected_population_input_mismatch')
    expected=P.seal(dict(schema=SCHEMA,machine_report_sha256=machine['artifact_content_sha256'],
        input_sha256=P.file_hash(path),universe_sha256=universe['artifact_content_sha256'],
        **actual,**P.AUTH))
    P.write(out/'frozen'/('expected-'+machine['artifact_content_sha256']+'.json'),expected)
    db=connect_ledger(data_root,provider_lock_held=True);census=Counter();gen=machine['artifact_content_sha256']
    census['imported_exact_responses']=import_exact_cache(data_root,day,db)
    with gzip.open(path,'rt') as handle:
        for line in handle:
            point=json.loads(line);census['eligible_points']+=1
            requests={arm:request(point,arm) for arm in V1.ARMS}
            owners=dict(db.execute('SELECT arm,identity FROM owners WHERE generation=? AND comparison=? AND opportunity=?',
                (gen,point['comparison'],point['canonical_id'])))
            if owners=={arm:req['paired_replay_id'] for arm,req in requests.items()}:
                census['eligible_requests']+=len(requests);census['resumed_prepared_points']+=1
                continue
            for arm in V1.ARMS:
                req=requests[arm];identity=req['paired_replay_id'];encoded=json.dumps(req,sort_keys=True,separators=(',',':'),ensure_ascii=True)
                existing=db.execute('SELECT request,state FROM requests WHERE identity=?',(identity,)).fetchone()
                if existing and json.loads(existing[0])['candidate_input']!=req['candidate_input']:raise ValueError('registered_request_digest_conflict')
                db.execute('INSERT OR IGNORE INTO requests(identity,request,state) VALUES (?,?,?)',(identity,encoded,'planned'))
                priority=3 if 'selected' in point['owners'] and not point['branch_id'].startswith('legacy_') else 2 if 'selected' in point['owners'] else 1
                db.execute('UPDATE requests SET priority=max(priority,?) WHERE identity=?',(priority,identity))
                db.execute('INSERT OR IGNORE INTO owners VALUES (?,?,?,?,?,?)',(gen,point['comparison'],point['canonical_id'],arm,identity,point['outcome']['status']))
                census['eligible_requests']+=1
            if census['eligible_points']%100==0:db.commit()
    db.commit()
    owner_states=dict(db.execute('SELECT r.state,count(*) FROM owners o JOIN requests r ON r.identity=o.identity WHERE o.generation=? GROUP BY r.state',(gen,)))
    if sum(owner_states.values())!=expected['expected_requests']:
        raise ValueError('path_expected_owner_ledger_missing')
    census['expected_owner_requests']=expected['expected_requests']
    for state,count in ledger_states(db,gen).items():
        census[state]=count
    db.close()
    report=P.seal(dict(schema=SCHEMA,source_date=day,machine_report_sha256=gen,input_path=str(path.resolve()),input_sha256=P.file_hash(path),
                       input_generation_sha256=input_gen,source_receipts=code_receipts,
                       expected_manifest_sha256=expected['artifact_content_sha256'],owner_states=owner_states,census=dict(census),call_limit=None,estimated_serial_seconds=census['planned']*2,
                       estimated_result_bytes=census['planned']*6000,status='prepared',**P.AUTH))
    P.write(out/'input-census.json',report);return report


def calls(data_root,day,*,stop_epoch=None,workers=4):
    """Bounded in-flight, unlimited count, durable replay across interrupted runs."""
    if not isinstance(workers,int) or isinstance(workers,bool) or not 1<=workers<=4:
        raise ValueError('path_provider_concurrency_invalid')
    from src.engine.scalping.ai_decision_quality import execute_openai_prompt_v2_candidate
    out=directory(data_root,day);census=json.loads((out/'input-census.json').read_text());gen=census['machine_report_sha256']
    with provider_lock_path(data_root).open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);db=connect_ledger(data_root,provider_lock_held=True)
        journal=Path(data_root)/'report/continuous_reversal_registered/v4/provider-response-journal.jsonl'
        reconcile_journal(db,journal);journal_lock=threading.Lock()
        def call(req):
            try:
                result=execute_openai_prompt_v2_candidate(req,timeout_sec=30)
                phase=req['candidate_input'].get('observation_phase',{}).get('stage',B.FIRST)
                arm=req['micro_reversion_replay_arm']
                try:errors=A.validate_response(result['candidate_response'],req['candidate_input'],arm=arm,phase=phase)
                except (ValueError,KeyError,TypeError):errors=['response_validation_failed']
                record=dict(result=result,validation_errors=errors)
            except Exception as exc:record=dict(error_type=type(exc).__name__,validation_errors=['provider_attempt_failed'])
            with journal_lock:P.append(journal,dict(request_identity=req['paired_replay_id'],request=req,record=record))
            return record
        count=0
        # Sort only small identity metadata once, never all request BLOBs for
        # every call. The SQLite cursor streams IDs; only in-flight payloads
        # enter Python memory. Recheck state before each durable reservation.
        queue=db.execute("SELECT r.identity FROM requests r INDEXED BY requests_priority CROSS JOIN owners o INDEXED BY owners_generation_identity WHERE r.state='planned' AND o.generation=? AND o.identity=r.identity GROUP BY r.identity ORDER BY max(r.priority) DESC,min(o.comparison),min(o.opportunity),min(o.arm),r.identity",(gen,))
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            running={}
            while True:
                while len(running)<workers and (stop_epoch is None or time.time()<stop_epoch):
                    queued=queue.fetchone()
                    row=db.execute("SELECT identity,request FROM requests WHERE identity=? AND state='planned'",(queued[0],)).fetchone() if queued else None
                    if queued and not row:continue
                    if not row:break
                    identity,raw=row;req=json.loads(raw)
                    db.execute("UPDATE requests SET state='reserved',reserved_at=? WHERE identity=? AND state='planned'",(datetime.now(K.KST).isoformat(),identity));db.commit()
                    running[pool.submit(call,req)]=identity
                if not running:break
                done,_=concurrent.futures.wait(running,return_when=concurrent.futures.FIRST_COMPLETED)
                for future in done:
                    identity=running.pop(future);result=future.result()
                    state='completed' if (result.get('result') or {}).get('provider_provenance',{}).get('response_id') else 'failed'
                    db.execute('UPDATE requests SET state=?,result=? WHERE identity=?',(state,json.dumps(result,ensure_ascii=True),identity));db.commit();count+=1
                    if count%25==0:print('registered actual responses',count,flush=True)
        queue.close()
        states=ledger_states(db,gen);db.close()
    report=P.seal(dict(schema=SCHEMA,source_date=day,status='evaluation_incomplete' if any(states.get(k) for k in ('planned','reserved','failed')) else 'completed',
                       new_calls=count,census=states,call_limit=None,uncertain_attempts_require_reconciliation=states.get('reserved',0),**P.AUTH))
    P.write(out/'call-completion.json',report);return report


def auxiliary_report(data_root,day,publication,parent_bundle,*,publish_policy=True):
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    out=directory(data_root,day);machine=json.loads((out/'machine-comparison.json').read_text());gen=machine['artifact_content_sha256']
    baseline={c['key']:c for c in machine['baseline_cells']}; oldaux={c['key']:c for c in machine['baseline_auxiliary_cells']}
    quality,quality_path=source_quality(data_root,day,json.loads(Path(machine['population_path']).read_text()))
    input_census=json.loads((out/'input-census.json').read_text())
    if (input_census['machine_report_sha256']!=gen
            or P.file_hash(input_census['input_path'])!=input_census['input_sha256']):
        raise ValueError('registered_input_census_source_changed')
    with gzip.open(input_census['input_path'],'rt') as handle:
        actual=input_owner_census(json.loads(line) for line in handle)
    declared=Counter(actual['comparisons'])
    expected_manifest=json.loads((out/'frozen'/('expected-'+gen+'.json')).read_text())
    universe=json.loads((out/'frozen'/('universe-'+gen+'.json')).read_text())
    if (expected_manifest['artifact_content_sha256']!=P.seal(expected_manifest)['artifact_content_sha256']
            or expected_manifest['artifact_content_sha256']!=input_census['expected_manifest_sha256']
            or universe['artifact_content_sha256']!=P.seal(universe)['artifact_content_sha256']
            or universe['artifact_content_sha256']!=expected_manifest['universe_sha256']
            or any(actual[k]!=expected_manifest[k] or actual[k]!=universe[k] for k in actual)
            or expected_manifest['input_sha256']!=input_census['input_sha256']):
        raise ValueError('path_expected_census_changed')
    if sum(declared.values())!=input_census['census']['eligible_points']:
        raise ValueError('registered_input_census_point_count_changed')
    db=connect_ledger(data_root);db.execute('BEGIN')
    metrics=defaultdict(lambda:{a:Counter() for a in V1.ARMS});gaps=Counter();expected=Counter()
    owner_states=dict(db.execute('SELECT r.state,count(*) FROM owners o JOIN requests r ON r.identity=o.identity WHERE o.generation=? GROUP BY r.state',(gen,)))
    missing_owner_requests=expected_manifest['expected_requests']-sum(owner_states.values())
    if missing_owner_requests<0:raise ValueError('path_ledger_unexpected_owner_requests')
    cursor=db.execute('SELECT o.comparison,o.opportunity,o.arm,o.outcome,r.state,r.result FROM owners o JOIN requests r INDEXED BY requests_outcome_cover ON r.identity=o.identity WHERE o.generation=? ORDER BY o.comparison,o.opportunity',(gen,))
    import itertools
    for (comparison,opp),records in itertools.groupby(cursor,key=lambda r:r[:2]):
        expected[comparison]+=1;rs={r[2]:r for r in records}
        if set(rs)!=set(V1.ARMS) or any(r[4]!='completed' for r in rs.values()):gaps[comparison]+=1;continue
        for arm,r in rs.items():
            result=json.loads(r[5]);m=metrics[comparison][arm];m['points']+=1;m['invalid_responses']+=bool(result['validation_errors'])
            if result['result']['candidate_response'].get('risk_verdict')=='PASS':m['pass_count']+=1;m['pass_wins']+=r[3]=='WIN'
    if any(expected[c]>declared[c] for c in expected):raise ValueError('registered_ledger_unexpected_point')
    for comparison,count in declared.items():gaps[comparison]+=count-expected[comparison]
    gaps=+gaps
    expected=declared
    # Immutable actual-response evidence, not a live WAL or mutable ledger.
    fd,name=tempfile.mkstemp(prefix='.actual-',suffix='.jsonl.gz',dir=out/'frozen');os.close(fd);tmp=Path(name)
    try:
        with tmp.open('wb') as raw,gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as handle:
            for identity,req,result in db.execute("SELECT identity,request,result FROM requests INDEXED BY requests_state_identity WHERE state='completed' AND EXISTS(SELECT 1 FROM owners o INDEXED BY owners_generation_identity WHERE o.identity=requests.identity AND o.generation=?) ORDER BY identity",(gen,)):
                handle.write((json.dumps(dict(request_identity=identity,request=json.loads(req),**json.loads(result)),ensure_ascii=True)+'\n').encode())
        with tmp.open('rb') as durable:os.fsync(durable.fileno())
        evidence=out/'frozen'/('actual-'+gen+'-'+P.file_hash(tmp)+'.jsonl.gz')
        if evidence.exists():tmp.unlink()
        else:os.replace(tmp,evidence)
    finally:
        if tmp.exists():tmp.unlink()
    db.close();proof=dict(path=str(evidence.resolve()),sha256=P.file_hash(evidence));published=[];acs=[];pending=[];regular_aux={};regular_machine={}
    for mc in machine['cells']:
        key=mc['key'];published_cell=dict(key=key,routes={});aux_cell=dict(key=key,routes={})
        for route,cell in mc['routes'].items():
            policies={};not_ready=[]
            regular=key.replace('|PRE|','|REGULAR|').replace('|AFTER|','|REGULAR|')
            inherited=(cell.get('local_metrics') is None and regular!=key
                       and cell.get('carry_source',{}).get('cell_key')==regular
                       and regular_machine.get((regular,route),{}).get('payload_sha256')==cell['payload_sha256'])
            for b in cell['payload']['branches']:
                bid=b['branch_id'];comparison='|'.join((key,route,bid,b.get('definition_sha256',P.digest(C.definition(bid))),b['decision_phase']))
                old=oldaux[key]['routes'][route]['payload']['branch_policies'].get(bid)
                if inherited:
                    old=regular_aux[regular,route]['branch_policies'].get(bid)
                    if old:
                        old=copy.deepcopy(old);old['local_metrics']=None
                        old['carry_source']=dict(comparison_report_sha256=gen,cell_key=regular,
                                                branch_id=bid,binding_sha256=P.digest(old['binding']),reason='no_sample_compatible_regular_selected')
                eligible=[a for a in V1.TIE_ORDER if metrics[comparison][a]['pass_count']]
                # No partial comparison is allowed to masquerade as a winner.
                if expected[comparison] and not gaps[comparison] and eligible:
                    arm=max(eligible,key=lambda a:(Fraction(metrics[comparison][a]['pass_wins'],metrics[comparison][a]['pass_count']),bool(old and old['arm']==a)))
                    policies[bid]=dict(arm=arm,binding=A.binding(b['decision_phase'],arm),local_metrics=dict(metrics[comparison][arm]),
                                       actual_response_evidence=[proof],comparison_key=comparison,candidates={a:dict(m) for a,m in metrics[comparison].items()})
                elif old:
                    policies[bid]=copy.deepcopy(old)
                else:not_ready.append(bid)
            if not_ready:
                pending.append(dict(cell_key=key,route=route,status='machine_selected_auxiliary_pending',branches=not_ready,comparison_gaps={b:gaps.get('|'.join((key,route,b,C.branch(b).get('definition_sha256',P.digest(C.definition(b))),C.branch(b)['decision_phase'])),0) for b in not_ready}))
                selected=copy.deepcopy(baseline[key]['routes'][route]);ap=copy.deepcopy(oldaux[key]['routes'][route]['payload'])
                selected['status']='carry_machine_selected_auxiliary_pending'
            else:
                selected=copy.deepcopy(cell);selected['status']='selected' if cell['local_metrics'] else 'carry'
                ap=dict(branch_policies=policies)
            selected.pop('candidates',None)
            selected['comparison_report_sha256']=gen
            published_cell['routes'][route]=selected
            aux_cell['routes'][route]=dict(payload=ap,payload_sha256=P.digest(ap),status='carry' if not_ready else 'selected_or_verified_carry')
            if '|REGULAR|' in key:
                regular_aux[key,route]=ap;regular_machine[key,route]=selected
        published.append(published_cell);acs.append(aux_cell)
    # The comparison report remains intact; issued reports explicitly separate
    # machine winners from the deployable machine+auxiliary pairs.
    comparison_path=out/'frozen'/('machine-comparison-'+gen+'.json')
    P.write(comparison_path,machine)
    issued=P.seal(dict(machine,cells=published,comparison_report_sha256=gen,
                       source_receipts=machine['source_receipts']+input_census['source_receipts']+[
                           dict(path=str(comparison_path.resolve()),sha256=P.file_hash(comparison_path)),
                           dict(path=str(quality_path.resolve()),sha256=P.file_hash(quality_path)),
                           dict(path=str((out/'input-census.json').resolve()),sha256=P.file_hash(out/'input-census.json')),
                           dict(path=str((out/'frozen'/('universe-'+gen+'.json')).resolve()),sha256=P.file_hash(out/'frozen'/('universe-'+gen+'.json')))],
                       source_row_exclusions=quality['totals'],
                       status='completed_with_scope_carry' if pending else 'completed',scope_pending=pending))
    auxiliary=P.seal(dict(schema=SCHEMA,source_date=day,target_date=day,publication_date=publication,
        status='completed_with_scope_carry' if pending else 'completed',cells=acs,machine_report_sha256=issued['artifact_content_sha256'],
        results_sources=[proof],source_receipts=[],scope_pending=pending,comparison_complete=not bool(gaps),
        owner_request_census=dict(expected=expected_manifest['expected_requests'],missing=missing_owner_requests,reconciled=not missing_owner_requests,**owner_states),
        comparison_statuses={c:'evaluation_incomplete' if gaps[c] else 'completed' if any(metrics[c][a]['pass_count'] for a in V1.ARMS) else 'completed_no_pass' for c in declared},
        eligible_comparisons=dict(expected),incomplete_comparisons=dict(gaps),primary_metric='actual_raw_PASS_wins_over_all_actual_raw_PASS',
        call_limit=None,validity_adjustment_in_rank=False,**P.AUTH))
    P.write(out/'machine.json',issued);P.write(out/'auxiliary.json',auxiliary)
    # Machine-stage bytes remain frozen once its terminal receipt commits.
    # Issued runtime pairs are a separate compiled source bound to that report.
    freeze=P.seal(dict(schema=SCHEMA,source_date=day,status='frozen',machine_report_sha256=gen,
                       call_limit=None,census=input_census['census'],input_sha256=input_census['input_sha256'],**P.AUTH))
    if publish_policy:
        P.write(P.directory(data_root,day)/'auxiliary.json',auxiliary)
        P.write(P.directory(data_root,day)/'call-freeze.json',freeze)
        canonical=P.directory(data_root,day)/'provider-results.jsonl';canonical.parent.mkdir(parents=True,exist_ok=True)
        with gzip.open(evidence,'rt') as src,canonical.open('w') as dst:
            for line in src:dst.write(line)
        import subprocess
        commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
        bundle=V3.stage(data_root,day,publication,issued,auxiliary,target_date=N.next_target(publication),release_commit=commit)
        P.write(Path(data_root)/'report/ai_entry_setup_paired_replay_batch'/f'compact_auxiliary_paired_economic_{day}.json',P.seal(dict(auxiliary,staged=dict(status='prepared',bundle_sha256=bundle['bundle_sha256'],target_date=bundle['target_date']))))
    return auxiliary


def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('--date',required=True);p.add_argument('--data-root',type=Path,default=Path('data'));p.add_argument('--mode',choices=('machine','prepare-inputs','calls','auxiliary'),required=True)
    p.add_argument('--publication-date');p.add_argument('--evaluate-only',action='store_true');args=p.parse_args(argv)
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    publication=args.publication_date or args.date;parent=N.load_effective(data_root=args.data_root,target_date=publication)
    if args.mode=='machine':result=machine_report(args.data_root,args.date,publication,parent)
    elif args.mode=='prepare-inputs':result=prepare_inputs(args.data_root,args.date,json.loads((directory(args.data_root,args.date)/'machine-comparison.json').read_text()))
    elif args.mode=='calls':result=calls(args.data_root,args.date)
    else:result=auxiliary_report(args.data_root,args.date,publication,parent,publish_policy=not args.evaluate_only)
    print(json.dumps(result if args.mode!='machine' else dict(status=result['status'],cells=len(result['cells']))));return 0


if __name__=='__main__':raise SystemExit(main())
