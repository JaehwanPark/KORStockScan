"""Verify automatic all-scope evidence before the existing bootstrap consumes it.

The initial carry is exact parent equivalence. Economic changes remain under
trailing_mechanical_policy's existing selector; this module cannot select them.
"""
from pathlib import Path
from src.engine.lifecycle import research_storage as storage
from src.engine.lifecycle.holding_window_generation import byte_generation,capture_window,verify_window
from src.engine.scalping.pre_submit_delay_initial_policy import digest,_atomic
from src.engine.scalping.trailing_situation_policy import PreparedTrailingPolicy

SCHEMA='main_trailing_initial_handoff_v1'


def native_stage_runner(command, *, env, cwd):
    """Execute existing bounded metadata CLIs inside the owner's CAS journal.

    The dispatcher still owns source preflight, real slot descriptors, the
    deadline and terminal validation. No trading or provider CLI is accepted.
    """
    import importlib
    import os
    if (len(command)<3 or command[1]!='-m'
        or command[2] not in {'src.engine.scalping.pre_submit_delay_tuning',
                              'src.engine.automation.postclose_done_controller'}
        or Path(cwd).resolve()!=Path(__file__).resolve().parents[3]):
        raise ValueError('research_native_stage_adapter_invalid')
    keys=('POSTCLOSE_STAGE_WORKER','POSTCLOSE_SOURCE_DATE','POSTCLOSE_POLICY_PUBLICATION_DATE',
          'POSTCLOSE_STAGE_DEADLINE_EPOCH','POSTCLOSE_PREPARED_EFFECTIVE_DATE')
    if env.get('POSTCLOSE_STAGE_WORKER')!='1':raise ValueError('research_native_stage_owner_missing')
    before={key:os.environ.get(key) for key in keys}
    try:
        for key in keys:
            if key in env:os.environ[key]=env[key]
        return importlib.import_module(command[2]).main(command[3:])
    finally:
        for key,value in before.items():
            if value is None:os.environ.pop(key,None)
            else:os.environ[key]=value


def verify_report(path, *, target_date, parent_sha256=None):
    from src.engine.lifecycle.research_input_budget import Claim
    from .main_trailing_all_scope_research import _sealed
    from .main_trailing_source_reuse import replay_session
    report = _sealed(Path(path))
    manifest_path = Path(report['input_manifest_path'])
    manifest = _sealed(manifest_path)
    with replay_session(manifest, manifest_path.parent), Claim(0) as memo_budget:
        return _verify_report(path,target_date=target_date,parent_sha256=parent_sha256,memo_budget=memo_budget)


def _verify_report(path, *, target_date, parent_sha256, memo_budget):
    from .main_trailing_all_scope_research import _sealed,code_contract,preflight_header,_source_path
    path=Path(path).resolve();generation=byte_generation(path);report=_sealed(path)
    if (report.get('schema')!='main_all_scope_exit_research_v2' or report.get('status')!='complete'
        or report.get('target_date')!=target_date or report.get('code_contract_sha256')!=code_contract()
        or report.get('allowed_runtime_apply') is not False):
        raise ValueError('main_trailing_research_handoff_invalid')
    manifest_path=Path(report['input_manifest_path'])
    if byte_generation(manifest_path)!=report['input_manifest_generation']:
        raise ValueError('main_trailing_research_manifest_changed')
    manifest=_sealed(manifest_path);root=manifest_path.parent
    preflight_header(manifest,root)
    from .main_trailing_source_assembler import verify_inventory
    verify_inventory(manifest,root)
    if manifest['target_date']!=target_date or manifest['source_date']!=report['source_date']:
        raise ValueError('main_trailing_research_dates_invalid')
    data_root=Path(manifest['source_data_root']).resolve()
    window=capture_window(data_root,manifest['consumed_dates'])
    if window['input_window_generation_sha256']!=report['input_window_generation_sha256']:
        raise ValueError('main_trailing_research_cost_window_changed')
    from src.engine.lifecycle.holding_research_cost import inventory as cost_inventory
    cost_paths={p.resolve() for p in cost_inventory(
        manifest.get('holding_research_cost_data_root') or data_root,manifest['consumed_dates'])}
    for source in storage.iter_tree(root,manifest['source_generations_ref']):
        p=Path(source['path'])
        from .main_trailing_source_assembler import source_generation_matches
        if (not p.resolve().is_relative_to(data_root) and p.resolve() not in cost_paths) or not source_generation_matches(data_root,manifest['source_date'],p,source['generation']):
            raise ValueError('main_trailing_research_source_changed')
    checked_paths=set()
    for part in storage.iter_tree(root,manifest['partitions_ref']):
        payload=_sealed(_source_path(root,part['path']),part['artifact_sha256'])
        for ref in payload['paths'].values():
            identity=digest(ref)
            if identity in checked_paths:continue
            memo_budget.grow(256)
            for _ in storage.iter_tree(root,ref): pass
            checked_paths.add(identity)
    for reference in storage.iter_tree(path.parent,report['partition_results_ref']):
        checkpoint=_sealed(storage.safe_path(path.parent,reference['path']))
        if checkpoint['artifact_sha256']!=reference['artifact_sha256']:
            raise ValueError('main_trailing_research_checkpoint_changed')
        from .main_trailing_partitioned_research import checkpoint_results
        for _ in checkpoint_results(checkpoint,path.parent): pass
    for key in ('missing_population_ids_ref',):
        for _ in storage.iter_tree(path.parent,report[key]): pass
    for _ in storage.iter_tree(path.parent,report['scope']['scopes_ref']): pass
    # Aggregated cohort/type references are also terminal evidence. Validate
    # their complete nested graph, not just the checkpoint's direct rows.
    checked=set()
    def graph(value):
        if isinstance(value,dict):
            if value.get('schema')==storage.SCHEMA:
                key=digest(value)
                if key in checked:return
                memo_budget.grow(256)
                checked.add(key)
                for row in storage.iter_tree(path.parent,value):graph(row)
            else:
                for child in value.values():graph(child)
        elif isinstance(value,list):
            for child in value:graph(child)
    graph(report['common_population_evaluation']);graph(report['trailing_situation_research'])
    # Sealed trees prove bytes, not arithmetic or candidate selection. Rebuild
    # metrics from the complete minimal checkpoints with the same global split.
    # This verifier copies no raw quotes, prompts or provider comparison ledger.
    import tempfile
    from .main_trailing_partitioned_research import checkpoint_results
    from .main_trailing_population_aggregation import aggregate
    from .main_trailing_situation_aggregation import research
    def partitions():
        for reference in storage.iter_tree(path.parent,report['partition_results_ref']):
            checkpoint=_sealed(storage.safe_path(path.parent,reference['path']))
            yield from checkpoint_results(checkpoint,path.parent)
    with tempfile.TemporaryDirectory(prefix='.trailing-verify-',dir=path.parent) as scratch:
        from src.engine.lifecycle.research_disk_budget import use
        with use(scratch),storage.compact_trees():
            evaluated=aggregate(partitions,output_root=scratch)
            parent_receipt=manifest['approved_parent_receipt']
            typed=research(partitions,grid=manifest.get('situation_classifier_grid'),
                candidates=manifest.get('candidates') or {},parent_values=parent_receipt['market_values'],
                parent_classifier_parameters=parent_receipt['classifier_parameters'],
                evaluation=evaluated,output_root=scratch)
            if (storage.logical_value(evaluated)!=storage.logical_value(report['common_population_evaluation'])
                or storage.logical_value(typed)!=storage.logical_value(report['trailing_situation_research'])):
                raise ValueError('main_trailing_research_pair_metrics_invalid')
    if report.get('evidence_root') not in (None,str(path.parent)):
        raise ValueError('main_trailing_research_evidence_root_invalid')
    policy=report['initial_policy'];parent=parent_sha256 or manifest['approved_parent_receipt']['market_values_sha256']
    PreparedTrailingPolicy.prepare(policy,target_date=target_date,parent_sha256=parent)
    if any(cell['disposition']!='parent_carry' for cell in policy['cells'].values()):
        raise ValueError('main_trailing_initial_handoff_requires_existing_selector')
    verify_window(data_root,window)
    if byte_generation(path)!=generation or code_contract()!=report['code_contract_sha256']:
        raise ValueError('main_trailing_research_report_or_code_changed')
    return report,generation


def observe_extension(holding_report, *, target_date, required=False):
    """Bounded monitor of issued metadata, separate from full native replay.

    The bootstrap still calls verify_extension. Health sweeps must detect a
    stale code/target binding without replaying every source and partition.
    """
    from .main_trailing_all_scope_research import _sealed, code_contract
    result = dict(status='not_observed', findings=[], target_date=target_date,
                  validation_scope='bounded_producer_generation_and_current_code',
                  full_source_revalidation_performed=False, runtime_effect=False)
    extension = holding_report.get('all_scope_trailing_research')
    if extension is None:
        if required:
            result.update(status='source_invalid', findings=['all_scope_research_extension_missing'])
        return result
    try:
        if not isinstance(extension, dict):
            raise ValueError('all_scope_research_extension_invalid')
        path = Path(extension['report_path'])
        before = path.stat()
        hashes = {}
        report = _sealed(path, generations=hashes)
        from src.engine.lifecycle.holding_window_generation import source_stat
        if source_stat(path.stat()) != source_stat(before):
            raise ValueError('all_scope_research_extension_changed_during_read')
        generation = dict(path=path.name, size=before.st_size, sha256=hashes[str(path)])
        if (report.get('schema') != 'main_all_scope_exit_research_v2'
                or report.get('status') != 'complete'
                or report.get('target_date') != target_date
                or report.get('source_date') != holding_report.get('date')
                or report.get('code_contract_sha256') != code_contract()
                or report.get('allowed_runtime_apply') is not False):
            raise ValueError('main_trailing_research_handoff_invalid')
        if (extension.get('report_generation') != generation
                or extension.get('status') != report['status']
                or extension.get('input_window_generation_sha256') != report['input_window_generation_sha256']
                or extension.get('initial_policy_sha256') != report['initial_policy']['policy_sha256']
                or extension.get('scope_count') != report['scope']['scope_count']
                or extension.get('allowed_runtime_apply') is not False
                or source_stat(path.stat()) != source_stat(before)):
            raise ValueError('all_scope_research_extension_binding_invalid')
        result.update(status='generation_current', source_date=report['source_date'],
                      report_path=str(path), report_generation=generation,
                      code_contract_sha256=report['code_contract_sha256'],
                      scope_count=report['scope']['scope_count'])
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        result.update(status='source_invalid', findings=[str(exc)])
    return result


def verify_extension(holding_report, *, target_date):
    extension=holding_report.get('all_scope_trailing_research')
    if extension is None: return None
    if not isinstance(extension,dict): raise ValueError('all_scope_research_extension_invalid')
    report,generation=verify_report(extension['report_path'],target_date=target_date)
    if (extension.get('report_generation')!=generation
        or report['source_date']!=holding_report.get('date')
        or extension.get('status')!=report['status']
        or extension.get('input_window_generation_sha256')!=report['input_window_generation_sha256']
        or extension.get('initial_policy_sha256')!=report['initial_policy']['policy_sha256']
        or extension.get('scope_count')!=report['scope']['scope_count']
        or extension.get('allowed_runtime_apply') is not False):
        raise ValueError('all_scope_research_extension_binding_invalid')
    return report


def publish_initial(data_root, report_path, *, target_date, expected_policy_sha256=None):
    """CAS under this family's writer lock; never changes numeric parents."""
    import fcntl
    from contextlib import ExitStack
    root=Path(data_root).resolve();directory=root/'threshold_cycle/scalp_trailing_situation'
    directory.mkdir(parents=True,exist_ok=True)
    lock=storage.safe_path(directory,'.publication.lock')
    with lock.open('a+b') as handle:
        fcntl.flock(handle,fcntl.LOCK_EX)
        policy_path=storage.safe_path(directory,f'initial_policy_{target_date}.json')
        current=None
        if policy_path.exists():
            previous=__import__('json').loads(policy_path.read_bytes())
            current=previous.get('policy_sha256')
            if current!=digest({k:v for k,v in previous.items() if k!='policy_sha256'}):
                raise ValueError('main_trailing_initial_incumbent_invalid')
        if current!=expected_policy_sha256: raise ValueError('main_trailing_initial_parent_cas_changed')
        report,generation=verify_report(report_path,target_date=target_date)
        from .scalp_trailing_mechanical_policy_apply import select_typed_bundle
        policy=select_typed_bundle(root,report,generation,report_path=report_path,target_date=target_date)
        marker_path=directory/f'initial_policy_{target_date}.publication.json'
        marker=dict(schema=SCHEMA,state='publishing',target_date=target_date,
            policy_sha256=policy['policy_sha256'],report_generation=generation)
        marker['artifact_sha256']=digest(marker)
        _atomic(marker_path,marker)
        _atomic(policy_path,policy)
        receipt=dict(schema=SCHEMA,target_date=target_date,source_date=report['source_date'],
            report_path=str(Path(report_path).resolve()),report_generation=generation,
            policy_sha256=policy['policy_sha256'],policy_generation=byte_generation(policy_path),
            code_contract_sha256=report['code_contract_sha256'])
        receipt['artifact_sha256']=digest(receipt)
        _atomic(directory/f'initial_policy_{target_date}.receipt.json',receipt)
        marker.pop('artifact_sha256');marker.update(state='verified',receipt_sha256=receipt['artifact_sha256'])
        marker['artifact_sha256']=digest(marker);_atomic(marker_path,marker)
        return receipt


def verify_initial(data_root,policy,*,target_date,parent_sha256):
    from .main_trailing_all_scope_research import _sealed
    directory=Path(data_root).resolve()/'threshold_cycle/scalp_trailing_situation'
    receipt=_sealed(directory/f'initial_policy_{target_date}.receipt.json')
    marker_path=directory/f'initial_policy_{target_date}.publication.json'
    if marker_path.exists():
        marker=_sealed(marker_path)
        if (marker.get('state')!='verified' or marker.get('target_date')!=target_date
            or marker.get('policy_sha256')!=policy['policy_sha256']
            or marker.get('receipt_sha256')!=receipt['artifact_sha256']):
            raise ValueError('main_trailing_initial_publication_incomplete')
    policy_path=directory/f'initial_policy_{target_date}.json'
    if (receipt.get('schema')!=SCHEMA or receipt.get('target_date')!=target_date
        or receipt.get('policy_sha256')!=policy['policy_sha256']
        or receipt.get('policy_generation')!=byte_generation(policy_path)):
        raise ValueError('main_trailing_initial_receipt_invalid')
    report,generation=verify_report(receipt['report_path'],target_date=target_date,parent_sha256=parent_sha256)
    from src.engine.scalping.trailing_situation_policy import initial_bundle
    source=report['initial_policy']
    expected=initial_bundle(source['parent_values'],parent_sha256=parent_sha256,
        source_date=report['source_date'],target_date=target_date,
        parent_classifier_parameters=source['parent_classifier_parameters'],
        classifier=report['trailing_situation_research'].get('classifier'),
        overrides={k:v['evidence'] for k,v in policy['cells'].items() if v['disposition']=='qualified_candidate'})
    if generation!=receipt['report_generation'] or expected!=policy:
        raise ValueError('main_trailing_initial_report_binding_invalid')
    return receipt
