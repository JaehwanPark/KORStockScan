"""Read-only policy stage projection plus bounded native decision receipts.

No projection creates execution authority or rewrites a sealed handoff.
"""
from __future__ import annotations
import json
import os
from datetime import datetime
from pathlib import Path
from src.engine.scalping import continuous_reversal as K
from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.scalping import mechanistic_entry_runtime_policy as N


def operating_scope(sid):
    _,market,_,route=sid.split('|')
    return route==('NXT' if market=='PRE' else 'SOR')


def report_state(report):
    cells=[r for c in report.get('cells',[]) for r in c.get('routes',{}).values()]
    initial=bool(report.get('initial_registration')) or any(c.get('status')=='operator_initial_registered' or c.get('initial_binding') for c in cells)
    basis=report.get('adoption_basis') or ('operator_designated' if initial else 'carried' if cells and all('carried' in c.get('status','') for c in cells) else 'comparison_selected' if report.get('comparison_complete') is True else 'not_applicable')
    comparison=report.get('comparison_state')
    if not comparison:
        values=set((report.get('comparison_statuses') or {}).values())
        if report.get('comparison_complete') is False or report.get('scope_pending') or 'incomplete' in values:comparison='incomplete'
        elif 'source_gap' in values or 'input_invalid' in values:comparison='source_gap'
        elif values=={'valid_empty'}:comparison='valid_empty'
        elif values=={'completed_unresolved'}:comparison='completed_unresolved'
        elif values=={'completed_no_pass'}:comparison='completed_no_pass'
        else:comparison='complete' if report.get('status') in {'completed','completed_with_scope_carry'} else 'incomplete'
    return dict(registration_state=report.get('registration_state') or ('registered' if cells else 'not_registered'),
        adoption_basis=basis,comparison_state=comparison,
        publication_state='published' if cells and report.get('status') in {'completed','completed_with_scope_carry'} else 'not_published',
        source_date=report.get('source_date'),target_date=report.get('effective_date') or report.get('target_date'),
        generation=report.get('artifact_content_sha256'),observed_at=report.get('generated_at'),snapshot_semantics='producer_as_of')


def record_decision(family,result):
    """Called only by the real bot after native family/signal validation."""
    from src.utils.constants import DATA_DIR
    from src.engine.automation.intraday_release_handoff import _identity
    a=result[0];event=a.get('event')
    if not event:return
    identity=_identity(os.getpid())
    from src.engine.infrastructure.runtime_release_router import selected_release
    selected,commit=selected_release(Path(DATA_DIR).resolve().parent)
    if identity['cwd']!=str(selected/'src'):raise ValueError('policy_status_pid_release_mismatch')
    current=N._read(N.root(Path(DATA_DIR))/'current.json')
    if current.get('family_sha256')!=family['family_sha256']:raise ValueError('policy_status_family_changed')
    sid=a['cell_key']+'|'+a['route'];day=datetime.now(K.KST).date().isoformat()
    receipt=P.seal(dict(schema='main_policy_decision_status_v1',source_date=family['source_date'],target_date=day,
        bundle_sha256=current['bundle_sha256'],family_sha256=family['family_sha256'],scope=sid,
        policy_validation_state='valid',validation_stage='intraday_decision',action=a['action'],reason=a['reason'],
        source_item=event['source_item'],native_epoch=event['native_epoch'],native_sequence=event['native_sequence'],
        observed_at=K.iso(event['epoch']),pid_identity=identity,release_commit=commit))
    N._atomic_write_json(N.root(Path(DATA_DIR))/'decisions'/day/str(os.getpid())/(P.digest(sid)+'.json'),receipt)


def current_view(data_root,*,day=None):
    """Join only same-generation receipts; a concurrent switch is unobservable."""
    from src.engine.automation.intraday_release_handoff import _identity
    data_root=Path(data_root).absolute();day=day or datetime.now(K.KST).date().isoformat()
    selector=data_root/'runtime/runtime_release_selection.json';pointer=N.root(data_root)/'current.json'
    before=(selector.read_bytes(),pointer.read_bytes());s=json.loads(before[0]);c=json.loads(before[1])
    b=N._read(N.root(data_root)/'generations'/(c['bundle_sha256']+'.json'));f=b['continuous_reversal']
    scopes={k+'|'+r:v for k,cell in f['machine_cells'].items() for r,v in cell['routes'].items()}
    result=dict(schema='main_current_policy_status_v1',source_date=f['source_date'],target_date=day,
        bundle_sha256=b['bundle_sha256'],manifest_sha256=f.get('operating_manifest',{}).get('detector_manifest_hash'),
        producer=str(pointer),observed_at=datetime.now(K.KST).isoformat(),registration_state='registered',
        activation_state='active',prepared_state='not_observed',pid_consumption_state='not_started',
        policy_validation_state='not_observed',validation_stage='launch_loader',
        startup_hold_state='held' if (data_root/'runtime/operator_startup_hold.json').exists() else 'not_held',
        contract_scope_count=len(scopes),operating_scope_count=sum(operating_scope(sid) for sid in scopes),
        loaded_scope_count=None,observed_decision_scope_count=None,route_decisions={},actual_order_submitted=False)
    try:
        active=N.load_effective(data_root=data_root,target_date=day)
        if active['bundle_sha256']!=b['bundle_sha256']:raise ValueError('policy_generation_changed')
        result['policy_validation_state']='valid'
    except (OSError,ValueError,KeyError,TypeError) as exc:
        result.update(policy_validation_state='invalid',validation_error=str(exc))
    pid=(s.get('actual_pid_receipt') or {}).get('pid');identity=None
    if pid:
        try:identity=_identity(pid)
        except (OSError,ValueError):pass
    if identity:
        result['pid_consumption_state']='not_observed'
        receipt_path=N.root(data_root)/'consumed'/day/(str(pid)+'.json')
        if receipt_path.exists():
            receipt=N._read(receipt_path)
            exact=(receipt.get('pid_identity')==identity and receipt.get('bundle_sha256')==b['bundle_sha256']
                and receipt.get('release_commit')==s['git_commit'] and identity['cwd']==str(Path(s['release_root'])/'src')
                and receipt.get('receipt_sha256')==P.digest({k:v for k,v in receipt.items() if k!='receipt_sha256'}))
            result['pid_consumption_state']='consumed_exact' if exact else 'mismatch'
            if exact:result['loaded_scope_count']=receipt.get('planned_scopes')
        decisions={}
        for path in (N.root(data_root)/'decisions'/day/str(pid)).glob('*.json'):
            r=N._read(path)
            if (r.get('artifact_content_sha256')==P.seal(r)['artifact_content_sha256'] and r.get('pid_identity')==identity
                    and r.get('release_commit')==s['git_commit'] and r.get('bundle_sha256')==b['bundle_sha256']
                    and r.get('target_date')==day and r.get('scope') in scopes):decisions[r['scope']]=r
        result.update(observed_decision_scope_count=len(decisions),route_decisions=decisions)
    try:
        from src.engine.automation import intraday_release_handoff as H
        if Path(H.DATA_DIR).resolve()==data_root.resolve() and H.verify(day,s['git_commit'])['status']=='pass':
            result['prepared_state']='verified'
    except (OSError,ValueError,KeyError,TypeError):pass
    try: after_identity=_identity(pid) if identity else None
    except (OSError,ValueError):after_identity=None
    if (selector.read_bytes(),pointer.read_bytes())!=before or identity!=after_identity:
        return dict(status='changed_during_read',target_date=day,actual_pid_consumed=False)
    result['status']='observed';return result
