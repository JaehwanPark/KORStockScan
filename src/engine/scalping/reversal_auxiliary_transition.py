"""Validated compact-response transitions; auxiliary publisher then machine lock.

Preparation reuses exact shared-store requests outside publication locks. Only
an explicit approved manifest may move the auxiliary pointer. No order owner.
"""
from __future__ import annotations

import base64
import copy
import fcntl
import hashlib
import json
from datetime import datetime
from pathlib import Path
from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.scalping import reversal_auxiliary_registry as G
from src.engine.scalping import reversal_auxiliary_intraday as I
from src.engine.scalping import reversal_auxiliary_tuning as T
from src.engine.scalping import reversal_auxiliary_wire as W
from src.engine.ai import offline_comparison_store as S

SCHEMA='auxiliary_compact_transition_v1'
BASELINE='incumbent_prompt_under_successor_wire'
_VERIFIED={}


def folder(data_root):
    return I.root(data_root)/'transitions'


def reference(path):
    return dict(path=str(Path(path).resolve()),sha256=P.file_hash(path))


def verify_reference(item):
    if P.file_hash(item['path'])!=item['sha256']:
        raise ValueError('auxiliary_transition_source_changed')


def payload_projection(envelope, registry):
    """Model-visible commitment, excluding transport IDs and local deadlines."""
    from src.engine.ai_engine_openai import OpenAIResponseRequest
    req=OpenAIResponseRequest(prompt=envelope['final_prompt'],user_input=json.dumps(envelope['wire_input'],ensure_ascii=True,sort_keys=True,separators=(',',':')),
        require_json=True,context_name='auxiliary_transition_parity',model_name=registry['model'],temperature=None,
        schema_name=registry['response_schema_version'],endpoint_name='analyze_target',request_id='parity',symbol='-',cache_key='-',
        submitted_at_perf=0,timeout_ms=5000,max_output_tokens=registry['max_output_tokens'],reasoning_effort=registry['reasoning_effort'],
        metadata={'auxiliary_registry_sha256':registry['registry_sha256']},response_schema_override=envelope['wire_schema'])
    p=req.build_provider_payload(use_schema_registry=True)
    return dict(model=p['model'],instructions_sha256=hashlib.sha256(p['instructions'].encode()).hexdigest(),
        input_sha256=hashlib.sha256(p['input'].encode()).hexdigest(),input_size=len(p['input'].encode()),
        schema=p['text']['format']['name'],schema_sha256=P.digest(p['text']['format']['schema']),strict=p['text']['format']['strict'],
        verbosity=p['text']['verbosity'],store=p['store'],max_output_tokens=p['max_output_tokens'],reasoning=p['reasoning'],temperature=p.get('temperature'))


def validate_actual(req, result):
    """Check stored raw output and original exact provider-request projection."""
    from src.engine.scalping.ai_decision_quality import execute_openai_prompt_v2_candidate
    receipt=result['provider_attempt_receipt']
    if receipt['attempt_receipt_content_sha256']!=P.digest({k:v for k,v in receipt.items() if k!='attempt_receipt_content_sha256'}):
        raise ValueError('auxiliary_raw_receipt_changed')
    raw=base64.b64decode(receipt['provider_output_bytes_b64'],validate=True)
    if (hashlib.sha256(raw).hexdigest()!=receipt['provider_output_bytes_sha256']
            or len(raw)!=receipt['provider_output_size_bytes'] or not receipt.get('response_id')
            or receipt.get('parse_status')!='pass' or json.loads(raw)!=result['candidate_response']
            or receipt['parsed_candidate_payload']!=result['candidate_response']
            or receipt['parsed_candidate_payload_sha256']!=P.digest(result['candidate_response'])):
        raise ValueError('auxiliary_raw_response_changed')
    expected=execute_openai_prompt_v2_candidate(req,_request_projection_only=True)['provider_request_projection']
    if receipt['provider_request_projection']!=expected or receipt['provider_request_projection_sha256']!=P.digest(expected):
        raise ValueError('auxiliary_provider_request_changed')
    if result.get('provider_provenance',{}).get('response_id')!=receipt['response_id']:
        raise ValueError('auxiliary_provider_identity_changed')
    text=expected['system_instructions']
    return dict(model=expected['model'],instructions_sha256=text['bytes_sha256'],input_sha256=expected['user_input_bytes_sha256'],
        input_size=expected['user_input_size_bytes'],schema=expected['response_schema_name'],schema_sha256=expected['response_schema_instance_sha256'],
        strict=expected['response_schema_strict'],verbosity=expected['text_verbosity'],store=expected['store'],
        max_output_tokens=expected['max_output_tokens'],reasoning=expected['reasoning'],temperature=expected['temperature'])


def prepare(data_root,research_report,bundle,*,scopes=None):
    from src.engine.scalping import reversal_auxiliary_research as R
    report=I.read(research_report)
    if not report.get('research_complete') or report['observed_current_pointer']['bundle_sha256']!=bundle['bundle_sha256']:
        raise ValueError('auxiliary_transition_research_parent_invalid')
    chosen={r['scope']:r for r in report['selected_research_candidates']}
    selected=set(chosen) if scopes is None else set(scopes)
    if not selected or not selected<=set(chosen):raise ValueError('auxiliary_transition_scope_unqualified')
    day=bundle['target_date'];before=I.current(data_root,bundle,day=day)
    bindings=I.effective_bindings(data_root,bundle,day=day)
    evaluations={}; sources=[reference(research_report)];pairs_checked=0;raw_checked=0;adoption_points={s:[] for s in selected}
    for experiment,ident in report['evaluations'].items():
        ep=R.directory(data_root,experiment)/'evaluations'/(ident+'.json')
        evaluation=I.read(ep)
        checked=T.evaluate(data_root,evaluation['source_date'],campaign_path=evaluation['campaign_path'])
        if checked!=evaluation:raise ValueError('auxiliary_transition_evaluation_changed')
        c,_,_=T.load_campaign(data_root,evaluation['source_date'],evaluation['campaign_path'])
        if c['parent_bundle_sha256']!=bundle['bundle_sha256']:raise ValueError('auxiliary_transition_campaign_parent_changed')
        sources.extend([reference(ep),reference(evaluation['campaign_path'])])
        evaluations[ident]=evaluation
        with S.Store(data_root) as store:
            rows=T.validate_campaign(store,c);owners={(r[1],r[2]):r for r in rows}
            for pair in c['pairs']:
                snapshot=store.get(pair['snapshot_obj']);decoded={}
                for role in ('current','candidate'):
                    row=owners[pair['opportunity_key'],role]
                    if row[4]!='completed' or not row[5]:raise ValueError('auxiliary_transition_pair_incomplete')
                    result=store.get(row[5])['result'];req=store.request(row[6])
                    original=G.load(data_root,pair[role+'_registry'])
                    inp,prompt,schema=G.production_request(snapshot,original)
                    actual=validate_actual(req,result)
                    if req['candidate'].get('compact_wire_contract'):
                        new=G.compact_definition(original,research_wire_contract=req['candidate']['compact_wire_contract'])
                        env=G.envelope(inp,new)
                        if payload_projection(env,new)!=actual:raise ValueError('auxiliary_transition_provider_parity_failed')
                        response=W.decode(result['candidate_response'],inp,original['base_arm'])
                        old,errors=T.response_projection(result,req,inp,original)
                        if errors or response!=old:raise ValueError('auxiliary_transition_decoder_parity_failed')
                    else:
                        response,errors=T.response_projection(result,req,inp,original)
                        if errors:raise ValueError('auxiliary_transition_response_invalid')
                    decoded[role]=response['risk_verdict'];raw_checked+=1
                pairs_checked+=1
                sid=pair['scope']
                if sid in selected and chosen[sid]['evaluation_sha256']==ident:
                    adoption_points[sid].append(dict(opportunity_key=pair['opportunity_key'],snapshot_obj=pair['snapshot_obj'],
                        requests=pair['requests'],response_objects={r:owners[pair['opportunity_key'],r][5] for r in ('current','candidate')},outcome=pair['outcome']['status'],verdicts=decoded))
    # Retain small immutable reader sources, never duplicate request/result ledgers.
    frozen=I.root(data_root)/'frozen_readers'/P.digest(I.code_hashes())
    frozen.mkdir(parents=True,exist_ok=True)
    for name,sha in I.code_hashes().items():
        original=Path(__file__).parent/name;dest=frozen/name
        if not dest.exists():dest.write_bytes(original.read_bytes())
        if P.file_hash(dest)!=sha:raise ValueError('auxiliary_frozen_reader_changed')
        sources.append(reference(dest))
    changes={};rollback={};details={}
    for sid in sorted(selected):
        selection=chosen[sid];e=evaluations[selection['evaluation_sha256']];m=e['scopes'][sid]
        if e.get('research',{}).get('purpose')=='development' or not T.improves(m['current'],m['candidate']):
            raise ValueError('auxiliary_transition_scope_unqualified')
        if bindings.get(sid)!=m['current_registry'] or m['candidate_registry']!=selection['candidate_registry']:
            raise ValueError('auxiliary_transition_incumbent_changed')
        points=adoption_points[sid]
        if len(points)!=m['paired_points'] or any(T.matrix([(p['outcome'],p['verdicts'][r]) for p in points])!=m[r] for r in ('current','candidate')):
            raise ValueError('auxiliary_transition_metrics_changed')
        v=G.compact_definition(G.load(data_root,m['candidate_registry']),research_wire_contract=selection['compact_wire'])
        changes[sid]=G.register(data_root,v);rollback[sid]=bindings[sid]
        sources.extend([reference(G.directory(data_root)/(m['candidate_registry']+'.json')),reference(G.directory(data_root)/(changes[sid]+'.json'))])
        details[sid]=dict(evaluation_sha256=selection['evaluation_sha256'],before=bindings[sid],after=changes[sid],metrics=m,points=points)
    manifest=P.seal(dict(schema=SCHEMA,base_bundle_sha256=bundle['bundle_sha256'],operating_day=day,
        expected_parent=(before or {}).get('artifact_content_sha256'),base_bindings_sha256=P.digest(bindings),
        comparison_baseline_kind=BASELINE,changes=changes,rollback_bindings=rollback,scopes=details,
        excluded_scopes=sorted(set(chosen)-selected),sources=sources,reader_code_hashes=I.code_hashes(),
        wire_contract=W.contract(),verified_pairs=pairs_checked,verified_raw_responses=raw_checked,new_provider_calls=0,
        actual_pid_consumed=False,actual_order_submitted=False))
    P.write(folder(data_root)/(manifest['artifact_content_sha256']+'.json'),manifest)
    return manifest


def validate_manifest(data_root,manifest,bundle):
    if (manifest.get('schema')!=SCHEMA or manifest.get('artifact_content_sha256')!=P.seal(manifest)['artifact_content_sha256']
            or manifest.get('base_bundle_sha256')!=bundle['bundle_sha256']
            or manifest.get('reader_code_hashes')!=I.code_hashes() or manifest.get('wire_contract')!=W.contract()
            or manifest.get('comparison_baseline_kind')!=BASELINE or not manifest.get('changes')
            or set(manifest['changes'])!=set(manifest['scopes'])):
        raise ValueError('auxiliary_transition_manifest_invalid')
    from src.engine.scalping.mechanistic_entry_runtime_policy import _signature
    dependencies=[(r['path'],_signature(Path(r['path']))) for r in manifest['sources']]
    key=(str(Path(data_root).resolve()),manifest['artifact_content_sha256'])
    if _VERIFIED.get(key)==dependencies:return manifest
    for item in manifest['sources']:verify_reference(item)
    research=I.read(manifest['sources'][0]['path'])
    selected={r['scope']:r for r in research.get('selected_research_candidates',[])}
    if (not research.get('research_complete') or not set(manifest['changes'])<=set(selected)
            or research.get('observed_current_pointer',{}).get('bundle_sha256')!=bundle['bundle_sha256']):
        raise ValueError('auxiliary_transition_scope_unqualified')
    evaluations={}
    for item in manifest['sources'][1:]:
        if '/evaluations/' in item['path']:
            evaluation=I.read(item['path']);evaluations[evaluation['artifact_content_sha256']]=evaluation
    for sid,ident in manifest['changes'].items():
        details=manifest['scopes'][sid];value=G.load(data_root,ident)
        chosen=selected[sid];evaluation=evaluations.get(chosen['evaluation_sha256'])
        if (not evaluation or evaluation.get('research',{}).get('purpose')=='development'
                or evaluation.get('parent_bundle_sha256')!=bundle['bundle_sha256']
                or details['evaluation_sha256']!=chosen['evaluation_sha256']
                or details['metrics']!=evaluation['scopes'][sid] or not T.improves(details['metrics']['current'],details['metrics']['candidate'])
                or value['research_registry_sha256']!=chosen['candidate_registry']
                or value['research_wire_contract']!=chosen.get('compact_wire')
                or details['before']!=chosen['current_registry']
                or len(details['points'])!=details['metrics']['paired_points']
                or any(T.matrix([(p['outcome'],p['verdicts'][r]) for p in details['points']])!=details['metrics'][r] for r in ('current','candidate'))):
            raise ValueError('auxiliary_transition_evidence_binding_changed')
        if value['schema']!=G.SCHEMA_V2 or details['after']!=ident or manifest['rollback_bindings'][sid]!=details['before']:
            raise ValueError('auxiliary_transition_registry_changed')
    _VERIFIED[key]=dependencies
    return manifest


def validate_published(data_root,record,bundle):
    m=I.read(folder(data_root)/(record['transition_manifest_sha256']+'.json'))
    if m['artifact_content_sha256']!=record['transition_manifest_sha256']:
        raise ValueError('auxiliary_transition_identity_changed')
    validate_manifest(data_root,m,bundle)
    # Subsequent scope rollbacks retain the original manifest as lineage only.
    if not record.get('rollback_reason') and any(record['bindings'].get(s)!=v for s,v in m['changes'].items()):
        raise ValueError('auxiliary_transition_binding_changed')
    return m


def publish(data_root,manifest,*,confirm,now=None):
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    if confirm!=I.AUTHORITY:raise ValueError('auxiliary_intraday_authority_required')
    clock=now or datetime.now(I.K.KST)
    if clock.tzinfo is None:raise ValueError('auxiliary_intraday_clock_invalid')
    day=clock.astimezone(I.K.KST).date().isoformat()
    # Heavy replay belongs to prepare, never under either publication lock.
    preliminary=N.load_effective(data_root=Path(data_root),target_date=day)
    validate_manifest(data_root,manifest,preliminary)
    aux=I.root(data_root);aux.mkdir(parents=True,exist_ok=True)
    with (aux/'publisher.lock').open('a') as alock:
        fcntl.flock(alock,fcntl.LOCK_EX)
        with (N.root(Path(data_root))/'publisher.lock').open('a') as mlock:
            fcntl.flock(mlock,fcntl.LOCK_EX)
            bundle=N.load_effective(data_root=Path(data_root),target_date=day)
            validate_manifest(data_root,manifest,bundle)
            before=I.current(data_root,bundle,day=day)
            ident=manifest['artifact_content_sha256']
            if before and before.get('transition_manifest_sha256')==ident and not before.get('rollback_reason'):
                return before
            if day!=manifest['operating_day'] or (before or {}).get('artifact_content_sha256')!=manifest['expected_parent']:
                raise ValueError('auxiliary_transition_parent_cas_failed')
            bindings=I.effective_bindings(data_root,bundle,day=day)
            if P.digest(bindings)!=manifest['base_bindings_sha256']:raise ValueError('auxiliary_transition_incumbent_changed')
            bindings.update(manifest['changes'])
            body=P.seal(dict(schema=I.SCHEMA,authority=confirm,day=day,effective_from=clock.isoformat(),
                base_bundle_sha256=bundle['bundle_sha256'],base_family_sha256=bundle['continuous_reversal']['family_sha256'],
                detector_manifest_hash=bundle['continuous_reversal']['operating_manifest']['detector_manifest_hash'],
                previous_overlay_sha256=manifest['expected_parent'],bindings=bindings,changes=manifest['changes'],
                independent_scopes=sorted(I.independent_scopes(data_root,bundle,before)|set(manifest['changes'])),
                code_hashes=I.code_hashes(),transition_manifest_sha256=ident,rollback_bindings=manifest['rollback_bindings'],
                revoked_overlays=(before or {}).get('revoked_overlays',[]),revoked_scope_overlays=(before or {}).get('revoked_scope_overlays',{}),
                actual_pid_consumed=False,actual_order_submitted=False))
            I.validate_record(data_root,body,bundle)
            N._atomic_write_json(aux/'generations'/(body['artifact_content_sha256']+'.json'),body)
            I.write_day_pointer(data_root,body)
            N._atomic_write_json(aux/'current.json',body)
            if I.current(data_root,bundle,day=day)!=body:raise ValueError('auxiliary_transition_readback_failed')
            return body


def rollback_scopes(data_root,*,expected_parent,reason,confirm,scopes,now=None):
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    if confirm!=I.AUTHORITY or not reason or not scopes:
        raise ValueError('auxiliary_rollback_authority_required')
    clock=now or datetime.now(I.K.KST)
    if clock.tzinfo is None:raise ValueError('auxiliary_intraday_clock_invalid')
    day=clock.astimezone(I.K.KST).date().isoformat();root=I.root(data_root)
    with (root/'publisher.lock').open('a') as alock:
        fcntl.flock(alock,fcntl.LOCK_EX)
        with (N.root(Path(data_root))/'publisher.lock').open('a') as mlock:
            fcntl.flock(mlock,fcntl.LOCK_EX)
            bundle=N.load_effective(data_root=Path(data_root),target_date=day)
            before=I.current(data_root,bundle,day=day)
            if (before or {}).get('artifact_content_sha256')!=expected_parent:
                raise ValueError('auxiliary_rollback_parent_changed')
            bindings=I.effective_bindings(data_root,bundle,day=day)
            restore=I.rollback_bindings(data_root,bundle,before)
            if not set(scopes)<=set(restore):raise ValueError('auxiliary_scope_rollback_source_missing')
            changes={sid:restore[sid] for sid in scopes}
            for ident in changes.values():G.load(data_root,ident)
            rejected={sid:bindings[sid] for sid in scopes}
            bindings.update(changes)
            revoked=copy.deepcopy((before or {}).get('revoked_scope_overlays',{}))
            cursor=before;seen=set()
            while cursor:
                token=cursor['artifact_content_sha256']
                if token in seen:raise ValueError('auxiliary_overlay_cycle')
                seen.add(token)
                affected={sid for sid in scopes if cursor['bindings'].get(sid)==rejected[sid]}
                revoked[token]=sorted(set(revoked.get(token,[]))|affected)
                previous=cursor.get('previous_overlay_sha256')
                cursor=I.read(root/'generations'/(previous+'.json')) if previous else None
            if expected_parent is None:revoked['inherited:'+bundle['bundle_sha256']]=sorted(scopes)
            record=P.seal(dict(schema=I.SCHEMA,authority=confirm,day=day,effective_from=clock.isoformat(),
                base_bundle_sha256=bundle['bundle_sha256'],base_family_sha256=bundle['continuous_reversal']['family_sha256'],
                detector_manifest_hash=bundle['continuous_reversal']['operating_manifest']['detector_manifest_hash'],
                previous_overlay_sha256=expected_parent,bindings=bindings,changes=changes,
                independent_scopes=sorted(I.independent_scopes(data_root,bundle,before)),code_hashes=I.code_hashes(),
                rollback_reason=reason,rollback_bindings=restore,revoked_scope_overlays=revoked,
                revoked_overlays=(before or {}).get('revoked_overlays',[]),actual_pid_consumed=False,actual_order_submitted=False))
            I.validate_record(data_root,record,bundle)
            N._atomic_write_json(root/'generations'/(record['artifact_content_sha256']+'.json'),record)
            I.write_day_pointer(data_root,record)
            N._atomic_write_json(root/'current.json',record)
            return record


def main(argv=None):
    import argparse
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root',type=Path,required=True)
    parser.add_argument('--mode',choices=['prepare','publish'],required=True)
    parser.add_argument('--research-report',type=Path)
    parser.add_argument('--manifest',type=Path)
    parser.add_argument('--operating-day',required=True)
    parser.add_argument('--scope',action='append')
    parser.add_argument('--confirm')
    args=parser.parse_args(argv)
    if args.mode=='prepare':
        if args.research_report is None:parser.error('--research-report required')
        bundle=N.load_effective(data_root=args.data_root,target_date=args.operating_day)
        result=prepare(args.data_root,args.research_report,bundle,scopes=args.scope)
    else:
        if args.manifest is None:parser.error('--manifest required')
        manifest=I.read(args.manifest)
        if manifest['operating_day']!=args.operating_day:raise ValueError('auxiliary_transition_operating_day_changed')
        result=publish(args.data_root,manifest,confirm=args.confirm)
    print(json.dumps({k:result[k] for k in ('artifact_content_sha256','changes','verified_pairs','effective_from','actual_pid_consumed') if k in result}))


if __name__=='__main__':main()
