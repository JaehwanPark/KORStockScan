"""Explicit operating membership, scope execution identity and native carry.

Evaluation never removes a registered detector. Incomplete union comparisons
carry the exact native pair; pending membership is not runtime authority.
"""
from __future__ import annotations
import copy
import fcntl
import json
import re
from datetime import datetime
from pathlib import Path
from src.engine.scalping import continuous_reversal as K
from src.engine.scalping import reversal_path_catalog as C
from src.engine.scalping import continuous_reversal_policy_v4 as V4
from src.engine.scalping import reversal_operating_auxiliary as A
from src.engine.scalping.continuous_reversal_postclose import digest, file_hash

SCHEMA = 'continuous_reversal_policy_v5'


def contract_modules():
    from src.engine.scalping import reversal_operating_runtime as R
    from src.engine.scalping import reversal_operating_backend as D
    from src.engine.scalping import reversal_operating_outbox as O
    return (*V4.contract_modules(), A, R, D, O, __import__(__name__, fromlist=['*']))


def scopes():
    return [(key, route) for key in C.cells() for route in C.ROUTES[key.split('|')[1]]]


def scope_id(key, route):
    return key + '|' + route


def wanted(parent):
    """Operator designated incumbent plus the eight definitions, exact scopes."""
    f = parent['continuous_reversal']
    if f['schema'] == SCHEMA:
        return copy.deepcopy(f['operating_manifest']['scopes'])
    V4.validate_family(f)
    return {scope_id(key, route): sorted({b['branch_id'] for b in f['machine_cells'][key]['routes'][route]['payload']['branches']}
        | {bid for bid in C.NEW_DEFINITIONS if C.applicable(bid, key, route)}) for key, route in scopes()}


def detector_manifest(parent, *, effective_date, changes=None):
    membership = wanted(parent)
    f = parent['continuous_reversal']
    old = f.get('operating_manifest')
    if changes is not None:
        if (changes.get('parent_bundle_sha256')!=parent['bundle_sha256']
                or changes.get('kind') not in {'ADD','REPLACE','RETIRE'}
                or not changes.get('operator_receipt') or not changes.get('scopes')):
            raise ValueError('v5_explicit_membership_change_receipt_invalid')
        for sid,change in changes['scopes'].items():
            if sid not in membership:raise ValueError('v5_membership_change_scope_invalid')
            previous=set(membership[sid]);remove=set(change.get('remove',[]));add=set(change.get('add',[]))
            if (not remove<=previous or (changes['kind']=='ADD' and remove)
                    or (changes['kind']=='RETIRE' and add) or not (previous-remove)|add):
                raise ValueError('v5_membership_change_invalid')
            key,route=sid.rsplit('|',1)
            result=(previous-remove)|add
            if any(b not in C.DEFINITIONS or not C.applicable(b,key,route) for b in result):
                raise ValueError('v5_membership_definition_or_scope_invalid')
            membership[sid]=sorted(result)
    manifest = dict(schema='main_operating_detector_manifest_v1', scopes=membership,
        definitions={bid: C.definition(bid) for bid in sorted({b for ids in membership.values() for b in ids})},
        registry_sha256=C.SHA256, parent_manifest_sha256=old['detector_manifest_hash'] if old else None,
        effective_date=effective_date, change_receipt=changes or dict(kind='INITIAL_ACTIVE_PLUS_EIGHT',
            parent_bundle_sha256=parent['bundle_sha256'], additions=sorted(C.NEW_DEFINITIONS)))
    # Effective date, receipt and report lineage do not reset identical FSMs.
    manifest['detector_manifest_hash'] = digest({k: manifest[k] for k in ('schema','scopes','definitions','registry_sha256')})
    return manifest


def scope_hash(ids, auxiliary, backend, code):
    return digest(dict(branches=[C.branch(b) for b in sorted(ids)], auxiliary=auxiliary,
                       backend=backend, code=code, label_contract=C.LABEL))


def validate_family(f):
    if (f.get('schema') != SCHEMA or f.get('family_sha256') != digest({k:v for k,v in f.items() if k!='family_sha256'})
            or f.get('hard_guards_unchanged') is not True or f.get('actual_order_submitted') is not False
            or f.get('registry_sha256') != C.SHA256 or f.get('label_contract') != C.LABEL
            or f.get('execution_code_sha256') != digest(f.get('contract_file_sha256'))
            or f.get('effective_mode') != 'next_session'
            or not f.get('source_date','') <= f.get('publication_date','') < f.get('effective_date','')
            or not re.fullmatch('[0-9a-f]{40}', str(f.get('release_commit')))):
        raise ValueError('v5_family_contract_invalid')
    m = f['operating_manifest']
    if m.get('detector_manifest_hash') != digest({k:m[k] for k in ('schema','scopes','definitions','registry_sha256')}):
        raise ValueError('v5_detector_manifest_changed')
    if set(m['scopes']) != {scope_id(k,r) for k,r in scopes()}:
        raise ValueError('v5_operating_scope_coverage_invalid')
    if set(m['definitions']) != {b for ids in m['scopes'].values() for b in ids}:
        raise ValueError('v5_definition_coverage_invalid')
    for bid, definition in m['definitions'].items():
        if definition != C.definition(bid):
            raise ValueError('v5_operating_definition_changed')
    native = f['native_parent_bundle']['continuous_reversal']
    V4.validate_family(native)
    if any(set(f.get(n,{})) != set(C.cells()) for n in ('machine_cells','auxiliary_cells')):
        raise ValueError('v5_cell_coverage_invalid')
    for name in ('machine_cells','auxiliary_cells'):
        if any(cell.get('key')!=key or set(cell.get('routes',{}))!=set(C.ROUTES[key.split('|')[1]]) for key,cell in f[name].items()):
            raise ValueError('v5_route_coverage_invalid')
    for key, route in scopes():
        sid = scope_id(key, route)
        ids = m['scopes'][sid]
        if not ids or ids != sorted(set(ids)) or any(not C.applicable(b, key, route) for b in ids):
            raise ValueError('v5_operating_membership_invalid')
        cell = f['machine_cells'][key]['routes'][route]
        aux = f['auxiliary_cells'][key]['routes'][route]
        backend = cell['backend']
        actual = [b['branch_id'] for b in cell['payload']['branches']]
        C.validate_payload(cell['payload'], key, route)
        if backend == 'union_v5':
            if actual != ids or aux['payload'].get('binding') != A.binding(aux['payload'].get('arm')) or not aux.get('actual_response_evidence'):
                raise ValueError('v5_union_pair_invalid')
        elif backend == 'registered_v4':
            if (cell['payload'] != native['machine_cells'][key]['routes'][route]['payload']
                    or aux['payload'] != native['auxiliary_cells'][key]['routes'][route]['payload']):
                raise ValueError('v5_native_carry_payload_changed')
        else:
            raise ValueError('v5_scope_backend_invalid')
        if cell.get('payload_sha256') != digest(cell['payload']) or aux.get('payload_sha256') != digest(aux['payload']):
            raise ValueError('v5_payload_hash_invalid')
        if cell['scope_execution_hash'] != scope_hash(actual, aux['payload'], backend, f['execution_code_sha256']):
            raise ValueError('v5_scope_execution_hash_invalid')
    execution = {scope_id(k,r):f['machine_cells'][k]['routes'][r]['scope_execution_hash'] for k,r in scopes()}
    if f.get('execution_manifest_hash') != digest(execution):
        raise ValueError('v5_execution_manifest_hash_invalid')


def validate_sources(bundle, data_root, *, code_root=None):
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    f = bundle['continuous_reversal']; validate_family(f)
    if code_root is not None:
        # The v5 envelope and its native v4 parent have different origin
        # commits. Attest the envelope checkout, then run its complete native
        # validator there; never relabel the nested parent's commit.
        import os
        import subprocess
        from src.engine.infrastructure.runtime_release_router import _release_identity
        origin=Path(code_root).resolve(strict=True)
        identity=_release_identity(Path(data_root).resolve().parent,str(origin/'src'),
                                   'operating_transition_parent',f['release_commit'])
        if identity['source_integrity']!='git_commit_and_clean_runtime_source':
            raise ValueError('v5_transition_parent_code_unattested')
        script=('import json,sys; from pathlib import Path; '
                'from src.engine.scalping.continuous_reversal_policy_v5 import validate_sources; '
                'validate_sources(json.load(sys.stdin),Path(sys.argv[1]))')
        subprocess.run([str(origin/'.venv/bin/python'),'-c',script,str(Path(data_root).resolve())],
            input=json.dumps(bundle),text=True,check=True,capture_output=True,timeout=120,cwd=origin,
            env={**os.environ,'PYTHONPATH':str(origin)})
        return bundle
    N.validate(f['native_parent_bundle'],target_date=f['native_parent_bundle']['target_date'])
    V4.validate_sources(f['native_parent_bundle'], data_root)
    for module in contract_modules():
        p = Path(code_root)/'src/engine/scalping'/Path(module.__file__).name if code_root else Path(module.__file__)
        if N._source_hash(str(p), N._signature(p)) != f['contract_file_sha256'].get(p.name):
            raise ValueError('v5_contract_code_changed:' + p.name)
    for name in ('machine','auxiliary'):
        p = N.root(Path(data_root))/'sources'/('reversal-'+f[name+'_report_sha256']+'.json')
        if file_hash(p) != f['report_file_sha256'][name]:
            raise ValueError('v5_report_snapshot_changed')
        report = N._read(p)
        if (report['artifact_content_sha256'] != digest({k:v for k,v in report.items() if k!='artifact_content_sha256'})
                or {c['key']:c for c in report['cells']} != f[name+'_cells']):
            raise ValueError('v5_report_binding_invalid')
        for record in report.get('source_receipts',[]) + report.get('results_sources',[]):
            p = Path(record['path'])
            if N._source_hash(str(p), N._signature(p)) != record['sha256']:
                raise ValueError('v5_frozen_source_changed')
    for key,route in scopes():
        for record in f['auxiliary_cells'][key]['routes'][route].get('actual_response_evidence',[]):
            p=Path(record['path'])
            if N._source_hash(str(p),N._signature(p))!=record['sha256']:
                raise ValueError('v5_actual_response_source_changed')
    return bundle


def assess(family, snapshot, *, symbol, session):
    validate_family(family)
    base = dict(schema='mechanistic_entry_policy_decision_v1', action='BLOCK', reason='no_current_operating_signal',
        policy_version=SCHEMA, primary_decision_owner='mechanistic_entry_adjudicator',
        ai_role='auxiliary_risk_screen_pass_veto_no_promotion', machine_signal_confirmed=False,
        price_reversal_confirmed=False, family_sha256=family['family_sha256'],
        runtime_effect=False, allowed_runtime_apply=False, actual_order_submitted=False, broker_order_forbidden=True)
    if snapshot is None:
        return base, None, None, None
    event, source = snapshot
    key = C.cell_key(symbol,session,event['confirmation_price']); route = event['venue']
    cell = family['machine_cells'][key]['routes'][route]
    if cell['backend'] == 'registered_v4':
        result = V4.assess(family['native_parent_bundle']['continuous_reversal'], snapshot, symbol=symbol, session=session)
        result[0]['operating_envelope_sha256'] = family['family_sha256']
        result[0]['scope_execution_hash'] = cell['scope_execution_hash']
        return result
    if event['symbol'] != symbol or event['market'] != K.market_bucket(session):
        raise ValueError('v5_snapshot_scope_conflict')
    selected = {b['branch_id'] for b in cell['payload']['branches']}
    if not set(event['branch_signals']) <= selected:
        raise ValueError('v5_snapshot_unregistered_policy')
    for bid, signal in event['branch_signals'].items():
        if C.matches(bid,signal,signal.get('branch_features',{})) is not True:
            raise ValueError('v5_signal_definition_invalid')
    aux = family['auxiliary_cells'][key]['routes'][route]['payload']
    inp,prompt,schema = A.production_request(source,aux['arm'],event=event)
    refs = [s['ref'] for s in inp['signals']]
    base.update(action='ENTER_NOW', reason='operating_independent_union_pass', machine_signal_confirmed=True,
        cell_key=key, route=route, event_id=event['event_id'], signal_id=event['signal_id'], event=event,
        canonical_opportunity_id=A.opportunity(event), opportunity_key=A.opportunity(event),
        matched_policy_refs=refs, still_valid_policy_refs=refs, signal_set_hash=digest(inp['signals']),
        matched_branches=sorted(event['branch_signals']), primary_branch=None, decision_phase='UNION',
        auxiliary_arm=aux['arm'], auxiliary_binding=aux['binding'],
        scope_execution_hash=cell['scope_execution_hash'], machine_component_sha256=family['execution_manifest_hash'])
    return base, inp, prompt, schema


def stage(data_root, day, publication, machine, auxiliary, *, target_date, release_commit):
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    if target_date != N.next_target(publication) or day > publication:
        raise ValueError('v5_target_date_invalid')
    root = N.root(Path(data_root)); root.mkdir(parents=True,exist_ok=True)
    with (root/'publisher.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        parent = V4.transition_parent(data_root, publication)
        if not parent or machine['parent_bundle_sha256'] != parent['bundle_sha256']:
            raise ValueError('v5_parent_cas_failed')
        for report in (machine,auxiliary):
            if (report['artifact_content_sha256'] != digest({k:v for k,v in report.items() if k!='artifact_content_sha256'})
                    or report['status'] not in {'completed','completed_with_scope_carry'}
                    or report['source_date'] != day or report['publication_date'] != publication):
                raise ValueError('v5_report_preflight_invalid')
        if auxiliary['machine_report_sha256'] != machine['artifact_content_sha256']:
            raise ValueError('v5_auxiliary_parent_invalid')
        hashes = {}
        for name, report in (('machine',machine),('auxiliary',auxiliary)):
            path = root/'sources'/('reversal-'+report['artifact_content_sha256']+'.json')
            N._atomic_write_json(path,report); hashes[name] = file_hash(path)
        native = parent['continuous_reversal'].get('native_parent_bundle', parent)
        f = dict(schema=SCHEMA, kernel_version=K.VERSION, registry_sha256=C.SHA256,
            branch_definition_sha256=C.SHA256, auxiliary_version=A.VERSION, label_contract=C.LABEL,
            source_date=day, publication_date=publication, effective_date=target_date, effective_mode='next_session',
            selection_metric='cumulative_raw_win_fraction', release_commit=release_commit,
            parent_bundle_sha256=parent['bundle_sha256'], native_parent_bundle=native,
            operating_manifest=machine['operating_manifest'], execution_code_sha256=machine['execution_code_sha256'],
            contract_file_sha256={Path(m.__file__).name:file_hash(m.__file__) for m in contract_modules()},
            machine_cells={c['key']:c for c in machine['cells']}, auxiliary_cells={c['key']:c for c in auxiliary['cells']},
            machine_report_sha256=machine['artifact_content_sha256'], auxiliary_report_sha256=auxiliary['artifact_content_sha256'],
            report_file_sha256=hashes, source_manifest_sha256=machine['source_manifest_sha256'],
            hard_guards_unchanged=True, actual_order_submitted=False)
        f['execution_manifest_hash'] = digest({scope_id(k,r):f['machine_cells'][k]['routes'][r]['scope_execution_hash'] for k,r in scopes()})
        f['family_sha256'] = digest(f); validate_family(f)
        bundle = copy.deepcopy(parent)
        for name in ('strategy_activation','winrate_selection','machine_evaluation_source','compact_evaluation_source'):
            bundle.pop(name,None)
        bundle.update(source_date=day, publication_date=publication, target_date=target_date,
            generated_at=datetime.now(K.KST).isoformat(), continuous_reversal=f,
            previous_bundle_sha256=parent['bundle_sha256'], machine_disposition='continuous_reversal_selected',
            compact_prompt_disposition='continuous_reversal_selected')
        source = dict(schema=SCHEMA,source_date=day,target_date=target_date,continuous_reversal=f,artifact_content_sha256=digest(f))
        path = root/'sources'/(digest(source)+'.json'); N._atomic_write_json(path,source)
        real = root/'sources'/(file_hash(path)+'.json'); N._atomic_write_json(real,source)
        bundle.update(source_file_sha256=file_hash(real),source_artifact_sha256=digest(f))
        bundle.pop('bundle_sha256',None); bundle['bundle_sha256'] = digest(bundle)
        N.validate(bundle,target_date=target_date); N._validate_bundle_sources(bundle,Path(data_root))
        N._atomic_write_json(root/'generations'/(bundle['bundle_sha256']+'.json'),bundle)
        N._atomic_write_json(root/'candidates'/('policy_'+target_date+'.json'),bundle)
        return bundle


def activate(data_root,target_date,*,now=None):
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    from src.engine.infrastructure.runtime_release_router import selected_release
    clock = now or datetime.now(K.KST)
    if clock.astimezone(K.KST).date().isoformat() != target_date:
        raise ValueError('v5_activation_not_today')
    root = N.root(Path(data_root))
    with (root/'publisher.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        bundle = N._read(root/'candidates'/('policy_'+target_date+'.json'))
        N.validate(bundle,target_date=target_date); validate_sources(bundle,data_root)
        _,commit = selected_release(Path(data_root).resolve().parent)
        f = bundle['continuous_reversal']
        if commit != f['release_commit']:
            raise ValueError('v5_activation_release_mismatch')
        parent = N.load_effective(data_root=Path(data_root),target_date=target_date)
        if parent and parent['bundle_sha256'] == bundle['bundle_sha256']:
            return dict(status='already_active',bundle_sha256=bundle['bundle_sha256'])
        if not parent or parent['bundle_sha256'] != f['parent_bundle_sha256']:
            raise ValueError('v5_activation_parent_cas_failed')
        receipt = dict(schema='continuous_reversal_current_v5',bundle_sha256=bundle['bundle_sha256'],
            previous_bundle_sha256=parent['bundle_sha256'],effective_from=clock.isoformat(),
            effective_date=target_date,family_sha256=f['family_sha256'],release_commit=commit)
        receipt['receipt_sha256'] = digest(receipt)
        N._atomic_write_json(root/'activations'/target_date/(receipt['receipt_sha256']+'.json'),receipt)
        N._atomic_write_json(root/'current.json',receipt)
        if N.load_effective(data_root=Path(data_root),target_date=target_date)['bundle_sha256'] != bundle['bundle_sha256']:
            raise ValueError('v5_activation_readback_failed')
        return dict(status='activated',**receipt)


def validate_active_claim(policy, active, *, now):
    """Validate the current envelope while preserving equivalent scope claims."""
    from src.engine.scalping import reversal_operating_backend as D
    from src.utils.constants import DATA_DIR
    if not active or active.get('continuous_reversal',{}).get('schema') != SCHEMA:
        raise ValueError('reversal_policy_changed_after_provider')
    f = active['continuous_reversal']; validate_family(f)
    a = policy['continuous_reversal_assessment']
    cell = f['machine_cells'][a['cell_key']]['routes'][a['route']]
    if cell['scope_execution_hash'] != a['scope_execution_hash'] or cell['backend'] != 'union_v5':
        raise ValueError('reversal_scope_execution_changed')
    D.configure_bundle(active,data_root=DATA_DIR,day=datetime.fromtimestamp(now,K.KST).date().isoformat())
    snap = D.validate_any_claim(policy['continuous_reversal_claim'],f['family_sha256'],now=now)
    remaining = {bid+':'+A.definition_hash(bid) for bid in snap[0]['branch_signals']}
    # Never add evidence that was absent at transmission time.
    valid = sorted(remaining.intersection(a['matched_policy_refs']))
    if not valid:
        raise ValueError('reversal_all_requested_signals_invalidated')
    return valid


def record_pid_consumption(data_root,bundle):
    # Same immutable code/PID/current-pointer attestation. The receipt records
    # mixed coverage explicitly rather than calling pending scopes consumed.
    import os
    from src.engine.automation.intraday_release_handoff import _identity
    from src.engine.infrastructure.runtime_release_router import selected_release
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    identity=_identity(os.getpid()); selected,commit=selected_release(Path(data_root).resolve().parent)
    f=bundle['continuous_reversal']; day=datetime.now(K.KST).date().isoformat()
    if identity['cwd']!=str(selected/'src') or commit!=f['release_commit']:
        raise ValueError('v5_consumption_release_mismatch')
    active=N.load_effective(data_root=Path(data_root),target_date=day)
    if not active or active['bundle_sha256']!=bundle['bundle_sha256']:
        raise ValueError('v5_consumption_generation_changed')
    path=N.root(Path(data_root))/'consumed'/day/(str(os.getpid())+'.json')
    if path.exists() and N._read(path).get('bundle_sha256')==bundle['bundle_sha256']:
        return
    count=sum(f['machine_cells'][k]['routes'][r]['backend']=='union_v5' for k,r in scopes())
    receipt=dict(schema='continuous_reversal_pid_consumption_v5',bundle_sha256=bundle['bundle_sha256'],
        family_sha256=f['family_sha256'],execution_manifest_hash=f['execution_manifest_hash'],
        release_commit=commit,pid_identity=identity,observed_at=datetime.now(K.KST).isoformat(),
        planned_scopes=len(scopes()),new_consumed_scopes=count,legacy_carried_scopes=len(scopes())-count,
        actual_pid_consumed=True,actual_order_submitted=False)
    receipt['receipt_sha256']=digest(receipt)
    N._atomic_write_json(path.parent/'history'/(str(os.getpid())+'-'+bundle['bundle_sha256']+'.json'),receipt)
    N._atomic_write_json(path,receipt)


def audit_observation(bundle, observation):
    """Report-only verifier for the outer envelope and exact native/union pair."""
    import hashlib
    import math
    from src.engine.scalping.ai_decision_trace import _json_bytes
    f=bundle['continuous_reversal'];validate_family(f)
    context=observation['label_context'];source=observation['source'];a=source['assessment']
    receipt=observation['runtime_consumption'];native=receipt.get('continuous_reversal') or {}
    raw=source.get('exact_payload');captured=datetime.fromisoformat(observation['captured_at'])
    if (not isinstance(raw,dict) or str(raw.get('stock_code'))!=str(context['stock_code'])
            or not context.get('evaluation_attempt_id') or raw.get('evaluation_attempt_id')!=context['evaluation_attempt_id']
            or K.market_bucket(raw.get('session_bucket'))!=K.market_bucket(context['session_bucket'])
            or receipt.get('bundle_sha256')!=bundle['bundle_sha256']):
        raise ValueError('v5_observation_identity_invalid')
    expected=dict(family_sha256=f['family_sha256'],bundle_sha256=bundle['bundle_sha256'],
        source_date=f['source_date'],publication_date=f['publication_date'],effective_date=f['effective_date'],
        machine_component_sha256=digest(f['machine_cells']),auxiliary_component_sha256=digest(f['auxiliary_cells']),
        event_id=a.get('event_id'),cell_key=a.get('cell_key'),rule=a.get('rule'),pid=receipt.get('pid'),
        process_start_ticks=receipt.get('process_start_ticks'),captured_at=observation['captured_at'],
        exact_payload_sha256=hashlib.sha256(_json_bytes(raw)).hexdigest(),assessment_sha256=hashlib.sha256(_json_bytes(a)).hexdigest())
    if any(native.get(k)!=v for k,v in expected.items()):raise ValueError('v5_consumption_receipt_mismatch')
    clock=native.get('snapshot_read_at');observed=raw.get('entry_machine_input_as_of')
    if (type(clock) not in (int,float) or type(observed) not in (int,float)
            or not math.isfinite(clock) or not observed<=clock<=captured.timestamp()):
        raise ValueError('v5_observation_clock_invalid')
    event=a.get('event')
    if event is None:
        if a.get('action')!='BLOCK' or a.get('reason')!='no_current_operating_signal':raise ValueError('v5_nonentry_receipt_invalid')
        return {},dict(policy_sha256=f['execution_manifest_hash'],leaf='NO_CURRENT_OPERATING_SIGNAL')
    key=C.cell_key(str(context['stock_code']),context['session_bucket'],event['confirmation_price']);route=event['venue']
    cell=f['machine_cells'][key]['routes'][route]
    if event['symbol']!=str(context['stock_code']) or event['market']!=K.market_bucket(context['session_bucket']) or not 0<=clock-event['epoch']<=5:
        raise ValueError('v5_event_scope_or_clock_invalid')
    request=source.get('auxiliary_request') or {}
    if a.get('action')=='ENTER_NOW' and any(digest(request.get(k))!=native.get(v) for k,v in
            [('input','input_sha256'),('prompt','prompt_sha256'),('response_schema','response_schema_sha256')]):
        raise ValueError('v5_auxiliary_request_hash_mismatch')
    if cell['backend']=='registered_v4':
        replay,_,_,_=V4.assess(f['native_parent_bundle']['continuous_reversal'],(event,None),symbol=event['symbol'],session=event['market'],build_request=False)
        for field in ('action','reason','policy_version','cell_key','route','primary_branch','matched_branches','auxiliary_arm','machine_component_sha256'):
            if a.get(field)!=replay.get(field):raise ValueError('v5_native_pair_receipt_mismatch:'+field)
        if a.get('action')=='ENTER_NOW':
            from src.engine.scalping import reversal_path_auxiliary as OLD
            arm=a['auxiliary_arm'];phase=a['decision_phase'];inp=request['input']
            if request['prompt']!=OLD.prompt(phase,arm):raise ValueError('v5_native_prompt_mismatch')
            if phase in OLD.PHASES:OLD.validate_input_signal(inp,a['auxiliary_event'])
    else:
        if a.get('policy_version')!=SCHEMA or a.get('scope_execution_hash')!=cell['scope_execution_hash']:
            raise ValueError('v5_scope_execution_receipt_mismatch')
        ids=set(event['branch_signals']);selected={b['branch_id'] for b in cell['payload']['branches']}
        if not ids or not ids<=selected or any(C.matches(b,s,s['branch_features']) is not True for b,s in event['branch_signals'].items()):
            raise ValueError('v5_unregistered_or_invalid_signal')
        refs=sorted(b+':'+A.definition_hash(b) for b in ids)
        inp=request['input'];arm=f['auxiliary_cells'][key]['routes'][route]['payload']['arm']
        if (a.get('matched_policy_refs')!=refs or a.get('opportunity_key')!=A.opportunity(event)
                or inp.get('schema')!=A.VERSION or [s['ref'] for s in inp['signals']]!=refs
                or a.get('signal_set_hash')!=digest(inp['signals']) or native.get('arm')!=arm
                or request['prompt']!=A.PROMPT+A.ARM_SUFFIXES[arm] or request['response_schema']!=A.response_schema(inp)
                or inp['common_context']['opportunity_key']!=A.opportunity(event)):
            raise ValueError('v5_union_request_receipt_mismatch')
    return cell['payload'],dict(policy_sha256=cell['scope_execution_hash'],leaf=key+'|'+route,
                                operating_backend=cell['backend'],new_scope_consumption=cell['backend']=='union_v5')
