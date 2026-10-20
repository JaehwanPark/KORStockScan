"""Exact reviewed code compatibility for an already-active Main policy.

Scalping validates policy sources; deployment owns the dated receipt. This
never selects a policy or changes thresholds, memberships, or order authority.
"""
from __future__ import annotations
import json
import subprocess
import os
from datetime import datetime, timedelta
from pathlib import Path
from src.engine.scalping import continuous_reversal_postclose as P

SCHEMA='main_active_policy_code_handoff_v1'
AUTHORITY='APPROVED_REVIEWED_ACTIVE_POLICY_CODE_HANDOFF'


def code_hashes():
    from src.engine.scalping.continuous_reversal_policy_v6 import contract_modules
    return {str(Path(m.__file__).resolve()):P.file_hash(m.__file__) for m in contract_modules()} | {
        str(Path(__file__).resolve()):P.file_hash(__file__)}


def path(data_root,day,commit,bundle_sha):
    return Path(data_root)/'runtime/mechanistic_entry_policy/code_handoffs'/day/commit/(bundle_sha+'.json')


def validate_receipt(receipt, *, day, commit, root, bundle_sha, pointer_sha):
    if (receipt.get('schema')!=SCHEMA or receipt.get('authority')!=AUTHORITY
            or receipt.get('artifact_content_sha256')!=P.seal(receipt)['artifact_content_sha256']
            or receipt.get('target_date')!=day or receipt.get('release_commit')!=commit
            or receipt.get('release_root')!=str(root) or receipt.get('bundle_sha256')!=bundle_sha
            or receipt.get('current_pointer_sha256')!=pointer_sha
            or receipt.get('policy_reselected') is not False
            or receipt.get('provider_called') is not False
            or not receipt.get('source_hashes') or not receipt.get('code_hashes')):
        raise ValueError('active_policy_code_handoff_invalid')
    return receipt


def _validated_origin_receipt(data_root, day, origin_root, origin_commit, bundle_sha, pointer_sha):
    """Reuse native sealed ancestry under the approved pipeline-reference scope."""
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    source = path(data_root, day, origin_commit, bundle_sha)
    if not source.exists():
        return None
    receipt = N._read(source)
    validate_receipt(receipt, day=day, commit=origin_commit, root=origin_root,
                     bundle_sha=bundle_sha, pointer_sha=pointer_sha)
    for name, expected in {**receipt['source_hashes'], **receipt['code_hashes']}.items():
        if not N.source_receipt_matches(dict(path=name, sha256=expected), data_root=data_root):
            raise ValueError('active_policy_origin_receipt_source_changed:' + name)
    refs = {**receipt['source_hashes'], **receipt['code_hashes']}
    refs[str(source.resolve())] = P.file_hash(source)
    return dict(bundle_sha256=bundle_sha, source_hashes=refs,
                verification_basis='native_sealed_code_handoff_pipeline_references')


def validate(bundle,data_root,*,original_error):
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    from src.engine.infrastructure.runtime_release_router import selected_release
    day=datetime.now(P.KST).date().isoformat();root,commit=selected_release(Path(data_root).resolve().parent)
    # Include the selector in the native dependency cache; a later selection
    # cannot keep the preceding compatibility result alive.
    selection=N._read(Path(data_root)/'runtime/runtime_release_selection.json')
    if selection.get('git_commit')!=commit or selection.get('release_root')!=str(root):
        raise ValueError('active_policy_code_selection_changed')
    if not path(data_root,day,commit,bundle['bundle_sha256']).exists():
        raise original_error
    selected_root, selected_commit = root, commit
    review = None
    if root != Path(__file__).resolve().parents[3]:
        from src.engine.automation import intraday_release_handoff as handoff
        review = handoff._PREDECESSOR_REVIEW.get()
        if (not review or review['day'] != day or review['root'] != root
                or review['commit'] != commit
                or review['code_root'] != Path(__file__).resolve().parents[3]
                or review['identity'].get('cwd') != str(root/'src')
                or (handoff.closed_consumption_observation(day) != review['closed_observation']
                    if review.get('closed_observation') else handoff._identity(review['identity']['pid']) != review['identity'])):
            raise ValueError('active_policy_code_reader_root_changed')
        root, commit = review['code_root'], review['code_commit']
    receipt_path=path(data_root,day,commit,bundle['bundle_sha256'])
    # Preserve the native reason for unregistered code and tomorrow's parent
    # transition. There is no generic historical-loader fallback.
    if not receipt_path.exists():raise original_error
    if root!=Path(__file__).resolve().parents[3]:raise ValueError('active_policy_code_reader_root_changed')
    pointer=N.root(Path(data_root))/'current.json'
    pointer_sha=N._source_hash(str(pointer),N._signature(pointer))
    r=N._read(receipt_path)
    validate_receipt(r,day=day,commit=commit,root=root,bundle_sha=bundle['bundle_sha256'],pointer_sha=pointer_sha)
    if review is not None and (r.get('origin_root') != str(selected_root)
            or r.get('origin_commit') != selected_commit
            or r.get('origin_selection_sha256') != P.file_hash(Path(data_root)/'runtime/runtime_release_selection.json')
            or r.get('actual_pid_consumed') is not False):
        raise ValueError('active_policy_predecessor_review_unbound')
    current={str(Path(m.__file__).resolve()) for m in __import__(
        'src.engine.scalping.continuous_reversal_policy_v6',fromlist=['contract_modules']).contract_modules()} | {str(Path(__file__).resolve())}
    if set(r['code_hashes'])!=current:raise ValueError('active_policy_code_membership_changed')
    for name,expected in {**r['source_hashes'],**r['code_hashes']}.items():
        if not N.source_receipt_matches(dict(path=name,sha256=expected),data_root=data_root):
            raise ValueError('active_policy_code_handoff_source_changed:'+name)
    if N._read(pointer)['bundle_sha256']!=bundle['bundle_sha256']:
        raise ValueError('active_policy_code_handoff_pointer_changed')
    if review is not None and (selected_release(Path(data_root).resolve().parent) != (selected_root, selected_commit)
            or N._read(Path(data_root)/'runtime/runtime_release_selection.json') != selection
            or (handoff.closed_consumption_observation(day) != review['closed_observation']
                if review.get('closed_observation') else handoff._identity(review['identity']['pid']) != review['identity'])):
        raise ValueError('active_policy_predecessor_review_changed')
    return bundle


_ORIGIN_SCRIPT = r'''
import sys,json,hashlib
from pathlib import Path
from src.engine.scalping import mechanistic_entry_runtime_policy as N
root=Path(sys.argv[1]).resolve();day=sys.argv[2];opened={}
def audit(event,args):
    if event!='open' or not isinstance(args[0],str):return
    p=Path(args[0]).absolute()
    if root not in p.parents or not p.is_file():return
    st=p.stat();opened.setdefault(str(p),(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns))
sys.addaudithook(audit)
try:
    b=N._load_current_uncached(root,day)
except ValueError as exc:
    # A dated code handoff can expire while the next day's issued code-refresh
    # candidate already attests the same active parent in its original release.
    # Use that immutable, fully validated ancestry only for this source handoff.
    if not str(exc).startswith('v4_contract_code_changed:'):
        raise
    from src.engine.scalping import continuous_reversal_policy_v6 as V
    candidate_path=N.root(root)/'candidates'/('policy_'+day+'.json')
    candidate=N._read(candidate_path)
    N.validate(candidate,target_date=day)
    f=candidate.get('continuous_reversal') or {}
    proof=f.get('code_refresh') or {}
    if (f.get('schema')!=V.SCHEMA or f.get('effective_mode')!='next_session'
            or f.get('effective_date')!=day or f.get('publication_date','')>=day
            or proof.get('authority')!=V.CODE_REFRESH_AUTHORITY):
        raise ValueError('active_policy_code_handoff_rollover_candidate_invalid')
    frozen=N._read(N.root(root)/'generations'/(candidate['bundle_sha256']+'.json'))
    if frozen!=candidate:
        raise ValueError('active_policy_code_handoff_rollover_generation_changed')
    N._validate_bundle_sources(frozen,root)
    b=V._attested_activation_parent(root,day,
        origin_root=proof['activation_parent_origin_root'],
        origin_commit=proof['activation_parent_origin_commit'])
    current=N._read(N.root(root)/'current.json')
    if b is None or b['bundle_sha256']!=current['bundle_sha256'] or b['bundle_sha256']!=f['parent_bundle_sha256']:
        raise ValueError('active_policy_code_handoff_rollover_parent_changed')
    # The mutable preparation alias is observed, not an immutable policy input.
    # The identical frozen generation and its full source receipts remain bound.
    opened.pop(str(candidate_path.absolute()),None)
refs={}
for name,identity in list(opened.items()):
    p=Path(name);st=p.stat()
    if identity!=(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns):raise ValueError('origin_source_changed_during_validation')
    refs[name]=N._source_hash(name,N._signature(p))
print(json.dumps(dict(bundle_sha256=b['bundle_sha256'],source_hashes=refs)))
'''


def _stopped_origin_receipt(data_root, day, origin_root, origin_commit, bundle_sha, pointer_sha):
    """Recover only the native ancestry of an exact failed selected transition."""
    from src.engine.automation import ordered_intraday_deploy as D
    workspace = Path(data_root).resolve().parent
    selected, selected_raw, _ = D._owned_metadata(Path(data_root)/'runtime/runtime_release_selection.json')
    failed_path = Path(data_root)/'runtime/release_transitions'/day/origin_commit/'status.json'
    failed, failed_raw, _ = D._owned_metadata(failed_path)
    prior_path = failed_path.with_name('selection-before.json')
    prior, prior_raw, _ = D._owned_metadata(prior_path)
    hold, hold_raw, _ = D._owned_metadata(Path(data_root)/'runtime/operator_startup_hold.json')
    identity = failed.get('predecessor_identity')
    expected_hold = dict(schema='ordered_deployment_startup_hold_v1',authority=D.CONFIRM,
        transition=str(failed_path),target_date=day,candidate_commit=origin_commit,old_pid_identity=identity)
    if (selected.get('actual_pid_consumed') is not False
            or selected.get('git_commit') != origin_commit or selected.get('release_root') != str(origin_root)
            or selected.get('deployment_transition') != str(failed_path)
            or selected.get('approval_scope') != 'ordered_intraday_deploy_and_restart'
            or selected.get('approved_by') != 'user' or hold != expected_hold
            or failed.get('schema') != 'ordered_intraday_deployment_v1' or failed.get('authority') != D.CONFIRM
            or failed.get('phase') != 'failed' or failed.get('status') != 'fail'
            or failed.get('failed_phase') != 'selected' or failed.get('target_date') != day
            or failed.get('candidate_commit') != origin_commit or failed.get('candidate_root') != str(origin_root)
            or failed.get('error') != 'deployment_validation_failed:src.engine.automation.intraday_release_handoff'
            or failed.get('policy_effect') != 'unchanged'
            or failed.get('original_selection_sha256') != D._digest(prior_raw)
            or prior.get('actual_pid_consumed') is not True
            or prior.get('git_commit') != failed.get('previous_commit')
            or prior.get('release_root') != failed.get('previous_root')
            or not isinstance(identity,dict) or (prior.get('actual_pid_receipt') or {}).get('pid') != identity.get('pid')
            or D._main_pids() or not D._session_absent()
            or (workspace/'restart.flag').exists() or (workspace/'restart.flag').is_symlink()):
        raise ValueError('active_policy_stopped_origin_invalid')
    previous, previous_commit = D.R.validate_release(workspace, prior)
    proof = D._stopped_intraday_predecessor(day, previous, previous_commit, identity, failed_path)
    checked = _validated_origin_receipt(data_root,day,previous,previous_commit,bundle_sha,pointer_sha)
    if checked is None:
        raise ValueError('active_policy_stopped_native_ancestry_missing')
    # The hold and selector are observed transition state, never frozen policy inputs.
    if (D._owned_metadata(Path(data_root)/'runtime/runtime_release_selection.json')[1] != selected_raw
            or D._owned_metadata(Path(data_root)/'runtime/operator_startup_hold.json')[1] != hold_raw
            or failed_path.read_bytes() != failed_raw or prior_path.read_bytes() != prior_raw
            or D._main_pids() or not D._session_absent()):
        raise ValueError('active_policy_stopped_origin_changed')
    checked['source_hashes'].update(proof['frozen_files'])
    checked['source_hashes'].update({str(failed_path):D._digest(failed_raw),str(prior_path):D._digest(prior_raw)})
    checked['verification_basis'] = 'verified_stopped_transition_original_native_code_ancestry'
    return checked


def _postclose_origin_receipt(data_root,day,source_date,origin_root,origin_commit,bundle_sha,pointer_sha,release_commit):
    """Bridge one midnight using exact stopped postclose/native ancestry.

    This is code-only custody for the unchanged active parent. It neither
    requires nor fabricates the downstream next-session policy/PREOPEN.
    """
    from src.engine.automation import ordered_intraday_deploy as D
    root=Path(data_root).resolve();workspace=root.parent
    if source_date!=(datetime.fromisoformat(day).date()-timedelta(days=1)).isoformat():
        raise ValueError('active_policy_postclose_source_date_invalid')
    selected,selected_raw,_=D._owned_metadata(root/'runtime/runtime_release_selection.json')
    next_day=selected.get('next_operating_date')
    try:
        canonical=datetime.fromisoformat(next_day).date().isoformat()
    except (TypeError,ValueError):
        raise ValueError('active_policy_postclose_next_date_invalid') from None
    def stopped():
        return (not D._main_pids() and D._session_absent()
                and not (workspace/'restart.flag').exists() and not (workspace/'restart.flag').is_symlink()
                and not (root/'runtime/operator_startup_hold.json').exists()
                and not (root/'runtime/operator_startup_hold.json').is_symlink())
    if (not stopped() or selected.get('git_commit')!=origin_commit
            or selected.get('release_root')!=str(origin_root)
            or selected.get('source_date')!=source_date or selected.get('approved_by')!='user'
            or selected.get('approval_scope')!='after_postclose_deploy_for_next_regular_start'
            or selected.get('actual_pid_consumed') is not False
            or next_day!=canonical or next_day<day):
        raise ValueError('active_policy_postclose_stopped_origin_invalid')
    paths=[root/'runtime/update_kospi_status'/('update_kospi_'+source_date+'.json'),
           root/'report/threshold_cycle_postclose_status'/('threshold_cycle_postclose_'+source_date+'.status.json')]
    observed=[D._owned_metadata(p) for p in paths];eod,failed=(v[0] for v in observed)
    state=eod.get('db_state') or {}
    import re
    if (eod.get('schema_version')!=1 or eod.get('target_date')!=source_date
            or eod.get('status') not in {'completed','completed_with_warnings'}
            or eod.get('failed_steps')!=[] or state.get('latest_quote_date')!=source_date
            or type(state.get('rows_on_latest_date')) is not int or state['rows_on_latest_date']<=0
            or failed.get('report_type')!='threshold_cycle_postclose_status'
            or failed.get('target_date')!=source_date or failed.get('status')!='failed'
            or failed.get('schema_version')!=2
            or not isinstance(failed.get('run_id'),str) or re.fullmatch('[0-9a-f]{32}',failed['run_id']) is None
            or type(failed.get('exit_code')) is not int or failed['exit_code']==0
            or failed.get('code_commit')!=origin_commit or failed.get('runtime_effect') is not False):
        raise ValueError('active_policy_postclose_terminal_evidence_invalid')
    checked=_validated_origin_receipt(root,source_date,origin_root,origin_commit,bundle_sha,pointer_sha)
    if checked is None:raise ValueError('active_policy_postclose_native_ancestry_missing')
    # Mutable observed aliases must not invalidate the issued code handoff when
    # the repaired postclose producer naturally publishes its next attempt.
    frozen=path(root,day,release_commit,bundle_sha).with_suffix('')/'postclose_origin'
    if any(p.is_symlink() for p in (frozen,*frozen.parents)):
        raise ValueError('active_policy_postclose_evidence_path_invalid')
    frozen.mkdir(parents=True,exist_ok=True)
    refs={}
    for original,(_,raw,identity) in zip(paths,observed):
        destination=frozen/original.name
        if destination.exists() or destination.is_symlink():
            if D._owned_metadata(destination)[1]!=raw:
                raise ValueError('active_policy_postclose_frozen_evidence_conflict')
        else:
            with destination.open('xb') as handle:
                os.fchmod(handle.fileno(),0o600);handle.write(raw);handle.flush();os.fsync(handle.fileno())
        if D._owned_metadata(original)[1:]!=(raw,identity):
            raise ValueError('active_policy_postclose_evidence_changed')
        refs[str(destination)]=D._digest(raw)
    if D._owned_metadata(root/'runtime/runtime_release_selection.json')[1]!=selected_raw or not stopped():
        raise ValueError('active_policy_postclose_origin_changed')
    checked['source_hashes'].update(refs)
    checked['verification_basis']='verified_previous_day_postclose_native_code_ancestry'
    return checked


def issue(data_root,day,*,origin_root,release_root,parity_path,confirm,recover_stopped_origin=False,postclose_source_date=None):
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    from src.engine.scalping import continuous_reversal_policy_v6 as V
    from src.engine.scalping import reversal_extended_catalog as C
    from src.engine.infrastructure.runtime_release_router import selected_release,validate_release,git
    if (confirm!=AUTHORITY or day!=datetime.now(P.KST).date().isoformat()
            or postclose_source_date is not None and recover_stopped_origin is not False):
        raise ValueError('active_policy_code_handoff_authority_required')
    workspace=Path(data_root).resolve().parent;origin_root=Path(origin_root).resolve();release_root=Path(release_root).resolve()
    selected,previous=selected_release(workspace)
    if selected!=origin_root or release_root!=Path(__file__).resolve().parents[3]:
        raise ValueError('active_policy_code_handoff_origin_changed')
    selection_path=workspace/'data/runtime/runtime_release_selection.json'
    selection_before=selection_path.read_bytes()
    selection_sha=P.file_hash(selection_path)
    commit=git(release_root,'rev-parse','HEAD')
    validate_release(workspace,dict(schema='runtime_release_selection_v1',workspace=str(workspace),release_root=str(release_root),git_commit=commit))
    pointer=N.root(Path(data_root))/'current.json';before=pointer.read_bytes();ptr=json.loads(before)
    bundle=N._read(N.root(Path(data_root))/'generations'/(ptr['bundle_sha256']+'.json'));N.validate(bundle,target_date=bundle['target_date'])
    parity=json.loads(Path(parity_path).read_text());codes=code_hashes()
    expected={Path(m.__file__).name:P.file_hash(m.__file__) for m in V.contract_modules()}
    if (parity.get('status')!='pass' or parity.get('mismatches')!=0
            or parity.get('parent_bundle_sha256')!=bundle['bundle_sha256']
            or parity.get('contract_file_sha256')!=expected
            or not parity.get('confirmation_parity',{}).get('hits')):
        raise ValueError('active_policy_code_handoff_parity_invalid')
    if any(d!=C.definition(b) for b,d in bundle['continuous_reversal']['operating_manifest']['definitions'].items()):
        raise ValueError('active_policy_code_handoff_definition_changed')
    checked=_validated_origin_receipt(data_root,day,origin_root,previous,bundle['bundle_sha256'],P.file_hash(pointer))
    if recover_stopped_origin is True:
        checked = _stopped_origin_receipt(data_root,day,origin_root,previous,bundle['bundle_sha256'],P.file_hash(pointer))
    elif recover_stopped_origin is not False:
        raise ValueError('active_policy_stopped_recovery_flag_invalid')
    if postclose_source_date is not None:
        checked=_postclose_origin_receipt(data_root,day,postclose_source_date,origin_root,previous,
            bundle['bundle_sha256'],P.file_hash(pointer),commit)
    if checked is None:
        output=subprocess.check_output([str(origin_root/'.venv/bin/python'),'-B','-c',_ORIGIN_SCRIPT,str(Path(data_root).resolve()),day],
            cwd=origin_root,env={**os.environ,'PYTHONPATH':str(origin_root)},text=True,timeout=120)
        checked=json.loads(output)
    if (checked['bundle_sha256']!=bundle['bundle_sha256'] or pointer.read_bytes()!=before
            or selection_path.read_bytes()!=selection_before):
        raise ValueError('active_policy_code_handoff_parent_changed')
    sources=dict(checked['source_hashes'])
    # A successor of a code-only release observes its predecessor selector.
    # This is transition provenance, not an immutable policy input: validate()
    # independently binds the current selector to this exact candidate root
    # and commit. All policy/source and prior receipt hashes remain frozen.
    observed_selection=sources.pop(str(selection_path.resolve()),None)
    if observed_selection is not None and observed_selection!=selection_sha:
        raise ValueError('active_policy_code_handoff_selection_changed')
    sources[str(Path(parity_path).resolve())]=P.file_hash(parity_path)
    for row in parity.get('targeted_validation',[]):
        if P.file_hash(row['path'])!=row['sha256']:raise ValueError('active_policy_code_handoff_test_evidence_changed')
        sources[row['path']]=row['sha256']
    r=P.seal(dict(schema=SCHEMA,authority=confirm,target_date=day,release_commit=commit,release_root=str(release_root),
        origin_root=str(origin_root),origin_commit=previous,bundle_sha256=bundle['bundle_sha256'],
        origin_selection_sha256=selection_sha,
        current_pointer_sha256=P.file_hash(pointer),source_hashes=sources,code_hashes=codes,
        pipeline_source_validation=N.PIPELINE_REFERENCE_VALIDATION,
        origin_verification_basis=checked.get('verification_basis','native_origin_validator'),
        pipeline_source_reference_count=sum(N.is_pipeline_source_reference(p,data_root=data_root) for p in sources),
        policy_reselected=False,provider_called=False,actual_pid_consumed=False,source_semantics_repair=True,
        **({'postclose_source_date':postclose_source_date} if postclose_source_date is not None else {})))
    dest=path(data_root,day,commit,bundle['bundle_sha256']);dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists() and N._read(dest)!=r:raise ValueError('active_policy_code_handoff_receipt_conflict')
    N._atomic_write_json(dest,r)
    return r
