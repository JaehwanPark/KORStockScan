"""Explicit same-day ADD publication, separate from sealed postclose artifacts.

Scalping owns the reviewed registration; startup automation attests the code PID.
This path never changes source dates, quotas, original PREOPEN files or orders.
"""
from __future__ import annotations
import argparse
import copy
import json
from datetime import datetime
from pathlib import Path
from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.scalping import mechanistic_entry_runtime_policy as N
from src.engine.scalping import reversal_extended_catalog as C
from src.engine.scalping import reversal_extended_registration as ER

AUTHORITY='APPROVED_INTRADAY_EXTENDED_REGISTRATION_20261008'


def validate_activation(family):
    a=family.get('registration_activation') or {}
    if (a.get('schema')!='main_extended_intraday_registration_v1' or a.get('authority')!=AUTHORITY
            or a.get('artifact_content_sha256')!=P.seal(a)['artifact_content_sha256']
            or a.get('parent_bundle_sha256')!=family['parent_bundle_sha256']
            or a.get('research_batch_sha256')!=C.RESEARCH_BATCH_SHA256
            or a.get('target_date')!=family['effective_date'] or a.get('publication_date')!=family['publication_date']
            or a.get('source_date')!=family['source_date'] or a.get('release_commit')!=family['release_commit']
            or family['publication_date']!=family['effective_date']
            or a.get('comparison_result_required') is not False):
        raise ValueError('extended_intraday_authority_or_date_invalid')
    approved={d['symbol_group']+'|'+d['market']+'|'+d['price_band']+'|'+d['route']:[b] for b,d in C.NEW_DEFINITIONS.items()}
    expected=copy.deepcopy(a.get('parent_scopes',{}))
    if not expected or a.get('approved_additions')!=approved:raise ValueError('extended_intraday_additions_invalid')
    for sid,ids in approved.items():
        if sid not in expected:raise ValueError('extended_intraday_parent_scope_missing')
        expected[sid]=sorted(set(expected[sid])|set(ids))
    if expected!=family['operating_manifest']['scopes']:
        raise ValueError('extended_intraday_membership_changed')
    return a


def stage(data_root,day,*,confirm,release_commit,now=None):
    from src.engine.scalping import continuous_reversal_policy_v6 as V
    from src.engine.scalping import continuous_reversal_operating_postclose as O
    clock=now or datetime.now(P.KST)
    if confirm!=AUTHORITY or clock.astimezone(P.KST).date().isoformat()!=day:
        raise ValueError('extended_intraday_explicit_today_authority_required')
    parent=N.load_effective(data_root=Path(data_root),target_date=day)
    change=ER.pending(data_root,parent,N.next_target(day))
    if change is None:
        if (parent['continuous_reversal'].get('registration_activation') or {}).get('research_batch_sha256')==C.RESEARCH_BATCH_SHA256:
            return parent
        raise ValueError('extended_intraday_registration_missing')
    candidate=N.root(Path(data_root))/'intraday_candidates'/('policy_'+day+'.json')
    if candidate.exists():
        prior=N._read(candidate);pf=prior.get('continuous_reversal',{});proof=pf.get('registration_activation') or {}
        if (pf.get('release_commit')==release_commit and pf.get('parent_bundle_sha256')==parent['bundle_sha256']
                and proof.get('registered_request_sha256')==change['artifact_content_sha256']):
            N.validate(prior,target_date=day);V.validate_sources(prior,data_root);return prior
    f=parent['continuous_reversal'];source_date=f['source_date']
    activation=P.seal(dict(schema='main_extended_intraday_registration_v1',authority=confirm,
        parent_bundle_sha256=parent['bundle_sha256'],parent_scopes=copy.deepcopy(f['operating_manifest']['scopes']),
        approved_additions={s:c['add'] for s,c in change['scopes'].items()},research_batch_sha256=C.RESEARCH_BATCH_SHA256,
        registered_request_sha256=change['artifact_content_sha256'],source_date=source_date,publication_date=day,
        target_date=day,original_planned_target=change['target_date'],release_commit=release_commit,
        requested_at=clock.isoformat(),comparison_result_required=False,actual_order_submitted=False))
    out=Path(data_root)/'report/continuous_reversal_intraday_registration'/day/activation['artifact_content_sha256']
    P.write(out/'authorization.json',activation)
    source=N.root(Path(data_root))/'sources'/('reversal-'+f['machine_report_sha256']+'.json')
    if P.file_hash(source)!=f['report_file_sha256']['machine']:raise ValueError('extended_intraday_parent_report_changed')
    manifest=V.detector_manifest(parent,effective_date=day,changes=change)
    code={Path(m.__file__).name:P.file_hash(m.__file__) for m in V.contract_modules()}
    machine=P.seal(dict(schema=O.SCHEMA,source_date=source_date,publication_date=day,target_date=day,status='completed',
        parent_bundle_sha256=parent['bundle_sha256'],operating_manifest=manifest,execution_code_sha256=P.digest(code),
        source_manifest_sha256=f['source_manifest_sha256'],registration_change=change,policy_schema=V.SCHEMA,
        source_receipts=[dict(path=str(source.resolve()),sha256=P.file_hash(source)),
            dict(path=str((out/'authorization.json').resolve()),sha256=P.file_hash(out/'authorization.json'))],
        population='frozen_registered_research_batch',observation_mode='explicit_registration_no_new_replay',
        cumulative_metrics=None,comparison_state='incomplete',registration_activation=activation,**P.AUTH))
    auxiliary=ER.initial_reports(data_root,source_date,day,parent,machine,publish_policy=False,output_directory=out,effective_date=day)
    issued=N._read(out/'machine.json')
    bundle=V.stage(data_root,source_date,day,issued,auxiliary,target_date=day,release_commit=release_commit,
        effective_mode='intraday',registration_activation=activation)
    P.write(out/'staged.json',P.seal(dict(status='staged',bundle_sha256=bundle['bundle_sha256'],source_date=source_date,
        target_date=day,actual_pid_consumed=False,provider_called=False)))
    return bundle


def activate(data_root,day,*,pid,confirm,now=None):
    from src.engine.automation import intraday_release_handoff as H
    from src.engine.scalping import continuous_reversal_policy_v6 as V
    if confirm!=AUTHORITY or Path(data_root).resolve()!=Path(H.DATA_DIR).resolve():
        raise ValueError('extended_intraday_activation_authority_required')
    clock=H._today(day,now);root,commit=H._selection();identity=H._identity(pid)
    check=H.verify(day,commit,now=clock);_,consumed_path=H._paths(day,commit);consumed=H._read(consumed_path)
    if (identity['cwd']!=str(root/'src') or check['status']!='pass' or consumed.get('status')!='pass'
            or consumed.get('pid_identity')!=identity or consumed.get('actual_pid_consumed') is not True
            or consumed.get('selected_release_commit')!=commit):
        raise ValueError('extended_intraday_code_consumption_missing')
    bootstrap=H._checked_bootstrap(day,pid)
    evidence=dict(schema='intraday_main_policy_code_pid_v1',target_date=day,release_commit=commit,pid_identity=identity,
        consumed_path=str(consumed_path),consumed_sha256=P.file_hash(consumed_path),manifest_sha256=bootstrap['manifest_sha256'],
        verified_at=clock.isoformat(),custody_and_order_paths='existing_native_main_guards_unchanged')
    return V.activate(data_root,day,now=clock,intraday_evidence=evidence)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data-root',type=Path,required=True)
    p.add_argument('--date',required=True);p.add_argument('--mode',choices=['stage','activate'],required=True)
    p.add_argument('--confirm',required=True);p.add_argument('--pid',type=int);a=p.parse_args(argv)
    if a.mode=='stage':
        from src.engine.infrastructure.runtime_release_router import selected_release
        _,commit=selected_release(a.data_root.resolve().parent)
        b=stage(a.data_root,a.date,confirm=a.confirm,release_commit=commit)
        result=dict(status='staged',bundle_sha256=b['bundle_sha256'],target_date=b['target_date'],actual_pid_consumed=False)
    else:result=activate(a.data_root,a.date,pid=a.pid,confirm=a.confirm)
    print(json.dumps(result,ensure_ascii=False));return 0


if __name__=='__main__':raise SystemExit(main())
