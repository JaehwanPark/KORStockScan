"""Read-only research-to-production input proof; native publisher owns activation.

Request, response, membership and provider receipts remain in their original
shared store. Preparation embeds only small immutable registry definitions.
"""
from __future__ import annotations

import copy
from collections import defaultdict
from datetime import date
from pathlib import Path
from types import FunctionType, SimpleNamespace

from src.engine.ai import offline_comparison_store as S
from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.scalping import continuous_reversal_policy_v5 as V
from src.engine.scalping import reversal_auxiliary_registry as G
from src.engine.scalping import reversal_auxiliary_intraday as I
from src.engine.scalping import reversal_auxiliary_tuning as T
from src.engine.scalping import reversal_auxiliary_research as R
from src.engine.scalping import reversal_auxiliary_risk_role_experiment as E
from src.engine.scalping import reversal_auxiliary_production_input as M
from src.engine.scalping import reversal_auxiliary_wire as W
from src.engine.scalping import reversal_cumulative_postclose as CP

SCHEMA = 'auxiliary_production_input_transition_v1'
REPORT_SCHEMA = 'auxiliary_input_transition_research_report_v1'
BASELINE = 'actual_incumbent_raw_input_and_prompt'
_VERIFIED = {}


def _require(value, reason):
    if not value:
        raise ValueError('auxiliary_input_transition_' + reason)


def _root(path):
    return str(Path(path).resolve())


def _reference(path):
    from src.engine.scalping import reversal_auxiliary_transition as X
    return X.reference(path)


def _read_reference(ref):
    from src.engine.scalping import reversal_auxiliary_transition as X
    _require(isinstance(ref, dict) and set(ref) == {'path', 'sha256'}, 'reference_invalid')
    X.verify_reference(ref)
    return I.read(ref['path'])


def code_hashes():
    from src.engine.scalping import reversal_auxiliary_transition as X
    from src.engine.scalping import ai_decision_quality as executor
    from src.engine import ai_engine_openai as engine
    from src.engine.scalping.mechanistic_entry_runtime_policy import _source_hash, _signature
    return {Path(path).name:_source_hash(str(Path(path)),_signature(Path(path))) for path in
            (__file__, G.__file__, T.__file__, R.__file__, E.__file__, M.__file__,
             W.__file__, CP.__file__, X.__file__, executor.__file__, engine.__file__)}


def _baseline_values(data_root, bundle, expected_parent):
    """Read the anchored predecessor; never register defaults or follow self."""
    family=bundle['continuous_reversal']
    result={}
    for key, route in V.scopes():
        if family['machine_cells'][key]['routes'][route]['backend'] not in {'union_v5','union_v6'}:
            continue
        payload=family['auxiliary_cells'][key]['routes'][route]['payload']
        value=G.definition(payload['arm'],input_version=payload['binding']['input_version'])
        result[V.scope_id(key,route)]=value['registry_sha256']
    result.update(I.inherited(data_root,bundle))
    if expected_parent is not None:
        predecessor=I.read(I.root(data_root)/'generations'/(expected_parent+'.json'))
        _require(predecessor['artifact_content_sha256']==expected_parent
                 and predecessor['base_bundle_sha256']==bundle['bundle_sha256'], 'predecessor_changed')
        I.validate_record(data_root,predecessor,bundle)
        result.update(predecessor['bindings'])
    for ident in set(result.values()):
        G.load(data_root,ident)
    return result


def _baseline(data_root, bundle, expected_parent):
    """Capture the exact immutable ancestry and compatibility read closure."""
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    from src.engine.scalping import reversal_auxiliary_compatibility as C
    from src.engine.scalping import reversal_auxiliary_transition as X
    observed={};outer=N._READ_DEPENDENCIES.get();token=N._READ_DEPENDENCIES.set(observed)
    paths=set();seen=set()
    def ancestry(path):
        path=Path(path)
        if str(path) in seen:return
        seen.add(str(path));paths.add(str(path))
        value=I.read(path)
        # inherited() caches its top-level registry dependencies. Always read
        # their immutable parent chain too, including entries subsequently
        # overridden by the anchored overlay, so cold/warm closures agree.
        for ident in set(value.get('auxiliary_registry_bindings',{}).values()):
            G.load(data_root,ident)
        old=value.get('auxiliary_reader_code_hashes',value.get('code_hashes'))
        if old is not None and old!=I.code_hashes():
            receipt=C.validate(data_root,bundle,path,old,I.code_hashes())
            paths.update((str(C.path(data_root,bundle,path,I.code_hashes())),receipt['evidence_path']))
            paths.update(item['path'] for item in receipt['frozen_readers'])
        if value.get('evaluation_path'):paths.add(value['evaluation_path'])
        if value.get('transition_manifest_sha256'):
            target=X.folder(data_root)/(value['transition_manifest_sha256']+'.json')
            paths.add(str(target));manifest=I.read(target)
            paths.update(ref['path'] for ref in manifest['sources'])
        if value.get('contract_repair_manifest_sha256'):
            target=I.root(data_root)/'contract_repairs'/(value['contract_repair_manifest_sha256']+'.json')
            paths.add(str(target));manifest=I.read(target)
            paths.update(manifest['source_hashes'])
    try:
        bindings=_baseline_values(data_root,bundle,expected_parent)
        source=N.root(Path(data_root))/'sources'/('reversal-'+bundle['continuous_reversal']['auxiliary_report_sha256']+'.json')
        if source.exists():ancestry(source)
        if expected_parent:ancestry(I.root(data_root)/'generations'/(expected_parent+'.json'))
    finally:
        N._READ_DEPENDENCIES.reset(token)
        if outer is not None:
            for path,signature in observed.items():
                _require(outer.setdefault(path,signature)==signature, 'baseline_dependency_changed')
    paths.update(observed)
    # Current selectors/pointers provide runtime CAS authority at the native
    # publisher. They are deliberately not frozen research evidence.
    mutable={_root(Path(data_root)/'runtime/runtime_release_selection.json'),
             _root(N.root(Path(data_root))/'current.json')}
    dependency_paths=sorted(str(Path(path).absolute()) for path in paths if _root(path) not in mutable
        and Path(path).name not in {'metadata.sqlite3','metadata.sqlite3-wal'})
    refs=[_reference(path) for path in dependency_paths]
    return bindings,refs,dependency_paths


def evaluate_readonly(data_root, day, *, campaign_path):
    """Run the original evaluator body with request-local read-only adapters.

    The module globals are copied, never patched. Only the evaluator's Store
    constructor and report writes are replaced; its calculations stay intact.
    """
    writes=[]
    def capture(path, value):
        writes.append((str(path),copy.deepcopy(value)))
    globals_copy=dict(T.evaluate.__globals__)
    globals_copy['S']=SimpleNamespace(Store=lambda root:S.Store(root,readonly=True))
    globals_copy['P']=SimpleNamespace(**{**vars(P),'write':capture})
    fn=FunctionType(T.evaluate.__code__,globals_copy,T.evaluate.__name__,T.evaluate.__defaults__,T.evaluate.__closure__)
    fn.__kwdefaults__=T.evaluate.__kwdefaults__
    result=fn(data_root,day,campaign_path=campaign_path)
    _require(len(writes)==3, 'readonly_evaluator_write_contract_changed')
    return result, writes


def _semantic_evaluation(value):
    # The immutable historical resolution retains its original used-budget
    # snapshot and code-generation receipt. Recompute decisions without
    # rewriting those historical bytes or requiring an old budget snapshot.
    return {k:v for k,v in value.items() if k not in
            {'artifact_content_sha256','resolution_sha256','policy_generation'}}


def _definition_chain(data_root, value):
    result={value['registry_sha256']:value}
    if value['schema']==G.SCHEMA_V2:
        original=G.load(data_root,value['research_registry_sha256'])
        result[original['registry_sha256']]=original
    return result


def _build(policy_root, ledger_root, report_path, bundle, selected, operating_day,
           expected_parent):
    from src.engine.scalping import reversal_auxiliary_transition as X
    report=I.read(report_path)
    _require(report.get('schema')==REPORT_SCHEMA and report.get('research_complete') is True
        and report.get('observed_current_pointer',{}).get('bundle_sha256')==bundle['bundle_sha256'], 'report_invalid')
    protocol=_read_reference(report['direct_protocol'])
    analysis=_read_reference(report['independent_analysis'])
    previous=_read_reference(report['previous_protocol'])
    projection=_read_reference(report['source_projection'])
    proposals=protocol.get('fixed_prepared_scope_proposals')
    _require(protocol.get('schema')=='auxiliary_direct_current_combined_protocol_v1'
        and protocol.get('parent_bundle_sha256')==bundle['bundle_sha256']
        and protocol.get('input_contract')==E.contract('ROLE_VOCAB_PATH')
        and protocol.get('risk_role_roles')==['candidate']
        and isinstance(proposals,list) and proposals==sorted(set(proposals))
        and all(s.split('|')[1]=='PRE' and not s.startswith('samsung|') for s in proposals)
        and report.get('selected_scopes')==sorted(set(report.get('selected_scopes',[])))
        and set(report['selected_scopes'])<=set(proposals)
        and set(selected)<=set(report['selected_scopes'])
        and analysis.get('protocol_sha256')==protocol['artifact_content_sha256']
        and protocol.get('previous_protocol_sha256')==previous['artifact_content_sha256']
        and previous.get('source_projection_sha256')==projection['artifact_content_sha256'], 'protocol_invalid')
    for item in (report,protocol,analysis):
        _require(all(item.get(k) is v for k,v in P.AUTH.items()), 'research_authority_changed')
    bindings,baseline_sources,baseline_paths=_baseline(policy_root,bundle,expected_parent)
    _require(bindings==protocol.get('bindings') and len(bindings)==128, 'baseline_changed')
    protocol_rows={p['opportunity_key']:p for p in protocol['rows']}
    reuse={p['opportunity_key']:p for p in protocol['candidate_reuse']}
    _require(len(protocol_rows)==len(protocol['rows'])==len(reuse)==50
        and set(protocol_rows)==set(reuse), 'protocol_membership_invalid')
    sources=[_reference(report_path),report['direct_protocol'],report['independent_analysis'],
        report['previous_protocol'],report['source_projection']]+baseline_sources
    source_paths={r['path'] for r in sources}
    def source(path):
        ref=_reference(path)
        if ref['path'] not in source_paths:
            sources.append(ref);source_paths.add(ref['path'])
    all_points={};per=defaultdict(list);registries={};recomputed={};exclusions=[]
    campaigns={};request_ids=set()
    evaluations=report.get('evaluations')
    _require(isinstance(evaluations,list) and evaluations, 'evaluations_missing')
    with S.Store(ledger_root,readonly=True) as store:
        objects_read=set()
        original_get=store.get
        def tracked_get(ident):
            objects_read.add(ident)
            return original_get(ident)
        store.get=tracked_get
        source_parts={}
        wanted_parts={r['source_records_object'] for r in protocol_rows.values()}
        _require(wanted_parts<={p['records_object'] for p in projection['source_parts']}, 'source_partition_missing')
        for part in projection['source_parts']:
            if part['records_object'] not in wanted_parts:
                continue
            points=store.get(part['records_object'])
            _require(P.digest(points)==part['records_sha256'], 'source_partition_changed')
            source_parts[part['records_object']]=points
        for ref in evaluations:
            frozen=_read_reference(ref);source(ref['path'])
            campaign,_,canonical=T.load_campaign(ledger_root,frozen['source_date'],frozen['campaign_path'])
            campaigns[campaign['artifact_content_sha256']]=campaign
            _require(campaign['parent_bundle_sha256']==bundle['bundle_sha256'], 'campaign_parent_changed')
            source(canonical)
            context=R.context(ledger_root,campaign['research']['experiment']);cfg=context['config']
            source(R.directory(ledger_root,campaign['research']['experiment'])/'configuration.json')
            source(R.root(ledger_root)/'allowance.json')
            for limit in (400,600,800,1400,2000,2047):
                funding=R.root(ledger_root)/('allowance-topup-'+str(limit)+'.json')
                if funding.exists():source(funding)
            if context.get('source_scope_sha256'):
                source(R.root(ledger_root)/'source-scopes'/(context['source_scope_sha256']+'.json'))
            _require(context['purpose']=='evaluation'
                and cfg.get('risk_role_contract')==protocol['input_contract']
                and cfg.get('risk_role_roles',['candidate'])==['candidate']
                and not cfg.get('native_current_contract') and not cfg.get('causal_prefix_contract'), 'candidate_input_contract_invalid')
            checked,writes=evaluate_readonly(ledger_root,frozen['source_date'],campaign_path=canonical)
            _require(_semantic_evaluation(checked)==_semantic_evaluation(frozen)
                and all(checked.get(k) is True for k in
                    ('request_completion','comparison_complete','request_accounting_complete')), 'evaluation_changed')
            recomputed[frozen['artifact_content_sha256']]=dict(
                evaluation_semantic_sha256=P.digest(_semantic_evaluation(checked)),
                frozen_resolution_sha256=frozen['resolution_sha256'],captured_report_writes=len(writes))
            owners={(row[1],row[2]):row for row in T.validate_campaign(store,campaign)}
            evaluated={p['opportunity_key']:p for p in checked['pairs']}
            for pair in campaign['pairs']:
                key=pair['opportunity_key'];sid=pair['scope']
                request_ids.update(pair['requests'].values())
                _require(key not in all_points and key in protocol_rows
                    and protocol_rows[key]['scope']==sid and reuse[key]['snapshot_obj']==pair['snapshot_obj']
                    and protocol_rows[key]['day']==pair['day'], 'point_membership_changed')
                _require(pair['current_registry']==bindings.get(sid), 'incumbent_changed')
                snapshot=store.get(pair['snapshot_obj']);snapshot_hash=P.digest(snapshot)
                metadata=protocol_rows[key]
                points=source_parts.get(metadata['source_records_object'])
                ordinal=metadata['source_records_ordinal']
                _require(points is not None and type(ordinal) is int and 0<=ordinal<len(points), 'source_ordinal_invalid')
                source_point=points[ordinal]
                _require(all(source_point.get(k)==pair.get(k) for k in ('opportunity_key','scope','day','outcome'))
                    and source_point.get('symbol')==metadata['symbol']
                    and list(CP.materialize(store,source_point,bundle['continuous_reversal']['operating_manifest']['scopes'][sid]))==snapshot,
                    'source_snapshot_or_label_changed')
                _require(key==M.U.opportunity(snapshot[0]), 'native_opportunity_changed')
                original=G.load(ledger_root,pair['current_registry']);candidate=G.load(ledger_root,pair['candidate_registry'])
                _require(original['schema']==candidate['schema']==G.SCHEMA_V2
                    and 'production_input_contract' not in original and 'production_input_contract' not in candidate,
                    'registry_version_invalid')
                for value in (original,candidate):
                    for ident,definition in _definition_chain(ledger_root,value).items():
                        source(G.directory(ledger_root)/(ident+'.json'))
                        registries[ident]=definition
                production=G.production_definition(candidate,scope_ids=[sid])
                native_input,native_prompt,native_schema=G.production_request(snapshot,production)
                native_req=G.request(snapshot,production)
                envelope=G.envelope(native_input,production)
                proof=dict(opportunity_key=key,scope=sid,snapshot_obj=pair['snapshot_obj'],
                    snapshot_sha256=snapshot_hash,outcome=copy.deepcopy(pair['outcome']),requests=copy.deepcopy(pair['requests']),
                    response_objects={},request_sha256={},result_sha256={},provider_proofs={},verdicts={},
                    logical_input_sha256=P.digest(native_input),production_definition_sha256=production['registry_sha256'])
                all_points[key]=proof
                if evaluated[key]['excluded']:
                    proof['excluded']=copy.deepcopy(evaluated[key]['excluded']);exclusions.append(key);continue
                for role,value in (('current',original),('candidate',candidate)):
                    owner=owners[key,role];rid=pair['requests'][role]
                    _require(owner[4]=='completed' and owner[5] is not None and owner[6]==rid, 'response_missing')
                    req=store.request(rid);record=store.get(owner[5]);result=record['result']
                    provenance=result.get('provider_provenance') or {}
                    _require(record.get('transport_invoked') is True and record.get('validation_errors')==[]
                        and provenance.get('provider')=='openai' and provenance.get('provider_none') is False,
                        'actual_provider_evidence_missing')
                    expected=T.expected_request(ledger_root,campaign,pair,role,snapshot,value)
                    _require(req==expected, 'request_changed')
                    inp=G.production_request(snapshot,value)[0]
                    logical=inp if role=='current' else E.project(inp,expected_contract=protocol['input_contract'])
                    if role=='current':
                        _require(req==G.request(snapshot,original)
                            and req['paired_replay_id']==reuse[key]['raw_current_identity']
                            and P.digest(req)==reuse[key]['raw_current_request_sha256'], 'raw_current_changed')
                    else:
                        _require(logical==native_input and native_input['signals']==inp['signals']
                            and native_req['candidate_input']==req['candidate_input']
                            and all(native_req['candidate'].get(k)==req['candidate'].get(k) for k in
                                ('system_prompt','response_schema','schema_name','provider','model','max_output_tokens','reasoning_effort')),
                            'production_request_parity_failed')
                    actual=X.validate_actual(req,result)
                    if role=='candidate':
                        _require(actual==X.payload_projection(envelope,production), 'provider_payload_parity_failed')
                    decoded,errors=T.response_projection(result,req,logical,value)
                    _require(not errors and decoded['risk_verdict']==evaluated[key]['verdicts'][role], 'response_invalid')
                    if role=='candidate':
                        _require(G.decode_response(result['candidate_response'],native_input,production)==decoded, 'decoder_parity_failed')
                    proof['response_objects'][role]=owner[5]
                    proof['request_sha256'][role]=P.digest(req)
                    proof['result_sha256'][role]=P.digest(store.get(owner[5]))
                    proof['provider_proofs'][role]=dict(request_projection=actual,
                        response_id=result['provider_attempt_receipt']['response_id'],
                        receipt_sha256=result['provider_attempt_receipt']['attempt_receipt_content_sha256'])
                    proof['verdicts'][role]=decoded['risk_verdict']
                cached=reuse[key]
                _require(cached['snapshot_sha256']==snapshot_hash
                    and cached['reused_candidate_request_id']==pair['requests']['candidate']
                    and cached['reused_candidate_request_sha256']==proof['request_sha256']['candidate']
                    and cached['reused_candidate_result_obj']==proof['response_objects']['candidate']
                    and cached['reused_candidate_result_sha256']==proof['result_sha256']['candidate']
                    and cached['reused_provider_response_id']==proof['provider_proofs']['candidate']['response_id'], 'cached_candidate_changed')
                _require(snapshot_hash==P.digest(snapshot), 'snapshot_mutated')
                per[sid].append(proof)
        for generation,campaign in campaigns.items():
            row=store.db.execute('SELECT descriptor_obj FROM generations WHERE generation=?',(generation,)).fetchone()
            _require(row is not None and P.seal(store.get(row[0]))==campaign, 'ledger_generation_descriptor_changed')
        metadata=dict(request_ids=sorted(request_ids),object_ids=sorted(objects_read),generations=sorted(campaigns))
        metadata['fingerprint_sha256']=_ledger_fingerprint(store,metadata)
        packs=set();object_ids=sorted(objects_read)
        for start in range(0,len(object_ids),400):
            chunk=object_ids[start:start+400]
            packs.update(row[0] for row in store.db.execute('SELECT DISTINCT pack FROM objects WHERE id IN ('+
                ','.join('?' for _ in chunk)+')',chunk))
        ledger_packs=sorted(str(S.store_root(ledger_root)/'packs'/pack) for pack in packs)
    _require(set(all_points)==set(protocol_rows), 'all_frozen_points_required')
    changes={};rollback={};details={};embedded={};unselected={}
    for sid in sorted(selected):
        points=per[sid]
        if not points:
            unselected[sid]='source_gap_or_no_common_valid_points';continue
        metrics={role:T.matrix([(p['outcome']['status'],p['verdicts'][role]) for p in points]) for role in ('current','candidate')}
        recorded=analysis['by_scope'][sid]['metrics']
        _require(all(all(recorded[role].get(k)==metrics[role].get(k) for k in ('TP','FP','FN','TN','pass_win_rate'))
            for role in metrics), 'analysis_metrics_changed')
        if not T.improves(metrics['current'],metrics['candidate']):
            unselected[sid]='same_point_pass_win_rate_not_improved';continue
        current_ids={reuse[p['opportunity_key']]['current_registry'] for p in points}
        candidate_ids={reuse[p['opportunity_key']]['candidate_registry'] for p in points}
        _require(current_ids=={bindings[sid]} and len(candidate_ids)==1, 'scope_registry_conflict')
        parent=registries[next(iter(candidate_ids))]
        definition=G.production_definition(parent,scope_ids=[sid])
        embedded.update(_definition_chain(ledger_root,parent));embedded[definition['registry_sha256']]=definition
        changes[sid]=definition['registry_sha256'];rollback[sid]=bindings[sid]
        details[sid]=dict(before=bindings[sid],after=definition['registry_sha256'],metrics=metrics,
            paired_points=len(points),points=points)
    return P.seal(dict(schema=SCHEMA,status='prepared' if changes else 'not_selected',
        base_bundle_sha256=bundle['bundle_sha256'],bundle_target_date=bundle['target_date'],operating_day=operating_day,
        expected_parent=expected_parent,policy_data_root=_root(policy_root),ledger_data_root=_root(ledger_root),
        base_bindings=bindings,base_bindings_sha256=P.digest(bindings),comparison_baseline_kind=BASELINE,
        baseline_dependency_paths=baseline_paths,
        requested_scopes=sorted(selected),changes=changes,rollback_bindings=rollback,scopes=details,
        unselected_scopes=unselected,excluded_scopes=sorted(set(report['selected_scopes'])-set(selected)),
        source_exclusions=exclusions,sources=sources,report_reference=_reference(report_path),
        registry_definitions=embedded,reader_code_hashes=I.code_hashes(),input_transition_code_hashes=code_hashes(),
        ledger_pack_paths=ledger_packs,
        ledger_metadata=metadata,
        wire_contract=W.contract(),verified_pairs=len(all_points)-len(exclusions),
        verified_raw_responses=2*(len(all_points)-len(exclusions)),point_proofs=[all_points[k] for k in sorted(all_points)],
        recomputed_evaluations=recomputed,new_provider_calls=0,db_writer_used=False,
        registry_registered=False,policy_published=False,actual_pid_consumed=False,actual_order_submitted=False))


def prepare(data_root, research_report, bundle, *, scopes=None, ledger_data_root=None, operating_day=None):
    policy_root=Path(data_root).resolve();ledger_root=Path(ledger_data_root or data_root).resolve()
    report=I.read(research_report)
    selected=report.get('selected_scopes',[]) if scopes is None else scopes
    _require(isinstance(selected,(list,tuple)) and len(selected)==len(set(selected)), 'scope_invalid')
    day=operating_day or bundle['target_date']
    _require(isinstance(day,str) and date.fromisoformat(day).isoformat()==day, 'operating_day_invalid')
    before=I.current(policy_root,bundle,day=day)
    manifest=_build(policy_root,ledger_root,research_report,bundle,list(selected),day,(before or {}).get('artifact_content_sha256'))
    if manifest['changes']:
        from src.engine.scalping import reversal_auxiliary_transition as X
        P.write(X.folder(policy_root)/(manifest['artifact_content_sha256']+'.json'),manifest)
    return manifest


def _ledger_fingerprint(store, metadata):
    """Targeted immutable selection metadata, independent of unrelated writes."""
    def rows(table,columns,ids,key):
        result=[]
        for start in range(0,len(ids),400):
            chunk=ids[start:start+400]
            result.extend(store.db.execute('SELECT '+columns+' FROM '+table+' WHERE '+key+' IN ('+
                ','.join('?' for _ in chunk)+') ORDER BY '+key,chunk))
        _require(len(result)==len(ids), 'ledger_metadata_rows_missing')
        return result
    objects=rows('objects','id,hash,pack,offset,length,size',metadata['object_ids'],'id')
    requests=rows('requests','id,identity,input_obj,candidate_obj,control_obj,envelope_obj,state,result_obj',metadata['request_ids'],'id')
    generations=rows('generations','generation,descriptor_obj,expected',metadata['generations'],'generation')
    owners={generation:sorted(store.owners(generation)) for generation in metadata['generations']}
    return P.digest([objects,requests,generations,owners])


def _database_signature(manifest):
    from src.engine.scalping.mechanistic_entry_runtime_policy import _signature
    db=S.store_root(manifest['ledger_data_root'])/'metadata.sqlite3';wal=Path(str(db)+'-wal')
    return (_signature(db),_signature(wal) if wal.exists() else None)


def _dependencies(data_root, manifest):
    from src.engine.scalping.mechanistic_entry_runtime_policy import _signature
    paths={ref['path'] for ref in manifest['sources']}
    paths.update(str(Path(__file__).parent/name) for name in manifest['input_transition_code_hashes']
        if name not in {'ai_engine_openai.py'})
    paths.add(str(Path(__file__).parents[1]/'ai_engine_openai.py'))
    paths.update(str(G.directory(data_root)/(ident+'.json')) for ident in set(manifest['base_bindings'].values()))
    paths.update(manifest['ledger_pack_paths'])
    paths.update(manifest['baseline_dependency_paths'])
    return [(path,_signature(path)) for path in sorted(paths)]


def validate_manifest(data_root, manifest, bundle, *, cached_only=False):
    _require(manifest.get('schema')==SCHEMA and manifest.get('status')=='prepared'
        and manifest.get('artifact_content_sha256')==P.seal(manifest)['artifact_content_sha256']
        and manifest.get('policy_data_root')==_root(data_root)
        and manifest.get('base_bundle_sha256')==bundle['bundle_sha256']
        and manifest.get('bundle_target_date')==bundle['target_date']
        and manifest.get('reader_code_hashes')==I.code_hashes()
        and manifest.get('input_transition_code_hashes')==code_hashes()
        and manifest.get('wire_contract')==W.contract()
        and manifest.get('changes'), 'manifest_invalid')
    # The native bundle loader owns its full content hash. Avoid serializing
    # the multi-megabyte bundle again on every live decision.
    key=(_root(data_root),manifest['artifact_content_sha256'],bundle['bundle_sha256'],
         bundle['target_date'],bundle['continuous_reversal']['family_sha256'])
    dependencies=_dependencies(data_root,manifest)
    database=_database_signature(manifest)
    cached=_VERIFIED.get(key)
    if cached and cached['dependencies']==dependencies:
        if cached['database']==database:
            return manifest
        _require(not cached_only, 'verification_cache_changed_before_publish')
        # An unrelated research INSERT must not trigger full price-path replay
        # or hold a live decision. Recheck only the selected immutable rows.
        before=_database_signature(manifest)
        with S.Store(manifest['ledger_data_root'],readonly=True) as store:
            store.db.execute('BEGIN')
            fingerprint=_ledger_fingerprint(store,manifest['ledger_metadata'])
        after=_database_signature(manifest)
        _require(fingerprint==manifest['ledger_metadata']['fingerprint_sha256'], 'selected_ledger_metadata_changed')
        _require(_dependencies(data_root,manifest)==dependencies, 'dependency_changed_during_validation')
        # A consistent selected-row snapshot is valid even while unrelated
        # writes continue. Never associate that snapshot with a newer global
        # DB signature; the next call then repeats only this targeted check.
        if before==after:
            _VERIFIED[key]=dict(dependencies=dependencies,database=after)
        return manifest
    _require(not cached_only, 'verification_cache_changed_before_publish')
    for ref in manifest['sources']:
        from src.engine.scalping import reversal_auxiliary_transition as X
        X.verify_reference(ref)
    rebuilt=_build(Path(data_root),Path(manifest['ledger_data_root']),manifest['report_reference']['path'],bundle,
        manifest['requested_scopes'],manifest['operating_day'],manifest['expected_parent'])
    _require(rebuilt==manifest, 'evidence_changed')
    _require(_dependencies(data_root,manifest)==dependencies, 'dependency_changed_during_validation')
    after_database=_database_signature(manifest)
    if len(_VERIFIED)>=64:
        _VERIFIED.clear()
    _VERIFIED[key]=dict(dependencies=dependencies,database=database if database==after_database else None)
    return manifest


def register_definitions(data_root, manifest):
    """Called only after native publisher authority, locks and parent CAS."""
    # Historical source and production definitions are immutable registry
    # entries. This does not copy request/response objects or change a ledger.
    values=manifest['registry_definitions'].values()
    for value in sorted(values,key=lambda v:('production_input_contract' in v,v['schema']==G.SCHEMA_V2,v['registry_sha256'])):
        G.register(data_root,value)
