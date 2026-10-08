"""Exact-source reader compatibility receipts for auxiliary-only code handoff.

Owned by scalping policy readers, not the machine policy or bootstrap authority.
Receipts attest reviewed v1 parity and retain original artifacts and identities.
"""
from pathlib import Path
from src.engine.scalping import continuous_reversal_postclose as P

SCHEMA = 'auxiliary_reader_compatibility_v1'


def path(data_root, bundle, source, new_hashes):
    key=P.digest([bundle['bundle_sha256'],P.file_hash(source),new_hashes])
    return Path(data_root)/'runtime/mechanistic_entry_policy/auxiliary/compatibility'/(key+'.json')


def validate(data_root, bundle, source, old_hashes, new_hashes):
    from src.engine.scalping import reversal_auxiliary_intraday as I
    target=path(data_root,bundle,source,new_hashes)
    receipt=I.read(target)
    if (receipt.get('schema')!=SCHEMA or receipt.get('base_bundle_sha256')!=bundle['bundle_sha256']
            or receipt.get('source_sha256')!=P.file_hash(source)
            or receipt.get('old_reader_hashes')!=old_hashes or receipt.get('new_reader_hashes')!=new_hashes):
        raise ValueError('auxiliary_reader_compatibility_invalid')
    original=I.read(source)
    if P.digest(original.get('auxiliary_registry_bindings',original.get('bindings',{})))!=receipt['v1_bindings_sha256']:
        raise ValueError('auxiliary_reader_binding_evidence_changed')
    evidence=I.read(receipt['evidence_path'])
    if (P.file_hash(receipt['evidence_path'])!=receipt['evidence_sha256']
            or evidence.get('status')!='pass' or evidence.get('new_reader_hashes')!=new_hashes
            or evidence.get('base_bundle_sha256')!=bundle['bundle_sha256']
            or evidence.get('source_sha256')!=receipt['source_sha256']
            or evidence.get('v1_bindings_sha256')!=receipt['v1_bindings_sha256']):
        raise ValueError('auxiliary_reader_parity_evidence_invalid')
    for item in receipt['frozen_readers']:
        if P.file_hash(item['path'])!=old_hashes.get(Path(item['path']).name):
            raise ValueError('auxiliary_frozen_reader_changed')
    if {Path(x['path']).name for x in receipt['frozen_readers']}!=set(old_hashes):
        raise ValueError('auxiliary_frozen_reader_incomplete')
    return receipt


def issue(data_root,bundle,source,old_hashes,new_hashes,*,evidence,frozen_readers):
    from src.engine.scalping import reversal_auxiliary_intraday as I
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    proof=I.read(evidence)
    body=P.seal(dict(schema=SCHEMA,base_bundle_sha256=bundle['bundle_sha256'],
        source_path=str(Path(source).resolve()),source_sha256=P.file_hash(source),
        old_reader_hashes=old_hashes,new_reader_hashes=new_hashes,
        v1_bindings_sha256=proof['v1_bindings_sha256'],evidence_path=str(Path(evidence).resolve()),
        evidence_sha256=P.file_hash(evidence),frozen_readers=frozen_readers,
        actual_pid_consumed=False,actual_order_submitted=False))
    dest=path(data_root,bundle,source,new_hashes)
    if dest.exists() and I.read(dest)!=body:raise ValueError('auxiliary_compatibility_immutable_conflict')
    N._atomic_write_json(dest,body)
    validate(data_root,bundle,source,old_hashes,new_hashes)
    return body
