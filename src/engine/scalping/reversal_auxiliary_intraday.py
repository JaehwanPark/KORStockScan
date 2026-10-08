"""Auxiliary-only overlays on a validated, immutable Main machine bundle.

No detector reconfiguration, replay, price, quantity or order authority. An old
five-second claim keeps the definition selected at its confirmation time.
"""
from __future__ import annotations

import argparse
import copy
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path
from src.engine.scalping import continuous_reversal as K
from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.scalping import continuous_reversal_policy_v5 as V
from src.engine.scalping import reversal_auxiliary_registry as G

SCHEMA = 'main_auxiliary_intraday_v1'
AUTHORITY = 'APPROVED_INTRADAY_AUXILIARY_TUNING'
_BASE_CONSUMED = set()
_INHERITED = {}


def root(data_root):
    return Path(data_root)/'runtime/mechanistic_entry_policy/auxiliary'


def read(path):
    from src.engine.scalping.mechanistic_entry_runtime_policy import _read
    v=_read(Path(path))
    if v.get('artifact_content_sha256')!=P.seal(v)['artifact_content_sha256']:
        raise ValueError('auxiliary_overlay_hash_invalid')
    return v


def code_hashes():
    from src.engine.scalping.mechanistic_entry_runtime_policy import _source_hash,_signature
    from src.engine.scalping import reversal_auxiliary_wire as W
    from src.engine.scalping import reversal_auxiliary_compatibility as C
    from src.engine.scalping import reversal_auxiliary_transition as X
    return {Path(p).name:_source_hash(str(Path(p)),_signature(Path(p))) for p in (__file__,G.__file__,W.__file__,C.__file__,X.__file__)}


def inherited(data_root, bundle):
    f=bundle['continuous_reversal']
    path=Path(data_root)/'runtime/mechanistic_entry_policy/sources'/('reversal-'+f['auxiliary_report_sha256']+'.json')
    if not path.exists():return {}
    from src.engine.scalping.mechanistic_entry_runtime_policy import _signature
    signature=_signature(path)
    from src.engine.scalping import reversal_auxiliary_compatibility as C
    reader_hashes=code_hashes()
    cached=_INHERITED.get(str(path))
    if cached and cached[0]==signature and cached[2]==reader_hashes:
        dependencies=cached[3]
        if all(_signature(Path(p))==sig for p,sig in dependencies):return copy.deepcopy(cached[1])
    if P.file_hash(path)!=f['report_file_sha256']['auxiliary']:
        raise ValueError('auxiliary_inherited_report_changed')
    report=read(path)
    refs=report.get('auxiliary_registry_bindings',{})
    dependencies=[]
    if refs and report.get('auxiliary_reader_code_hashes')!=reader_hashes:
        receipt=C.validate(data_root,bundle,path,report.get('auxiliary_reader_code_hashes'),reader_hashes)
        for p in [C.path(data_root,bundle,path,reader_hashes),receipt['evidence_path']]+[r['path'] for r in receipt['frozen_readers']]:
            dependencies.append((str(p),_signature(Path(p))))
    valid={V.scope_id(k,r) for k,r in V.scopes()}
    if not isinstance(refs,dict) or not set(refs)<=valid:
        raise ValueError('auxiliary_inheritance_scope_invalid')
    for sid,value in refs.items():
        key,route=sid.rsplit('|',1)
        if G.load(data_root,value)['input_version']!=f['auxiliary_cells'][key]['routes'][route]['payload']['binding']['input_version']:
            raise ValueError('auxiliary_inherited_input_version_mismatch')
    if _signature(path)!=signature:raise ValueError('auxiliary_inherited_report_changed')
    dependencies.extend((str(G.directory(data_root)/(ident+'.json')),_signature(G.directory(data_root)/(ident+'.json'))) for ident in set(refs.values()))
    _INHERITED[str(path)]=(signature,copy.deepcopy(refs),reader_hashes,dependencies)
    return refs


def independent_scopes(data_root,bundle,overlay=None):
    """Remember measured market scopes across postclose generations."""
    f=bundle['continuous_reversal']
    path=Path(data_root)/'runtime/mechanistic_entry_policy/sources'/('reversal-'+f['auxiliary_report_sha256']+'.json')
    inherited(data_root,bundle)  # Verify the immutable report before reading metadata.
    result=set(read(path).get('auxiliary_independent_scopes',[])) if path.exists() else set()
    result.update((overlay or {}).get('independent_scopes',[]))
    return result


def current(data_root, bundle, *, day=None):
    day=day or datetime.now(K.KST).date().isoformat()
    path=root(data_root)/'current.json'
    if not path.exists():
        historical=root(data_root)/'days'/day/(bundle['bundle_sha256']+'.json')
        if not historical.exists():return None
        path=historical
    v=read(path)
    if v.get('day')!=day or v.get('base_bundle_sha256')!=bundle['bundle_sha256']:
        historical=root(data_root)/'days'/day/(bundle['bundle_sha256']+'.json')
        if not historical.exists():return None
        v=read(historical)
    if v.get('schema')!=SCHEMA or v.get('authority')!=AUTHORITY:
        raise ValueError('auxiliary_overlay_authority_invalid')
    if v.get('day')!=day or v.get('base_bundle_sha256')!=bundle['bundle_sha256']:
        return None
    validate_record(data_root,v,bundle,check_definitions=False)
    return v


def validate_record(data_root,v,bundle,*,check_definitions=True):
    f=bundle['continuous_reversal']
    if datetime.fromisoformat(v['effective_from']).tzinfo is None:
        raise ValueError('auxiliary_overlay_clock_invalid')
    if (v.get('schema')!=SCHEMA or v.get('authority')!=AUTHORITY
            or v.get('base_bundle_sha256')!=bundle['bundle_sha256']
            or v.get('base_family_sha256')!=f['family_sha256']
            or v.get('detector_manifest_hash')!=f['operating_manifest']['detector_manifest_hash']
            or not isinstance(v.get('bindings'),dict)
            or datetime.fromisoformat(v['effective_from']).astimezone(K.KST).date().isoformat()!=v['day']):
        raise ValueError('auxiliary_overlay_contract_invalid')
    if v.get('code_hashes')!=code_hashes():
        from src.engine.scalping import reversal_auxiliary_compatibility as C
        C.validate(data_root,bundle,root(data_root)/'generations'/(v['artifact_content_sha256']+'.json'),v.get('code_hashes'),code_hashes())
    valid={V.scope_id(k,r) for k,r in V.scopes()}
    if not set(v['bindings'])<=valid:raise ValueError('auxiliary_overlay_scope_invalid')
    for sid,ident in v['bindings'].items():
        key,route=sid.rsplit('|',1)
        if f['machine_cells'][key]['routes'][route]['backend'] not in {'union_v5','union_v6'}:
            raise ValueError('auxiliary_overlay_native_scope_unsupported')
        if not isinstance(ident,str) or not re.fullmatch('[a-f0-9]{64}',ident):
            raise ValueError('auxiliary_overlay_registry_identity_invalid')
        if check_definitions and G.load(data_root,ident)['input_version']!=f['auxiliary_cells'][key]['routes'][route]['payload']['binding']['input_version']:
            raise ValueError('auxiliary_overlay_input_version_mismatch')
    if v.get('evaluation_sha256'):
        evidence=read(v['evaluation_path'])
        if (evidence['artifact_content_sha256']!=v['evaluation_sha256']
                or evidence['parent_bundle_sha256']!=bundle['bundle_sha256']):
            raise ValueError('auxiliary_overlay_evaluation_changed')
    if v.get('transition_manifest_sha256'):
        from src.engine.scalping import reversal_auxiliary_transition as X
        X.validate_published(data_root,v,bundle)
    return v


def effective_bindings(data_root,bundle,*,day=None):
    f=bundle['continuous_reversal'];result={}
    for key,route in V.scopes():
        if f['machine_cells'][key]['routes'][route]['backend'] not in {'union_v5','union_v6'}:continue
        payload=f['auxiliary_cells'][key]['routes'][route]['payload']
        value=G.definition(payload['arm'],input_version=payload['binding']['input_version'])
        result[V.scope_id(key,route)]=G.register(data_root,value)
    result.update(inherited(data_root,bundle))
    v=current(data_root,bundle,day=day)
    if v:result.update(v['bindings'])
    return result


def at_confirmation(data_root,bundle,epoch):
    day=datetime.fromtimestamp(epoch,K.KST).date().isoformat()
    v=current(data_root,bundle,day=day)
    visited=set()
    while v:
        ident=v['artifact_content_sha256']
        if ident in visited:raise ValueError('auxiliary_overlay_cycle')
        visited.add(ident)
        if datetime.fromisoformat(v['effective_from']).timestamp()<=epoch:return v
        previous=v.get('previous_overlay_sha256')
        if previous is None:return None
        if not re.fullmatch('[a-f0-9]{64}',previous):raise ValueError('auxiliary_overlay_parent_invalid')
        v=read(root(data_root)/'generations'/(previous+'.json'))
        validate_record(data_root,v,bundle,check_definitions=False)
    return None


def selected_definition(data_root,bundle,assessment):
    epoch=assessment['event']['epoch'];sid=V.scope_id(assessment['cell_key'],assessment['route'])
    v=at_confirmation(data_root,bundle,epoch)
    ident=(v or {}).get('bindings',{}).get(sid) or inherited(data_root,bundle).get(sid)
    base_arm=bundle['continuous_reversal']['auxiliary_cells'][assessment['cell_key']]['routes'][assessment['route']]['payload']['arm']
    input_version=bundle['continuous_reversal']['auxiliary_cells'][assessment['cell_key']]['routes'][assessment['route']]['payload']['binding']['input_version']
    if ident==G.definition(base_arm,input_version=input_version)['registry_sha256']:
        return None,v  # Unchanged scopes retain their original runtime path.
    return (G.load(data_root,ident),v) if ident else (None,v)


def apply_request(data_root,bundle,snapshot,result):
    a,inp,prompt,schema=result
    if a.get('policy_version') not in {V.SCHEMA,'continuous_reversal_policy_v6'} or a.get('action')!='ENTER_NOW':return result
    if 'bundle_sha256' not in bundle:
        bundle=dict(bundle,bundle_sha256=bundle['machine_bundle_sha256'])
    value,overlay=selected_definition(data_root,bundle,a)
    if value is None:return result
    inp,prompt,schema=G.production_request(snapshot,value)
    a=copy.deepcopy(a)
    if P.digest(inp['signals'])!=a['signal_set_hash']:
        raise ValueError('auxiliary_overlay_machine_evidence_changed')
    if value['schema']==G.SCHEMA_V2:
        envelope=G.envelope(inp,value)
        a['auxiliary_wire_contract']=envelope['contract']
        a['auxiliary_wire_hashes']=envelope['hashes']
    a.update(auxiliary_arm=value['base_arm'],auxiliary_binding=G.binding(value),
             auxiliary_registry_sha256=value['registry_sha256'],
             auxiliary_overlay_sha256=(overlay or {}).get('artifact_content_sha256'),
             auxiliary_base_bundle_sha256=bundle['bundle_sha256'])
    return a,inp,prompt,schema


def validate_decision(data_root,policy,active,*,now):
    a=policy['continuous_reversal_assessment']
    if a.get('policy_version') not in {V.SCHEMA,'continuous_reversal_policy_v6'} or a.get('action')!='ENTER_NOW':return
    if active is None:raise ValueError('auxiliary_active_bundle_missing')
    value,overlay=selected_definition(data_root,active,a)
    actual=a.get('auxiliary_registry_sha256')
    if value is None:
        if actual:raise ValueError('auxiliary_decision_generation_changed')
        return
    if (actual!=value['registry_sha256'] or a.get('auxiliary_binding')!=G.binding(value)
            or a.get('auxiliary_base_bundle_sha256')!=active['bundle_sha256']
            or a.get('auxiliary_overlay_sha256')!=(overlay or {}).get('artifact_content_sha256')
            or not 0<=now-a['event']['epoch']<=5):
        raise ValueError('auxiliary_decision_generation_changed')
    latest=current(data_root,active,day=datetime.fromtimestamp(now,K.KST).date().isoformat())
    sid=V.scope_id(a['cell_key'],a['route'])
    if latest and (a.get('auxiliary_overlay_sha256') in latest.get('revoked_overlays',[])
            or sid in latest.get('revoked_scope_overlays',{}).get(a.get('auxiliary_overlay_sha256') or 'inherited:'+active['bundle_sha256'],[])):
        raise ValueError('auxiliary_decision_generation_revoked')


def validate_submit(data_root,fields,*,now):
    """Keep the originally selected binding through the final local submit gate."""
    a=fields.get('entry_mechanistic_policy_decision') or {}
    if not a.get('auxiliary_registry_sha256'):return
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    active=N.load_effective(data_root=Path(data_root),target_date=datetime.fromtimestamp(now,K.KST).date().isoformat())
    validate_decision(data_root,dict(continuous_reversal_assessment=a),active,now=now)


@contextmanager
def publisher_locks(data_root):
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    folder=root(data_root);folder.mkdir(parents=True,exist_ok=True)
    with (folder/'publisher.lock').open('a') as auxiliary_lock:
        fcntl.flock(auxiliary_lock,fcntl.LOCK_EX)
        with (N.root(Path(data_root))/'publisher.lock').open('a') as machine_lock:
            fcntl.flock(machine_lock,fcntl.LOCK_EX)
            yield


def publish(data_root,evaluation,*,expected_parent,confirm,now=None):
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    from src.engine.scalping import reversal_auxiliary_tuning as T
    if confirm!=AUTHORITY:raise ValueError('auxiliary_intraday_authority_required')
    clock=now or datetime.now(K.KST);day=clock.astimezone(K.KST).date().isoformat()
    if clock.tzinfo is None:raise ValueError('auxiliary_intraday_clock_invalid')
    report=T.read(evaluation)
    # Recompute from the immutable campaign and actual durable responses.
    if report.get('research',{}).get('purpose') == 'development':
        raise ValueError('auxiliary_development_evaluation_not_publishable')
    if report.get('campaign_path'):
        checked=T.evaluate(data_root,report['source_date'],campaign_path=report['campaign_path'])
        _, evaluation_dir, _ = T.load_campaign(data_root,report['source_date'],report['campaign_path'])
    else:
        checked=T.evaluate(data_root,report['source_date'])
        evaluation_dir=T.directory(data_root,report['source_date'])
    if report['artifact_content_sha256']!=checked['artifact_content_sha256']:
        raise ValueError('auxiliary_evaluation_changed')
    if report.get('research'):
        from src.engine.scalping import reversal_auxiliary_research as R
        cfg=R.context(data_root,report['research']['experiment'])['config']
        if not cfg.get('native_current_contract') or cfg.get('native_output_tokens_override') is not None or cfg.get('compact_wire_contract'):
            raise ValueError('auxiliary_research_native_comparison_required')
    folder=root(data_root);folder.mkdir(parents=True,exist_ok=True)
    with publisher_locks(data_root):
        active=N.load_effective(data_root=Path(data_root),target_date=day)
        if not active or active['bundle_sha256']!=report['parent_bundle_sha256']:
            raise ValueError('auxiliary_base_parent_changed')
        before=current(data_root,active,day=day)
        actual=(before or {}).get('artifact_content_sha256')
        if before and before.get('evaluation_sha256')==report['artifact_content_sha256']:
            return before
        if actual!=expected_parent:raise ValueError('auxiliary_parent_cas_failed')
        bindings=effective_bindings(data_root,active,day=day);changes={}
        for sid,metrics in report['scopes'].items():
            if bindings.get(sid)!=metrics['current_registry']:
                raise ValueError('auxiliary_comparison_incumbent_changed')
            if metrics['improved'] and T.improves(metrics['current'],metrics['candidate']):
                changes[sid]=metrics['candidate_registry']
        if not changes:return dict(status='incumbent_kept',reason='no_paired_improvement',actual_pid_consumed=False)
        measured=independent_scopes(data_root,active,before)
        measured.update(s for s,v in report['scopes'].items() if v['paired_points']>0)
        # Only genuinely unobserved PRE/AFTER inherit their REGULAR result.
        for sid in list(bindings):
            regular=sid.replace('|PRE|','|REGULAR|').replace('|AFTER|','|REGULAR|')
            if sid!=regular and regular in changes and sid not in measured:
                family=active['continuous_reversal'];key,route=sid.rsplit('|',1)
                if family['auxiliary_cells'][key]['routes'][route].get('inherited_from'):
                    changes[sid]=changes[regular]
        bindings.update(changes)
        clock=now or datetime.now(K.KST)
        if clock.astimezone(K.KST).date().isoformat()!=day:
            raise ValueError('auxiliary_publication_day_changed')
        body=P.seal(dict(schema=SCHEMA,authority=confirm,day=day,effective_from=clock.isoformat(),
            base_bundle_sha256=active['bundle_sha256'],base_family_sha256=active['continuous_reversal']['family_sha256'],
            detector_manifest_hash=report['detector_manifest_hash'],previous_overlay_sha256=actual,
            evaluation_sha256=report['artifact_content_sha256'],
            evaluation_path=str((evaluation_dir/'evaluations'/(report['artifact_content_sha256']+'.json')).resolve()),
            bindings=bindings,changes=changes,independent_scopes=sorted(measured),code_hashes=code_hashes(),
            revoked_overlays=(before or {}).get('revoked_overlays',[]),
            revoked_scope_overlays=(before or {}).get('revoked_scope_overlays',{}),rollback_bindings=rollback_bindings(data_root,active,before),
            actual_pid_consumed=False,actual_order_submitted=False))
        validate_record(data_root,body,active)
        N._atomic_write_json(folder/'generations'/(body['artifact_content_sha256']+'.json'),body)
        write_day_pointer(data_root,body)
        N._atomic_write_json(folder/'current.json',body)
        if current(data_root,active,day=day)!=body:raise ValueError('auxiliary_overlay_readback_failed')
        return body


def record_pid_consumption(data_root,bundle):
    from src.engine.scalping import continuous_reversal_policy_v5 as V
    if bundle['continuous_reversal']['schema']=='continuous_reversal_policy_v6':
        from src.engine.scalping import continuous_reversal_policy_v6 as V
    """Unchanged v5 code pins permit a reviewed code-only release handoff."""
    from src.engine.automation import intraday_release_handoff as H
    from src.engine.infrastructure.runtime_release_router import selected_release
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    selected,commit=selected_release(Path(data_root).resolve().parent)
    identity=H._identity(os.getpid());day=datetime.now(K.KST).date().isoformat()
    if identity['cwd']!=str(selected/'src'):raise ValueError('auxiliary_pid_release_mismatch')
    active=N.load_effective(data_root=Path(data_root),target_date=day)
    if not active or active['bundle_sha256']!=bundle['bundle_sha256']:
        raise ValueError('auxiliary_pid_generation_changed')
    if commit==bundle['continuous_reversal']['release_commit']:
        V.record_pid_consumption(data_root,bundle)
    else:
        # Handoff attests current PID plus the original, unchanged bootstrap.
        cache_key=(str(data_root),day,os.getpid(),identity['start_ticks'],commit,bundle['bundle_sha256'])
        if cache_key not in _BASE_CONSUMED:
            path,consumed_path=H._paths(day,commit)
            handoff=H.verify(day,commit); consumed=H._read(consumed_path)
            if (handoff.get('status')!='pass' or consumed.get('actual_pid_consumed') is not True
                    or consumed.get('pid_identity')!=identity or consumed.get('handoff_sha256')!=H._sha(path)):
                raise ValueError('auxiliary_base_code_handoff_missing')
            N._validate_bundle_sources(bundle,Path(data_root))  # Use the trusted data anchor.
            _BASE_CONSUMED.add(cache_key)
        f=bundle['continuous_reversal'];count=sum(f['machine_cells'][k]['routes'][r]['backend'] in {'union_v5','union_v6'} for k,r in V.scopes())
        receipt=dict(schema='continuous_reversal_pid_consumption_v6' if f['schema']=='continuous_reversal_policy_v6' else 'continuous_reversal_pid_consumption_v5',bundle_sha256=bundle['bundle_sha256'],
            family_sha256=f['family_sha256'],execution_manifest_hash=f['execution_manifest_hash'],
            release_commit=commit,policy_origin_release_commit=f['release_commit'],pid_identity=identity,
            observed_at=datetime.now(K.KST).isoformat(),planned_scopes=len(V.scopes()),new_consumed_scopes=count,
            legacy_carried_scopes=len(V.scopes())-count,actual_pid_consumed=True,actual_order_submitted=False)
        receipt['receipt_sha256']=P.digest(receipt)
        dest=N.root(Path(data_root))/'consumed'/day/(str(os.getpid())+'.json')
        if not dest.exists() or N._read(dest).get('release_commit')!=commit or N._read(dest).get('bundle_sha256')!=bundle['bundle_sha256']:
            N._atomic_write_json(dest,receipt)
    v=current(data_root,bundle,day=day)
    refs=(v or {}).get('bindings') or inherited(data_root,bundle)
    for ident in set(refs.values()):G.load(data_root,ident)
    receipt=P.seal(dict(schema=SCHEMA,day=day,base_bundle_sha256=bundle['bundle_sha256'],
        overlay_sha256=(v or {}).get('artifact_content_sha256'),bindings=refs,code_hashes=code_hashes(),
        release_commit=commit,pid_identity=identity,actual_pid_consumed=True,actual_order_submitted=False))
    dest=root(data_root)/'consumed'/day/(str(os.getpid())+'.json')
    if not dest.exists() or read(dest)!=receipt:N._atomic_write_json(dest,receipt)


def rollback(data_root,*,expected_parent,reason,confirm,now=None,scopes=None):
    """Revoke a defective overlay and restore its verified predecessor."""
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    if confirm!=AUTHORITY or not reason or (scopes is None and not expected_parent):
        raise ValueError('auxiliary_rollback_authority_required')
    if scopes is not None:
        from src.engine.scalping.reversal_auxiliary_transition import rollback_scopes
        return rollback_scopes(data_root,expected_parent=expected_parent,reason=reason,confirm=confirm,now=now,scopes=scopes)
    clock=now or datetime.now(K.KST);day=clock.astimezone(K.KST).date().isoformat()
    folder=root(data_root)
    with publisher_locks(data_root):
        bundle=N.load_effective(data_root=Path(data_root),target_date=day)
        before=read(folder/'current.json')
        if (before['artifact_content_sha256']!=expected_parent or before['day']!=day
                or before['base_bundle_sha256']!=bundle['bundle_sha256']):
            raise ValueError('auxiliary_rollback_parent_changed')
        previous=before.get('previous_overlay_sha256')
        if previous:
            older=read(folder/'generations'/(previous+'.json'));validate_record(data_root,older,bundle)
            bindings=older['bindings']
        else:
            bindings={}
            for key,route in V.scopes():
                cell=bundle['continuous_reversal']['auxiliary_cells'][key]['routes'][route]
                if bundle['continuous_reversal']['machine_cells'][key]['routes'][route]['backend'] in {'union_v5','union_v6'}:
                    value=G.definition(cell['payload']['arm'],input_version=cell['payload']['binding']['input_version']);bindings[V.scope_id(key,route)]=G.register(data_root,value)
            bindings.update(inherited(data_root,bundle))
        record=P.seal(dict(before,effective_from=clock.isoformat(),bindings=bindings,changes=bindings,
            previous_overlay_sha256=expected_parent,rollback_reason=reason,evaluation_sha256=None,
            code_hashes=code_hashes(),revoked_overlays=sorted(set(before.get('revoked_overlays',[])+[expected_parent])),
            actual_pid_consumed=False))
        validate_record(data_root,record,bundle)
        N._atomic_write_json(folder/'generations'/(record['artifact_content_sha256']+'.json'),record)
        write_day_pointer(data_root,record)
        N._atomic_write_json(folder/'current.json',record)
        return record


def audit_observation(bundle,observation):
    from src.engine.scalping import continuous_reversal_policy_v5 as V
    if bundle['continuous_reversal']['schema']=='continuous_reversal_policy_v6':
        from src.engine.scalping import continuous_reversal_policy_v6 as V
    """Verify original overlay bytes, then delegate unchanged machine checks."""
    a=observation['source']['assessment']
    if not a.get('auxiliary_registry_sha256'):return V.audit_observation(bundle,observation)
    from src.utils.constants import DATA_DIR
    from src.engine.scalping.ai_decision_trace import _json_bytes
    source=observation['source'];request=source['auxiliary_request'];native=observation['runtime_consumption']['continuous_reversal']
    if any(P.digest(request.get(k))!=native.get(v) for k,v in
           [('input','input_sha256'),('prompt','prompt_sha256'),('response_schema','response_schema_sha256')]):
        raise ValueError('auxiliary_observation_request_changed')
    if hashlib.sha256(_json_bytes(a)).hexdigest()!=native.get('assessment_sha256'):
        raise ValueError('auxiliary_observation_assessment_changed')
    value=G.load(DATA_DIR,a['auxiliary_registry_sha256'])
    if request['prompt']!=value['prompt'] or a['auxiliary_binding']!=G.binding(value):
        raise ValueError('auxiliary_observation_registry_changed')
    if value['schema']==G.SCHEMA_V2:
        env=G.envelope(request['input'],value)
        if a.get('auxiliary_wire_contract')!=env['contract'] or a.get('auxiliary_wire_hashes')!=env['hashes']:
            raise ValueError('auxiliary_observation_wire_changed')
    # The sealed historical record owns provenance even after a later cutover.
    if a.get('auxiliary_overlay_sha256'):
        rec=read(root(DATA_DIR)/'generations'/(a['auxiliary_overlay_sha256']+'.json'))
        validate_record(DATA_DIR,rec,bundle)
        if rec['bindings'].get(V.scope_id(a['cell_key'],a['route']))!=value['registry_sha256']:
            raise ValueError('auxiliary_observation_scope_changed')
        if datetime.fromisoformat(rec['effective_from']).timestamp()>a['event']['epoch']:
            raise ValueError('auxiliary_observation_before_effective_time')
    elif inherited(DATA_DIR,bundle).get(V.scope_id(a['cell_key'],a['route']))!=value['registry_sha256']:
        raise ValueError('auxiliary_observation_inheritance_changed')
    # Only a temporary compatibility view is adapted. Stored evidence is never
    # rewritten and original hashes were checked above.
    adapted=copy.deepcopy(observation)
    arm=bundle['continuous_reversal']['auxiliary_cells'][a['cell_key']]['routes'][a['route']]['payload']['arm']
    adapted['source']['auxiliary_request']['prompt']=G.projector(value['input_version']).PROMPT+G.projector(value['input_version']).ARM_SUFFIXES[arm]
    adapted['runtime_consumption']['continuous_reversal']['arm']=arm
    adapted['runtime_consumption']['continuous_reversal']['prompt_sha256']=P.digest(adapted['source']['auxiliary_request']['prompt'])
    return V.audit_observation(bundle,adapted)


def record_decoded_response(data_root,assessment,request_identity,raw,decoded,value):
    """A separate immutable projection; never change the native raw outbox hash."""
    from src.engine.scalping.mechanistic_entry_runtime_policy import _atomic_write_json
    import base64
    path=Path(data_root)/'runtime/initial_quantity/operating_opportunities'/(assessment['opportunity_key']+'.json')
    native=json.loads(path.read_text())
    if native.get('sha256')!=P.digest({k:v for k,v in native.items() if k!='sha256'}):
        raise ValueError('auxiliary_native_response_receipt_changed')
    event=next((h['binding'] for h in native['history'] if h['state']=='response_received'),None)
    if not event or event['request_sha256']!=request_identity or event['response']!=raw:
        raise ValueError('auxiliary_native_response_binding_changed')
    receipt=event.get('provider_receipt') or {};output=base64.b64decode(receipt['auxiliary_raw_output_bytes_b64'],validate=True)
    if (receipt.get('auxiliary_response_status')!='completed' or not receipt.get('openai_response_id') or hashlib.sha256(output).hexdigest()!=receipt.get('openai_response_sha256')
            or json.loads(output)!=raw or receipt.get('auxiliary_provider_request',{}).get('registry_sha256')!=value['registry_sha256']):
        raise ValueError('auxiliary_provider_response_binding_changed')
    body=P.seal(dict(schema='auxiliary_decoded_response_receipt_v1',opportunity_key=assessment['opportunity_key'],
        native_response_binding_sha256=P.digest(event),request_sha256=request_identity,registry_sha256=value['registry_sha256'],
        wire_contract=value['wire_contract'],raw_parsed_sha256=P.digest(raw),raw_output_sha256=receipt['openai_response_sha256'],
        provider_response_id=receipt['openai_response_id'],decoded_response=decoded,decoded_response_sha256=P.digest(decoded)))
    dest=root(data_root)/'responses'/(request_identity+'.json')
    if dest.exists() and read(dest)!=body:raise ValueError('auxiliary_decoded_response_conflict')
    _atomic_write_json(dest,body)
    return body


def write_day_pointer(data_root,record):
    from src.engine.scalping.mechanistic_entry_runtime_policy import _atomic_write_json
    _atomic_write_json(root(data_root)/'days'/record['day']/(record['base_bundle_sha256']+'.json'),record)


def rollback_bindings(data_root,bundle,overlay=None):
    f=bundle['continuous_reversal']
    p=Path(data_root)/'runtime/mechanistic_entry_policy/sources'/('reversal-'+f['auxiliary_report_sha256']+'.json')
    inherited(data_root,bundle)
    values=dict(read(p).get('auxiliary_rollback_bindings',{})) if p.exists() else {}
    values.update((overlay or {}).get('rollback_bindings',{}))
    return values


def lineage_sources(data_root,bundle,overlay=None):
    from src.engine.scalping import reversal_auxiliary_compatibility as C
    from src.engine.scalping import reversal_auxiliary_transition as X
    refs={}
    def add(p):
        p=Path(p);refs[str(p.resolve())]=dict(path=str(p.resolve()),sha256=P.file_hash(p))
    f=bundle['continuous_reversal']
    p=Path(data_root)/'runtime/mechanistic_entry_policy/sources'/('reversal-'+f['auxiliary_report_sha256']+'.json')
    if p.exists():
        report=read(p)
        for item in report.get('source_receipts',[]):
            X.verify_reference(item);refs[item['path']]=item
        if report.get('auxiliary_registry_bindings') and report.get('auxiliary_reader_code_hashes')!=code_hashes():
            receipt=C.validate(data_root,bundle,p,report.get('auxiliary_reader_code_hashes'),code_hashes())
            for r in [C.path(data_root,bundle,p,code_hashes()),receipt['evidence_path']]+[v['path'] for v in receipt['frozen_readers']]:add(r)
    rec=overlay;visited=set()
    while rec:
        ident=rec['artifact_content_sha256']
        if ident in visited:raise ValueError('auxiliary_overlay_cycle')
        visited.add(ident);add(root(data_root)/'generations'/(ident+'.json'))
        if rec.get('transition_manifest_sha256'):
            p=X.folder(data_root)/(rec['transition_manifest_sha256']+'.json');add(p)
            for item in read(p)['sources']:
                X.verify_reference(item);refs[item['path']]=item
        previous=rec.get('previous_overlay_sha256')
        rec=read(root(data_root)/'generations'/(previous+'.json')) if previous else None
    for ident in set(rollback_bindings(data_root,bundle,overlay).values()):add(G.directory(data_root)/(ident+'.json'))
    return list(refs.values())


def validate_inheritance_cutoff(data_root,bundle):
    f=bundle.get('continuous_reversal',{})
    if not f.get('auxiliary_report_sha256'):return
    p=Path(data_root)/'runtime/mechanistic_entry_policy/sources'/('reversal-'+f['auxiliary_report_sha256']+'.json')
    report=read(p)
    if not report.get('evaluated_base_bundle'):return
    day=report['operating_day'];base=report['evaluated_base_bundle']
    p=root(data_root)/'days'/day/(base+'.json')
    current_path=root(data_root)/'current.json'
    if not current_path.exists():
        from src.engine.scalping.mechanistic_entry_runtime_policy import _signature
        parent=current_path.parent
        while not parent.exists():parent=parent.parent
        _signature(parent)  # Creating a previously absent pointer invalidates the dependency cache.
    latest=read(current_path) if current_path.exists() else {}
    if latest.get('base_bundle_sha256')!=base or latest.get('day')!=day:
        latest=read(p) if p.exists() else {}
    if latest.get('artifact_content_sha256')!=report.get('evaluated_overlay_parent'):
        raise ValueError('auxiliary_prepared_overlay_generation_changed')


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root',type=Path,required=True)
    parser.add_argument('--mode',choices=['publish','rollback'],default='publish')
    parser.add_argument('--evaluation',type=Path)
    parser.add_argument('--expected-parent')
    parser.add_argument('--reason')
    parser.add_argument('--scope',action='append',help='Restore only named scopes, including inherited v2 bindings')
    parser.add_argument('--confirm',required=True)
    args=parser.parse_args(argv)
    if args.mode=='publish':
        if args.evaluation is None:parser.error('--evaluation required for publish')
        result=publish(args.data_root,args.evaluation,expected_parent=args.expected_parent,confirm=args.confirm)
    else:result=rollback(args.data_root,expected_parent=args.expected_parent,reason=args.reason,confirm=args.confirm,scopes=args.scope)
    print(json.dumps(result))


if __name__=='__main__':main()
