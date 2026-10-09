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
from src.engine.scalping import reversal_extended_catalog as C
from src.engine.scalping import continuous_reversal_policy_v4 as V4
from src.engine.scalping import reversal_extended_union as A
from src.engine.scalping.continuous_reversal_postclose import digest, file_hash

SCHEMA = 'continuous_reversal_policy_v6'
CODE_REFRESH_AUTHORITY = 'reviewed_identical_policy_code_refresh'


def contract_modules():
    from src.engine.scalping import continuous_reversal_policy_v5 as V5
    from src.engine.scalping import reversal_extended_state as R
    from src.engine.scalping import reversal_extended_auxiliary as T
    from src.engine.scalping import reversal_extended_runtime as E
    from src.engine.scalping import reversal_extended_registration as ER
    from src.engine.scalping import reversal_current_backend as D
    from src.engine.scalping import reversal_extended_intraday as INTRA
    return (*V5.contract_modules(),C,A,R,T,E,ER,D,INTRA,__import__(__name__,fromlist=['*']))


def scopes():
    return [(key, route) for key in C.cells() for route in C.ROUTES[key.split('|')[1]]]


def scope_id(key, route):
    return key + '|' + route


def wanted(parent):
    """Retain membership; only an explicit change receipt adds definitions."""
    f = parent['continuous_reversal']
    if f['schema'] in {SCHEMA,'continuous_reversal_policy_v5'}:
        return copy.deepcopy(f['operating_manifest']['scopes'])
    raise ValueError('v6_operating_parent_required')


def detector_manifest(parent, *, effective_date, changes=None):
    membership = wanted(parent)
    f = parent['continuous_reversal']
    old = f.get('operating_manifest')
    if changes is not None:
        if (changes.get('parent_bundle_sha256')!=parent['bundle_sha256']
                or changes.get('kind') not in {'ADD','REPLACE','RETIRE'}
                or not changes.get('operator_receipt') or not changes.get('scopes')):
            raise ValueError('v6_explicit_membership_change_receipt_invalid')
        for sid,change in changes['scopes'].items():
            if sid not in membership:raise ValueError('v6_membership_change_scope_invalid')
            previous=set(membership[sid]);remove=set(change.get('remove',[]));add=set(change.get('add',[]))
            if (not remove<=previous or (changes['kind']=='ADD' and remove)
                    or (changes['kind']=='RETIRE' and add) or not (previous-remove)|add):
                raise ValueError('v6_membership_change_invalid')
            key,route=sid.rsplit('|',1)
            result=(previous-remove)|add
            if any(b not in C.DEFINITIONS or not C.applicable(b,key,route) for b in result):
                raise ValueError('v6_membership_definition_or_scope_invalid')
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
            or f.get('branch_definition_sha256') != C.SHA256 or f.get('auxiliary_version') != A.VERSION
            or f.get('execution_code_sha256') != digest(f.get('contract_file_sha256'))
            or f.get('effective_mode') not in {'next_session','intraday'}
            or not f.get('source_date','') <= f.get('publication_date','') <= f.get('effective_date','')
            or not re.fullmatch('[0-9a-f]{40}', str(f.get('release_commit')))):
        raise ValueError('v6_family_contract_invalid')
    if f['effective_mode']=='next_session':
        if f['publication_date']>=f['effective_date']:raise ValueError('v6_next_session_date_invalid')
    else:
        from src.engine.scalping.reversal_extended_intraday import validate_activation
        validate_activation(f)
    m = f['operating_manifest']
    if m.get('schema')!='main_operating_detector_manifest_v1' or m.get('registry_sha256')!=C.SHA256:
        raise ValueError('v6_detector_registry_invalid')
    if m.get('detector_manifest_hash') != digest({k:m[k] for k in ('schema','scopes','definitions','registry_sha256')}):
        raise ValueError('v6_detector_manifest_changed')
    if set(m['scopes']) != {scope_id(k,r) for k,r in scopes()}:
        raise ValueError('v6_operating_scope_coverage_invalid')
    if set(m['definitions']) != {b for ids in m['scopes'].values() for b in ids}:
        raise ValueError('v6_definition_coverage_invalid')
    for bid, definition in m['definitions'].items():
        if definition != C.definition(bid):
            raise ValueError('v6_operating_definition_changed')
    native = f['native_parent_bundle']['continuous_reversal']
    V4.validate_family(native)
    if any(set(f.get(n,{})) != set(C.cells()) for n in ('machine_cells','auxiliary_cells')):
        raise ValueError('v6_cell_coverage_invalid')
    for name in ('machine_cells','auxiliary_cells'):
        if any(cell.get('key')!=key or set(cell.get('routes',{}))!=set(C.ROUTES[key.split('|')[1]]) for key,cell in f[name].items()):
            raise ValueError('v6_route_coverage_invalid')
    for key, route in scopes():
        sid = scope_id(key, route)
        ids = m['scopes'][sid]
        if not ids or ids != sorted(set(ids)) or any(not C.applicable(b, key, route) for b in ids):
            raise ValueError('v6_operating_membership_invalid')
        cell = f['machine_cells'][key]['routes'][route]
        aux = f['auxiliary_cells'][key]['routes'][route]
        backend = cell['backend']
        actual = [b['branch_id'] for b in cell['payload']['branches']]
        C.validate_payload(cell['payload'], key, route)
        if backend == 'union_v6':
            if actual != ids or aux['payload'].get('binding') != A.binding(aux['payload'].get('arm')) or not (aux.get('actual_response_evidence') or aux.get('initial_binding',{}).get('operator_receipt')):
                raise ValueError('v6_union_pair_invalid')
            if not aux.get('actual_response_evidence'):
                from src.engine.scalping.reversal_extended_registration import AUTHORITY
                proof=aux['initial_binding']
                if (proof.get('operator_receipt')!=AUTHORITY or proof.get('research_batch_sha256')!=C.RESEARCH_BATCH_SHA256
                        or proof.get('comparison_result_required') is not False):
                    raise ValueError('v6_initial_registration_proof_invalid')
        elif backend == 'registered_v4':
            if (cell['payload'] != native['machine_cells'][key]['routes'][route]['payload']
                    or aux['payload'] != native['auxiliary_cells'][key]['routes'][route]['payload']):
                raise ValueError('v6_native_carry_payload_changed')
        else:
            raise ValueError('v6_scope_backend_invalid')
        if cell.get('payload_sha256') != digest(cell['payload']) or aux.get('payload_sha256') != digest(aux['payload']):
            raise ValueError('v6_payload_hash_invalid')
        if cell['scope_execution_hash'] != scope_hash(actual, aux['payload'], backend, f['execution_code_sha256']):
            raise ValueError('v6_scope_execution_hash_invalid')
    execution = {scope_id(k,r):f['machine_cells'][k]['routes'][r]['scope_execution_hash'] for k,r in scopes()}
    if f.get('execution_manifest_hash') != digest(execution):
        raise ValueError('v6_execution_manifest_hash_invalid')


def validate_sources(bundle, data_root, *, code_root=None):
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    with N.source_anchor(data_root):
        return _validate_sources(bundle,Path(data_root).absolute(),code_root=code_root)


def _validate_sources(bundle, data_root, *, code_root=None):
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
            raise ValueError('v6_transition_parent_code_unattested')
        script=('import json,sys; from pathlib import Path; '
                'from src.engine.scalping.continuous_reversal_policy_v6 import validate_sources; '
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
            raise ValueError('v6_contract_code_changed:' + p.name)
    for name in ('machine','auxiliary'):
        p = N.root(Path(data_root))/'sources'/('reversal-'+f[name+'_report_sha256']+'.json')
        if file_hash(p) != f['report_file_sha256'][name]:
            raise ValueError('v6_report_snapshot_changed')
        report = N._read(p)
        if (report['artifact_content_sha256'] != digest({k:v for k,v in report.items() if k!='artifact_content_sha256'})
                or {c['key']:c for c in report['cells']} != f[name+'_cells']):
            raise ValueError('v6_report_binding_invalid')
        if name=='machine' and f['effective_mode']=='intraday' and report.get('registration_activation')!=f['registration_activation']:
            raise ValueError('v6_intraday_report_authority_changed')
        for record in report.get('source_receipts',[]) + report.get('results_sources',[]):
            p = Path(record['path'])
            if N._source_hash(str(p), N._signature(p)) != record['sha256']:
                raise ValueError('v6_frozen_source_changed')
    for key,route in scopes():
        for record in f['auxiliary_cells'][key]['routes'][route].get('actual_response_evidence',[]):
            p=Path(record['path'])
            if N._source_hash(str(p),N._signature(p))!=record['sha256']:
                raise ValueError('v6_actual_response_source_changed')
    if f.get('code_refresh') is not None:
        _validate_code_refresh(bundle, data_root)
    return bundle


def _behavioral_family(family):
    """Code/reseal identities may change; all trading and evidence fields stay."""
    value = copy.deepcopy(family)
    for key in ('contract_file_sha256', 'execution_code_sha256', 'release_commit',
                'family_sha256', 'machine_report_sha256', 'auxiliary_report_sha256',
                'report_file_sha256', 'execution_manifest_hash', 'code_refresh'):
        value.pop(key, None)
    native = value.pop('native_parent_bundle', None)
    if native is not None:
        value['native_parent_family'] = _behavioral_family(native['continuous_reversal'])
    for cell in value['machine_cells'].values():
        for route in cell['routes'].values():
            route.pop('scope_execution_hash', None)
    return value


def _validate_code_refresh(bundle, data_root):
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    f = bundle['continuous_reversal']; proof = f['code_refresh']
    if (f['effective_mode'] != 'next_session'
            or proof.get('schema') != 'main_identical_policy_code_refresh_v1'
            or proof.get('authority') != CODE_REFRESH_AUTHORITY
            or proof.get('policy_reselected') is not False
            or proof.get('provider_called') is not False or not proof.get('reason')
            or not re.fullmatch('[0-9a-f]{64}', str(proof.get('source_bundle_sha256')))
            or not re.fullmatch('[0-9a-f]{40}', str(proof.get('activation_parent_origin_commit')))
            or not Path(str(proof.get('activation_parent_origin_root',''))).is_absolute()):
        raise ValueError('v6_code_refresh_proof_invalid')
    p = N.root(Path(data_root))/'generations'/(proof['source_bundle_sha256']+'.json')
    N._signature(p)
    original = N._read(p)
    N.validate(original, target_date=bundle['target_date'])
    if (original['bundle_sha256'] != proof['source_bundle_sha256']
            or _behavioral_family(original['continuous_reversal']) != _behavioral_family(f)):
        raise ValueError('v6_code_refresh_policy_changed')
    allowed = {'continuous_reversal', 'generated_at', 'source_file_sha256',
               'source_artifact_sha256', 'bundle_sha256'}
    if ({k:v for k,v in bundle.items() if k not in allowed}
            != {k:v for k,v in original.items() if k not in allowed}):
        raise ValueError('v6_code_refresh_bundle_changed')
    return original


def _write_refreshed_bundle(original, data_root, *, release_commit, proof):
    """Private, immutable generation builder after origin attestation."""
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    root = N.root(Path(data_root))
    bundle = copy.deepcopy(original); f = bundle['continuous_reversal']
    if f['schema'] not in {V4.SCHEMA, SCHEMA}:
        raise ValueError('v6_code_refresh_schema_unsupported')
    if f['schema'] == SCHEMA:
        f['native_parent_bundle'] = _write_refreshed_bundle(
            f['native_parent_bundle'], data_root, release_commit=release_commit, proof=None)
        f['code_refresh'] = proof
    modules = contract_modules() if f['schema'] == SCHEMA else V4.contract_modules()
    f['contract_file_sha256'] = {Path(m.__file__).name:file_hash(m.__file__) for m in modules}
    f['release_commit'] = release_commit
    if f['schema'] == SCHEMA:
        f['execution_code_sha256'] = digest(f['contract_file_sha256'])
        for key, route in scopes():
            cell = f['machine_cells'][key]['routes'][route]
            ids = [b['branch_id'] for b in cell['payload']['branches']]
            cell['scope_execution_hash'] = scope_hash(ids, f['auxiliary_cells'][key]['routes'][route]['payload'],
                                                     cell['backend'], f['execution_code_sha256'])
        f['execution_manifest_hash'] = digest({scope_id(k,r):f['machine_cells'][k]['routes'][r]['scope_execution_hash'] for k,r in scopes()})
    for name in ('machine','auxiliary'):
        old_path = root/'sources'/('reversal-'+original['continuous_reversal'][name+'_report_sha256']+'.json')
        report = copy.deepcopy(N._read(old_path))
        old_sha = file_hash(old_path)
        if old_sha != original['continuous_reversal']['report_file_sha256'][name]:
            raise ValueError('v6_code_refresh_report_changed')
        report['source_receipts'] = report.get('source_receipts',[]) + [dict(path=str(old_path.resolve()),sha256=old_sha)]
        report['cells'] = [copy.deepcopy(f[name+'_cells'][c['key']]) for c in report['cells']]
        if f['schema'] == SCHEMA and name == 'machine':
            report['execution_code_sha256'] = f['execution_code_sha256']
        if name == 'auxiliary':report['machine_report_sha256'] = f['machine_report_sha256']
        report['artifact_content_sha256'] = digest({k:v for k,v in report.items() if k!='artifact_content_sha256'})
        path = root/'sources'/('reversal-'+report['artifact_content_sha256']+'.json')
        N._atomic_write_json(path,report)
        f[name+'_report_sha256'] = report['artifact_content_sha256']
        f['report_file_sha256'][name] = file_hash(path)
    f['family_sha256'] = digest({k:v for k,v in f.items() if k!='family_sha256'})
    source = dict(schema=f['schema'],source_date=bundle['source_date'],target_date=bundle['target_date'],
                  continuous_reversal=f,artifact_content_sha256=digest(f))
    provisional = root/'sources'/(digest(source)+'.json')
    N._atomic_write_json(provisional,source)
    source_path = root/'sources'/(file_hash(provisional)+'.json')
    N._atomic_write_json(source_path,source)
    bundle.update(generated_at=datetime.now(K.KST).isoformat(),source_file_sha256=file_hash(source_path),
                  source_artifact_sha256=digest(f))
    bundle['bundle_sha256'] = digest({k:v for k,v in bundle.items() if k!='bundle_sha256'})
    N.validate(bundle,target_date=bundle['target_date'])
    N._validate_bundle_sources(bundle,Path(data_root))
    N._atomic_write_json(root/'generations'/(bundle['bundle_sha256']+'.json'),bundle)
    return bundle


def _attested_activation_parent(data_root, target_date, *, origin_root, origin_commit):
    """Validate the unchanged active bundle in the previous reviewed release.

    A policy may have outlived several code-only deployments. Its complete
    strict validator, not the policy's old release label, proves unchanged pins.
    This path is exclusive to staging/activating an explicit code refresh.
    """
    import os
    import subprocess
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    from src.engine.infrastructure.runtime_release_router import _release_identity
    origin = Path(origin_root).resolve(strict=True)
    identity = _release_identity(Path(data_root).resolve().parent,str(origin/'src'),
                                 'code_refresh_activation_parent',origin_commit)
    if identity['source_integrity'] != 'git_commit_and_clean_runtime_source':
        raise ValueError('v6_code_refresh_activation_origin_unattested')
    script = ('import sys; from pathlib import Path; '
              'from src.engine.scalping import mechanistic_entry_runtime_policy as N; '
              'b=N._load_current_uncached(Path(sys.argv[1]),sys.argv[2]); '
              'print(b["bundle_sha256"] if b else "none")')
    result = subprocess.run([str(origin/'.venv/bin/python'),'-c',script,str(Path(data_root).resolve()),target_date],
        text=True,check=True,capture_output=True,timeout=120,cwd=origin,env={**os.environ,'PYTHONPATH':str(origin)})
    ident = result.stdout.strip()
    if not re.fullmatch('[0-9a-f]{64}',ident):
        raise ValueError('v6_code_refresh_activation_parent_missing')
    bundle = N._read(N.root(Path(data_root))/'generations'/(ident+'.json'))
    N.validate(bundle,target_date=bundle['target_date'])
    if bundle['bundle_sha256'] != ident:
        raise ValueError('v6_code_refresh_activation_parent_changed')
    return bundle


def stage_code_refresh(data_root, target_date, *, expected_bundle_sha256,
                       origin_root, activation_parent_origin_root, activation_parent_origin_commit, release_commit,
                       reason, confirm, now=None):
    """Rebind an issued next-session candidate; no activation or reselection.

    The current pointer, dates, memberships, thresholds, auxiliary evidence and
    registration authority are unchanged. A sealed successor replaces only
    the exact candidate after both immutable predecessors have been verified.
    """
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    from src.engine.infrastructure.runtime_release_router import _release_identity
    if (confirm != CODE_REFRESH_AUTHORITY or not str(reason).strip()
            or not re.fullmatch('[0-9a-f]{40}',str(release_commit))
            or not re.fullmatch('[0-9a-f]{40}',str(activation_parent_origin_commit))):
        raise ValueError('v6_code_refresh_authority_required')
    clock = now or datetime.now(K.KST)
    if clock.tzinfo is None or target_date <= clock.astimezone(K.KST).date().isoformat():
        raise ValueError('v6_code_refresh_future_candidate_required')
    data_root = Path(data_root).absolute(); root = N.root(data_root)
    code_root = Path(__file__).resolve().parents[3]
    identity = _release_identity(data_root.resolve().parent,str(code_root/'src'),
                                 'code_refresh_candidate',release_commit)
    if identity['source_integrity'] != 'git_commit_and_clean_runtime_source':
        raise ValueError('v6_code_refresh_release_unattested')
    with (root/'publisher.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        path = root/'candidates'/('policy_'+target_date+'.json')
        original = N._read(path); f = original['continuous_reversal']
        N.validate(original,target_date=target_date)
        if (original['bundle_sha256'] != expected_bundle_sha256 or f['schema'] != SCHEMA
                or f['effective_mode'] != 'next_session'):
            raise ValueError('v6_code_refresh_candidate_cas_failed')
        current = N._read(root/'current.json')
        if current['bundle_sha256'] != f['parent_bundle_sha256']:
            raise ValueError('v6_code_refresh_activation_parent_changed')
        current_pins = {Path(m.__file__).name:file_hash(m.__file__) for m in contract_modules()}
        if f['release_commit'] == release_commit and f['contract_file_sha256'] == current_pins:
            N._validate_bundle_sources(original,data_root)
            return original
        N._validate_bundle_sources(original,data_root,historical_code_root=origin_root)
        active = _attested_activation_parent(data_root,target_date,origin_root=activation_parent_origin_root,
                                             origin_commit=activation_parent_origin_commit)
        if active is None or active['bundle_sha256'] != current['bundle_sha256']:
            raise ValueError('v6_code_refresh_activation_parent_changed')
        proof = dict(schema='main_identical_policy_code_refresh_v1',authority=confirm,
            source_bundle_sha256=expected_bundle_sha256,origin_root=str(Path(origin_root).resolve()),
            activation_parent_origin_root=str(Path(activation_parent_origin_root).resolve()),
            activation_parent_origin_commit=activation_parent_origin_commit,
            reason=reason,policy_reselected=False,provider_called=False)
        # Keep the attested original generations addressable after the pointer
        # moves. Do not modify the active pointer or any original source bytes.
        generation = root/'generations'/(original['bundle_sha256']+'.json')
        if not generation.is_file() or N._read(generation) != original:
            raise ValueError('v6_code_refresh_original_generation_missing')
        successor = _write_refreshed_bundle(original,data_root,release_commit=release_commit,proof=proof)
        if N._read(root/'current.json') != current or N._read(path) != original:
            raise ValueError('v6_code_refresh_parent_changed_during_stage')
        N._atomic_write_json(path,successor)
        return successor


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
        raise ValueError('v6_snapshot_scope_conflict')
    selected = {b['branch_id'] for b in cell['payload']['branches']}
    if not set(event['branch_signals']) <= selected:
        raise ValueError('v6_snapshot_unregistered_policy')
    for bid, signal in event['branch_signals'].items():
        if C.matches(bid,signal,signal.get('branch_features',{})) is not True:
            raise ValueError('v6_signal_definition_invalid')
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


def stage(data_root, day, publication, machine, auxiliary, *, target_date, release_commit,effective_mode='next_session',registration_activation=None):
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    if (effective_mode not in {'next_session','intraday'} or day > publication
            or target_date!=(publication if effective_mode=='intraday' else N.next_target(publication))):
        raise ValueError('v6_target_date_invalid')
    root = N.root(Path(data_root)); root.mkdir(parents=True,exist_ok=True)
    with (root/'publisher.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        parent = N.load_effective(data_root=Path(data_root),target_date=publication)
        if not parent or machine['parent_bundle_sha256'] != parent['bundle_sha256']:
            raise ValueError('v6_parent_cas_failed')
        for report in (machine,auxiliary):
            if (report['artifact_content_sha256'] != digest({k:v for k,v in report.items() if k!='artifact_content_sha256'})
                    or report['status'] not in {'completed','completed_with_scope_carry'}
                    or report['source_date'] != day or report['publication_date'] != publication):
                raise ValueError('v6_report_preflight_invalid')
        if auxiliary['machine_report_sha256'] != machine['artifact_content_sha256']:
            raise ValueError('v6_auxiliary_parent_invalid')
        hashes = {}
        for name, report in (('machine',machine),('auxiliary',auxiliary)):
            path = root/'sources'/('reversal-'+report['artifact_content_sha256']+'.json')
            N._atomic_write_json(path,report); hashes[name] = file_hash(path)
        native = parent['continuous_reversal'].get('native_parent_bundle', parent)
        f = dict(schema=SCHEMA, kernel_version=K.VERSION, registry_sha256=C.SHA256,
            branch_definition_sha256=C.SHA256, auxiliary_version=A.VERSION, label_contract=C.LABEL,
            source_date=day, publication_date=publication, effective_date=target_date, effective_mode=effective_mode,
            selection_metric='cumulative_raw_win_fraction', release_commit=release_commit,
            parent_bundle_sha256=parent['bundle_sha256'], native_parent_bundle=native,
            operating_manifest=machine['operating_manifest'], execution_code_sha256=machine['execution_code_sha256'],
            contract_file_sha256={Path(m.__file__).name:file_hash(m.__file__) for m in contract_modules()},
            machine_cells={c['key']:c for c in machine['cells']}, auxiliary_cells={c['key']:c for c in auxiliary['cells']},
            machine_report_sha256=machine['artifact_content_sha256'], auxiliary_report_sha256=auxiliary['artifact_content_sha256'],
            report_file_sha256=hashes, source_manifest_sha256=machine['source_manifest_sha256'],
            hard_guards_unchanged=True, actual_order_submitted=False)
        if effective_mode=='intraday':f['registration_activation']=registration_activation
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
        N._atomic_write_json(root/('intraday_candidates' if effective_mode=='intraday' else 'candidates')/('policy_'+target_date+'.json'),bundle)
        return bundle


def activate(data_root,target_date,*,now=None,intraday_evidence=None):
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    from src.engine.infrastructure.runtime_release_router import selected_release
    clock = now or datetime.now(K.KST)
    if clock.astimezone(K.KST).date().isoformat() != target_date:
        raise ValueError('v6_activation_not_today')
    root = N.root(Path(data_root))
    with (root/'publisher.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        bundle = N._read(root/('intraday_candidates' if intraday_evidence is not None else 'candidates')/('policy_'+target_date+'.json'))
        N.validate(bundle,target_date=target_date); validate_sources(bundle,data_root)
        selected,commit = selected_release(Path(data_root).resolve().parent)
        f = bundle['continuous_reversal']
        if commit != f['release_commit']:
            raise ValueError('v6_activation_release_mismatch')
        if f['effective_mode']=='intraday':
            from src.engine.automation.intraday_release_handoff import _identity
            e=intraday_evidence or {}
            if (e.get('schema')!='intraday_main_policy_code_pid_v1' or e.get('target_date')!=target_date
                    or e.get('release_commit')!=commit or not e.get('pid_identity')
                    or _identity(e['pid_identity']['pid'])!=e['pid_identity'] or e['pid_identity']['cwd']!=str(selected/'src')
                    or file_hash(e['consumed_path'])!=e.get('consumed_sha256')):
                raise ValueError('v6_intraday_code_pid_not_verified')
        try:
            parent = N.load_effective(data_root=Path(data_root),target_date=target_date)
        except ValueError as exc:
            proof = f.get('code_refresh')
            if not proof or not str(exc).startswith(('v4_contract_code_changed:', 'v5_contract_code_changed:', 'v6_contract_code_changed:')):
                raise
            # Only an explicitly staged identical-policy successor can cross
            # this boundary. Runtime loads never use historical validation.
            _validate_code_refresh(bundle, data_root)
            parent = _attested_activation_parent(Path(data_root),target_date,
                origin_root=proof['activation_parent_origin_root'],origin_commit=proof['activation_parent_origin_commit'])
        if parent and parent['bundle_sha256'] == bundle['bundle_sha256']:
            return dict(status='already_active',bundle_sha256=bundle['bundle_sha256'])
        if not parent or parent['bundle_sha256'] != f['parent_bundle_sha256']:
            raise ValueError('v6_activation_parent_cas_failed')
        receipt = dict(schema='continuous_reversal_current_v6',bundle_sha256=bundle['bundle_sha256'],
            previous_bundle_sha256=parent['bundle_sha256'],effective_from=clock.isoformat(),
            effective_date=target_date,family_sha256=f['family_sha256'],release_commit=commit)
        if intraday_evidence is not None:receipt['intraday_code_pid_evidence']=intraday_evidence
        receipt['receipt_sha256'] = digest(receipt)
        N._atomic_write_json(root/'activations'/target_date/(receipt['receipt_sha256']+'.json'),receipt)
        N._atomic_write_json(root/'current.json',receipt)
        if N.load_effective(data_root=Path(data_root),target_date=target_date)['bundle_sha256'] != bundle['bundle_sha256']:
            raise ValueError('v6_activation_readback_failed')
        return dict(status='activated',**receipt)


def validate_active_claim(policy, active, *, now):
    """Validate the current envelope while preserving equivalent scope claims."""
    from src.engine.scalping import reversal_current_backend as D
    from src.utils.constants import DATA_DIR
    if not active or active.get('continuous_reversal',{}).get('schema') != SCHEMA:
        raise ValueError('reversal_policy_changed_after_provider')
    f = active['continuous_reversal']; validate_family(f)
    a = policy['continuous_reversal_assessment']
    cell = f['machine_cells'][a['cell_key']]['routes'][a['route']]
    if cell['scope_execution_hash'] != a['scope_execution_hash'] or cell['backend'] != 'union_v6':
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
        raise ValueError('v6_consumption_release_mismatch')
    active=N.load_effective(data_root=Path(data_root),target_date=day)
    if not active or active['bundle_sha256']!=bundle['bundle_sha256']:
        raise ValueError('v6_consumption_generation_changed')
    path=N.root(Path(data_root))/'consumed'/day/(str(os.getpid())+'.json')
    if path.exists() and N._read(path).get('bundle_sha256')==bundle['bundle_sha256']:
        return
    count=sum(f['machine_cells'][k]['routes'][r]['backend']=='union_v6' for k,r in scopes())
    receipt=dict(schema='continuous_reversal_pid_consumption_v6',bundle_sha256=bundle['bundle_sha256'],
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
        raise ValueError('v6_observation_identity_invalid')
    expected=dict(family_sha256=f['family_sha256'],bundle_sha256=bundle['bundle_sha256'],
        source_date=f['source_date'],publication_date=f['publication_date'],effective_date=f['effective_date'],
        machine_component_sha256=digest(f['machine_cells']),auxiliary_component_sha256=digest(f['auxiliary_cells']),
        event_id=a.get('event_id'),cell_key=a.get('cell_key'),rule=a.get('rule'),pid=receipt.get('pid'),
        process_start_ticks=receipt.get('process_start_ticks'),captured_at=observation['captured_at'],
        exact_payload_sha256=hashlib.sha256(_json_bytes(raw)).hexdigest(),assessment_sha256=hashlib.sha256(_json_bytes(a)).hexdigest())
    if any(native.get(k)!=v for k,v in expected.items()):raise ValueError('v6_consumption_receipt_mismatch')
    clock=native.get('snapshot_read_at');observed=raw.get('entry_machine_input_as_of')
    if (type(clock) not in (int,float) or type(observed) not in (int,float)
            or not math.isfinite(clock) or not observed<=clock<=captured.timestamp()):
        raise ValueError('v6_observation_clock_invalid')
    event=a.get('event')
    if event is None:
        if a.get('action')!='BLOCK' or a.get('reason')!='no_current_operating_signal':raise ValueError('v6_nonentry_receipt_invalid')
        return {},dict(policy_sha256=f['execution_manifest_hash'],leaf='NO_CURRENT_OPERATING_SIGNAL')
    key=C.cell_key(str(context['stock_code']),context['session_bucket'],event['confirmation_price']);route=event['venue']
    cell=f['machine_cells'][key]['routes'][route]
    if event['symbol']!=str(context['stock_code']) or event['market']!=K.market_bucket(context['session_bucket']) or not 0<=clock-event['epoch']<=5:
        raise ValueError('v6_event_scope_or_clock_invalid')
    request=source.get('auxiliary_request') or {}
    if a.get('action')=='ENTER_NOW' and any(digest(request.get(k))!=native.get(v) for k,v in
            [('input','input_sha256'),('prompt','prompt_sha256'),('response_schema','response_schema_sha256')]):
        raise ValueError('v6_auxiliary_request_hash_mismatch')
    if cell['backend']=='registered_v4':
        replay,_,_,_=V4.assess(f['native_parent_bundle']['continuous_reversal'],(event,None),symbol=event['symbol'],session=event['market'],build_request=False)
        for field in ('action','reason','policy_version','cell_key','route','primary_branch','matched_branches','auxiliary_arm','machine_component_sha256'):
            if a.get(field)!=replay.get(field):raise ValueError('v6_native_pair_receipt_mismatch:'+field)
        if a.get('action')=='ENTER_NOW':
            from src.engine.scalping import reversal_path_auxiliary as OLD
            arm=a['auxiliary_arm'];phase=a['decision_phase'];inp=request['input']
            if request['prompt']!=OLD.prompt(phase,arm):raise ValueError('v6_native_prompt_mismatch')
            if phase in OLD.PHASES:OLD.validate_input_signal(inp,a['auxiliary_event'])
    else:
        if a.get('policy_version')!=SCHEMA or a.get('scope_execution_hash')!=cell['scope_execution_hash']:
            raise ValueError('v6_scope_execution_receipt_mismatch')
        ids=set(event['branch_signals']);selected={b['branch_id'] for b in cell['payload']['branches']}
        if not ids or not ids<=selected or any(C.matches(b,s,s['branch_features']) is not True for b,s in event['branch_signals'].items()):
            raise ValueError('v6_unregistered_or_invalid_signal')
        refs=sorted(b+':'+A.definition_hash(b) for b in ids)
        inp=request['input'];arm=f['auxiliary_cells'][key]['routes'][route]['payload']['arm']
        if (a.get('matched_policy_refs')!=refs or a.get('opportunity_key')!=A.opportunity(event)
                or inp.get('schema')!=A.VERSION or [s['ref'] for s in inp['signals']]!=refs
                or a.get('signal_set_hash')!=digest(inp['signals']) or native.get('arm')!=arm
                or request['prompt']!=A.PROMPT+A.ARM_SUFFIXES[arm] or request['response_schema']!=A.response_schema(inp)
                or inp['common_context']['opportunity_key']!=A.opportunity(event)):
            raise ValueError('v6_union_request_receipt_mismatch')
        from src.engine.scalping import reversal_extended_auxiliary as T
        for bid,signal in event['branch_signals'].items():
            if bid not in C.NEW_DEFINITIONS:continue
            T.validate_signal(signal)
            projected=next(s for s in inp['signals'] if s['policy_id']==bid)
            typed=dict(schema=T.VERSION,observed_signal=projected['observed_signal'],signal_kind=projected['phase'],
                source_item=signal['source_item'],as_of=K.iso(signal['epoch']),observation_phase=projected['observation_phase'],
                entry_setup_evidence_v1=dict(facts=projected['facts']))
            T.validate_input_signal(typed,signal)
    return cell['payload'],dict(policy_sha256=cell['scope_execution_hash'],leaf=key+'|'+route,
                                operating_backend=cell['backend'],new_scope_consumption=cell['backend']=='union_v6')
