"""Exact reviewed code compatibility for an already-active Main policy.

Scalping validates policy sources; deployment owns the dated receipt. This
never selects a policy or changes thresholds, memberships, or order authority.
"""
from __future__ import annotations
import json
import subprocess
import os
from datetime import datetime
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


def validate(bundle,data_root,*,original_error):
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    from src.engine.infrastructure.runtime_release_router import selected_release
    day=datetime.now(P.KST).date().isoformat();root,commit=selected_release(Path(data_root).resolve().parent)
    # Include the selector in the native dependency cache; a later selection
    # cannot keep the preceding compatibility result alive.
    selection=N._read(Path(data_root)/'runtime/runtime_release_selection.json')
    if selection.get('git_commit')!=commit or selection.get('release_root')!=str(root):
        raise ValueError('active_policy_code_selection_changed')
    receipt_path=path(data_root,day,commit,bundle['bundle_sha256'])
    # Preserve the native reason for unregistered code and tomorrow's parent
    # transition. There is no generic historical-loader fallback.
    if not receipt_path.exists():raise original_error
    if root!=Path(__file__).resolve().parents[3]:raise ValueError('active_policy_code_reader_root_changed')
    pointer=N.root(Path(data_root))/'current.json'
    pointer_sha=N._source_hash(str(pointer),N._signature(pointer))
    r=N._read(receipt_path)
    validate_receipt(r,day=day,commit=commit,root=root,bundle_sha=bundle['bundle_sha256'],pointer_sha=pointer_sha)
    current={str(Path(m.__file__).resolve()) for m in __import__(
        'src.engine.scalping.continuous_reversal_policy_v6',fromlist=['contract_modules']).contract_modules()} | {str(Path(__file__).resolve())}
    if set(r['code_hashes'])!=current:raise ValueError('active_policy_code_membership_changed')
    for name,expected in {**r['source_hashes'],**r['code_hashes']}.items():
        p=Path(name)
        if N._source_hash(str(p),N._signature(p))!=expected:
            raise ValueError('active_policy_code_handoff_source_changed:'+name)
    if N._read(pointer)['bundle_sha256']!=bundle['bundle_sha256']:
        raise ValueError('active_policy_code_handoff_pointer_changed')
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
b=N._load_current_uncached(root,day)
refs={}
for name,identity in list(opened.items()):
    p=Path(name);st=p.stat()
    if identity!=(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns):raise ValueError('origin_source_changed_during_validation')
    with p.open('rb') as f:refs[name]=hashlib.file_digest(f,'sha256').hexdigest()
print(json.dumps(dict(bundle_sha256=b['bundle_sha256'],source_hashes=refs)))
'''


def issue(data_root,day,*,origin_root,release_root,parity_path,confirm):
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    from src.engine.scalping import continuous_reversal_policy_v6 as V
    from src.engine.scalping import reversal_extended_catalog as C
    from src.engine.infrastructure.runtime_release_router import selected_release,validate_release,git
    if confirm!=AUTHORITY or day!=datetime.now(P.KST).date().isoformat():
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
        policy_reselected=False,provider_called=False,actual_pid_consumed=False,source_semantics_repair=True))
    dest=path(data_root,day,commit,bundle['bundle_sha256']);dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists() and N._read(dest)!=r:raise ValueError('active_policy_code_handoff_receipt_conflict')
    N._atomic_write_json(dest,r)
    return r
