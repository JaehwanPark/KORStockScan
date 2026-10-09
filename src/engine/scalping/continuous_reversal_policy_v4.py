"""Versioned path-phase 48-cell route policy, publication and native CAS activation."""
from __future__ import annotations
import copy
import fcntl
import json
import re
from datetime import datetime
from fractions import Fraction
from pathlib import Path
from src.engine.scalping import continuous_reversal as K
from src.engine.scalping import continuous_reversal_branches as B
from src.engine.scalping import reversal_path_auxiliary as A
from src.engine.scalping import reversal_auxiliary_contract as V1
from src.engine.scalping import reversal_path_catalog as C
from src.engine.scalping import reversal_path_runtime as R
from src.engine.scalping.continuous_reversal_postclose import digest, file_hash
SCHEMA = 'continuous_reversal_policy_v4'


def contract_modules():
    from src.trading.market import session_contract as SESSION
    from src.engine.scalping import continuous_reversal_path_postclose as PC
    from src.engine.scalping import reversal_policy_backend as D
    from src.engine.scalping import continuous_reversal_policy_v3 as PREVIOUS
    return (SESSION,K,B,A,V1,C,R,PC,D,A.OLD,C.OLD,R.OLD,PREVIOUS,__import__(__name__,fromlist=['*']))


def migrate(family):
    """Lossless behavioral migration; inherited ranking is not local evidence."""
    from src.engine.scalping.continuous_reversal_policy import validate_family as old_validate
    old_validate(family)
    if family['schema'] == SCHEMA:
        return copy.deepcopy(family['machine_cells']), copy.deepcopy(family['auxiliary_cells'])
    if family['schema'] == 'continuous_reversal_policy_v3':
        return copy.deepcopy(family['machine_cells']), copy.deepcopy(family['auxiliary_cells'])
    from src.engine.scalping.continuous_reversal_policy_v3 import migrate as prior_migrate
    return prior_migrate(family)


def validate_family(f):
    if (not isinstance(f,dict) or f.get('schema') != SCHEMA or f.get('kernel_version') != K.VERSION
            or f.get('branch_registry_version') != C.VERSION or f.get('registry_sha256') != C.SHA256
            or f.get('branch_definition_sha256') != C.SHA256 or f.get('registry_manifest') != C.MANIFEST
            or f.get('auxiliary_version') != A.VERSION or f.get('label_contract') != C.LABEL
            or f.get('selection_metric') != 'cumulative_raw_win_fraction'
            or f.get('hard_guards_unchanged') is not True or f.get('actual_order_submitted') is not False
            or f.get('family_sha256') != digest({k:v for k,v in f.items() if k!='family_sha256'})):
        raise ValueError('v4_family_contract_invalid')
    if (f.get('effective_mode') not in {'intraday','next_session'}
            or re.fullmatch(r'[0-9a-f]{40}',str(f.get('release_commit') or '')) is None
            or re.fullmatch(r'[0-9a-f]{64}',str(f.get('parent_bundle_sha256') or '')) is None):
        raise ValueError('v4_release_parent_invalid')
    for name in ('machine_cells','auxiliary_cells'):
        if set(f.get(name,{})) != set(C.cells()):
            raise ValueError('v4_cell_coverage_invalid')
        for key, cell in f[name].items():
            if cell.get('key') != key or set(cell.get('routes',{})) != set(C.ROUTES[key.split('|')[1]]):
                raise ValueError('v4_route_coverage_invalid')
            for route, value in cell['routes'].items():
                p = value.get('payload')
                if value.get('payload_sha256') != digest(p):
                    raise ValueError('v4_payload_hash_invalid')
                if name == 'machine_cells':
                    C.validate_payload(p, key, route)
                    if set(value.get('branch_metrics',{})) != {b['branch_id'] for b in p['branches']}:
                        raise ValueError('v4_branch_metrics_coverage_invalid')
                    for m in [value.get('local_metrics'), *value['branch_metrics'].values(), *value.get('priority_metrics',{}).values()]:
                        if m is not None and (type(m.get('wins')) is not int or type(m.get('resolved')) is not int or not 0<=m['wins']<=m['resolved'] or m['resolved']<=0):
                            raise ValueError('v4_fraction_invalid')
                    if value.get('local_metrics') is None and not value.get('carry_source'):
                        raise ValueError('v4_machine_carry_missing')
                else:
                    branches = f['machine_cells'][key]['routes'][route]['payload']['branches']
                    if set(p) != {'branch_policies'} or set(p['branch_policies']) != {b['branch_id'] for b in branches}:
                        raise ValueError('v4_auxiliary_branch_coverage_invalid')
                    for b in branches:
                        policy = p['branch_policies'][b['branch_id']]; arm = policy.get('arm'); m = policy.get('local_metrics')
                        if arm not in V1.ARMS or policy.get('binding') != A.binding(b['decision_phase'],arm):
                            raise ValueError('v4_auxiliary_binding_invalid')
                        if m is None and not policy.get('carry_source'):
                            raise ValueError('v4_auxiliary_carry_missing')
                        if m is not None and (type(m.get('pass_wins')) is not int or type(m.get('pass_count')) is not int or not 0<=m['pass_wins']<=m['pass_count'] or m['pass_count']<=0 or not policy.get('actual_response_evidence')):
                            raise ValueError('v4_auxiliary_actual_fraction_invalid')
                        if b['decision_phase'] != B.FIRST and not policy.get('actual_response_evidence'):
                            raise ValueError('v4_confirmed_actual_evidence_missing')


def validate_sources(bundle, data_root, *, code_root=None):
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    f = bundle['continuous_reversal']; validate_family(f)
    from src.engine.scalping import continuous_reversal_path_postclose as PC
    if code_root is not None:
        import os
        import subprocess
        from src.engine.infrastructure.runtime_release_router import _release_identity
        origin=Path(code_root).resolve(strict=True)
        identity=_release_identity(Path(data_root).resolve().parent,str(origin/'src'),
                                   'reversal_transition_parent',f['release_commit'])
        if identity['source_integrity']!='git_commit_and_clean_runtime_source':
            raise ValueError('v4_transition_parent_code_unattested')
        # The origin owns its pin inventory as well as the pinned bytes. A new
        # common module is not retroactively required by a sealed old family.
        # Current runtime validation below remains strict and never falls back.
        script=('import json,sys; from pathlib import Path; '
                'from src.engine.scalping.continuous_reversal_policy_v4 import validate_sources; '
                'validate_sources(json.load(sys.stdin),Path(sys.argv[1]))')
        subprocess.run([str(origin/'.venv/bin/python'),'-c',script,str(Path(data_root).resolve())],
            input=json.dumps(bundle),text=True,check=True,capture_output=True,timeout=120,cwd=origin,
            env={**os.environ,'PYTHONPATH':str(origin)})
        return bundle
    for m in contract_modules():
        path = Path(m.__file__)
        if N._source_hash(str(path),N._signature(path)) != f['contract_file_sha256'].get(path.name):
            raise ValueError('v4_contract_code_changed:'+path.name)
    for name in ('machine','auxiliary'):
        path = N.root(Path(data_root))/'sources'/f"reversal-{f[name+'_report_sha256']}.json"
        if N._source_hash(str(path),N._signature(path)) != f['report_file_sha256'][name]:
            raise ValueError('v4_report_snapshot_changed')
        report = N._read(path)
        if (report.get('source_date') != f['source_date'] or report.get('publication_date') != f['publication_date']
                or report.get('status') not in {'completed','completed_with_scope_carry'}
                or report.get('artifact_content_sha256') != digest({k:v for k,v in report.items() if k!='artifact_content_sha256'})
                or {c['key']:c for c in report['cells']} != f[name+'_cells']):
            raise ValueError('v4_report_binding_invalid')
        for record in report.get('source_receipts',[])+report.get('results_sources',[]):
            path = Path(record['path'])
            if N._source_hash(str(path),N._signature(path)) != record['sha256']:
                raise ValueError('v4_frozen_source_changed')
    for cell in f['auxiliary_cells'].values():
        for value in cell['routes'].values():
            for p in value['payload']['branch_policies'].values():
                records = p.get('actual_response_evidence') or []
                for record in [records] if isinstance(records,dict) else records:
                    path = Path(record['path'])
                    if N._source_hash(str(path),N._signature(path)) != record['sha256']:
                        raise ValueError('v4_actual_response_source_changed')
    return bundle


def transition_parent(data_root,target_date):
    """Validate a changed-code predecessor in its immutable origin checkout.

    Runtime loads stay strict; historical validation never enters their cache.
    """
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    try:return N.load_effective(data_root=Path(data_root),target_date=target_date)
    except ValueError as exc:
        if not str(exc).startswith(('v3_contract_code_changed:','v4_contract_code_changed:')):raise
    receipt=N._read(N.root(Path(data_root))/'current.json')
    bundle=N._read(N.root(Path(data_root))/'generations'/(receipt['bundle_sha256']+'.json'))
    commit=bundle['continuous_reversal']['release_commit']
    selection=N._read(Path(data_root)/'runtime/runtime_release_selection.json')
    for root_key,commit_key in (('release_root','git_commit'),('previous_release_root','previous_git_commit')):
        if selection.get(commit_key)!=commit:continue
        parent=N._load_current_uncached(Path(data_root),target_date,historical_code_root=selection[root_key])
        if not parent or N._read(N.root(Path(data_root))/'current.json')!=receipt:
            raise ValueError('v4_transition_parent_changed')
        return parent
    raise ValueError('v4_transition_parent_origin_release_missing')


def stage_code_refresh(data_root,day,*,release_commit,reason):
    """Rebind identical issued policies to reviewed code, without reselection."""
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    parent=transition_parent(data_root,day);f=parent['continuous_reversal'];refs=[];reports={}
    for name in ('machine','auxiliary'):
        path=N.root(Path(data_root))/'sources'/('reversal-'+f[name+'_report_sha256']+'.json')
        reports[name]=copy.deepcopy(N._read(path));refs.append(dict(path=str(path.resolve()),sha256=file_hash(path)))
    m,a=reports['machine'],reports['auxiliary']
    for name,report in reports.items():
        if {c['key']:c for c in report['cells']}!=f[name+'_cells']:raise ValueError('v4_code_refresh_policy_changed')
        report['source_receipts']=report.get('source_receipts',[])+refs
        report['code_refresh']=dict(parent_bundle_sha256=parent['bundle_sha256'],reason=reason,
                                    policy_cells_unchanged=True,comparison_reexecuted=False)
    m['parent_bundle_sha256']=parent['bundle_sha256'];m['publication_date']=day
    m['artifact_content_sha256']=digest({k:v for k,v in m.items() if k!='artifact_content_sha256'})
    a['machine_report_sha256']=m['artifact_content_sha256'];a['publication_date']=day
    a['artifact_content_sha256']=digest({k:v for k,v in a.items() if k!='artifact_content_sha256'})
    return stage(data_root,m['source_date'],day,m,a,target_date=day,release_commit=release_commit,effective_mode='intraday')


def primary(cell, matched):
    order = {b['branch_id']:i for i,b in enumerate(cell['payload']['branches'])}
    def rank(bid):
        m = cell['branch_metrics'].get(bid)
        if m is None:
            m = cell.get('priority_metrics',{}).get(bid)
        return (m is not None, Fraction(m['wins'],m['resolved']) if m else Fraction(0), -order[bid])
    return max(matched, key=rank)


def assess(family, snapshot, *, symbol, session, build_request=True):
    validate_family(family)
    result = dict(machine_signal_confirmed=False, schema='mechanistic_entry_policy_decision_v1', action='BLOCK', reason='no_current_reversal_signal',
        policy_version=SCHEMA, primary_decision_owner='mechanistic_entry_adjudicator',
        ai_role='auxiliary_risk_screen_pass_veto_no_promotion', price_reversal_confirmed=False,
        runtime_effect=False, allowed_runtime_apply=False, actual_order_submitted=False, broker_order_forbidden=True)
    if snapshot is None:
        return result, None, None, None
    event, source = snapshot
    if event['symbol'] != symbol or event['market'] != K.market_bucket(session) or event.get('registry_sha256') != C.SHA256:
        raise ValueError('v4_snapshot_scope_conflict')
    key = C.cell_key(symbol,session,event['confirmation_price']); route = event['venue']
    cell = family['machine_cells'][key]['routes'][route]
    matched = [b['branch_id'] for b in cell['payload']['branches'] if b['branch_id'] in event['branch_signals']]
    for bid in matched:
        signal=event['branch_signals'][bid]
        if (signal.get('decision_phase')!=C.branch(bid)['decision_phase'] or signal.get('epoch')!=event['epoch']
                or signal.get('source_item')!=event['source_item'] or signal.get('event_id')!=event['event_id']
                or C.matches(bid,signal,signal.get('branch_features',{})) is not True):
            raise ValueError('v4_signal_definition_or_timeline_invalid')
        if bid in C.NEW_DEFINITIONS and signal.get('branch_definition_sha256')!=C.branch(bid)['definition_sha256']:
            raise ValueError('v4_signal_definition_hash_invalid')
        if signal['decision_phase'] in A.PHASES:
            A.validate_signal(signal)
        if signal['decision_phase']==B.CONFIRMED and (signal.get('branch_definition_sha256')!=C.branch(bid)['definition_sha256']
                or not 0<=signal['epoch']-signal['anchor_epoch']<=5
                or not signal['confirmation_price']>signal['anchor_price']>signal['low_price']):
            raise ValueError('v4_confirmation_definition_invalid')
    result.update(cell_key=key, route=route, event_id=event['event_id'], signal_id=event['signal_id'], event=event,
        matched_branches=matched, branch_states=[dict(branch_id=b['branch_id'],status='matched' if b['branch_id'] in matched else 'condition_not_met') for b in cell['payload']['branches']],
        branch_definition_sha256=C.SHA256, machine_component_sha256=digest(family['machine_cells']),
        family_sha256=family['family_sha256'])
    if not matched:
        result['reason'] = 'selected_reversal_condition_not_met'
        return result, None, None, None
    bid = primary(cell,matched); signal = event['branch_signals'][bid]; phase = signal['decision_phase']
    result.update(machine_signal_confirmed=True, signal_kind=phase,
                  price_reversal_confirmed=phase in {B.FIRST,B.CONFIRMED})
    if phase not in {B.FIRST,B.CONFIRMED}: A.validate_signal(signal)
    result['auxiliary_event'] = signal
    # The external event is the primary timeline. Keep all other timelines as
    # lineage, never splice another confirmation tick into its AI input.
    result['event'] = dict(signal, **{k:event[k] for k in
        ('branch_signals','anchor_lineage','canonical_opportunity_id','registry_sha256')})
    if signal['entry_ask'] is None:
        result.update(action='RECHECK',reason='entry_quote_source_missing')
        return result, None, None, None
    p = family['auxiliary_cells'][key]['routes'][route]['payload']['branch_policies'][bid]
    result.update(action='ENTER_NOW', reason='continuous_reversal_branch_union_pass', primary_branch=bid,
                  decision_phase=phase, auxiliary_arm=p['arm'], auxiliary_binding=p['binding'],
                  canonical_opportunity_id=event['canonical_opportunity_id'], primary_rank_reason='raw_fraction_then_frozen_order')
    if not build_request:
        return result, None, None, None
    inp,prompt,schema = A.production_request(source['branch_inputs'][bid],p['arm'],phase=phase,event=signal)
    return result, inp, prompt, schema

def stage(data_root,day,publication,machine,auxiliary,*,target_date,release_commit,effective_mode="next_session"):
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    root=N.root(Path(data_root));root.mkdir(parents=True,exist_ok=True)
    if effective_mode not in {"next_session","intraday"} or (effective_mode=="next_session" and target_date!=N.next_target(publication)):
        raise ValueError("reversal_v4_target_mode_invalid")
    if effective_mode=="intraday" and target_date!=publication:
        raise ValueError("reversal_v4_intraday_date_invalid")
    if not re.fullmatch(r"[0-9a-f]{40}",release_commit):raise ValueError("reversal_v4_release_commit_missing")
    for report in (machine,auxiliary):
        if (report.get('artifact_content_sha256')!=digest({k:v for k,v in report.items() if k!='artifact_content_sha256'})
                or report.get('status') not in {'completed','completed_with_scope_carry'} or report.get('source_date')!=day
                or report.get('publication_date')!=publication):raise ValueError('reversal_v4_report_preflight_invalid')
    if auxiliary.get('machine_report_sha256')!=machine['artifact_content_sha256']:
        raise ValueError('reversal_v4_auxiliary_machine_parent_invalid')
    if (effective_mode not in {'intraday','next_session'} or day>publication
            or target_date!=(publication if effective_mode=='intraday' else N.next_target(publication))):
        raise ValueError('reversal_v4_effective_date_invalid')
    with (root/"publisher.lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        parent=transition_parent(data_root,publication)
        if not parent:raise ValueError("reversal_v4_parent_missing")
        if machine.get('parent_bundle_sha256')!=parent['bundle_sha256']:
            raise ValueError('reversal_v4_report_incumbent_parent_changed')
        hashes={}
        for name,report in (("machine",machine),("auxiliary",auxiliary)):
            path=root/"sources"/f"reversal-{report['artifact_content_sha256']}.json"
            N._atomic_write_json(path,report);hashes[name]=file_hash(path)
        f=dict(schema=SCHEMA,kernel_version=K.VERSION,branch_registry_version=C.VERSION,
               branch_definition_sha256=C.SHA256,auxiliary_version=A.VERSION,
               source_date=day,publication_date=publication,effective_date=target_date,effective_mode=effective_mode,
               selection_metric="cumulative_raw_win_fraction",label_contract=machine["label_contract"],
               machine_report_sha256=machine["artifact_content_sha256"],auxiliary_report_sha256=auxiliary["artifact_content_sha256"],
               report_file_sha256=hashes,kernel_sha256=file_hash(K.__file__),
               contract_file_sha256={Path(m.__file__).name:file_hash(m.__file__) for m in contract_modules()},
               source_manifest_sha256=machine["source_manifest_sha256"],
               machine_cells={c['key']:c for c in machine['cells']},auxiliary_cells={c['key']:c for c in auxiliary['cells']},
               parent_bundle_sha256=parent['bundle_sha256'],release_commit=release_commit,
               registry_manifest=C.MANIFEST, registry_sha256=C.SHA256, hard_guards_unchanged=True,actual_order_submitted=False)
        f["family_sha256"]=digest(f);validate_family(f)
        bundle=copy.deepcopy(parent)
        for name in ("strategy_activation","winrate_selection","machine_evaluation_source","compact_evaluation_source"):
            bundle.pop(name,None)
        bundle.update(source_date=day,publication_date=publication,target_date=target_date,
                      generated_at=datetime.now(K.KST).isoformat(),continuous_reversal=f,
                      previous_bundle_sha256=parent["bundle_sha256"],machine_disposition="continuous_reversal_selected",
                      compact_prompt_disposition="continuous_reversal_selected")
        source=dict(schema=SCHEMA,source_date=day,target_date=target_date,continuous_reversal=f,artifact_content_sha256=digest(f))
        source_path=root/"sources"/(digest(source)+".json")
        N._atomic_write_json(source_path,source)
        # The native source filename is the physical file digest.
        real=root/"sources"/(file_hash(source_path)+".json")
        if real!=source_path:N._atomic_write_json(real,source)
        bundle.update(source_file_sha256=file_hash(real),source_artifact_sha256=digest(f))
        bundle.pop("bundle_sha256",None);bundle["bundle_sha256"]=digest(bundle)
        N.validate(bundle,target_date=target_date);N._validate_bundle_sources(bundle,Path(data_root))
        N._atomic_write_json(root/"generations"/(bundle['bundle_sha256']+".json"),bundle)
        N._atomic_write_json(root/"candidates"/f"policy_{target_date}.json",bundle)
        return bundle


def load_candidate(data_root,target_date):
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    bundle=N._read(N.root(Path(data_root))/"candidates"/f"policy_{target_date}.json")
    N.validate(bundle,target_date=target_date)
    if bundle["continuous_reversal"]["schema"]!=SCHEMA:raise ValueError("reversal_v4_candidate_schema_invalid")
    return N._validate_bundle_sources(bundle,Path(data_root))


def activate(data_root,target_date,*,now=None,intraday_evidence=None):
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    from src.engine.infrastructure.runtime_release_router import selected_release
    clock=now or datetime.now(K.KST)
    if clock.astimezone(K.KST).date().isoformat()!=target_date:raise ValueError("reversal_v4_activation_not_today")
    root=N.root(Path(data_root))
    with (root/"publisher.lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        bundle=load_candidate(data_root,target_date);family=bundle["continuous_reversal"]
        selected_root,commit=selected_release(Path(data_root).resolve().parent)
        # The router validates the immutable selected checkout. Activation is
        # tied to its code commit, not a workspace or a future target claim.
        if commit!=family["release_commit"]:raise ValueError("reversal_v4_activation_release_mismatch")
        if family['effective_mode']=='intraday':
            from src.engine.automation.intraday_release_handoff import _identity
            e=intraday_evidence or {}
            if (e.get('schema')!='intraday_main_policy_code_pid_v1' or e.get('target_date')!=target_date
                    or e.get('release_commit')!=commit or not e.get('pid_identity')
                    or _identity(e['pid_identity']['pid'])!=e['pid_identity']
                    or e['pid_identity']['cwd']!=str(selected_root/'src')
                    or file_hash(e['consumed_path'])!=e.get('consumed_sha256')):
                raise ValueError('reversal_v4_intraday_code_pid_not_verified')
        parent=transition_parent(data_root,target_date)
        if parent and parent["bundle_sha256"]==bundle["bundle_sha256"]:
            return dict(status="already_active",bundle_sha256=bundle["bundle_sha256"])
        if not parent or parent["bundle_sha256"]!=family["parent_bundle_sha256"]:
            raise ValueError("reversal_v4_activation_parent_cas_failed")
        receipt=dict(schema="continuous_reversal_current_v4",bundle_sha256=bundle["bundle_sha256"],
                     previous_bundle_sha256=parent["bundle_sha256"],effective_from=clock.isoformat(),
                     effective_date=target_date,family_sha256=family["family_sha256"],release_commit=commit)
        if intraday_evidence:receipt['intraday_code_pid_evidence']=intraday_evidence
        receipt["receipt_sha256"]=digest(receipt)
        N._atomic_write_json(root/'activations'/target_date/(receipt['receipt_sha256']+'.json'),receipt)
        # Until current.json commits the generation, effective resolution must
        # ignore the new dated v2 bytes and retain the current parent.
        # Preserve the original PREOPEN dated file. Intraday adoption changes
        # only the native current pointer, after the new code PID is verified.
        N._atomic_write_json(root/"current.json",receipt)
        if N.load_effective(data_root=Path(data_root),target_date=target_date)["bundle_sha256"]!=bundle["bundle_sha256"]:
            raise ValueError("reversal_v4_activation_readback_failed")
        return dict(status="activated",**receipt)


_CONSUMED=set()


def record_pid_consumption(data_root,bundle):
    """Executed by the actual Main consumer, never by the activation CLI."""
    import os
    from src.engine.automation.intraday_release_handoff import _identity
    from src.engine.infrastructure.runtime_release_router import selected_release
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    identity=_identity(os.getpid());key=(identity['start_ticks'],bundle['bundle_sha256'])
    if key in _CONSUMED:return
    selected,commit=selected_release(Path(data_root).resolve().parent)
    if identity['cwd']!=str(selected/'src') or commit!=bundle['continuous_reversal']['release_commit']:
        raise ValueError('reversal_v4_consumption_release_mismatch')
    current=N._load_current(Path(data_root),datetime.now(K.KST).date().isoformat())
    if not current or current['bundle_sha256']!=bundle['bundle_sha256']:
        raise ValueError('reversal_v4_consumption_generation_changed')
    receipt=dict(schema='continuous_reversal_pid_consumption_v4',bundle_sha256=bundle['bundle_sha256'],
                 family_sha256=bundle['continuous_reversal']['family_sha256'],release_commit=commit,pid_identity=identity,
                 observed_at=datetime.now(K.KST).isoformat(),actual_pid_consumed=True,actual_order_submitted=False)
    receipt['receipt_sha256']=digest(receipt)
    consumed_root=N.root(Path(data_root))/'consumed'/datetime.now(K.KST).date().isoformat()
    N._atomic_write_json(consumed_root/'history'/(str(os.getpid())+'-'+bundle['bundle_sha256']+'.json'),receipt)
    N._atomic_write_json(consumed_root/(str(os.getpid())+'.json'),receipt)
    _CONSUMED.add(key)
