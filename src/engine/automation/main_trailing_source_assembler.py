"""Automatic source-only Main exit research input assembly.

Consumes verified master, original bootstrap/census and native AI traces. It
never reads the holding report it extends, rewrites journals, calls providers,
or allocates aggregate broker costs. Missing paths/costs remain census gaps.
"""
from collections import Counter
from datetime import date, datetime, timedelta
import gzip
import hashlib
import json
from pathlib import Path
from zoneinfo import ZoneInfo
import time

from src.engine.lifecycle import research_storage as storage
from src.engine.lifecycle.holding_window_generation import byte_generation, capture_window, verify_window
from src.engine.lifecycle.research_input_budget import Claim
from src.engine.scalping.pre_submit_delay_initial_policy import digest, _atomic, number
from src.engine.scalping.universal_trailing_replay import completed_sources
from src.engine.scalping.micro_reversion.symbol_master import VerifiedSymbolMaster

SCHEMA = 'main_all_scope_exit_automatic_source_v1'


def input_inventory(root,days,master_path,parent_path):
    if not days: raise ValueError('all_scope_assembly_date_window_empty')
    paths={Path(master_path),Path(parent_path)}
    for day in days:
        for namespace,stem in (('ai_decision_trace','ai_decision_trace'),('ai_decision_payloads','ai_decision_payloads'),('ai_decision_prompts','ai_decision_prompts'),
                               ('ai_decision_requests','ai_decision_requests')):
            paths.update((Path(root)/namespace).glob(stem+'_'+day+'.jsonl*'))
        paths.update((Path(root)/'report/monitor_snapshots').glob('trade_review_'+day+'*.json'))
    paths.update((Path(root)/'runtime/holding_path_votes').glob('*.jsonl*'))
    paths.update((Path(root)/'runtime/mechanistic_entry_policy/decisions'/days[-1]).glob('*/*.json'))
    return [{'path':str(p.resolve()),'generation':byte_generation(p)} for p in sorted(paths) if p.is_file()]


def verify_inventory(manifest, assembly_root):
    """Detect new files as well as changes to previously consumed sources."""
    if 'assembly_inventory_ref' not in manifest:
        return  # Historical manually normalized manifests retain their contract.
    from .main_trailing_all_scope_research import code_contract
    if manifest.get('assembly_code_contract_sha256')!=code_contract():
        raise ValueError('all_scope_assembly_code_changed')
    root=Path(manifest['source_data_root']).resolve()
    _,master=universe(root,manifest['source_date'])
    current=input_inventory(root,manifest['consumed_dates'],master['path'],
        root/'runtime/policy_bootstrap'/f"runtime_policy_bootstrap_{manifest['source_date']}.json")
    from itertools import zip_longest
    if any(old!=new for old,new in zip_longest(
            storage.iter_tree(assembly_root,manifest['assembly_inventory_ref']),current)):
        raise ValueError('all_scope_assembly_inventory_changed')


def read(path):
    before = byte_generation(path)
    opener = gzip.open if path.suffix=='.gz' else open
    with Claim(4*1024*1024*8),opener(path,'rb') as handle:
        raw=handle.read(4*1024*1024+1)
        if len(raw)>4*1024*1024: raise ValueError('all_scope_source_partition_required')
        value=json.loads(raw)
    if byte_generation(path)!=before: raise ValueError('all_scope_source_changed')
    return value,before


def universe(root, day):
    directory=Path(root)/'report/micro_reversion_economic_reference'
    candidates=[p for p in directory.glob('micro_reversion_symbol_master_????-??-??.json*')
        if p.name.removesuffix('.gz').removesuffix('.json')[-10:]<=day and p.name.endswith(('.json','.json.gz'))]
    if not candidates: raise ValueError('all_scope_verified_universe_missing')
    latest=max(p.name.removesuffix('.gz').removesuffix('.json')[-10:] for p in candidates)
    aliases=[p for p in candidates if p.name.removesuffix('.gz').removesuffix('.json')[-10:]==latest]
    values=[(p,*read(p)) for p in aliases]
    if len({digest(value) for _,value,_ in values})!=1:
        raise ValueError('all_scope_universe_alias_conflict')
    path,payload,generation=values[0]
    master=VerifiedSymbolMaster.from_payload(payload,require_canonical_owner=True)
    rows=[]
    for code in sorted({r['symbol'] for r in payload['records']}):
        found=master.lookup(code,as_of=date.fromisoformat(day))
        record=found.record
        known=datetime.fromisoformat(record.verified_at).timestamp() if record else None
        # Listing metadata alone cannot prove a current trading halt is absent.
        rows.append({'code':code,'known_at':known,'tradable':None,
                     'master_lookup_status':found.status.value})
    return rows,{'path':str(path),'generation':generation,'semantic_sha256':digest(payload)}


def select_stream(root,namespace,day,sources):
    plain=Path(root)/namespace/f'{namespace}_{day}.jsonl'
    aliases=[p for p in (plain,Path(str(plain)+'.gz')) if p.exists()]
    if not aliases:return None
    hashes=[]
    for path in aliases:
        generation=byte_generation(path);sources[str(path)]=generation
        if path.suffix=='.gz':
            sha=hashlib.sha256()
            with gzip.open(path,'rb') as handle:
                for block in iter(lambda:handle.read(65536),b''):sha.update(block)
            hashes.append(sha.hexdigest())
        else:hashes.append(generation['sha256'])
        if byte_generation(path)!=generation:raise ValueError('all_scope_stream_changed')
    if len(set(hashes))!=1:raise ValueError('all_scope_plain_gzip_conflict')
    return aliases[0]


def _native_index(root,days,sources,gaps,db):
    from src.engine.scalping.ai_decision_trace import _json_bytes
    db.execute('CREATE TABLE native(id TEXT PRIMARY KEY,body TEXT,semantic TEXT,conflict INTEGER DEFAULT 0) WITHOUT ROWID')
    for day in days:
        path=select_stream(root,'ai_decision_payloads',day,sources)
        if path is None:continue
        generation=sources[str(path)]
        opener=gzip.open if path.suffix=='.gz' else open
        limit=2*1024*1024
        with opener(path,'rb') as handle,Claim(limit*8):
            while True:
                offset=handle.tell();raw=handle.readline(limit+1)
                if not raw:break
                if len(raw)>limit or not raw.endswith(b'\n'):
                    while raw and not raw.endswith(b'\n'):raw=handle.readline(storage.RECORD_BYTES)
                    gaps['native_payload_oversize_or_partial']+=1;continue
                try:
                    row=json.loads(raw)
                    if row.get('schema')!='mechanistic_entry_observation_v1':continue
                    identity=row['machine_observation_sha256']
                    if hashlib.sha256(_json_bytes({k:v for k,v in row.items() if k!='machine_observation_sha256'})).hexdigest()!=identity:
                        raise ValueError('native_observation_hash_invalid')
                    source=row['source'];assessment=source['assessment'];event=assessment.get('event') or {}
                    if assessment.get('action')!='ENTER_NOW':continue
                    if not (assessment.get('canonical_opportunity_id') and row['label_context'].get('evaluation_attempt_id')):continue
                    fields={k:event[k] for k in ('at','event_id','native_epoch','planned_qty','buy_basis_krw','entry_cost_model','item','source_item',
                        'execution_plan_sha256','entry_depth_verified','trailing_entry_context','universal_trailing_quote') if k in event}
                    minimal={'canonical_opportunity_id':assessment['canonical_opportunity_id'],
                        'machine_observation_sha256':identity,'evaluation_attempt_id':row['label_context']['evaluation_attempt_id'],
                        'symbol':row['label_context']['stock_code'],'bundle_sha256':row['bundle_sha256'],
                        'captured_at':row['captured_at'],'fields':fields,
                        'source_reference':{'path':str(path),'decoded_offset':offset,'sha256':hashlib.sha256(raw).hexdigest()}}
                    body=storage.encoded(minimal).decode()
                    if len(body.encode())>storage.RECORD_BYTES:raise ValueError('native_projection_partition_required')
                    semantic=digest({k:v for k,v in minimal.items() if k!='source_reference'})
                    db.execute('INSERT INTO native(id,body,semantic) VALUES (?,?,?) ON CONFLICT(id) DO UPDATE SET '
                        'conflict=CASE WHEN native.semantic!=excluded.semantic THEN 1 ELSE conflict END, '
                        'body=CASE WHEN native.semantic=excluded.semantic AND excluded.body<native.body '
                        'THEN excluded.body ELSE native.body END',(identity,body,semantic))
                except (ValueError,TypeError,KeyError,AttributeError):gaps['native_payload_binding_invalid']+=1
        if byte_generation(path)!=generation:raise ValueError('all_scope_native_payload_changed')


def _trace_rows(root, days, sources, gaps, exclude=lambda *args:None,db=None,as_of=None):
    from src.engine.scalping.market_weakness_research import project_trace
    for day in days:
        path=select_stream(root,'ai_decision_trace',day,sources)
        if path is None:
            gaps['native_trace_missing']+=1;continue
        generation=sources[str(path)]
        opener=gzip.open if path.suffix=='.gz' else open
        # Legacy trace envelopes may include replay context above the compact
        # row limit. Decode one bounded complete envelope and retain primitives
        # only; larger records are drained and explicitly quarantined.
        envelope_limit=2*1024*1024
        with opener(path,'rb') as handle,Claim(envelope_limit*8):
            while True:
                start=handle.tell();raw=handle.readline(envelope_limit+1)
                if not raw: break
                reference={'path':str(path),'decoded_offset':start,'encoding':'gzip' if path.suffix=='.gz' else 'plain'}
                if len(raw)>envelope_limit or not raw.endswith(b'\n'):
                    while raw and not raw.endswith(b'\n'): raw=handle.readline(storage.RECORD_BYTES)
                    gaps['native_trace_oversize_or_partial']+=1
                    exclude('native_trace_oversize_or_partial',reference);continue
                if len(raw)>storage.RECORD_BYTES: gaps['native_large_envelope_projected']+=1
                try:
                    original=json.loads(raw)
                    projected,reason=project_trace(original,day)
                except (ValueError,TypeError,KeyError):
                    projected,reason=None,'native_trace_invalid'
                if not projected:
                    gaps[reason]+=1
                    if reason!='not_entry_trace': exclude(reason,reference)
                    continue
                if projected['machine_action']!='ENTER_NOW' or projected['auxiliary_verdict']!='PASS':
                    gaps['native_not_enter_pass']+=1;continue
                if projected['identity_grade']!='canonical':
                    found=db.execute('SELECT body FROM native WHERE id=? AND conflict=0',
                        (original.get('machine_observation_sha256'),)).fetchone() if db is not None else None
                    bound=json.loads(found[0]) if found else None
                    if (not bound or bound['evaluation_attempt_id']!=projected['evaluation_attempt_id']
                        or bound['symbol']!=projected['symbol'] or bound['bundle_sha256']!=projected['machine_hash']
                        or datetime.fromisoformat(bound['captured_at'])>datetime.fromisoformat(projected['decision_ts'])):
                        gaps['native_canonical_identity_missing']+=1
                        exclude('native_canonical_identity_missing',{**reference,'evaluation_attempt_id':projected['evaluation_attempt_id'],
                            'decision_trace_id':projected['decision_trace_id']});continue
                    projected['opportunity_id']=bound['canonical_opportunity_id']
                    original['entry_mechanistic_policy_decision']={'event':bound['fields'],
                        'observation_sha256':bound['machine_observation_sha256']}
                    gaps['native_canonical_identity_recovered']+=1
                assessment=original.get('entry_mechanistic_policy_decision') or {}
                event=assessment.get('event') or {}
                clock=datetime.fromisoformat(projected['decision_ts']).timestamp()
                if as_of is not None and clock>as_of:
                    gaps['native_decision_after_cutoff']+=1
                    exclude('native_decision_after_cutoff',reference);continue
                native_at=event.get('at')
                try:
                    native_clock=datetime.fromisoformat(native_at)
                    if native_clock.tzinfo is None or native_clock.timestamp()>clock: raise ValueError('native_clock_invalid')
                    native_clock=native_clock.timestamp()
                except (ValueError,TypeError):
                    native_clock=None;gaps['native_signal_clock_missing']+=1
                source_quote=event.get('universal_trailing_quote')
                path_events=[source_quote] if isinstance(source_quote,dict) else []
                position=dict(position_key='cf:'+projected['opportunity_id'],evidence_kind='enter_pass_opportunity_cf',
                    owner='main',automatic_management_allowed=True,symbol=projected['symbol'],entry_at=clock,
                    qty=event.get('planned_qty'),buy_basis_krw=event.get('buy_basis_krw'),cost_model=event.get('entry_cost_model') or {},
                    route=projected['route'],item=event.get('item') or event.get('source_item'),entry_action='ENTER_NOW',auxiliary_effective_verdict='PASS',
                    machine_observation_sha256=assessment.get('observation_sha256'),native_evaluation_id=projected['evaluation_attempt_id'],
                    native_signal_at=native_clock,auxiliary_completed_at=clock,
                    execution_plan_sha256=event.get('execution_plan_sha256'),entry_depth_verified=event.get('entry_depth_verified') is True,
                    entry_context=event.get('trailing_entry_context'),operating_ai_required=True,
                    source_reference={'path':str(path),'decoded_offset':start,'size':handle.tell()-start,
                        'encoding':'gzip' if path.suffix=='.gz' else 'plain','sha256':hashlib.sha256(raw).hexdigest()})
                if not path_events: gaps['native_forward_path_unobserved']+=1
                yield position,path_events
        if byte_generation(path)!=generation: raise ValueError('all_scope_native_trace_changed')


def _operating(root, day, sources, gaps):
    """Exact-date native decision receipts prove operation, not full coverage."""
    operating=set()
    base=Path(root)/'runtime/mechanistic_entry_policy/decisions'/day
    for path in sorted(base.glob('*/*.json')):
        try:
            value,generation=read(path)
            if (value.get('schema')!='main_policy_decision_status_v1' or value.get('target_date')!=day
                or value.get('policy_validation_state')!='valid'
                or value.get('artifact_content_sha256')!=digest({k:v for k,v in value.items()
                    if k!='artifact_content_sha256'})):
                raise ValueError('native_receipt_invalid')
            parts=value['scope'].split('|')
            if len(parts)!=4: raise ValueError('native_scope_invalid')
            symbol,market,_,route=parts
            if market=='AFTER': market='INTEGRATED_AFTERMARKET'
            if market=='PRE': market='PREMARKET'
            operating.add('|'.join((symbol,market,route)))
            sources[str(path)]=generation
        except (ValueError,TypeError,KeyError,AttributeError):
            gaps['native_operating_receipt_invalid']+=1
    return sorted(operating)


def large_completed_sources(root,raw,day,output,dependency):
    """Stream a legacy projection sealed by its original census producer."""
    from src.engine.lifecycle.research_json_stream import completed_rows
    from src.engine.scalping.pre_submit_delay_initial_policy import number
    sidecar=raw.with_suffix('.completed_projection.json')
    receipt_path=Path(str(sidecar)+'.dependencies.json')
    receipt,receipt_generation=read(receipt_path)
    generation=byte_generation(sidecar)
    if (receipt.get('schema')!='holding_projection_dependency_receipt_v1'
        or receipt.get('date')!=day or receipt.get('projection')!=generation
        or receipt.get('artifact_sha256')!=digest({k:v for k,v in receipt.items() if k!='artifact_sha256'})
        or not receipt.get('census_sha256') or receipt.get('meta',{}).get('snapshot_profile')!='postclose_exit'
        or receipt.get('meta',{}).get('actual_cost_source_generation')!=dependency['cost_generation']):
        raise ValueError('all_scope_large_completed_receipt_invalid')
    stat=raw.stat()
    identity={
        'device':stat.st_dev,'inode':stat.st_ino,'size':stat.st_size,'mtime_ns':stat.st_mtime_ns,'ctime_ns':stat.st_ctime_ns}
    if raw.is_symlink() or receipt.get('snapshot_identity')!=identity:
        raise ValueError('all_scope_large_completed_snapshot_changed')
    count=0
    for trade,quote_ref in completed_rows(sidecar,output):
        count+=1
        quotes=lambda:storage.iter_tree(output,quote_ref)
        first=next(quotes(),{})
        for key,quote_key in (('entry_quote_route','route'),('entry_quote_item','item'),('trailing_replay_cost_model','entry_cost_model')):
            if not trade.get(key):trade[key]=first.get(quote_key)
        buy_ref=trade.get('buy_fill_legs_ref');sell_ref=trade.get('sell_fill_legs_ref')
        buys=lambda:storage.iter_tree(output,buy_ref) if buy_ref else iter(())
        first_leg=next(buys(),None);trade['buy_fill_legs']=[first_leg] if first_leg is not None else []
        invalid_sell=False
        if sell_ref:
            latest=None;latest_at=None
            for leg in storage.iter_tree(output,sell_ref):
                try:
                    value=datetime.fromisoformat(leg['at']);clock=(value.replace(tzinfo=ZoneInfo('Asia/Seoul')) if value.tzinfo is None else value).timestamp()
                    if latest_at is None or clock>latest_at:latest,latest_at=leg,clock
                except (ValueError,TypeError,KeyError,AttributeError):invalid_sell=True
            trade['sell_fill_legs']=[latest] if latest is not None and not invalid_sell else []
        def adds(trade=trade,buys=buys):
            iterator=buys();next(iterator,None);model=trade.get('trailing_replay_cost_model') or {}
            for leg in iterator:
                try:
                    value=datetime.fromisoformat(leg['at']);clock=(value.replace(tzinfo=ZoneInfo('Asia/Seoul')) if value.tzinfo is None else value).timestamp()
                    cost=leg.get('buy_cost_krw')
                    if (cost is None and model.get('allocation')=='frozen_configured_round_trip_rate_on_sell_model_only'
                        and number(model.get('buy_cost_krw'))==0):cost=0
                    yield dict(kind='ADD',event_at=clock,known_at=clock,qty=leg['qty'],buy_amount_krw=leg['amount_krw'],
                        buy_cost_krw=cost,buy_generation_sha256=digest(leg))
                except (ValueError,TypeError,KeyError,AttributeError):
                    yield dict(kind='ADD',known_at=None)
        # The resident producer sorts quotes plus every ADD when fills exist.
        # Sort on disk as well: timeline append order is not event-time proof.
        invalid_buy=False
        if buy_ref:
            for leg in buys():
                try:
                    datetime.fromisoformat(leg['at']);leg['qty'];leg['amount_krw']
                except (ValueError,TypeError,KeyError,AttributeError,OverflowError):invalid_buy=True
        if first_leg is not None:
            with storage.index(output/'scratch') as ordering:
                ordering.execute('CREATE TABLE events(clock REAL,ordinal INTEGER,body TEXT)')
                for ordinal,event in enumerate(__import__('itertools').chain(quotes(),adds())):
                    clock=number(event.get('known_at'))
                    if clock is None:invalid_buy=True
                    ordering.execute('INSERT INTO events VALUES (?,?,?)',
                        (clock,ordinal,storage.encoded(event).decode()))
                event_ref=storage.write_tree(output,(json.loads(body) for body, in
                    ordering.execute('SELECT body FROM events ORDER BY clock,ordinal')))
        else:event_ref=quote_ref
        positions,_=completed_sources([trade])
        for position in positions:
            if invalid_buy or trade.get('projection_source_gap'):position['entry_at']=None
            position['symbol']=str(trade.get('stock_code') or trade.get('code') or '')
            position['source_reference']={'path':str(sidecar),'id':position['position_key'],'projection_generation':generation}
            yield trade,position,storage.iter_tree(output,event_ref)
    if count!=receipt.get('completed_count'):raise ValueError('all_scope_large_completed_census_changed')
    if byte_generation(sidecar)!=generation or byte_generation(receipt_path)!=receipt_generation:
        raise ValueError('all_scope_large_completed_source_changed')


def assemble(root, output, *, source_date, target_date, start_date='2026-09-29', as_of=None, immutable=False):
    from src.engine.lifecycle.research_disk_budget import use
    with use(output),storage.compact_trees():
        return _assemble(root,output,source_date=source_date,target_date=target_date,
            start_date=start_date,as_of=as_of,immutable=immutable)


def _assemble(root, output, *, source_date, target_date, start_date='2026-09-29', as_of=None, immutable=False):
    root,output=Path(root).resolve(),Path(output).resolve()
    if output==root or output.is_relative_to(root):
        raise ValueError('all_scope_isolated_assembly_required')
    output.mkdir(parents=True,exist_ok=True)
    days=[];cursor=date.fromisoformat(max(start_date,'2026-09-29'))
    while cursor<=date.fromisoformat(source_date): days.append(cursor.isoformat());cursor+=timedelta(days=1)
    if not days: raise ValueError('all_scope_assembly_date_window_empty')
    rows,master_source=universe(root,source_date)
    window=capture_window(root,days)
    parent_path=root/'runtime/policy_bootstrap'/f'runtime_policy_bootstrap_{source_date}.json'
    parent,parent_generation=read(parent_path)
    from .main_trailing_all_scope_research import code_contract
    code=code_contract();inventory=input_inventory(root,days,master_source['path'],parent_path)
    signature=digest([source_date,target_date,days,as_of,code,window['input_window_generation_sha256'],inventory])
    if immutable:
        output=output/'generations'/signature
        output.mkdir(parents=True,exist_ok=True)
    existing=output/'manifest.json'
    if existing.exists():
        try:
            previous,_=read(existing)
            if (previous.get('artifact_sha256')==digest({k:v for k,v in previous.items() if k!='artifact_sha256'})
                and previous.get('assembly_input_generation_sha256')==signature):
                for part in storage.iter_tree(output,previous['partitions_ref']):
                    value,_=read(output/part['path'])
                    if digest(value)!=part['artifact_sha256']:raise ValueError('assembly_partition_changed')
                    for ref in value['paths'].values():
                        for _ in storage.iter_tree(output,ref):pass
                for _ in storage.iter_tree(output,previous['population_ids_ref']):pass
                return existing
        except (ValueError,TypeError,KeyError,OSError):pass
    from src.engine.automation.runtime_policy_bootstrap import _digest_json
    if parent.get('manifest_sha256')!=_digest_json({k:v for k,v in parent.items() if k!='manifest_sha256'}):
        raise ValueError('all_scope_parent_manifest_invalid')
    parent_copy=output/'parent.json';_atomic(parent_copy,parent)
    sources={str(parent_path):parent_generation,master_source['path']:master_source['generation']}
    gaps=Counter();as_of=time.time() if as_of is None else number(as_of)
    if as_of is None or as_of<datetime.fromisoformat(source_date+'T00:00:00+09:00').timestamp():
        raise ValueError('all_scope_assembly_cutoff_invalid')
    operating=_operating(root,source_date,sources,gaps)
    from src.engine.holding_exit_observation_report import _verified_trade_review_projection
    def records():
        for day in days:
            dependency=window['dependencies'][day]
            if dependency['status']=='source_gap': gaps['completed_snapshot_source_gap']+=1;continue
            raw=root/'report/monitor_snapshots'/f'trade_review_{day}.json'
            if not raw.exists():
                if date.fromisoformat(day).weekday()<5: gaps['completed_snapshot_missing']+=1
                continue
            sidecar=raw.with_suffix('.completed_projection.json')
            if sidecar.exists() and sidecar.stat().st_size>4*1024*1024:
                sources[str(sidecar)]=byte_generation(sidecar)
                receipt=Path(str(sidecar)+'.dependencies.json');sources[str(receipt)]=byte_generation(receipt)
                cohort=large_completed_sources(root,raw,day,output,dependency)
            else:
                projection=_verified_trade_review_projection(raw,day,data_root=root)
                if projection is None: gaps['completed_snapshot_unverified']+=1;continue
                sources[str(sidecar)]=byte_generation(sidecar)
                def resident(projection=projection,sidecar=sidecar):
                    for trade in projection['sections']['completed_trade_projection']:
                        positions,paths=completed_sources([trade])
                        for position in positions:
                            position['symbol']=str(trade.get('stock_code') or trade.get('code') or '')
                            position['source_reference']={'path':str(sidecar),'id':position['position_key']}
                            yield trade,position,paths[position['position_key']]
                cohort=resident()
            for trade,position,events in cohort:
                if str(trade.get('strategy') or '').upper() not in {'SCALP','SCALPING'}:
                    gaps['non_main_trade']+=1;continue
                from src.engine.ai.holding_vote_replay_source import assemble_votes
                event_ref=storage.write_tree(output,iter(events))
                first = next(storage.iter_tree(output,event_ref), {})
                source = position.get('holding_vote_source') or first.get('holding_vote_source')
                if source is not None:
                    position['operating_ai_required'] = source.get('required')
                    position['holding_vote_replay_ref'] = assemble_votes(root,output,source,sources)
                yield position,event_ref
                alternative={**position,'position_key':'alternative:'+position['position_key'],
                    'evidence_kind':'actual_entry_alternative_exit','actual_cost_reconciliation':None,'situation_pin':None}
                yield alternative,event_ref
        yield from _trace_rows(root,days,sources,gaps,exclude,db,as_of=as_of)
    with storage.index(output/'scratch') as db:
        db.execute('CREATE TABLE exclusions(id TEXT PRIMARY KEY,body TEXT) WITHOUT ROWID')
        def exclude(reason,reference):
            value={'reason':reason,'source_reference':reference}
            db.execute('INSERT OR IGNORE INTO exclusions VALUES (?,?)',(digest(value),storage.encoded(value).decode()))
        _native_index(root,days,sources,gaps,db)
        # Dedup whole populations before any replay/selection, not partition by
        # partition. Position and CF identities stay in disjoint namespaces.
        for position,events in records():
            event_ref=events if isinstance(events,dict) and events.get('schema')==storage.SCHEMA else storage.write_tree(output,iter(events))
            value={'position':position,'events_ref':event_ref}
            semantic={'position':{k:v for k,v in position.items() if k!='source_reference'},'events_ref':event_ref}
            storage.put(db,position['position_key'],value,content_sha=digest(storage.logical_value(semantic)))
        def parts():
            # A bounded batch amortizes metadata fsync/hash without sharing
            # position state. Record limits cap this batch below 1 MiB.
            batch=[]
            def emit(batch):
                payload={'source_date':source_date,'positions':[v['position'] for _,v in batch],
                    'paths':{i:v['events_ref'] for i,v in batch},'cost_generations':{
                        day:window['dependencies'][day]['cost_generation'] for day in days}}
                payload['artifact_sha256']=digest(payload)
                name='inputs/'+digest(payload)+'.json';_atomic(output/name,payload)
                return {'path':name,'artifact_sha256':digest(payload),'consumed_dates':days}
            with Claim(16*storage.RECORD_BYTES*8):
                for identity,value,_ in storage.records(db):
                    batch.append((identity,value))
                    if len(batch)==16:
                        yield emit(batch);batch=[]
                if batch:yield emit(batch)
        partition_ref=storage.write_tree(output,parts())
        population_ref=storage.write_tree(output,(i for i,_,_ in storage.records(db)))
        quarantined_ref=storage.write_tree(output,({'identity':i,'copies':n,'reason':'canonical_source_conflict'}
                                                  for i,_,n in storage.records(db,conflicts=True)))
        excluded_ref=storage.write_tree(output,(json.loads(b) for b, in db.execute('SELECT body FROM exclusions ORDER BY id')))
    for name,generation in sources.items():
        if byte_generation(Path(name))!=generation: raise ValueError('all_scope_assembly_source_changed')
    verify_window(root,window)
    source_ref=storage.write_tree(output,({'path':name,'generation':generation} for name,generation in sorted(sources.items())))
    if input_inventory(root,days,master_source['path'],parent_path)!=inventory:
        raise ValueError('all_scope_assembly_inventory_changed')
    inventory_ref=storage.write_tree(output,inventory)
    from src.engine.scalping.trailing_situation_policy import registered_research_grid
    receipt=parent['scalp_trailing_mechanical_policy_receipt']
    candidates,grid=registered_research_grid(receipt['market_values'],receipt['classifier_parameters'])
    manifest=dict(schema='main_all_scope_exit_input_manifest_v2',source_date=source_date,target_date=target_date,
        as_of=as_of,universe=rows,universe_source_sha256=master_source['semantic_sha256'],
        approved_parent_receipt=parent['scalp_trailing_mechanical_policy_receipt'],
        approved_parent_source={'path':'parent.json','sha256':byte_generation(parent_copy)['sha256']},
        consumed_dates=days,partitions_ref=partition_ref,population_ids_ref=population_ref,
        source_data_root=str(root),source_generations_ref=source_ref,
        assembly_code_contract_sha256=code,assembly_input_generation_sha256=signature,
        assembly_inventory_ref=inventory_ref,input_window_generation_sha256=window['input_window_generation_sha256'],
        assembly_census={'source_gaps':dict(gaps),'quarantined':quarantined_ref,'excluded_native_sources_ref':excluded_ref},
        candidates=candidates,situation_classifier_grid=grid,
        operating=operating,coverage={},runtime_effect=False,allowed_runtime_apply=False)
    manifest['artifact_sha256']=digest(manifest)
    path=output/'manifest.json';_atomic(path,manifest)
    return path
