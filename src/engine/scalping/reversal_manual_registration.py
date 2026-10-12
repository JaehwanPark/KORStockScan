"""Operator-issued residual pattern intake; no discovery or provider calls.

Scalping owns membership. Frozen research, native parity and the exact incumbent
are retained independently of later comparisons or actual order economics.
"""
from __future__ import annotations

import copy
import fcntl
import json
from pathlib import Path
from src.engine.scalping import reversal_extended_catalog as C
from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.scalping import mechanistic_entry_runtime_policy as N

AUTHORITY = 'APPROVED_RESIDUAL_PATTERN_IMPLEMENTATION_REGISTRATION_20261013'
PROPOSAL_SHA256 = 'f31188ad6ff02803c5fb8dbb990e7f297d959ae0364924e4363d6271e7c1d1d1'


def pending_path(data_root):
    return N.root(Path(data_root))/'residual-registration.json'


def approved_scopes():
    scopes = {}
    for bid, d in C.ADDITIONAL_DEFINITIONS.items():
        sid = '|'.join((d['symbol_group'], d['market'], d['price_band'], d['route']))
        scopes.setdefault(sid, dict(add=[], remove=[]))['add'].append(bid)
    for scope in scopes.values():
        scope['add'].sort()
    return scopes


def validate_request(request):
    if (request.get('artifact_content_sha256') != P.seal(request)['artifact_content_sha256']
            or request.get('schema') != 'main_residual_registration_request_v1'
            or request.get('operator_receipt') != AUTHORITY or request.get('kind') != 'ADD'
            or request.get('research_batch_sha256') != PROPOSAL_SHA256
            or request.get('scopes') != approved_scopes()
            or request.get('definition_hashes') != {b:P.digest(d) for b,d in C.ADDITIONAL_DEFINITIONS.items()}
            or request.get('registry_sha256') != C.SUCCESSOR_SHA256
            or request.get('comparison_result_required') is not False):
        raise ValueError('residual_registration_authority_or_definition_changed')
    for receipt in request.get('source_receipts', []):
        if P.file_hash(receipt['path']) != receipt['sha256']:
            raise ValueError('residual_registration_evidence_changed')
    if not request.get('source_receipts'):
        raise ValueError('residual_registration_evidence_missing')
    return request


def pending(data_root, parent, target_date):
    path = pending_path(data_root)
    if not path.exists():
        return None
    request = validate_request(N._read(path))
    scopes = parent['continuous_reversal'].get('operating_manifest', {}).get('scopes', {})
    if all(set(change['add']) <= set(scopes.get(sid, [])) for sid,change in request['scopes'].items()):
        return None
    if request['parent_bundle_sha256'] != parent['bundle_sha256'] or request['target_date'] != target_date:
        raise ValueError('residual_registration_parent_or_target_changed')
    return request


def load_offline_parent(data_root, publication):
    """Attest a closed-source incumbent only for this explicit ADD publication."""
    from src.engine.scalping import continuous_reversal_policy_v6 as V
    request = validate_request(N._read(pending_path(data_root)))
    if publication != request['publication_date']:
        raise ValueError('residual_offline_parent_publication_mismatch')
    proof = request['activation_parent_origin']
    parent = V._attested_activation_parent(data_root, publication,
        origin_root=proof['root'], origin_commit=proof['commit'])
    if parent['bundle_sha256'] != request['parent_bundle_sha256']:
        raise ValueError('residual_offline_parent_cas_failed')
    return parent


def intake(data_root, proposal_path, parity_path, *, parent, publication,
           origin_root, origin_commit, confirm):
    from src.engine.scalping import continuous_reversal_policy_v6 as V
    if confirm != AUTHORITY:
        raise ValueError('residual_explicit_registration_authority_required')
    proposal_path, parity_path = Path(proposal_path), Path(parity_path)
    proposals = json.loads(proposal_path.read_text())
    parity = json.loads(parity_path.read_text())
    if (proposals.get('proposal_count') != 6 or len(proposals.get('proposals', [])) != 6
            or P.file_hash(proposal_path) != PROPOSAL_SHA256
            or proposals.get('parent_bundle_sha256') != parent['bundle_sha256']
            or parity.get('status') != 'pass' or parity.get('mismatches') != 0
            or parity.get('proposal_sha256') != P.file_hash(proposal_path)
            or parity.get('registry_sha256') != C.SUCCESSOR_SHA256
            or set(parity.get('branch_ids', [])) != set(C.ADDITIONAL_DEFINITIONS)
            or set(parity.get('portfolios', {})) != set(approved_scopes())):
        raise ValueError('residual_research_or_native_parity_invalid')
    for row in proposals['proposals']:
        sid = row['scope']; root = row['definition']['root']; filters = row['definition']['filters']
        matches = [b for b in approved_scopes().get(sid, {}).get('add', [])
                   if C.definition(b)['root_confirmation'] == root and C.definition(b)['filters'] == filters]
        if len(matches) != 1:
            raise ValueError('residual_frozen_definition_mismatch')
    actual = V._attested_activation_parent(data_root, publication,
        origin_root=origin_root, origin_commit=origin_commit)
    if actual['bundle_sha256'] != parent['bundle_sha256']:
        raise ValueError('residual_intake_parent_cas_failed')
    receipts=[]
    frozen=Path(data_root)/'report/continuous_reversal_operating/registrations'/P.file_hash(proposal_path)
    frozen.mkdir(parents=True, exist_ok=True)
    for path in (proposal_path, parity_path):
        sha=P.file_hash(path); destination=frozen/(sha+'.json')
        if destination.exists() and P.file_hash(destination) != sha:
            raise ValueError('residual_registration_archive_conflict')
        if not destination.exists():
            with destination.open('xb') as handle:handle.write(path.read_bytes())
        receipts.append(dict(path=str(destination.resolve()),sha256=sha))
    from src.engine.scalping import continuous_reversal_operating_postclose as O
    original_reports={}
    for name in ('machine-comparison','auxiliary'):
        path=O.directory(data_root,publication)/(name+'.json')
        value=N._read(path)
        if (value.get('artifact_content_sha256')!=P.seal(value)['artifact_content_sha256']
                or value.get('source_date')!=publication):
            raise ValueError('residual_original_postclose_report_invalid')
        sha=P.file_hash(path);destination=frozen/(sha+'.json')
        if not destination.exists():
            with destination.open('xb') as handle:handle.write(path.read_bytes())
        if P.file_hash(destination)!=sha:raise ValueError('residual_registration_archive_conflict')
        receipt=dict(path=str(destination.resolve()),sha256=sha)
        receipts.append(receipt);original_reports[name]=receipt
    for receipt in parity['source_receipts']:
        path=Path(receipt['path']);sha=receipt['sha256']
        if P.file_hash(path) != sha:raise ValueError('residual_parity_source_changed')
        if path.stat().st_size <= 64*1024*1024 and 'tmp' in path.parts:
            destination=frozen/sha
            if not destination.exists():
                with destination.open('xb') as handle:handle.write(path.read_bytes())
            if P.file_hash(destination) != sha:raise ValueError('residual_registration_archive_conflict')
            path=destination
        receipts.append(dict(path=str(path.resolve()),sha256=sha))
    for module in (C, __import__('src.engine.scalping.reversal_extended_state', fromlist=['*']),
                   __import__('src.engine.scalping.reversal_extended_auxiliary', fromlist=['*'])):
        expected=parity['code_hashes'].get(Path(module.__file__).name)
        if expected != P.file_hash(module.__file__):
            raise ValueError('residual_parity_code_changed')
    request=P.seal(dict(schema='main_residual_registration_request_v1',kind='ADD',
        parent_bundle_sha256=parent['bundle_sha256'],operator_receipt=confirm,
        research_batch_sha256=P.file_hash(proposal_path),registry_sha256=C.SUCCESSOR_SHA256,
        scopes=approved_scopes(),definition_hashes={b:P.digest(d) for b,d in C.ADDITIONAL_DEFINITIONS.items()},
        publication_date=publication,target_date=N.next_target(publication),source_receipts=receipts,
        original_reports=original_reports,
        activation_parent_origin=dict(root=str(Path(origin_root).resolve()),commit=origin_commit),
        registration_state='registered',activation_state='pending_next_session_publication',
        comparison_result_required=False,actual_order_submitted=False))
    validate_request(request)
    with (N.root(Path(data_root))/'publisher.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        actual=V._attested_activation_parent(data_root, publication,
            origin_root=origin_root,origin_commit=origin_commit)
        if actual['bundle_sha256'] != parent['bundle_sha256']:
            raise ValueError('residual_intake_parent_changed_during_freeze')
        path=pending_path(data_root)
        if path.exists() and N._read(path) != request:
            raise ValueError('residual_registration_request_conflict')
        N._atomic_write_json(path, request)
    return request


def run_postclose(data_root, day, publication, mode):
    """Native explicit ADD stages. Frozen comparison work is not reset or spent."""
    from src.engine.scalping import continuous_reversal_policy_v6 as V
    from src.engine.scalping import continuous_reversal_operating_postclose as O
    from src.engine.scalping import reversal_extended_registration as ER
    request=validate_request(N._read(pending_path(data_root)))
    if day!=publication or publication!=request['publication_date']:
        raise ValueError('residual_registration_source_date_changed')
    parent=load_offline_parent(data_root,publication)
    change=pending(data_root,parent,N.next_target(publication))
    if change is None:raise ValueError('residual_registration_already_consumed')
    if mode not in {'machine','auxiliary'}:
        return dict(status='not_called_registration_no_new_provider_requests',
            provider_calls=0,original_comparison_requests_preserved=True,actual_order_submitted=False)
    original=N._read(request['original_reports']['machine-comparison']['path'])
    if original.get('parent_bundle_sha256')!=parent['bundle_sha256']:
        raise ValueError('residual_original_machine_parent_changed')
    manifest=V.detector_manifest(parent,effective_date=change['target_date'],changes=change)
    machine=P.seal(dict(original,operating_manifest=manifest,registration_change=change,
        selection_basis='cumulative_raw_win_fraction',
        execution_code_sha256=P.digest({Path(m.__file__).name:P.file_hash(m.__file__) for m in V.contract_modules()}),
        policy_schema=V.SCHEMA,registration_state='registered',adoption_basis='operator_designated',
        membership_status='registered',comparison_complete=False,comparison_state='incomplete',scope_pending=[],
        manual_registration_basis='frozen_native_parity_and_exact_scope_OR',
        original_comparison_generation=original['artifact_content_sha256'],
        source_receipts=original.get('source_receipts',[])+change['source_receipts']))
    out=O.directory(data_root,day)
    if mode=='machine':
        P.write(out/'machine-comparison.json',machine)
        isolated=Path(data_root)/'report/continuous_reversal_operating/registrations'/change['research_batch_sha256']/'typed-publication'
        ER.initial_reports(data_root,day,publication,parent,machine,publish_policy=False,output_directory=isolated)
        issued=N._read(isolated/'machine.json')
        P.write(out/'machine.json',issued);P.write(P.directory(data_root,day)/'machine.json',issued)
        standard=Path(data_root)/'report/ai_decision_action_outcome_calibration'
        P.write(standard/f'winrate_policy_{day}.json',issued)
        P.write(standard/f'winrate_policy_terminal_{day}.json',P.seal(dict(schema=O.SCHEMA,
            source_date=day,target_date=day,status='completed',report_sha256=issued['artifact_content_sha256'],
            selection_basis=issued['selection_basis'],disposition='continuous_reversal_selected',
            policy_sha256=manifest['detector_manifest_hash'],staged=dict(status='machine_component_prepared'),**P.AUTH)))
        return issued
    issued=N._read(out/'machine.json')
    if issued.get('registration_change')!=change or issued.get('operating_manifest')!=manifest:
        raise ValueError('residual_registration_machine_stage_changed')
    isolated=Path(data_root)/'report/continuous_reversal_operating/registrations'/change['research_batch_sha256']/'typed-publication'
    auxiliary=N._read(isolated/'auxiliary.json')
    if auxiliary['machine_report_sha256']!=issued['artifact_content_sha256']:
        raise ValueError('residual_registration_auxiliary_binding_changed')
    prior=N._read(change['original_reports']['auxiliary']['path'])
    auxiliary=P.seal(dict(auxiliary,
        prior_comparison_generation=dict(receipt=change['original_reports']['auxiliary'],
            owner_request_census=prior.get('owner_request_census'),comparison_state=prior.get('comparison_state'),
            interpretation='preserved_original_request_generation_not_new_comparison'),
        new_provider_requests=0,original_comparison_requests_preserved=True))
    # Reports are published under the normal source-date owner. Actual provider
    # results and the shared campaign store remain immutable history.
    P.write(out/'auxiliary.json',auxiliary);P.write(P.directory(data_root,day)/'auxiliary.json',auxiliary)
    import subprocess
    commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    bundle=V.stage(data_root,day,publication,issued,auxiliary,target_date=change['target_date'],release_commit=commit)
    P.write(Path(data_root)/'report/ai_entry_setup_paired_replay_batch'/f'compact_auxiliary_paired_economic_{day}.json',
        P.seal(dict(auxiliary,staged=dict(status='prepared',bundle_sha256=bundle['bundle_sha256'],target_date=bundle['target_date']))))
    return auxiliary
