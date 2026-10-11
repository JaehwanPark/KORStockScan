"""Offline stop source references, partitioned by whole position identity.

Owns no live collection. Source rows remain in the original pipeline ledger;
sealed indexes contain offsets and hashes, never duplicate AI/quote bodies.
"""
from collections import Counter, OrderedDict
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import tempfile

from src.engine.scalping import main_stop_policy as policy
from src.engine.scalping.pre_submit_delay_initial_policy import _atomic
from src.engine.lifecycle import research_storage as storage
from src.engine.lifecycle.research_disk_budget import temporary, INDEX_LIMIT
from src.engine.lifecycle.holding_window_generation import byte_generation
from src.utils.jsonl_io import open_text_auto

PARTITIONS = 16
SCHEMA = 'main_stop_source_reference_index_v1'


def extract(event):
    if not isinstance(event,dict) or event.get('stage')!='main_stop_source':return None
    fields=event.get('fields')
    row=fields.get('main_stop_source') if isinstance(fields,dict) else None
    if isinstance(row,str):row=json.loads(row)
    if not isinstance(row,dict):raise ValueError('stop_source_row_invalid')
    return row


def prepare(root, inventory, loader, census):
    """Decode a changed source once; unchanged sources reuse sealed references."""
    result=[]
    decoder=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    for name,generation in inventory.items():
        identity=policy.digest(dict(path=name,generation=generation,decoder=decoder))
        directory=Path(root)/'source_index'/identity
        manifest=directory/'index.json'
        if manifest.exists():
            body,_=policy.bounded_object(manifest)
            if (body.get('schema')!=SCHEMA or body.get('identity')!=identity
                    or body.get('sha256')!=policy.digest({k:v for k,v in body.items() if k!='sha256'})):
                raise ValueError('stop_source_index_invalid')
        else:
            directory.mkdir(parents=True,exist_ok=True)
            counts=Counter();refs={}
            with temporary(INDEX_LIMIT),tempfile.TemporaryDirectory(prefix='.refs-',dir=directory) as scratch:
                handles={};used=0
                try:
                    for event,offset,line_sha in loader(Path(name),counts,references=True):
                        try:row=extract(event)
                        except ValueError:counts['malformed']+=1;continue
                        if row is None:continue
                        key,at=row.get('position_key'),row.get('at')
                        if not isinstance(key,str) or not key or not policy.finite(at):
                            counts['unidentifiable']+=1;continue
                        cell=str(row.get('role',''))+'|'+str(row.get('market',''))
                        bucket=int(hashlib.sha256(key.encode()).hexdigest()[:8],16)%PARTITIONS
                        record=dict(id=f'{key}|{float(at):020.6f}',position_key=key,at=at,
                            cell=cell,offset=offset,line_sha256=line_sha,content_sha256=policy.digest(row))
                        raw=storage.encoded(record)+b'\n'
                        used+=len(raw)
                        if used>INDEX_LIMIT:raise ValueError('stop_daily_reference_spool_budget_exceeded')
                        if bucket not in handles:handles[bucket]=open(Path(scratch)/str(bucket),'wb')
                        handles[bucket].write(raw);counts['raw']+=1
                finally:
                    for handle in handles.values():handle.close()
                for bucket in sorted(handles):
                    with open(Path(scratch)/str(bucket)) as handle:
                        refs[str(bucket)]=storage.write_tree(directory,(json.loads(line) for line in handle))
            if byte_generation(Path(name))!=generation:raise ValueError('stop_source_index_generation_changed')
            body=dict(schema=SCHEMA,identity=identity,source=name,generation=generation,
                      partitions=refs,census=dict(counts))
            body['sha256']=policy.digest(body);_atomic(manifest,body)
        census.update(body['census'])
        result.append((directory,body))
    return result


class Position:
    def __init__(self,db,key,cell,first,last,checkpoint):
        self.db,self.key,self.cell,self.first,self.last=db,key,cell,first,last
        self.checkpoint=checkpoint
        self.low,self.high=key+'|',key+'|'+chr(0x10ffff)
        digest=hashlib.sha256()
        for sha,conflict in db.execute('SELECT sha,conflicted FROM records WHERE id>=? AND id<=? ORDER BY id',(self.low,self.high)):
            digest.update(f'{sha}:{conflict}\n'.encode())
        self.source_sha256=digest.hexdigest()

    def rows(self):
        handles=OrderedDict()
        try:
            for body,conflict in self.db.execute('SELECT body,conflicted FROM records WHERE id>=? AND id<=? ORDER BY id',(self.low,self.high)):
                self.checkpoint()
                if conflict:yield {};continue
                ref=json.loads(body);name=ref['path']
                if name not in handles:
                    if len(handles)>=8:handles.popitem(last=False)[1].close()
                    handles[name]=open_text_auto(Path(name),errors='strict')
                handle=handles[name];handles.move_to_end(name)
                handle.seek(ref['offset']);line=handle.readline(2*1024*1024+1)
                if hashlib.sha256(line.encode()).hexdigest()!=ref['line_sha256']:
                    raise ValueError('stop_source_reference_changed')
                row=extract(json.loads(line))
                if policy.digest(row)!=ref['content_sha256']:raise ValueError('stop_source_reference_invalid')
                yield row
        finally:
            for handle in handles.values():handle.close()

    @contextmanager
    def materialized(self,directory):
        """Decode a changed position once for the finite candidate block."""
        with storage.index(directory) as db:
            for n,row in enumerate(self.rows()):storage.put(db,f'{n:020d}',row)
            def rows():
                for raw, in db.execute('SELECT body FROM records ORDER BY id'):
                    self.checkpoint()
                    yield json.loads(raw)
            yield rows


def positions(prepared, directory, census, *, checkpoint=lambda:None):
    # Whole positions stay in one partition, including cross-date duplicates.
    # Only compact references enter the sort index. Each partition is disposed
    # before the next one; the global census/selection lives with the publisher.
    for bucket in range(PARTITIONS):
        relevant=[(root,body) for root,body in prepared if str(bucket) in body['partitions']]
        if not relevant:continue
        with storage.index(directory) as db:
            for root,body in relevant:
                for ref in storage.iter_tree(root,body['partitions'][str(bucket)]):
                    checkpoint()
                    storage.put(db,ref['id'],dict(ref,path=body['source']),content_sha=ref['content_sha256'])
            db.execute('CREATE TABLE positions (id TEXT PRIMARY KEY,cell TEXT,first_at REAL,last_at REAL)')
            for raw,conflict in db.execute('SELECT body,conflicted FROM records ORDER BY id'):
                ref=json.loads(raw)
                db.execute('INSERT INTO positions VALUES (?,?,?,?) ON CONFLICT(id) DO UPDATE SET last_at=max(last_at,excluded.last_at)',
                    (ref['position_key'],ref['cell'],ref['at'],ref['at']))
                census['conflicting_rows' if conflict else 'deduplicated']+=1
            for key,cell,first,last in db.execute('SELECT id,cell,first_at,last_at FROM positions ORDER BY first_at,id'):
                yield Position(db,key,cell,first,last,checkpoint)
