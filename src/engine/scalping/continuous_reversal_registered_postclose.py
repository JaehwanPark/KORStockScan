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
from collections import Counter, defaultdict
from datetime import datetime
from fractions import Fraction
from pathlib import Path
from src.engine.scalping import continuous_reversal as K
from src.engine.scalping import continuous_reversal_branches as B
from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.scalping import reversal_registered_catalog as C
from src.engine.scalping import reversal_registered_runtime as R
from src.engine.scalping import continuous_reversal_policy_v3 as V3
from src.engine.scalping import reversal_auxiliary_phases as A
from src.engine.scalping import reversal_auxiliary_contract as V1

SCHEMA = 'continuous_reversal_registered_postclose_v1'


def directory(data_root, day):
    return Path(data_root)/'report/continuous_reversal_registered'/day


def active(data_root, day):
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    bundle = N.load_effective(data_root=Path(data_root),target_date=day)
    return bundle if (bundle or {}).get('continuous_reversal',{}).get('schema') == V3.SCHEMA else None


def freeze_registration(data_root, day, research):
    """Copy minimal research custody into immutable, content-addressed sources."""
    out = directory(data_root,day)/'registered-sources'; out.mkdir(parents=True,exist_ok=True)
    records = []
    for name in ('research.py','supplement.py','validation.json','today-receipt.json','today.json.gz','union-summary.json','delivery.json'):
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


def replay(rows, *, symbol, venue, session, bars=None):
    """Features see the prefix only; labels run after all signals are frozen."""
    ids = [i for i in C.MANIFEST['definitions'] if C.applicable(i,C.cell_key(symbol,session,rows[0][3] or 1),venue)]
    # General type definitions depend on anchor price bands, not the first price.
    ids = list(dict.fromkeys(ids+[i for i in C.MANIFEST['definitions'] for b in C.BANDS
                    if C.applicable(i, f'{C.group(symbol)}|{K.market_bucket(session)}|{b}',venue)])) if C.group(symbol) != 'samsung' else ids
    anchor = next((r for r in rows if r[8]), None)
    state = R.State(branch_ids=ids,session_anchor=anchor); points=[]
    for index,row in enumerate(rows):
        for ready in state.observe(row,symbol=symbol,venue=venue,session=session):
            e = ready['event']; signals=e['branch_signals']
            base = {k:v for k,v in e.items() if k not in ('branch_signals','anchor_lineage','branch_features') and not k.startswith('_')}
            p = dict(event=base, entry_index=index, branch_hits=list(signals),
                     confirmed_signals={b:s for b,s in signals.items() if s['decision_phase']==B.CONFIRMED},
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
    out=directory(data_root,day); partitions=[]; receipts=[]
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
    bars={d:P.completed_bars(data_root,d,snapshot_sink=snapshot_sink) for d in dates}
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
        fingerprint=P.digest([C.SHA256,code,rec, bars[rec['day']][1],C.LABEL,source['artifact_content_sha256']])
        dst=out/'partitions'/(fingerprint+'.jsonl.gz'); meta=dst.with_suffix('.receipt.json'); dst.parent.mkdir(parents=True,exist_ok=True)
        if not dst.exists() or not meta.exists():
            raw=json.loads(gzip.decompress(Path(rec['path']).read_bytes()))['symbols']; census=Counter(); n=0
            tmp=dst.with_suffix('.partial')
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
                        points,counts=replay(strict,symbol=symbol,venue=rec['venue'],session=rec['session'],bars=supplement)
                        census.update(counts)
                        for point in points:
                            handle.write(json.dumps(point,ensure_ascii=True,allow_nan=False,separators=(',',':'))+'\n'); n+=1
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
    out=directory(data_root,day).parent;matches=[]
    for path in out.glob('????-??-??/registered-sources/registration-*.json'):
        if not '2026-06-05'<=path.parent.parent.name<=day:continue
        value=json.loads(path.read_text())
        if value.get('registry_sha256')!=C.SHA256:continue
        if value.get('artifact_content_sha256')!=P.seal(value)['artifact_content_sha256']:
            raise ValueError('registered_registration_receipt_invalid')
        records=value['source_receipts']
        if any(P.file_hash(r['path'])!=r['sha256'] for r in records):
            raise ValueError('registered_registration_source_changed')
        matches.append((value['artifact_content_sha256'],records+[dict(path=str(path.resolve()),sha256=P.file_hash(path))]))
    if not matches:return []
    if len({P.digest(records[:-1]) for _,records in matches})>1:
        raise ValueError('registered_registration_source_ambiguous')
    return sorted(matches)[0][1]


def metric(counter):
    return dict(wins=counter['WIN'],resolved=sum(counter[x] for x in ('WIN','FAIL_STOP','FAIL_TIMEOUT')),
                excluded=counter['UNRESOLVED'],counts=dict(counter))


def select(candidates, incumbent):
    eligible=[c for c in candidates if c['metrics']['resolved']]
    if not eligible:return None
    return max(eligible,key=lambda c:(Fraction(c['metrics']['wins'],c['metrics']['resolved']),c['payload_sha256']==incumbent['payload_sha256'],-candidates.index(c)))


def machine_report(data_root,day,publication,parent_bundle,*,source=None,publish_outputs=True):
    old,aux=V3.migrate(parent_bundle['continuous_reversal']); value,path=population(data_root,day,source=source)
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
            cell['routes'][route]=selected
            selected_scopes[key,route]=selected
        cells.append(cell)
    history_receipts=[record for r in history['consumed_versions'] if r.get('sha256') for record in
        (dict(path=r['path'],sha256=r['sha256']),dict(path=r['definition_path'],sha256=r['definition_sha256']))]
    report=P.seal(dict(schema=SCHEMA,source_date=day,target_date=day,publication_date=publication,status='completed',
        report_scope='main_mechanistic_entry',cells=cells,baseline_cells=list(old.values()),baseline_auxiliary_cells=list(aux.values()),
        parent_bundle_sha256=parent_bundle['bundle_sha256'],source_manifest_sha256=value['source_manifest_sha256'],
        population_path=str(path.resolve()),source_receipts=value['source_receipts']+[dict(path=str(path.resolve()),sha256=P.file_hash(path))]+registration_receipts(data_root,day)+history_receipts,
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
    from src.engine.scalping import continuous_reversal_branch_postclose as BP
    req=BP.request(point,arm)
    # Comparison owner/event/branch is excluded. Exact bytes plus generation
    # settings own transport reuse. The event timeline is already in the input.
    body={k:req[k] for k in ('candidate_input','candidate','control','stage')}
    identity=P.digest([point.get('canonical_id',point['event_id']),point['phase'],body])
    req['paired_replay_id']=identity
    return req


def import_exact_cache(data_root,day,db):
    paths=P.result_paths(data_root,day)+sorted((Path(data_root)/'report/continuous_reversal_v2').glob('????-??-??/provider-results.jsonl'))
    count=0
    for path in paths:
        if not '2026-06-05' <= path.parent.name <= day:continue
        with path.open() as handle:
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


def connect_ledger(data_root):
    path=Path(data_root)/'report/continuous_reversal_registered/request-ledger.sqlite3';path.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(path,timeout=30)
    db.execute('PRAGMA journal_mode=WAL');db.execute('PRAGMA synchronous=FULL')
    db.execute('CREATE TABLE IF NOT EXISTS requests(identity TEXT PRIMARY KEY, request TEXT NOT NULL, state TEXT NOT NULL, result TEXT, reserved_at TEXT)')
    if 'priority' not in {r[1] for r in db.execute('PRAGMA table_info(requests)')}:
        db.execute('ALTER TABLE requests ADD COLUMN priority INTEGER NOT NULL DEFAULT 0')
    db.execute('CREATE TABLE IF NOT EXISTS owners(generation TEXT, comparison TEXT, opportunity TEXT, arm TEXT, identity TEXT, outcome TEXT, PRIMARY KEY(generation,comparison,opportunity,arm))')
    db.execute('CREATE INDEX IF NOT EXISTS owners_generation_identity ON owners(generation,identity)')
    db.execute('CREATE INDEX IF NOT EXISTS requests_state_identity ON requests(state,identity)')
    db.execute('CREATE INDEX IF NOT EXISTS requests_priority ON requests(state,priority DESC,identity)')
    db.commit();return db


def prepare_inputs(data_root,day,machine):
    """No point/date cap. Reconstruct only selected and actual baseline paths."""
    value=json.loads(Path(machine['population_path']).read_text());winner={c['key']:c for c in machine['cells']};baseline={c['key']:c for c in machine['baseline_cells']}
    out=directory(data_root,day); path=out/'frozen'/('inputs-'+machine['artifact_content_sha256']+'.jsonl.gz')
    if not path.exists():
        tmp=path.with_suffix('.partial');tmp.parent.mkdir(parents=True,exist_ok=True)
        quarantined=set(machine.get('duplicate_census',{}).get('quarantined_identities',[]));seen=set()
        with gzip.open(tmp,'wt') as handle:
            for part in value['partitions']:
                rec=part['normalized_source'];raw=json.loads(gzip.decompress(Path(rec['path']).read_bytes()))['symbols'];features={}
                with gzip.open(part['path'],'rt') as points:
                    for line in points:
                        p=json.loads(line);e=p['event']
                        if p['canonical_id'] in quarantined or p['canonical_id'] in seen:continue
                        seen.add(p['canonical_id'])
                        if p['outcome']['status']=='UNRESOLVED':continue
                        key=C.cell_key(e['symbol'],e['market'],e['confirmation_price']);route=e['venue'];owners={}
                        for label,cells in (('selected',winner),('applied_baseline',baseline)):
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
                            values={k:float(v[i]) if math.isfinite(v[i]) else None for k,v in fs.items()}
                            values.update({k:signal[k] for k in K.INPUT_FEATURES[4:]})
                            signal['entry_index']=i
                            inp=K.make_input(signal,rows,values)
                            point=dict(event_id=signal['event_id'],event=signal,input=inp,phase=C.branch(bid)['decision_phase'],outcome=p['outcome'],
                                       comparison='|'.join((key,route,bid,C.branch(bid).get('definition_sha256',P.digest(C.definition(bid))),C.branch(bid)['decision_phase'])),
                                       canonical_id=p['canonical_id'],branch_id=bid,owners=labels)
                            handle.write(json.dumps(point,ensure_ascii=True,allow_nan=False,separators=(',',':'))+'\n')
                print('registered inputs',rec['day'],rec['venue'],rec['session'],flush=True)
        os.replace(tmp,path)
    db=connect_ledger(data_root);census=Counter();gen=machine['artifact_content_sha256']
    census['imported_exact_responses']=import_exact_cache(data_root,day,db)
    with gzip.open(path,'rt') as handle:
        for line in handle:
            point=json.loads(line);census['eligible_points']+=1
            for arm in V1.ARMS:
                req=request(point,arm);identity=req['paired_replay_id'];encoded=json.dumps(req,sort_keys=True,separators=(',',':'),ensure_ascii=True)
                existing=db.execute('SELECT request,state FROM requests WHERE identity=?',(identity,)).fetchone()
                if existing and json.loads(existing[0])['candidate_input']!=req['candidate_input']:raise ValueError('registered_request_digest_conflict')
                db.execute('INSERT OR IGNORE INTO requests(identity,request,state) VALUES (?,?,?)',(identity,encoded,'planned'))
                priority=3 if 'selected' in point['owners'] and not point['branch_id'].startswith('legacy_') else 2 if 'selected' in point['owners'] else 1
                db.execute('UPDATE requests SET priority=max(priority,?) WHERE identity=?',(priority,identity))
                db.execute('INSERT OR IGNORE INTO owners VALUES (?,?,?,?,?,?)',(gen,point['comparison'],point['canonical_id'],arm,identity,point['outcome']['status']))
                census['eligible_requests']+=1
            if census['eligible_points']%100==0:db.commit()
    db.commit()
    for state,count in db.execute('SELECT r.state,count(DISTINCT r.identity) FROM requests r JOIN owners o ON o.identity=r.identity WHERE o.generation=? GROUP BY r.state',(gen,)):
        census[state]=count
    db.close()
    report=P.seal(dict(schema=SCHEMA,source_date=day,machine_report_sha256=gen,input_path=str(path.resolve()),input_sha256=P.file_hash(path),
                       census=dict(census),call_limit=None,estimated_serial_seconds=census['planned']*2,
                       estimated_result_bytes=census['planned']*6000,status='prepared',**P.AUTH))
    P.write(out/'input-census.json',report);return report


def calls(data_root,day,*,stop_epoch=None,workers=4):
    """Bounded in-flight, unlimited count, durable replay across interrupted runs."""
    from src.engine.scalping.ai_decision_quality import execute_openai_prompt_v2_candidate
    out=directory(data_root,day);census=json.loads((out/'input-census.json').read_text());gen=census['machine_report_sha256']
    with (out/'provider-worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);db=connect_ledger(data_root)
        def call(req):
            try:
                result=execute_openai_prompt_v2_candidate(req,timeout_sec=30)
                phase=req['candidate_input'].get('observation_phase',{}).get('stage',B.FIRST)
                arm=req['micro_reversion_replay_arm']
                return dict(result=result,validation_errors=A.validate_response(result['candidate_response'],req['candidate_input'],arm=arm,phase=phase))
            except Exception as exc:return dict(error_type=type(exc).__name__,validation_errors=['provider_attempt_failed'])
        count=0
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            running={}
            while True:
                while len(running)<workers and (stop_epoch is None or time.time()<stop_epoch):
                    row=db.execute("SELECT r.identity,r.request FROM requests r JOIN owners o ON o.identity=r.identity WHERE r.state='planned' AND o.generation=? ORDER BY r.priority DESC,o.comparison,o.opportunity,o.arm,r.identity LIMIT 1",(gen,)).fetchone()
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
        states={s:n for s,n in db.execute('SELECT r.state,count(DISTINCT r.identity) FROM requests r JOIN owners o ON o.identity=r.identity WHERE o.generation=? GROUP BY r.state',(gen,))};db.close()
    report=P.seal(dict(schema=SCHEMA,source_date=day,status='evaluation_incomplete' if any(states.get(k) for k in ('planned','reserved','failed')) else 'completed',
                       new_calls=count,census=states,call_limit=None,uncertain_attempts_require_reconciliation=states.get('reserved',0),**P.AUTH))
    P.write(out/'call-completion.json',report);return report


def auxiliary_report(data_root,day,publication,parent_bundle,*,publish_policy=True):
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    out=directory(data_root,day);machine=json.loads((out/'machine-comparison.json').read_text());gen=machine['artifact_content_sha256']
    baseline={c['key']:c for c in machine['baseline_cells']}; oldaux={c['key']:c for c in machine['baseline_auxiliary_cells']}
    db=connect_ledger(data_root);groups=defaultdict(lambda:defaultdict(dict));metrics=defaultdict(lambda:{a:Counter() for a in V1.ARMS});gaps=Counter();expected=Counter()
    cursor=db.execute('SELECT o.comparison,o.opportunity,o.arm,o.outcome,r.state,r.result FROM owners o JOIN requests r ON r.identity=o.identity WHERE o.generation=? ORDER BY o.comparison,o.opportunity',(gen,))
    import itertools
    for (comparison,opp),records in itertools.groupby(cursor,key=lambda r:r[:2]):
        expected[comparison]+=1;rs={r[2]:r for r in records}
        if set(rs)!=set(V1.ARMS) or any(r[4]!='completed' for r in rs.values()):gaps[comparison]+=1;continue
        for arm,r in rs.items():
            result=json.loads(r[5]);m=metrics[comparison][arm];m['points']+=1;m['invalid_responses']+=bool(result['validation_errors'])
            if result['result']['candidate_response'].get('risk_verdict')=='PASS':m['pass_count']+=1;m['pass_wins']+=r[3]=='WIN'
    # Immutable actual-response evidence, not a live WAL or mutable ledger.
    evidence=out/'frozen'/('actual-'+gen+'-'+str(db.execute("SELECT count(*) FROM requests WHERE state='completed'").fetchone()[0])+'.jsonl.gz')
    if not evidence.exists():
        with gzip.open(evidence,'wt') as handle:
            for identity,req,result in db.execute("SELECT identity,request,result FROM requests WHERE state='completed' AND EXISTS(SELECT 1 FROM owners o WHERE o.identity=requests.identity AND o.generation=?)",(gen,)):
                handle.write(json.dumps(dict(request_identity=identity,request=json.loads(req),**json.loads(result)),ensure_ascii=True)+'\n')
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
                       source_receipts=machine['source_receipts']+[dict(path=str(comparison_path.resolve()),sha256=P.file_hash(comparison_path))],
                       status='completed_with_scope_carry' if pending else 'completed',scope_pending=pending))
    auxiliary=P.seal(dict(schema=SCHEMA,source_date=day,target_date=day,publication_date=publication,
        status='completed_with_scope_carry' if pending else 'completed',cells=acs,machine_report_sha256=issued['artifact_content_sha256'],
        results_sources=[proof],source_receipts=[],scope_pending=pending,comparison_complete=not bool(gaps),
        eligible_comparisons=dict(expected),incomplete_comparisons=dict(gaps),primary_metric='actual_raw_PASS_wins_over_all_actual_raw_PASS',
        call_limit=None,validity_adjustment_in_rank=False,**P.AUTH))
    P.write(out/'machine.json',issued);P.write(out/'auxiliary.json',auxiliary)
    # Machine-stage bytes remain frozen once its terminal receipt commits.
    # Issued runtime pairs are a separate compiled source bound to that report.
    P.write(P.directory(data_root,day)/'auxiliary.json',auxiliary)
    input_census=json.loads((out/'input-census.json').read_text())
    freeze=P.seal(dict(schema=SCHEMA,source_date=day,status='frozen',machine_report_sha256=gen,
                       call_limit=None,census=input_census['census'],input_sha256=input_census['input_sha256'],**P.AUTH))
    P.write(P.directory(data_root,day)/'call-freeze.json',freeze)
    canonical=P.directory(data_root,day)/'provider-results.jsonl';canonical.parent.mkdir(parents=True,exist_ok=True)
    with gzip.open(evidence,'rt') as src,canonical.open('w') as dst:
        for line in src:dst.write(line)
    if publish_policy:
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
