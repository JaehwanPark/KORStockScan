"""Auxiliary-only overlays on a validated, immutable Main machine bundle.

No detector reconfiguration, replay, price, quantity or order authority. An old
five-second claim keeps the definition selected at its confirmation time.
"""
from __future__ import annotations

import argparse
import copy
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
    return {Path(p).name:_source_hash(str(Path(p)),_signature(Path(p))) for p in (__file__,G.__file__)}


def inherited(data_root, bundle):
    f=bundle['continuous_reversal']
    path=Path(data_root)/'runtime/mechanistic_entry_policy/sources'/('reversal-'+f['auxiliary_report_sha256']+'.json')
    if not path.exists():return {}
    from src.engine.scalping.mechanistic_entry_runtime_policy import _signature
    signature=_signature(path)
    cached=_INHERITED.get(str(path))
    if cached and cached[0]==signature:return copy.deepcopy(cached[1])
    if P.file_hash(path)!=f['report_file_sha256']['auxiliary']:
        raise ValueError('auxiliary_inherited_report_changed')
    report=read(path)
    refs=report.get('auxiliary_registry_bindings',{})
    if refs and report.get('auxiliary_reader_code_hashes')!=code_hashes():
        raise ValueError('auxiliary_inherited_reader_changed')
    valid={V.scope_id(k,r) for k,r in V.scopes()}
    if not isinstance(refs,dict) or not set(refs)<=valid:
        raise ValueError('auxiliary_inheritance_scope_invalid')
    for value in refs.values():G.load(data_root,value)
    if _signature(path)!=signature:raise ValueError('auxiliary_inherited_report_changed')
    _INHERITED[str(path)]=(signature,copy.deepcopy(refs))
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
    if not path.exists():return None
    v=read(path)
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
            or v.get('code_hashes')!=code_hashes()
            or not isinstance(v.get('bindings'),dict)
            or datetime.fromisoformat(v['effective_from']).astimezone(K.KST).date().isoformat()!=v['day']):
        raise ValueError('auxiliary_overlay_contract_invalid')
    valid={V.scope_id(k,r) for k,r in V.scopes()}
    if not set(v['bindings'])<=valid:raise ValueError('auxiliary_overlay_scope_invalid')
    for sid,ident in v['bindings'].items():
        key,route=sid.rsplit('|',1)
        if f['machine_cells'][key]['routes'][route]['backend']!='union_v5':
            raise ValueError('auxiliary_overlay_native_scope_unsupported')
        if not isinstance(ident,str) or not re.fullmatch('[a-f0-9]{64}',ident):
            raise ValueError('auxiliary_overlay_registry_identity_invalid')
        if check_definitions:G.load(data_root,ident)
    if v.get('evaluation_sha256'):
        evidence=read(v['evaluation_path'])
        if (evidence['artifact_content_sha256']!=v['evaluation_sha256']
                or evidence['parent_bundle_sha256']!=bundle['bundle_sha256']):
            raise ValueError('auxiliary_overlay_evaluation_changed')
    return v


def effective_bindings(data_root,bundle,*,day=None):
    f=bundle['continuous_reversal'];result={}
    for key,route in V.scopes():
        if f['machine_cells'][key]['routes'][route]['backend']!='union_v5':continue
        value=G.definition(f['auxiliary_cells'][key]['routes'][route]['payload']['arm'])
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
    if ident==G.definition(base_arm)['registry_sha256']:
        return None,v  # Unchanged scopes retain their original runtime path.
    return (G.load(data_root,ident),v) if ident else (None,v)


def apply_request(data_root,bundle,snapshot,result):
    a,inp,prompt,schema=result
    if a.get('policy_version')!=V.SCHEMA or a.get('action')!='ENTER_NOW':return result
    if 'bundle_sha256' not in bundle:
        bundle=dict(bundle,bundle_sha256=bundle['machine_bundle_sha256'])
    value,overlay=selected_definition(data_root,bundle,a)
    if value is None:return result
    inp,prompt,schema=G.production_request(snapshot,value)
    a=copy.deepcopy(a)
    if P.digest(inp['signals'])!=a['signal_set_hash']:
        raise ValueError('auxiliary_overlay_machine_evidence_changed')
    a.update(auxiliary_arm=value['base_arm'],auxiliary_binding=G.binding(value),
             auxiliary_registry_sha256=value['registry_sha256'],
             auxiliary_overlay_sha256=(overlay or {}).get('artifact_content_sha256'),
             auxiliary_base_bundle_sha256=bundle['bundle_sha256'])
    return a,inp,prompt,schema


def validate_decision(data_root,policy,active,*,now):
    a=policy['continuous_reversal_assessment']
    if a.get('policy_version')!=V.SCHEMA or a.get('action')!='ENTER_NOW':return
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
    if latest and a.get('auxiliary_overlay_sha256') in latest.get('revoked_overlays',[]):
        raise ValueError('auxiliary_decision_generation_revoked')


def validate_submit(data_root,fields,*,now):
    """Keep the originally selected binding through the final local submit gate."""
    a=fields.get('entry_mechanistic_policy_decision') or {}
    if not a.get('auxiliary_registry_sha256'):return
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    active=N.load_effective(data_root=Path(data_root),target_date=datetime.fromtimestamp(now,K.KST).date().isoformat())
    validate_decision(data_root,dict(continuous_reversal_assessment=a),active,now=now)


def publish(data_root,evaluation,*,expected_parent,confirm,now=None):
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    from src.engine.scalping import reversal_auxiliary_tuning as T
    if confirm!=AUTHORITY:raise ValueError('auxiliary_intraday_authority_required')
    clock=now or datetime.now(K.KST);day=clock.astimezone(K.KST).date().isoformat()
    if clock.tzinfo is None:raise ValueError('auxiliary_intraday_clock_invalid')
    report=T.read(evaluation)
    # Recompute from the immutable campaign and actual durable responses.
    checked=T.evaluate(data_root,report['source_date'])
    if report['artifact_content_sha256']!=checked['artifact_content_sha256']:
        raise ValueError('auxiliary_evaluation_changed')
    folder=root(data_root);folder.mkdir(parents=True,exist_ok=True)
    with (folder/'publisher.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
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
            evaluation_path=str((T.directory(data_root,report['source_date'])/'evaluations'/(report['artifact_content_sha256']+'.json')).resolve()),
            bindings=bindings,changes=changes,independent_scopes=sorted(measured),code_hashes=code_hashes(),
            revoked_overlays=(before or {}).get('revoked_overlays',[]),
            actual_pid_consumed=False,actual_order_submitted=False))
        validate_record(data_root,body,active)
        N._atomic_write_json(folder/'generations'/(body['artifact_content_sha256']+'.json'),body)
        N._atomic_write_json(folder/'current.json',body)
        if current(data_root,active,day=day)!=body:raise ValueError('auxiliary_overlay_readback_failed')
        return body


def record_pid_consumption(data_root,bundle):
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
        f=bundle['continuous_reversal'];count=sum(f['machine_cells'][k]['routes'][r]['backend']=='union_v5' for k,r in V.scopes())
        receipt=dict(schema='continuous_reversal_pid_consumption_v5',bundle_sha256=bundle['bundle_sha256'],
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


def rollback(data_root,*,expected_parent,reason,confirm,now=None):
    """Revoke a defective overlay and restore its verified predecessor."""
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    if confirm!=AUTHORITY or not reason or not expected_parent:
        raise ValueError('auxiliary_rollback_authority_required')
    clock=now or datetime.now(K.KST);day=clock.astimezone(K.KST).date().isoformat()
    folder=root(data_root)
    with (folder/'publisher.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
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
                if bundle['continuous_reversal']['machine_cells'][key]['routes'][route]['backend']=='union_v5':
                    value=G.definition(cell['payload']['arm']);bindings[V.scope_id(key,route)]=G.register(data_root,value)
            bindings.update(inherited(data_root,bundle))
        record=P.seal(dict(before,effective_from=clock.isoformat(),bindings=bindings,changes=bindings,
            previous_overlay_sha256=expected_parent,rollback_reason=reason,evaluation_sha256=None,
            code_hashes=code_hashes(),revoked_overlays=sorted(set(before.get('revoked_overlays',[])+[expected_parent])),
            actual_pid_consumed=False))
        validate_record(data_root,record,bundle)
        N._atomic_write_json(folder/'generations'/(record['artifact_content_sha256']+'.json'),record)
        N._atomic_write_json(folder/'current.json',record)
        return record


def audit_observation(bundle,observation):
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
    adapted['source']['auxiliary_request']['prompt']=G.A.PROMPT+G.A.ARM_SUFFIXES[arm]
    adapted['runtime_consumption']['continuous_reversal']['arm']=arm
    adapted['runtime_consumption']['continuous_reversal']['prompt_sha256']=P.digest(adapted['source']['auxiliary_request']['prompt'])
    return V.audit_observation(bundle,adapted)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root',type=Path,required=True)
    parser.add_argument('--mode',choices=['publish','rollback'],default='publish')
    parser.add_argument('--evaluation',type=Path)
    parser.add_argument('--expected-parent')
    parser.add_argument('--reason')
    parser.add_argument('--confirm',required=True)
    args=parser.parse_args(argv)
    if args.mode=='publish':
        if args.evaluation is None:parser.error('--evaluation required for publish')
        result=publish(args.data_root,args.evaluation,expected_parent=args.expected_parent,confirm=args.confirm)
    else:result=rollback(args.data_root,expected_parent=args.expected_parent,reason=args.reason,confirm=args.confirm)
    print(json.dumps(result))


if __name__=='__main__':main()
