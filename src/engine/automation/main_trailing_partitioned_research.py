"""All-population orchestration for automatically assembled Main sources.

Bounded input/result trees lift per-object limits without changing replay,
source authority, approved parents or the economic selector's guards.
"""
from collections import Counter
from contextlib import ExitStack
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
import json
import tempfile

from src.engine.lifecycle import research_storage as storage
from src.engine.lifecycle.holding_window_generation import byte_generation, capture_window, verify_window
from src.engine.lifecycle.research_input_budget import Claim
from src.engine.scalping.pre_submit_delay_initial_policy import digest, number, _atomic
from src.engine.scalping.trailing_mechanical_policy import classifier_hash
from src.engine.scalping.trailing_mechanical_strength import StrengthDecision
from src.engine.scalping.trailing_situation_policy import initial_bundle
from .main_trailing_situation_aggregation import research as research_registered_grid
from src.engine.scalping.universal_trailing_replay import (
    PreparedPath, PreparedVariants, summarize_partitions,
    research_entry_window_start, apply_research_entry_window,
)
from .main_trailing_path_projection import EventSequence, stream_pairs
from .main_trailing_population_aggregation import aggregate
from src.engine.lifecycle.research_disk_budget import use, reclaim_missing

SCHEMA='main_all_scope_exit_research_v2'
CACHE_BYTES=64*1024*1024


def _cache_pairs(factory,config,cache_root,quota):
    """Keep every observation while bounding each physical cache record."""
    for event,feature in stream_pairs(factory(),config):
        if len(storage.encoded([event,feature]))>storage.RECORD_BYTES and feature[2]:
            strength=dict(feature[2])
            observations=strength.pop('new_observations')
            strength['new_observations_ref']=storage.write_tree(
                cache_root,observations,quota=quota,inline=False)
            feature=[feature[0],feature[1],strength]
        yield [event,feature]


def _cached_pairs(cache_root,reference):
    for event,feature in storage.iter_tree(cache_root,reference):
        if feature[2] and 'new_observations_ref' in feature[2]:
            strength=dict(feature[2])
            reference=strength.pop('new_observations_ref')
            strength['new_observations']=list(storage.iter_tree(cache_root,reference))
            feature=[feature[0],feature[1],strength]
        yield event,feature


def _prepared(factory,config,*,count,end,last_add,cache_root,quota,counters):
    if count*1024 <= CACHE_BYTES-quota['used']:
        try:
            ref=storage.write_tree(cache_root,_cache_pairs(factory,config,cache_root,quota),quota=quota,inline=False)
            raw_pairs=lambda: _cached_pairs(cache_root,ref)
            counters['feature_cache_created']+=1
        except ValueError as exc:
            if str(exc) not in {'research_cache_budget_exceeded','research_shard_record_partition_required'}: raise
            raw_pairs=lambda: stream_pairs(factory(),config)
            counters['feature_cache_overflow_streamed']+=1
    else:
        raw_pairs=lambda: stream_pairs(factory(),config)
        counters['feature_cache_large_path_streamed']+=1
    def pairs():
        for event,(market,permission,strength) in raw_pairs():
            yield event,(market,SimpleNamespace(**permission) if permission else None,
                StrengthDecision(**{**strength,'new_observations':tuple(strength['new_observations'])}) if strength else None)
    return PreparedPath(EventSequence(pairs,count),(),classifier_hash(config),pairs,end,last_add)



def checkpoint_results(checkpoint,root):
    if 'result' in checkpoint:
        yield checkpoint['result'];return
    aliases=checkpoint['candidate_aliases']
    for value in storage.iter_tree(root,checkpoint['result_records_ref']):
        with Claim(max(4096,4096*len(aliases))):
            value=storage.expand_outcomes(root,value)
            identity=value['identity'];outcomes=value['outcomes']
            if set(outcomes)!=set(aliases.values()):
                raise ValueError('all_scope_checkpoint_candidate_census_invalid')
            if value['common']!=all(r['modeled_net_pnl_krw'] is not None for r in outcomes.values()):
                raise ValueError('all_scope_checkpoint_cohort_invalid')
            yield {'candidate_aliases':aliases,'population_context':{identity:value['context']},
                'minimal_results':{identity:outcomes},'eligible_ids': [identity] if outcomes[aliases['incumbent']]['modeled_net_pnl_krw'] is not None else [],
                'common_ids':[identity] if value['common'] else []}

def run(manifest_path,*,input_root,output_root=None,dry_run=True,resume=False):
    from . import main_trailing_all_scope_research as owner
    root=Path(input_root).resolve()
    manifest=owner._sealed(Path(manifest_path))
    manifest_generation=byte_generation(Path(manifest_path))
    if manifest.get('schema')!='main_all_scope_exit_input_manifest_v2': raise ValueError('all_scope_input_manifest_invalid')
    with Claim(len(storage.encoded(manifest))*8),Claim(0) as scope_budget:
        scope=owner.preflight_header(manifest,root,scope_budget=scope_budget)
        from .main_trailing_source_assembler import verify_inventory
        verify_inventory(manifest,root)
        data_root=Path(manifest['source_data_root']).resolve()
        window=capture_window(data_root,manifest['consumed_dates'])
        if window['input_window_generation_sha256']!=manifest['input_window_generation_sha256']:
            raise ValueError('all_scope_cost_window_changed_reassemble_required')
        for source in storage.iter_tree(root,manifest['source_generations_ref']):
            path=Path(source['path']);generation=source['generation']
            if not path.resolve().is_relative_to(data_root) or byte_generation(path)!=generation:
                raise ValueError('all_scope_automatic_source_generation_invalid')
        if output_root is None:
            # Full inventory validation is still bounded and source-only.
            count=0
            for part in storage.iter_tree(root,manifest['partitions_ref']):
                owner._sealed(owner._source_path(root,part['path']),part['artifact_sha256']);count+=1
            return {'schema':SCHEMA,'status':'preflight_only','scope':scope,'partition_count':count,'runtime_effect':False}
        out=Path(output_root).resolve()
        if out==root or out.is_relative_to(root): raise ValueError('all_scope_isolated_output_root_required')
        out.mkdir(parents=True,exist_ok=True)
        if dry_run:
            with tempfile.TemporaryDirectory(prefix='.trailing-check-',dir=out) as scratch,use(scratch),storage.compact_trees():
                return _run(manifest,root,Path(scratch),scope,window,data_root,resume=False,owner=owner,
                    manifest_path=Path(manifest_path),manifest_generation=manifest_generation)
        with use(out),storage.compact_trees():
            return _run(manifest,root,out,scope,window,data_root,resume=resume,owner=owner,
                manifest_path=Path(manifest_path),manifest_generation=manifest_generation)


def _run(manifest,root,out,scope,window,data_root,*,resume,owner,manifest_path,manifest_generation):
    counters=Counter();parent=manifest['approved_parent_receipt'];candidates=manifest.get('candidates',{})
    entry_window_start=research_entry_window_start(manifest['consumed_dates'])
    contract=owner.code_contract()
    report_path=out/f"research_{manifest['source_date']}.json"
    if resume and report_path.exists():
        try:
            from .main_trailing_research_handoff import verify_report
            previous,generation=verify_report(report_path,target_date=manifest['target_date'])
            if (previous['input_manifest_path']!=str(manifest_path.resolve())
                or previous['input_manifest_generation']!=manifest_generation
                or previous['input_window_generation_sha256']!=window['input_window_generation_sha256']):
                raise ValueError('all_scope_completed_report_generation_changed')
            # Keep durable bytes immutable: invocation counters are returned
            # separately and never invalidate an already referenced receipt.
            previous['counters']={'checkpoint_reused':previous['partition_results_ref']['count'],
                                  'complete_report_reused':1}
            previous['artifact_sha256']=digest({k:v for k,v in previous.items() if k!='artifact_sha256'})
            return previous
        except (OSError,ValueError,TypeError,KeyError):
            counters['complete_report_invalid_rebuilt']+=1
    # Scope rows are evidence, not an active map retained during path replay.
    scope_ref=storage.write_tree(out,scope['scopes'])
    scope_summary={k:v for k,v in scope.items() if k!='scopes'};scope_summary['scopes_ref']=scope_ref
    def result_refs():
        for part in storage.iter_tree(root,manifest['partitions_ref']):
            path=owner._source_path(root,part['path']);generation=byte_generation(path)
            key=digest([part,generation,window['input_window_generation_sha256'],parent,candidates,contract,
                        manifest['as_of'],entry_window_start])
            cache=out/'partitions'/f'{key}.json'
            if resume and cache.exists():
                try:
                    old=owner._sealed(cache)
                    if old.get('input_generation_sha256')!=key: raise ValueError('all_scope_checkpoint_invalid')
                    # Every path leaf is verified independently even when no
                    # source feature is decoded/reclassified during resume.
                    payload=owner._sealed(path,part['artifact_sha256'])
                    for description in payload['paths'].values():
                        for _ in storage.iter_tree(root,description): pass
                    for _ in checkpoint_results(old,out): pass
                    counters['checkpoint_reused']+=1
                    yield {'path':str(cache.relative_to(out)),'artifact_sha256':old['artifact_sha256'],
                           'input_generation_sha256':key}
                    continue
                except (OSError,ValueError,TypeError,KeyError):
                    counters['checkpoint_invalid_rebuilt']+=1
            payload=owner._sealed(path,part['artifact_sha256'])
            if len(payload['positions'])>500: raise ValueError('all_scope_partition_position_budget_exceeded')
            with Claim(len(storage.encoded(payload))*8),tempfile.TemporaryDirectory(prefix='.features-',dir=out) as scratch:
                quota={'used':0,'limit':CACHE_BYTES};paths={}
                for identity,description in payload['paths'].items():
                    def factory(description=description):
                        for event in storage.iter_tree(root,description):
                            known=number(event.get('known_at'))
                            if known is None or known<=manifest['as_of']: yield event
                    count,end,last_add=0,0,0
                    for event in factory():
                        count+=1;end=max(end,number(event.get('known_at')) or 0)
                        if event.get('kind')=='ADD': last_add=max(last_add,number(event.get('known_at')) or 0)
                    variants={}
                    for candidate in [parent,*candidates.values()]:
                        config=candidate.get('classifier_parameters') if 'market_values' in candidate else None
                        sha=classifier_hash(config)
                        if sha not in variants:
                            variants[sha]=_prepared(factory,config,count=count,end=end,last_add=last_add,cache_root=Path(scratch),
                                quota=quota,counters=counters)
                    paths[identity]=PreparedVariants(variants)
                from src.engine.scalping.universal_trailing_replay import actual_cost_available_epoch
                positions=[apply_research_entry_window(p,window_start_at=entry_window_start)
                           for p in payload['positions']]
                entry_window_excluded=sum(bool(p.get('research_entry_window_exclusion')) for p in positions)
                if entry_window_excluded:
                    counters['entry_before_research_window']+=entry_window_excluded
                positions = [{**p, 'actual_cost_reconciliation':{}}
                    if p.get('evidence_kind') == 'actual_completed' and (
                        actual_cost_available_epoch(p.get('actual_cost_reconciliation') or {}) is None
                        or actual_cost_available_epoch(p.get('actual_cost_reconciliation') or {}) > manifest['as_of'])
                    else p for p in positions]
                if payload.get('cost_generations')!={d:window['dependencies'][d]['cost_generation'] for d in part['consumed_dates']}:
                    positions=[{**p,'actual_cost_reconciliation':{}} if p.get('evidence_kind')=='actual_completed' else p for p in positions]
                # Retain one position's results. All numeric candidates share
                # one feature stream, including paths too large for the cache.
                candidate_items=list(candidates.items());aliases={}
                def position_results():
                    for position in positions:
                        with Claim(4096*(len(candidate_items)+1)):
                            combined=summarize_partitions([position],paths,candidates,incumbent={
                                'market_values':parent['market_values'],'classifier_parameters':parent['classifier_parameters']})
                            aliases.update(combined['candidate_aliases'])
                            identity=combined['population_ids'][0]
                            outcomes=combined['minimal_results'][identity]
                            value=dict(identity=identity,context=combined['population_context'][identity],
                                outcomes=outcomes,common=all(r['modeled_net_pnl_krw'] is not None for r in outcomes.values()))
                            yield storage.compact_outcomes(out,value)
                records_ref=storage.write_tree(out,position_results())
                checkpoint={'schema':SCHEMA,'input_generation_sha256':key,
                    'candidate_aliases':aliases,'result_records_ref':records_ref}
                checkpoint['artifact_sha256']=digest(checkpoint);_atomic(cache,checkpoint)
                counters['decoded_partitions']+=1
                counters['feature_cache_evicted_bytes']+=quota['used']
            if byte_generation(path)!=generation: raise ValueError('all_scope_source_changed_during_replay')
            reclaim_missing()
            yield {'path':str(cache.relative_to(out)),'artifact_sha256':checkpoint['artifact_sha256'],
                   'input_generation_sha256':key}
    refs=storage.write_tree(out,result_refs())
    def results():
        for ref in storage.iter_tree(out,refs):
            checkpoint=owner._sealed(storage.safe_path(out,ref['path']))
            if checkpoint['artifact_sha256']!=ref['artifact_sha256']: raise ValueError('all_scope_checkpoint_changed')
            yield from checkpoint_results(checkpoint,out)
    evaluation=aggregate(results,output_root=out)
    # External census also handles populations larger than one object.
    with storage.index(out) as db:
        for identity in storage.iter_tree(root,manifest['population_ids_ref']): storage.put(db,identity,{'expected':True})
        actual=evaluation.get('population_ids_ref')
        if actual:
            for identity in storage.iter_tree(out,actual):
                if not db.execute('SELECT 1 FROM records WHERE id=?',(identity,)).fetchone():
                    raise ValueError('all_scope_global_census_unexpected_identity')
                db.execute('UPDATE records SET conflicted=1 WHERE id=?',(identity,))
        missing=storage.write_tree(out,(i for i,_,_ in storage.records(db)))
    # The registered type research shares the already fixed common split.
    # Its external implementation is below this producer, not a shard vote.
    type_research=research_registered_grid(results,grid=manifest.get('situation_classifier_grid'),candidates=candidates,
        parent_values=parent['market_values'],parent_classifier_parameters=parent['classifier_parameters'],
        evaluation=evaluation,output_root=out)
    baseline=initial_bundle(parent['market_values'],parent_sha256=parent['market_values_sha256'],
        source_date=manifest['source_date'],target_date=manifest['target_date'],
        parent_classifier_parameters=parent['classifier_parameters'],classifier=type_research.get('classifier'))
    verify_window(data_root,window)
    from .main_trailing_source_assembler import verify_inventory
    verify_inventory(manifest,root)
    for source in storage.iter_tree(root,manifest['source_generations_ref']):
        if byte_generation(Path(source['path']))!=source['generation']:
            raise ValueError('all_scope_source_changed_before_publication')
    if byte_generation(manifest_path)!=manifest_generation:
        raise ValueError('all_scope_manifest_changed_during_research')
    owner.preflight_header(owner._sealed(manifest_path),root)
    for part in storage.iter_tree(root,manifest['partitions_ref']):
        payload=owner._sealed(owner._source_path(root,part['path']),part['artifact_sha256'])
        for reference in payload['paths'].values():
            for _ in storage.iter_tree(root,reference): pass
    if owner.code_contract()!=contract: raise ValueError('all_scope_code_changed_during_research')
    body=dict(schema=SCHEMA,source_date=manifest['source_date'],target_date=manifest['target_date'],
        status='complete' if missing['count']==0 else 'source_gap',
        eligible_evaluation_complete=missing['count']==0,
        raw_census_complete=not any(manifest['assembly_census'].get('source_gaps',{}).values()),
        evidence_root=str(out.resolve()),scope=scope_summary,partition_results_ref=refs,
        missing_population_ids_ref=missing,common_population_evaluation=evaluation,trailing_situation_research=type_research,
        assembly_census=manifest['assembly_census'],input_window_generation_sha256=window['input_window_generation_sha256'],
        code_contract_sha256=contract,input_manifest_path=str(manifest_path),
        input_manifest_generation=manifest_generation,counters=dict(counters),initial_policy=baseline,runtime_effect=False,
        allowed_runtime_apply=False,actual_pid_consumed=False)
    body['artifact_sha256']=digest(body)
    _atomic(out/f"research_{manifest['source_date']}.json",body)
    _atomic(out/f"initial_policy_{manifest['target_date']}.json",baseline)
    return body
