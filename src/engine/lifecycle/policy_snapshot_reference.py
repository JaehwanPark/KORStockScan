"""Immutable replay-policy blobs; compact references never authorize trades."""
from __future__ import annotations
import copy
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from src.engine.lifecycle.avg_down_replay import canonical_digest

SCHEMA='frozen_replay_policy_reference_v1'
MANIFEST_SCHEMA='frozen_replay_policy_snapshot_manifest_v1'
MAX_BYTES=16*1024*1024

def is_reference(value):return isinstance(value,dict) and value.get('schema')==SCHEMA

def validate(value):
    if (not is_reference(value) or not re.fullmatch('[0-9a-f]{64}',str(value.get('sha256')))
            or not isinstance(value.get('rules'),dict)
            or value.get('rules_sha256')!=canonical_digest(value['rules'])
            or not Path(str(value.get('path'))).is_absolute()
            or Path(str(value.get('path'))).parent.name!='replay_policy_snapshots'
            or Path(str(value.get('path'))).name!=value['sha256']+'.json'):
        raise ValueError('replay_policy_reference_invalid')
    return value

def _encoded(value):
    raw=json.dumps(value,sort_keys=True,ensure_ascii=True,separators=(',',':'),allow_nan=False).encode()
    if len(raw)>MAX_BYTES:raise ValueError('replay_policy_snapshot_budget_exceeded')
    return raw


def _write_once(path,raw):
    folder=path.parent;folder.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.stat().st_size>MAX_BYTES or path.read_bytes()!=raw:
            raise ValueError('replay_policy_snapshot_archive_conflict')
    else:
        fd,name=tempfile.mkstemp(dir=folder,prefix='.policy-')
        try:
            with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
            os.replace(name,path)
            fd=os.open(folder,os.O_RDONLY|os.O_DIRECTORY)
            try:os.fsync(fd)
            finally:os.close(fd)
        finally:
            if os.path.exists(name):os.unlink(name)


def persist(snapshot,data_root):
    if snapshot.get('schema')!='avg_down_full_policy_snapshot_v1' or not isinstance(snapshot.get('rules'),dict):
        raise ValueError('replay_policy_snapshot_schema_invalid')
    sha=hashlib.sha256(_encoded(snapshot)).hexdigest();folder=Path(data_root)/'observations/replay_policy_snapshots'
    folder.mkdir(parents=True,exist_ok=True);path=folder/(sha+'.json')
    ref=dict(schema=SCHEMA,path=str(path.resolve()),sha256=sha,
        rules=copy.deepcopy(snapshot['rules']),rules_sha256=canonical_digest(snapshot['rules']))
    if path.exists():
        # Keep already issued inline blobs readable and immutable.
        if resolve(ref)!=snapshot:raise ValueError('replay_policy_snapshot_archive_conflict')
        return ref
    def part(value):
        raw=_encoded(value);digest=hashlib.sha256(raw).hexdigest()
        _write_once(folder/'parts'/(digest+'.json'),raw)
        return digest
    components={};files=None
    for key,value in snapshot.items():
        if key=='files' and isinstance(value,dict):
            files={name:part(body) for name,body in value.items()}
        else:components[key]=part(value)
    manifest=dict(schema=MANIFEST_SCHEMA,snapshot_sha256=sha,components=components)
    if files is not None:manifest['files_components']=files
    manifest['content_sha256']=canonical_digest(manifest)
    _write_once(path,_encoded(manifest))
    return ref

def resolve(value):
    if not is_reference(value):return value
    validate(value);path=Path(value['path'])
    if path.stat().st_size>MAX_BYTES:raise ValueError('replay_policy_snapshot_budget_exceeded')
    raw=path.read_bytes()
    decoded=json.loads(raw)
    if decoded.get('schema')==MANIFEST_SCHEMA:
        if (decoded.get('snapshot_sha256')!=value['sha256']
                or decoded.get('content_sha256')!=canonical_digest({k:v for k,v in decoded.items() if k!='content_sha256'})
                or not isinstance(decoded.get('components'),dict) or len(decoded['components'])>64):
            raise ValueError('replay_policy_snapshot_source_changed')
        snapshot={};read_bytes=0
        def part(digest):
            nonlocal read_bytes
            if not re.fullmatch('[0-9a-f]{64}',str(digest)):
                raise ValueError('replay_policy_component_digest_invalid')
            part=path.parent/'parts'/(digest+'.json')
            read_bytes+=part.stat().st_size
            if read_bytes>MAX_BYTES:raise ValueError('replay_policy_snapshot_budget_exceeded')
            data=part.read_bytes()
            if hashlib.sha256(data).hexdigest()!=digest:raise ValueError('replay_policy_snapshot_source_changed')
            return json.loads(data)
        for key,digest in decoded['components'].items():snapshot[key]=part(digest)
        if 'files_components' in decoded:
            files=decoded['files_components']
            if not isinstance(files,dict) or len(files)>4096 or 'files' in snapshot:
                raise ValueError('replay_policy_snapshot_file_manifest_invalid')
            snapshot['files']={key:part(digest) for key,digest in files.items()}
    else:
        if hashlib.sha256(raw).hexdigest()!=value['sha256']:raise ValueError('replay_policy_snapshot_source_changed')
        snapshot=decoded
    if canonical_digest(snapshot)!=value['sha256'] or snapshot.get('rules')!=value['rules']:
        raise ValueError('replay_policy_snapshot_rule_conflict')
    return snapshot
