"""Explicit, content-bound next-session ADD intake; no research or AI quota reset."""
from __future__ import annotations
import copy
import fcntl
import json
from pathlib import Path
from src.engine.scalping import reversal_extended_catalog as C
from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.scalping import mechanistic_entry_runtime_policy as N

AUTHORITY='APPROVED_PRE_AFTER_PLAN_IMPLEMENTATION_20261008'


def pending_path(data_root):return N.root(Path(data_root))/'extended-registration.json'


def intake(data_root,research_dir,parent,*,confirm,publication):
    if confirm!=AUTHORITY:raise ValueError('extended_registration_authority_required')
    research_dir=Path(research_dir);batch=json.loads((research_dir/'proposed-registration-batch.json').read_text())
    if (batch.get('batch_sha256')!=P.digest({k:v for k,v in batch.items() if k!='batch_sha256'})
            or batch['batch_sha256']!=C.RESEARCH_BATCH_SHA256
            or batch['baseline_bundle']!=parent['bundle_sha256']):
        raise ValueError('extended_research_parent_or_batch_changed')
    if len(batch['candidates'])!=13 or {r['branch_id'] for r in batch['candidates']}!=set(C.NEW_DEFINITIONS):
        raise ValueError('extended_registration_census_invalid')
    changes={}
    for r in batch['candidates']:
        bid=r['branch_id'];key,route=r['scope'].rsplit('|',1)
        if (r['definition']!=C.definition(bid) or r['definition_sha256']!=P.digest(r['definition'])
                or not C.applicable(bid,key,route)):
            raise ValueError('extended_registration_definition_changed')
        changes[r['scope']]=dict(add=[bid],remove=[])
    frozen=Path(data_root)/'report/continuous_reversal_operating/registrations'/batch['batch_sha256']
    frozen.mkdir(parents=True,exist_ok=True);receipts=[]
    for name in ('proposed-registration-batch.json','manifest.json','result.json','source-coverage.json',
                 'validation-native.json','validation-labels.json','coverage-defect-reproduction.json','research.py','finish.py','validate.py'):
        src=research_dir/name;content=src.read_bytes();sha=P.file_hash(src);dest=frozen/(sha+src.suffix)
        if dest.exists() and dest.read_bytes()!=content:raise ValueError('extended_research_archive_conflict')
        if not dest.exists():
            with dest.open('xb') as handle:handle.write(content)
        receipts.append(dict(name=name,path=str(dest.resolve()),sha256=sha))
    byname={r['name']:r for r in receipts}
    if batch['source_manifest_sha256']!=byname['manifest.json']['sha256'] or batch['result_sha256']!=byname['result.json']['sha256']:
        raise ValueError('extended_research_evidence_changed')
    # Preserve exact small research inputs outside tmp. Shared normalized raw
    # partitions remain references, never a second cumulative raw ledger.
    manifest=json.loads((research_dir/'manifest.json').read_text())
    retained=list(manifest['code'])+list(manifest['bar_receipts'])
    retained += [dict(path=p['path'],sha256=p['sha256']) for p in manifest['partitions']]
    retained += [dict(path=str(research_dir/'baseline-bundle.json'),sha256=manifest['baseline_file_sha256']),
                 dict(path=str(research_dir/'relabel_native.py'),sha256=manifest['relabel_code_sha256'])]
    for item in retained:
        src=Path(item['path'])
        if P.file_hash(src)!=item['sha256']:raise ValueError('extended_research_reference_changed')
        dest=frozen/item['sha256']
        if not dest.exists():
            with dest.open('xb') as handle:handle.write(src.read_bytes())
        if P.file_hash(dest)!=item['sha256']:raise ValueError('extended_research_archive_conflict')
        receipts.append(dict(name=src.name,original_path=str(src),path=str(dest.resolve()),sha256=item['sha256']))
    with N.source_anchor(data_root):
        for part in manifest['partitions']:
            raw=part['source'];path=N.source_path(raw['path'])
            if P.file_hash(path)!=raw['sha256']:raise ValueError('extended_research_raw_changed')
            receipts.append(dict(name='shared_normalized_source',path=str(path),sha256=raw['sha256']))
    request=P.seal(dict(schema='main_extended_registration_request_v1',kind='ADD',
        research_batch_sha256=batch['batch_sha256'],parent_bundle_sha256=parent['bundle_sha256'],
        operator_receipt=confirm,scopes=changes,definition_hashes={bid:P.digest(C.definition(bid)) for bid in C.NEW_DEFINITIONS},
        target_date=N.next_target(publication),publication_date=publication,source_receipts=receipts,
        registration_state='registered',activation_state='pending_next_session_publication',
        comparison_result_required=False,actual_order_submitted=False))
    path=pending_path(data_root)
    with (N.root(Path(data_root))/'publisher.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        if N.load_effective(data_root=Path(data_root),target_date=publication)['bundle_sha256']!=parent['bundle_sha256']:
            raise ValueError('extended_registration_parent_cas_failed')
        if path.exists():
            old=P.seal(json.loads(path.read_text()))
            if old!=request:raise ValueError('extended_registration_request_conflict')
            return old
        N._atomic_write_json(path,request)
    return request


def pending(data_root,parent,target_date):
    path=pending_path(data_root)
    if not path.exists():return None
    r=N._read(path)
    if r.get('artifact_content_sha256')!=P.seal(r)['artifact_content_sha256'] or r.get('operator_receipt')!=AUTHORITY:
        raise ValueError('extended_registration_authority_changed')
    if (r.get('research_batch_sha256')!=C.RESEARCH_BATCH_SHA256 or r.get('kind')!='ADD'
            or r.get('definition_hashes')!={b:P.digest(C.definition(b)) for b in C.NEW_DEFINITIONS}):
        raise ValueError('extended_registration_definition_changed')
    for receipt in r['source_receipts']:
        if P.file_hash(receipt['path'])!=receipt['sha256']:raise ValueError('extended_registration_evidence_changed')
    f=parent['continuous_reversal'];membership=f.get('operating_manifest',{}).get('scopes',{})
    if f.get('schema')=='continuous_reversal_policy_v6' and all(set(v['add'])<=set(membership.get(s,[])) for s,v in r['scopes'].items()):
        return None  # Same IDs/definitions were validated by the current family.
    if r['target_date']!=target_date or r['parent_bundle_sha256']!=parent['bundle_sha256']:
        raise ValueError('extended_registration_target_or_parent_changed')
    expected={d['symbol_group']+'|'+d['market']+'|'+d['price_band']+'|'+d['route']:dict(add=[b],remove=[]) for b,d in C.NEW_DEFINITIONS.items()}
    if r['scopes']!=expected:raise ValueError('extended_registration_scopes_changed')
    return r


def initial_reports(data_root,day,publication,parent,machine,*,publish_policy=True,output_directory=None,effective_date=None):
    """Registration is explicit; incomplete auxiliary comparison is diagnostic."""
    from src.engine.scalping import continuous_reversal_operating_postclose as O
    from src.engine.scalping import continuous_reversal_policy_v6 as V
    from src.engine.scalping import reversal_extended_union as A
    from src.engine.scalping import reversal_auxiliary_registry as G
    from src.engine.scalping import reversal_auxiliary_intraday as I
    from src.engine.scalping import reversal_auxiliary_tuning as T
    from src.engine.scalping import continuous_reversal_shared_ledger as L
    from src.engine.ai import offline_comparison_store as S
    import gzip
    import subprocess
    change=pending(data_root,parent,N.next_target(publication))
    if not change or machine.get('registration_change')!=change:
        raise ValueError('extended_registration_machine_binding_invalid')
    expected=V.detector_manifest(parent,effective_date=effective_date or change['target_date'],changes=change)
    if machine['operating_manifest']!=expected:raise ValueError('extended_registration_manifest_changed')
    if output_directory is not None and publish_policy:raise ValueError('extended_registration_isolated_output_required')
    mc=copy.deepcopy(parent['continuous_reversal']['machine_cells']);ac=copy.deepcopy(parent['continuous_reversal']['auxiliary_cells']);bindings={}
    current_bindings=I.effective_bindings(data_root,parent,day=publication)
    for key,route in V.scopes():
        sid=V.scope_id(key,route);ids=expected['scopes'][sid]
        old=parent['continuous_reversal']['auxiliary_cells'][key]['routes'][route]
        arm=old['payload']['arm'];binding=A.binding(arm)
        payload=dict(composition='ANY_MATCH_ONE_INTENT',branches=[C.branch(b) for b in ids]);aux=dict(arm=arm,binding=binding)
        mc[key]['routes'][route]=dict(payload=payload,payload_sha256=P.digest(payload),backend='union_v6',
            scope_execution_hash=V.scope_hash(ids,aux,'union_v6',machine['execution_code_sha256']),
            status='operator_initial_registered' if sid in change['scopes'] else 'verified_membership_carried')
        ac[key]['routes'][route]=dict(payload=aux,payload_sha256=P.digest(aux),actual_response_evidence=[],
            local_metrics=None,inherited_from=old.get('inherited_from'),initial_binding=dict(operator_receipt=change['operator_receipt'],
            research_batch_sha256=change['research_batch_sha256'],source_scope=sid,source_bundle_sha256=parent['bundle_sha256'],
            comparison_result_required=False,response_evidence_role='typed_contract_fixture_verified_no_new_actual_comparison_claim'))
        previous=G.load(data_root,current_bindings[sid])
        prior_projector=G.projector(previous['input_version'])
        custom=previous['prompt']!=prior_projector.PROMPT+prior_projector.ARM_SUFFIXES[previous['base_arm']]
        bindings[sid]=G.register(data_root,G.definition(previous['base_arm'],input_version=A.VERSION,
            prompt=previous['prompt'] if custom else None,hypothesis=previous['hypothesis'],development_keys=previous['development_keys']))
    comparison_receipts=[];proofs=[];campaign=None;evaluation=None;ownerstates={}
    if output_directory is None and T.config(data_root) is not None:
        campaign=T.read(T.directory(data_root,day)/'latest-campaign.json')
        if campaign['machine_report_sha256']!=machine['artifact_content_sha256'] or campaign['parent_bundle_sha256']!=parent['bundle_sha256']:
            raise ValueError('extended_registration_comparison_generation_changed')
        evaluation=T.evaluate(data_root,day)
        for path in (T.directory(data_root,day)/'campaigns'/(campaign['artifact_content_sha256']+'.json'),
                     T.directory(data_root,day)/'evaluations'/(evaluation['artifact_content_sha256']+'.json')):
            comparison_receipts.append(dict(path=str(path.resolve()),sha256=P.file_hash(path)))
        from collections import Counter
        with S.Store(data_root) as store:
            T.validate_campaign(store,campaign)
            snapshot=store.snapshot(campaign['artifact_content_sha256'])
            (T.directory(data_root,day)/'frozen').mkdir(parents=True,exist_ok=True)
            evidence=L.response_evidence(store,T.directory(data_root,day),snapshot)
            ownerstates=dict(Counter(r[4] for r in store.owners(campaign['artifact_content_sha256'])))
        proofs.append(dict(path=str(evidence.resolve()),sha256=P.file_hash(evidence)))
    for ident in sorted(set(bindings.values())|set(current_bindings.values())):
        path=G.directory(data_root)/(ident+'.json')
        comparison_receipts.append(dict(path=str(path.resolve()),sha256=P.file_hash(path)))
    receipts=machine['source_receipts']+change['source_receipts']+comparison_receipts+[dict(path=str(pending_path(data_root).resolve()),sha256=P.file_hash(pending_path(data_root)))]
    issued=P.seal(dict(machine,cells=list(mc.values()),status='completed',source_receipts=receipts,
        membership_status='registered',registration_state='registered',adoption_basis='operator_designated',comparison_state='incomplete',scope_pending=[]))
    # Keep the comparison result distinct; registration never asserts provider PASS.
    auxiliary=P.seal(dict(schema=O.SCHEMA,source_date=day,target_date=day,publication_date=publication,status='completed',
        cells=list(ac.values()),machine_report_sha256=issued['artifact_content_sha256'],source_receipts=change['source_receipts']+comparison_receipts,results_sources=proofs,
        auxiliary_registry_bindings=bindings,auxiliary_independent_scopes=sorted(I.independent_scopes(data_root,parent,I.current(data_root,parent,day=publication))),
        comparison_complete=False,comparison_state='incomplete',comparison_contract='bounded_registered_prompt_pair',
        initial_registration=change,registration_state='registered',adoption_basis='operator_designated',scope_pending=[],
        scope_census=dict(planned=len(V.scopes()),new_ready=len(V.scopes()),new_actual_pid_consumed=0,native_carried=0,contract_gaps=0),
        comparison_evaluation=evaluation,owner_request_census=dict(expected=(campaign or {}).get('expected_owner_requests',0),missing=0,**ownerstates),
        observation_mode='confirmation_replay',call_limit=T.LIMIT,**P.AUTH))
    auxiliary=P.seal(dict(auxiliary,auxiliary_reader_code_hashes=I.code_hashes()))
    out=Path(output_directory) if output_directory is not None else O.directory(data_root,day)
    P.write(out/'machine.json',issued);P.write(out/'auxiliary.json',auxiliary)
    if publish_policy:
        P.write(P.directory(data_root,day)/'auxiliary.json',auxiliary)
        P.write(P.directory(data_root,day)/'call-freeze.json',P.seal(dict(schema=O.SCHEMA,source_date=day,status='frozen',
            comparison_contract=T.SCHEMA,machine_report_sha256=machine['artifact_content_sha256'],
            campaign_sha256=(campaign or {}).get('artifact_content_sha256'),call_limit=T.LIMIT,census=ownerstates,
            registration_without_comparison_gate=True,**P.AUTH)))
        with (P.directory(data_root,day)/'provider-results.jsonl').open('w') as dest:
            for proof in proofs:
                with gzip.open(proof['path'],'rt') as src:
                    for line in src:dest.write(line)
        commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
        bundle=V.stage(data_root,day,publication,issued,auxiliary,target_date=N.next_target(publication),release_commit=commit)
        P.write(Path(data_root)/'report/ai_entry_setup_paired_replay_batch'/f'compact_auxiliary_paired_economic_{day}.json',
            P.seal(dict(auxiliary,staged=dict(status='prepared',bundle_sha256=bundle['bundle_sha256'],target_date=bundle['target_date']))))
    return auxiliary
