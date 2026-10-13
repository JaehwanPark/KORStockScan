"""Bounded Main stop research and immutable publication after exit snapshots.

Consumes existing pipeline receipts, never calls a model/broker or invents
numerical selection authority. Missing cells retain their verified parent.
"""
from __future__ import annotations
import argparse
from collections import Counter
from contextvars import ContextVar
from dataclasses import asdict
from datetime import date, timedelta
import hashlib
import json
import tempfile
import time
from pathlib import Path

from src.engine.scalping import main_stop_policy as policy
from src.engine.scalping.main_stop_replay import candidates, replay, choose, validate_experiment
from src.engine.lifecycle import research_storage as storage
from src.engine.lifecycle.holding_window_generation import byte_generation, source_stat
from src.engine.lifecycle.research_admission import direct_job
from src.engine.scalping.pre_submit_delay_initial_policy import _atomic
from src.utils.jsonl_io import open_text_auto
from . import main_stop_source_index as source_index

STAGE = 'main_stop_confirmation'
START_DATE = '2026-10-12'
_DEADLINE = ContextVar('main_stop_research_deadline',default=None)
MAX_RESEARCH_SECONDS = 14400  # Same upper bound as the native stage dispatcher.


def checkpoint():
    deadline=_DEADLINE.get()
    if deadline is not None and time.monotonic()>=deadline:
        raise ValueError('stop_research_deadline_exceeded')


def report_path(root, day):
    return Path(root)/'report/main_stop_confirmation'/f'main_stop_research_{day}.json'


def committed_path(root, day):
    return Path(root)/'threshold_cycle/main_stop_confirmation'/f'committed_{day}.json'


def bounded(path, limit=1024*1024):
    return policy.bounded_object(path,limit)


def verified_dependency_stats(inventory):
    """Bind stat identities to the bytes verified in that same read window."""
    result = {}
    for name, expected in inventory.items():
        path = Path(name)
        before = list(source_stat(path.stat()))
        if byte_generation(path) != expected or list(source_stat(path.stat())) != before:
            raise ValueError('stop_source_changed_during_read')
        result[name] = before
    return result


def census_dependencies(directory, reference):
    """Seal shard identities after native tree validation, including children."""
    result={}
    def visit(ref,depth=0):
        if 'rows' in ref:return
        if depth>16:raise ValueError('stop_census_depth_invalid')
        path=storage.safe_path(directory,ref['path'])
        before=list(source_stat(path.stat()))
        value,sha=bounded(path,4*1024*1024)
        if sha!=ref['sha256'] or before!=list(source_stat(path.stat())):
            raise ValueError('stop_census_generation_changed')
        result[ref['path']]=before
        if len(result)>8192:raise ValueError('stop_census_dependency_manifest_unbounded')
        for child in value.get('children',[]):visit(child,depth+1)
    visit(reference)
    return result


def code_sha():
    return policy.implementation_sha()


def operator_sources(root, target):
    from .operator_policy_succession import source_snapshot
    return source_snapshot(Path(root)/'runtime', Path(root)/'threshold_cycle/operator_runtime_env_locks',
                           {'KORSTOCKSCAN_'+policy.KEYS[k] for k in policy.TUNABLE}, target)


def vote_watch(root, day):
    """Dependency discovery, including previously absent vote/request files.

    This is an invalidation hint. Consumed originals still receive independent
    byte hashes; a directory/file stat is never economic proof.
    """
    digest=hashlib.sha256()
    directories=[Path(root)/'runtime/holding_path_votes']
    directories.extend(Path(root)/name for name in (
        'ai_decision_payloads','ai_decision_prompts','ai_decision_requests'))
    for directory in directories:
        # scandir keeps enumeration bounded; filesystem order is made irrelevant
        # with an integer multiset digest rather than retaining every pathname.
        import os
        total=0;count=0
        if directory.exists():
            with os.scandir(directory) as entries:
                for entry in entries:
                    if not entry.is_file(follow_symlinks=False):continue
                    if directory.name!='holding_path_votes':
                        stem=entry.name[len(directory.name)+1:][:10]
                        if not '2026-09-29'<=stem<=day:continue
                        if entry.name.endswith('.jsonl.gz'):
                            # The request reader prefers the surviving original.
                            # Cleanup may add an unused gzip companion without
                            # changing any consumed source. A gzip-only source,
                            # original mutation or removal still invalidates.
                            from src.engine.ai.holding_vote_replay_source import request_source_shadowed
                            if request_source_shadowed(Path(entry.path)):continue
                    value=policy.digest([entry.name,list(source_stat(entry.stat(follow_symlinks=False)))])
                    total=(total+int(value,16))%(1<<256);count+=1
        digest.update(policy.digest([str(directory),count,f'{total:064x}']).encode())
    return digest.hexdigest()


def baseline(root, target):
    # Reuse the verified incumbent owner; do not rebuild or mutate PREOPEN.
    from src.engine.automation import runtime_policy_bootstrap as boot
    incumbent,path,basis=boot._load_incumbent(target)
    if Path(root).resolve()!=Path(boot.DATA_DIR).resolve():raise ValueError('stop_incumbent_root_mismatch')
    env=incumbent['env_overrides']
    def read(key):
        value=env.get('KORSTOCKSCAN_'+key)
        if value is None:return None
        return int(value) if key in {policy.KEYS[k] for k in ('grace_sec','window_sec','min_span_sec','min_samples')} else float(value)
    value=policy.StopValues.from_rules(read)
    parents = {f'{r}|{m}':value for r in policy.ROLES for m in policy.MARKETS}
    if env.get(policy.ENV_FILE):
        # The incumbent receipt already verifies historical custody. Read its
        # exact values as a migration parent, never as current executable code.
        previous = policy.load_bundle(env[policy.ENV_FILE],env[policy.ENV_SHA],env[policy.ENV_DATE],require_current_code=False)
        policy.validate_runtime_environment(previous,env)
        # A new operator instruction outranks a carried numerical challenger.
        current_sources = operator_sources(root,target)
        prior_sources = [row for row in previous.get('operator_sources',[]) if not (
            Path(row['path']).name.startswith('operator_runtime_overrides_')
            and Path(row['path']).stem[-10:] < target)]
        if current_sources != prior_sources:
            raise ValueError('stop_new_operator_instruction_requires_reconciliation')
        parents = {key:policy.StopValues.parse(cell['values']) for key,cell in previous['cells'].items()}
    return parents,dict(
        path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),verification=basis,
        effective_values=asdict(value))


def sources(root, day):
    result=[];d=date.fromisoformat('2026-09-29')
    while d<=date.fromisoformat(day):
        base=Path(root)/'pipeline_events'/f'pipeline_events_{d.isoformat()}.jsonl'
        for logical in (base,base.with_name(base.stem+'.late.jsonl')):
            path=logical if logical.exists() else logical.with_suffix('.jsonl.gz')
            if path.exists():result.append(path)
        d+=timedelta(days=1)
    return result


def source_events(path, census, *, references=False):
    """Bound each line and expose undecodable source instead of dropping it."""
    with open_text_auto(path, errors='strict') as handle:
        while True:
            checkpoint()
            offset=handle.tell()
            line=handle.readline(2*1024*1024+1)
            if not line:break
            if len(line.encode())>2*1024*1024:
                # Isolate this physical record without retaining its full body.
                # Its role is unverified, so numeric selection stays fail-closed;
                # a source-gap carry can still preserve the verified incumbent.
                digest=hashlib.sha256(line.encode());size=len(line.encode())
                complete=line.endswith('\n')
                while not complete:
                    checkpoint()
                    tail=handle.readline(65536)
                    if not tail:break
                    raw=tail.encode();digest.update(raw);size+=len(raw)
                    complete=tail.endswith('\n')
                census['oversized_raw_rows']+=1
                census['oversized_raw_bytes']+=size
                census['unidentifiable_raw_rows']+=1
                if not complete:census['oversized_unterminated_raw_rows']+=1
                if census['oversized_raw_rows']<=8:
                    census[f'oversized_raw_record:{path}:{offset}:{digest.hexdigest()}']+=1
                continue
            if not line.strip():continue
            try:row=json.loads(line)
            except ValueError:
                census['unidentifiable_raw_rows']+=1
                continue
            if not isinstance(row,dict):
                census['unidentifiable_raw_rows']+=1
                continue
            yield (row,offset,hashlib.sha256(line.encode()).hexdigest()) if references else row


def read_committed(root, day, *, pointer=None, verify_full=False):
    if pointer is None: pointer,_=bounded(committed_path(root,day))
    if pointer.get('schema')!='main_stop_committed_v1' or pointer.get('source_date')!=day:
        raise ValueError('stop_commit_identity_invalid')
    directory=Path(root)/'threshold_cycle/main_stop_confirmation/generations'/pointer['generation']
    if len(pointer['generation'])!=64 or any(c not in '0123456789abcdef' for c in pointer['generation']):
        raise ValueError('stop_commit_generation_invalid')
    bundle,sha=bounded(directory/'policy.json')
    report,rsha=bounded(directory/'report.json')
    if (sha!=pointer['policy_byte_sha256'] or rsha!=pointer['report_byte_sha256']
            or report.get('report_sha256')!=policy.digest({k:v for k,v in report.items() if k!='report_sha256'})
            or report.get('source_date')!=day or report.get('target_date')!=bundle.get('target_date')
            or report.get('policy_sha256')!=bundle.get('policy_sha256')
            or bundle.get('research_sha256')!=report.get('research_sha256')):
        raise ValueError('stop_commit_binding_invalid')
    research = {k:v for k,v in report.items() if k not in {
        'research_sha256','status','policy_sha256','report_sha256'}}
    if policy.digest(research) != report['research_sha256']:
        raise ValueError('stop_research_binding_invalid')
    if bundle.get('code_sha256')!=report['code_sha256']:
        raise ValueError('stop_code_generation_changed')
    if report.get('code_sha256')!=code_sha():
        if verify_full:
            raise ValueError('stop_code_generation_changed')
        policy.verify_runtime_code_contract(bundle, bundle['target_date'])
    policy.validate_bundle(bundle,bundle['target_date'])
    if bundle.get('operator_sources') != operator_sources(root,bundle['target_date']):
        raise ValueError('stop_operator_sources_changed')
    if report.get('vote_watch_sha256')!=vote_watch(root,day):
        raise ValueError('stop_vote_source_set_changed')
    if report.get('source_catalog_sha256')!=policy.digest([str(p) for p in sources(root,day)]):
        raise ValueError('stop_raw_source_set_changed')
    for label in ('parent_receipt','snapshot_receipt'):
        ref=report.get(label) or {}
        if not ref.get('path') or bounded(ref['path'],8*1024*1024)[1]!=ref.get('sha256'):
            raise ValueError('stop_native_source_changed:'+label)
    # The native publisher hashes all bytes once. Routine semantic monitoring
    # checks its sealed dependency identities without rescanning raw ledgers.
    expected_files = {**report.get('source_inventory', {}), **report.get('vote_source_inventory', {}),
                      **(report.get('economic_sources') or {}).get('files', {})}
    for path, expected in expected_files.items():
        before = report['dependency_stats'].get(path)
        if before != list(source_stat(Path(path).stat())):
            raise ValueError('stop_native_source_generation_changed')
        if verify_full and byte_generation(Path(path)) != expected:
            raise ValueError('stop_native_source_bytes_changed')
    economic = report.get('economic_sources') or {}
    from src.engine.lifecycle.broker_cost_reconciliation import source_generation
    for cost_day, expected in economic.get('cost_generations', {}).items():
        if source_generation(Path(root), cost_day) != expected:
            raise ValueError('stop_native_cost_generation_changed')
    for cell in bundle['cells'].values():
        if cell['status'] == 'selected':
            from .operator_policy_succession import stop_key_authority
            auth = stop_key_authority(root, bundle['target_date'], cell['authority']['allowed_keys'])
            if auth['sha256'] != cell['authority']['operator_lock_sha256']:
                raise ValueError('stop_operator_sources_changed')
    ref = report['opportunity_census']
    for name,expected in report['census_dependencies'].items():
        if list(source_stat(storage.safe_path(directory,name).stat()))!=expected:
            raise ValueError('stop_census_shard_generation_changed')
    if verify_full or 'rows' in ref:
        for _ in storage.iter_tree(directory, ref): pass
    elif byte_generation(storage.safe_path(directory, ref['path']))['sha256'] != ref['sha256']:
        raise ValueError('stop_census_manifest_changed')
    return bundle,report,pointer,directory


def completed_evidence(root, days):
    """Stream only metadata from native verified projections; never clone paths."""
    from src.engine.holding_exit_observation_report import _verified_trade_review_projection
    from src.engine.lifecycle.research_json_stream import Reader
    fields={'id','record_id','status','main_automatic_management_allowed','actual_cost_reconciliation'}
    for day in days:
        snapshot=Path(root)/'report/monitor_snapshots'/f'trade_review_{day}.json'
        if _verified_trade_review_projection(snapshot,day,data_root=Path(root),metadata_only=True) is None:
            continue
        sidecar=snapshot.with_suffix('.completed_projection.json')
        before=byte_generation(sidecar)
        def project(reader):
            row={}
            def visit(key,r):
                if key in fields:row[key]=r.value(storage.RECORD_BYTES)
                else:r.skip()
                return iter(())
            for _ in reader.fields(visit):pass
            row['source_date']=day;row['source_sha256']=before['sha256']
            return row
        with sidecar.open() as handle:
            yield from Reader(handle).target(('sections','completed_trade_projection'),project)
        if byte_generation(sidecar)!=before:raise ValueError('stop_cost_projection_changed')


def publish(root, day, target, *, parents, parent_receipt, source_paths, snapshot_receipt,
            experiments=None, completed=(), economic_sources=None):
    from src.engine.lifecycle.research_disk_budget import use
    token=_DEADLINE.set(time.monotonic()+MAX_RESEARCH_SECONDS)
    try:
        with use(Path(root)/'threshold_cycle/main_stop_confirmation',
                 durable_limit=2*1024**3,temp_limit=2*1024**3):
            return _publish(root,day,target,parents=parents,parent_receipt=parent_receipt,
                source_paths=source_paths,snapshot_receipt=snapshot_receipt,
                experiments=experiments,completed=completed,economic_sources=economic_sources)
    except (ValueError,MemoryError) as exc:
        if isinstance(exc,MemoryError) or any(word in str(exc) for word in ('budget','deadline','unbounded')):
            # Preserve the incumbent/pointers and completed per-position caches.
            # This bounded failure receipt is not a successful target policy.
            _atomic(Path(root)/'report/main_stop_confirmation'/f'resume_{day}.json',dict(
                schema='main_stop_resume_v1',source_date=day,target_date=target,status='incomplete',
                reason=str(exc),parent_receipt=parent_receipt,policy_mutated=False,
                target_policy_published=False,resume_root=str(Path(root)/'threshold_cycle/main_stop_confirmation'),
                next_action='repair_budget_or_source_then_resume_same_verified_dependencies'))
        raise
    finally:_DEADLINE.reset(token)


def _publish(root, day, target, *, parents, parent_receipt, source_paths, snapshot_receipt,
             experiments=None, completed=(), economic_sources=None):
    root=Path(root)
    checkpoint()
    algorithm_sha=code_sha()
    if not '2026-09-29'<=day<target:raise ValueError('stop_publication_date_invalid')
    if set(parents)!={f'{r}|{m}' for r in policy.ROLES for m in policy.MARKETS}:raise ValueError('stop_parent_cells_invalid')
    if not parent_receipt.get('sha256') or not snapshot_receipt.get('sha256'):raise ValueError('stop_parent_or_snapshot_unverified')
    economic_sources = economic_sources or dict(files={}, cost_generations={})
    authority_sources = operator_sources(root,target)
    vote_watch_sha=vote_watch(root,day)
    source_catalog=[str(p) for p in sources(root,day)]
    source_catalog_sha=policy.digest(source_catalog)
    inventory={str(p):byte_generation(p) for p in source_paths}
    if not set(source_catalog)<=set(inventory):
        raise ValueError('stop_source_catalog_not_consumed')
    input_stat_identity={name:list(source_stat(Path(name).stat()))
                         for name in {**inventory,**economic_sources.get('files',{})}}
    generation=policy.digest(dict(inventory=inventory,snapshot=snapshot_receipt,parent=parent_receipt,
        parents={k:asdict(v) for k,v in parents.items()},code=algorithm_sha,source_date=day,target_date=target,
        experiments=experiments or {},economic_sources=economic_sources,operator_sources=authority_sources,
        vote_watch_sha256=vote_watch_sha,source_catalog_sha256=source_catalog_sha,
        input_stat_identity=input_stat_identity))
    pointer_path=committed_path(root,day)
    if pointer_path.exists():
        pointer,_=bounded(pointer_path)
        if pointer['generation']==generation:
            previous,report,_,_=read_committed(root,day)
            return previous,report
    directory=root/'threshold_cycle/main_stop_confirmation/generations'/generation
    source_sha=policy.digest(inventory)
    if len(experiments or {}) > 1:raise ValueError("stop_one_cell_experiment_required")
    census=Counter();cells={};evidence=[]
    vote_sources={}
    with storage.index(directory) as db:
        db.execute('CREATE TABLE census (id TEXT PRIMARY KEY, body TEXT)')
        db.execute('CREATE TABLE actual (id TEXT PRIMARY KEY, body TEXT, day TEXT)')
        for row in completed:
            checkpoint()
            if not economic_sources.get('files'):raise ValueError('stop_completed_source_inventory_missing')
            key=str(row.get('id') or row.get('record_id') or '')
            if not key:raise ValueError('stop_completed_identity_missing')
            raw=storage.encoded(row)
            if len(raw)>storage.RECORD_BYTES:raise ValueError('stop_completed_record_unbounded')
            db.execute('INSERT INTO actual VALUES (?,?,?) ON CONFLICT(id) DO UPDATE SET body=excluded.body, day=excluded.day WHERE excluded.day>=day',
                (key,raw.decode(),row['source_date']))
        prepared_sources=source_index.prepare(root/'threshold_cycle/main_stop_confirmation',inventory,source_events,census)
        work={}
        for cell,parent in parents.items():
            grid=candidates(parent);counts=Counter();stats={name:dict(train_n=0,train_total=0,train_delta=0.,train_delta_sq=0.,holdout_n=0,holdout_total=0,holdout_delta=0.,holdout_delta_sq=0.,train_safety_regressions=0,holdout_safety_regressions=0) for name in grid if name!='parent'}
            contract=(experiments or {}).get(cell)
            if contract:
                validate_experiment(contract,parent_sha=policy.digest(asdict(parent)),source_sha=source_sha,code_sha=algorithm_sha)
                from .operator_policy_succession import stop_key_authority
                if stop_key_authority(root,target,contract['allowed_keys'])['sha256'] != contract['operator_lock_sha256']:
                    raise ValueError('stop_operator_sources_changed')
                # A research reservation narrows the simultaneous comparison;
                # unsupported sensitivity axes cannot censor an eligible axis.
                grid = {k:v for k,v in grid.items() if k=='parent' or (k.split(':')[0] in contract['allowed_keys']
                    and abs(getattr(v,k.split(':')[0])-getattr(parent,k.split(':')[0]))<=contract['max_daily_change'][k.split(':')[0]])}
                stats = {k:v for k,v in stats.items() if k in grid}
            work[cell]=(grid,counts,stats,contract)
        for position in source_index.positions(prepared_sources,directory,census,checkpoint=checkpoint):
            checkpoint()
            cell,key,first,last=position.cell,position.key,position.first,position.last
            if cell not in work:
                census['unmapped_positions']+=1
                row=dict(position_key=key,cell=cell,status='source_gap',reason='scope_unmapped')
                db.execute('INSERT INTO census VALUES (?,?)',(key,storage.encoded(row).decode()))
                continue
            grid,counts,stats,contract=work[cell]
            counts['positions']+=1
            path_rows=position.rows
            from src.engine.ai.holding_vote_replay_source import assemble_votes, PreparedVotes
            first_row = next(path_rows(), {})
            source = first_row.get('holding_vote_source')
            reference = assemble_votes(root, directory, source, vote_sources) if source else None
            logical_votes = ({k:v for k,v in reference.items() if k!='root'} if reference else None)
            cache_key=policy.digest(dict(code=algorithm_sha,position=key,source=position.source_sha256,
                votes=storage.logical_value(logical_votes),grid={k:asdict(v) for k,v in grid.items()}))
            cache=root/'threshold_cycle/main_stop_confirmation/replay_cache'/f'{cache_key}.json'
            outcomes=None
            if cache.exists():
                cached,_=bounded(cache)
                if (cached.get('cache_key')!=cache_key or cached.get('sha256')!=policy.digest({k:v for k,v in cached.items() if k!='sha256'})
                        or set(cached.get('outcomes',{}))!=set(grid)):
                    raise ValueError('stop_replay_checkpoint_invalid')
                outcomes=cached['outcomes']
            if outcomes is None:
                with tempfile.TemporaryDirectory(prefix='.votes-', dir=directory) as scratch:
                    prepared = PreparedVotes(reference, scratch)
                    try:
                        def vote_reader(row, at):
                            try:
                                snap = prepared.snapshot(row.get('holding_vote_source'), at,
                                    market=row['market'],route=row['route'],epoch=row['transport_epoch'],entry_at=first)
                                return dict(snap,source_verified=True)
                            except (ValueError, OSError, TypeError, KeyError):
                                return dict(source_verified=False)
                        with position.materialized(directory) as prepared_rows:
                            outcomes={name:replay(prepared_rows(),value, vote_reader=vote_reader) for name,value in grid.items()}
                    finally:prepared.close()
                cached=dict(cache_key=cache_key,outcomes=outcomes)
                cached['sha256']=policy.digest(cached)
                _atomic(cache,cached)

            incumbent=outcomes['parent'];counts[incumbent['status']+':'+str(incumbent['reason'])]+=1
            # Entire positions are split. No samples from one holding cross
            # train/holdout, and the full max grace horizon is embargoed.
            split=None
            if contract:
                if last<contract['split_at']-contract['embargo_sec']:split='train'
                elif first>contract['split_at']+contract['embargo_sec']:split='holdout'
            actual_row=db.execute('SELECT body FROM actual WHERE id=?',(str(first_row.get('record_id')),)).fetchone()
            actual=json.loads(actual_row[0]) if actual_row else {}
            cost=actual.get('actual_cost_reconciliation') or {}
            economic_source=(actual.get('status')=='COMPLETED'
                and actual.get('main_automatic_management_allowed') is True
                and cost.get('status')=='actual_cost_reconciled'
                and all(policy.finite(cost.get(k)) for k in ('exact_pnl_krw','exact_profit_rate'))
                and bool(cost.get('receipt_sha256') and cost.get('raw_sha256')))
            counts['actual_cost_verified' if economic_source else 'actual_cost_or_terminal_gap']+=1
            common=economic_source and all(x['status']=='modeled' for x in outcomes.values())
            if split:
                for stat in stats.values():stat[split+'_total']+=1
            if split and common:
                for name,row in outcomes.items():
                    if name=='parent':continue
                    stat=stats[name];stat[split+'_n']+=1
                    delta=row['modeled_net_krw']-incumbent['modeled_net_krw']
                    stat[split+'_delta']+=delta
                    stat[split+'_delta_sq']+=delta*delta
                    stat[split+'_safety_regressions']+=int(row['mae_pct']<incumbent['mae_pct'] or row['exposure_sec']>incumbent['exposure_sec'])
            summary=dict(position_key=key,cell=cell,status=incumbent['status'],reason=incumbent['reason'],
                actual_cost_verified=economic_source, split=split, common=common)
            db.execute('INSERT INTO census VALUES (?,?)',(key,storage.encoded(summary).decode()))
            evidence.append(summary)
            if len(evidence)>64:evidence.pop(0)
        for cell,parent in parents.items():
            grid,counts,stats,contract=work[cell]
            winner,status=choose(stats,contract)
            if census.get('unidentifiable_raw_rows') or census.get('unidentifiable'):
                winner,status=None,'source_gap'
            selected=grid[winner] if winner else parent
            authority={} if not winner else dict(allowed_keys=[winner.split(':')[0]],
                operator_lock_sha256=contract['operator_lock_sha256'],experiment_sha256=contract['experiment_sha256'],
                source_sha256=source_sha,code_sha256=algorithm_sha,target_date=target,
                parent_values_sha256=policy.digest(asdict(parent)))
            cells[cell]=dict(status=status,values=asdict(selected),parent_values=asdict(parent),authority=authority,
                source_census=dict(counts),selection_evidence=dict(holdout_verified=bool(winner),
                    comparison_kind='modeled_alternative_exit_not_actual_profit',selected_candidate=winner,
                    aggregates=stats,experiment=contract),rollback_values=asdict(parent))
        opportunity_census=storage.write_tree(directory,(json.loads(body) for body, in db.execute('SELECT body FROM census ORDER BY id')))
    if code_sha()!=algorithm_sha:raise ValueError('stop_code_changed_during_research')
    checkpoint()
    if vote_watch(root,day)!=vote_watch_sha:raise ValueError('stop_vote_source_set_changed')
    if policy.digest([str(p) for p in sources(root,day)])!=source_catalog_sha:
        raise ValueError('stop_raw_source_set_changed')
    dependency_stats = verified_dependency_stats({**inventory, **vote_sources,
                                                  **economic_sources.get('files',{})})
    if any(dependency_stats[name]!=value for name,value in input_stat_identity.items()):
        raise ValueError('stop_source_changed_during_research')
    research=dict(schema='main_stop_research_v1',source_date=day,target_date=target,source_sha256=source_sha,
        vote_selection_mode='separate_holding_vote_family_parent_carry',
        protect_line_generator_status='conditional_existing_line_provenance_only',
        protect_line_authority='existing_main_trailing_owner_no_new_line_strategy',
        parent_receipt=parent_receipt,snapshot_receipt=snapshot_receipt,code_sha256=algorithm_sha,
        source_inventory=inventory,source_catalog_sha256=source_catalog_sha,
        vote_source_inventory=vote_sources,vote_watch_sha256=vote_watch_sha,
        economic_sources=economic_sources, opportunity_census=opportunity_census,
        census_dependencies=census_dependencies(directory,opportunity_census),
        dependency_stats=dependency_stats,
        census=dict(census),examples=evidence,actual_order_submitted=False,actual_profit_verified=False)
    research_sha=policy.digest(research)
    bundle=dict(schema=policy.SCHEMA,source_date=day,target_date=target,valid_until=target,
        research_sha256=research_sha,cells=cells,parent_receipt=parent_receipt,operator_sources=authority_sources,
        code_sha256=algorithm_sha)
    bundle['policy_sha256']=policy.digest(bundle);policy.validate_bundle(bundle,target)
    report=dict(research,research_sha256=research_sha,status='published_policy',policy_sha256=bundle['policy_sha256'])
    report['report_sha256']=policy.digest(report)
    for name,value in (('policy.json',bundle),('report.json',report)):
        path=directory/name
        if path.exists() and bounded(path)[0]!=value:raise ValueError('stop_immutable_generation_collision')
        _atomic(path,value)
    pointer=dict(schema='main_stop_committed_v1',source_date=day,target_date=target,generation=generation,
        policy_byte_sha256=hashlib.sha256((directory/'policy.json').read_bytes()).hexdigest(),
        report_byte_sha256=hashlib.sha256((directory/'report.json').read_bytes()).hexdigest())
    # Aliases are compatibility surfaces; readers use the single atomic pointer.
    _atomic(policy.policy_path(root,target),bundle);_atomic(report_path(root,day),report)
    _atomic(pointer_path,pointer)
    read_committed(root,day,verify_full=True)
    _atomic(pointer_path.with_name('target_'+target+'.json'),pointer)
    return bundle,report


def handoff(root,target, *, effective_env=None, require_terminal=False):
    target_pointer=committed_path(root,target).with_name('target_'+target+'.json')
    if not target_pointer.exists():return {},dict(status='not_installed',target_date=target)
    pointer,_=bounded(target_pointer)
    bundle,report,pointer,directory=read_committed(root,pointer['source_date'],pointer=pointer)
    if bundle['target_date']!=target:raise ValueError('stop_handoff_target_invalid')
    if effective_env is not None:
        policy.validate_runtime_environment(bundle,effective_env)
    if require_terminal:
        from .postclose_summary_handoff import stage_receipt_issues
        issues = stage_receipt_issues(Path(root)/'report',bundle['source_date'],STAGE)
        if issues:raise ValueError('stop_terminal_handoff_unverified:' + ','.join(issues))
    env={policy.ENV_FILE:str(directory/'policy.json'),policy.ENV_SHA:pointer['policy_byte_sha256'],policy.ENV_DATE:target}
    return env,dict(status='verified_carried' if all(c['status']!='selected' for c in bundle['cells'].values()) else 'policy_selected',
        source_date=bundle['source_date'],target_date=target,policy_sha256=bundle['policy_sha256'],
        generation=pointer['generation'],report_sha256=report['report_sha256'],actual_pid_consumed=False)


def runtime_consumption(root, bundle):
    """Read the native loader and durable pins; never run trading evaluation."""
    from src.engine.lifecycle.research_admission import start_ticks
    from src.engine.scalping.position_peak_ledger import DEFAULT_LEDGER_PATH
    directory=Path(root)/'runtime/main_stop_confirmation'/bundle['target_date']
    result=dict(status='not_observed',actual_pid_consumed=False,pin_count=0,findings=[])
    files=sorted(directory.glob('pid_*.json')) if directory.exists() else []
    if len(files)>64:raise ValueError('stop_pid_archive_unbounded')
    current=[]
    for path in files:
        receipt,_=bounded(path,32768)
        if (receipt.get('schema')!='main_stop_loaded_policy_v1'
                or receipt.get('receipt_sha256')!=policy.digest({k:v for k,v in receipt.items() if k!='receipt_sha256'})
                or receipt.get('target_date')!=bundle['target_date']):
            raise ValueError('stop_pid_receipt_invalid')
        pid=receipt.get('pid')
        if type(pid) is not int or pid<=0:raise ValueError('stop_pid_receipt_invalid')
        try:
            live=start_ticks(pid)==receipt['start_ticks'] and str(Path(f'/proc/{pid}/cwd').resolve(strict=True))==receipt['process_cwd']
        except (OSError,ValueError):live=False
        if not live:continue
        if len(current)>=8:raise ValueError('stop_live_loader_census_unbounded')
        loaded,loaded_sha=bounded(receipt['policy_file'])
        policy.validate_bundle(loaded,bundle['target_date'])
        if (loaded_sha!=receipt['policy_byte_sha256']
                or loaded['policy_sha256']!=receipt['policy_sha256']
                or policy.digest({k:c['values'] for k,c in loaded['cells'].items()})!=receipt.get('loaded_cells_sha256')):
            raise ValueError('stop_pid_loaded_map_invalid')
        current.append(receipt)
    if not current:
        expected=Path(root)/'runtime/policy_bootstrap'/f"runtime_policy_bootstrap_verify_{bundle['target_date']}.json"
        if expected.exists():
            verification,_=bounded(expected)
            if verification.get('target_date')==bundle['target_date'] and verification.get('pid_passed') is True:
                result['findings'].append('main_stop_verified_pid_loader_not_observed')
        return result
    result.update(status='loader_observed',actual_pid_consumed=True,
        current_pids=[row['pid'] for row in current],loaded_generations=[row['policy_sha256'] for row in current])
    if bundle['policy_sha256'] not in result['loaded_generations']:
        result['findings'].append('main_stop_current_pid_policy_mismatch')
        result['actual_pid_consumed']=False
    ledger_path=Path(root)/'runtime'/DEFAULT_LEDGER_PATH.name
    if ledger_path.exists():
        ledger,_=bounded(ledger_path,8*1024*1024)
        for key,row in (ledger.get('positions') or {}).items():
            pin=row.get('main_stop_policy_pin')
            if pin is None:continue
            policy.pin_values(pin,key)
            if pin['policy_sha256']==bundle['policy_sha256'] and pin['values']!=bundle['cells'][pin['role']+'|'+pin['market']]['values']:
                result['findings'].append('main_stop_position_pin_mismatch')
            result['pin_count']+=1
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--date',required=True);parser.add_argument('--target',required=True);parser.add_argument('--publication-date')
    args=parser.parse_args()
    from src.utils.constants import DATA_DIR
    from src.engine.log_archive_service import verified_postclose_exit_snapshot_manifest
    from src.engine.build_next_stage2_checklist import _next_krx_trading_day
    if args.target!=_next_krx_trading_day(args.publication_date or args.date):raise ValueError('stop_next_session_target_invalid')
    with direct_job(DATA_DIR,STAGE,args.date):
        snapshot=verified_postclose_exit_snapshot_manifest(args.date,data_root=DATA_DIR)
        if snapshot is None:raise ValueError('stop_exit_snapshot_unverified')
        parents,receipt=baseline(DATA_DIR,args.target)
        experiment_path=Path(DATA_DIR)/'runtime/research/main_stop_confirmation'/f'experiments_{args.date}.json'
        experiments=bounded(experiment_path)[0] if experiment_path.exists() else {}
        paths=sources(DATA_DIR,args.date)
        days=sorted({p.name.split('_')[-1][:10] for p in paths})
        from src.engine.lifecycle.broker_cost_reconciliation import source_generation
        files={}
        for day in days:
            path=Path(DATA_DIR)/'report/monitor_snapshots'/f'trade_review_{day}.json'
            for item in (path,path.with_suffix('.completed_projection.json')):
                if item.exists():files[str(item)]=byte_generation(item)
        economic_sources=dict(files=files,cost_generations={day:source_generation(DATA_DIR,day) for day in days})
        publish(DATA_DIR,args.date,args.target,parents=parents,parent_receipt=receipt,
            source_paths=sources(DATA_DIR,args.date),snapshot_receipt=dict(path=str(snapshot),sha256=hashlib.sha256(snapshot.read_bytes()).hexdigest()),experiments=experiments,
            completed=completed_evidence(DATA_DIR, days),economic_sources=economic_sources)
    return 0


if __name__=='__main__':raise SystemExit(main())
