"""Bounded metadata for first accepted session prints and raw-prefix cursors.

Only the existing source preparation/writer owns disk I/O. An incomplete
prefix never certifies the absence of an older stream anchor.
"""
from __future__ import annotations
import json
import math
import threading
from pathlib import Path
from datetime import datetime
from src.engine.scalping import continuous_reversal as K
from src.engine.scalping.continuous_reversal_postclose import digest

SCHEMA='native_session_anchor_index_v2'
LIMIT=16*1024*1024
_SINK=None
_LOCK=threading.Lock();_VERSIONS={};_PENDING=set()

def configure_sink(sink):
    global _SINK
    _SINK=sink

def location(root,day):return Path(root)/'runtime/continuous_reversal/session_anchors'/f'{day}.json'

def valid(key,row,day):
    try:
        from src.trading.market.session_contract import market_source_partition_venue
        return (len(key)==5 and key[4]==day and len(row)==4
            and all(type(v) in (int,float) and math.isfinite(v) for v in row)
            and type(row[1]) is int and row[1]>0 and type(row[2]) is int and row[2]>0 and row[3]>0
            and str(datetime.fromtimestamp(row[0],K.KST).date())==day
            and key[2].split('_',1)[0]==key[0] and market_source_partition_venue(key[2])==key[1])
    except (ValueError,TypeError,IndexError,OverflowError):return False

def load(root,day):
    path=location(root,day)
    if not path.exists():return None
    if path.stat().st_size>LIMIT:raise ValueError('session_anchor_index_budget_exceeded')
    value=json.loads(path.read_text())
    if (value.get('schema') not in {SCHEMA,'native_session_anchor_index_v1'} or value.get('day')!=day
            or value.get('content_sha256')!=digest({k:v for k,v in value.items() if k!='content_sha256'})):
        raise ValueError('session_anchor_index_contract_invalid')
    if not isinstance(value.get('anchors'),list) or not isinstance(value.get('cursors'),dict):
        raise ValueError('session_anchor_index_shape_invalid')
    for path,cursor in value['cursors'].items():
        if (not isinstance(path,str) or not isinstance(cursor,dict)
                or any(type(cursor.get(k)) is not int for k in ('inode','bytes','offset'))
                or cursor['inode']<=0 or cursor['bytes'] < -1 or cursor['offset']<0):
            raise ValueError('session_anchor_index_cursor_invalid')
    records={}
    for entry in value['anchors']:
        key=tuple(entry['key']);row=entry['row']
        if not valid(key,row,day) or key in records:raise ValueError('session_anchor_index_identity_invalid')
        records[key]=row
    gaps={tuple(k) for k in value.get('unobservable_streams',[])}
    if any(len(k)!=5 or k[4]!=day for k in gaps):raise ValueError('session_anchor_gap_identity_invalid')
    # A v1 index did not record identifiable lost first facts. It proves its
    # retained anchors, but cannot certify that absent streams are new.
    cursors=value.get('cursors',{}) if value['schema']==SCHEMA else {}
    return records,cursors,gaps

def save(root,day,anchors,cursors,*,unobservable_streams=()):
    from src.engine.scalping.mechanistic_entry_runtime_policy import _atomic_write_json
    body=dict(schema=SCHEMA,day=day,anchors=[dict(key=list(k),row=v,
        source_ref=dict(item=k[2],epoch=v[1],sequence=v[2],received_epoch=v[0],price=v[3]))
        for k,v in sorted(anchors.items()) if k[4]==day],cursors=cursors,
        unobservable_streams=[list(k) for k in sorted(unobservable_streams) if k[4]==day])
    if any(not valid(tuple(r['key']),r['row'],day) for r in body['anchors']):
        raise ValueError('session_anchor_index_invalid_first_fact')
    body['content_sha256']=digest(body)
    if len(json.dumps(body).encode())>LIMIT:raise ValueError('session_anchor_index_budget_exceeded')
    path=location(root,day);path.parent.mkdir(parents=True,exist_ok=True);_atomic_write_json(path,body)
    return dict(structured_append_succeeded=True,anchor_count=len(body['anchors']))

def enqueue(root,day,owner,*,advance=True):
    if _SINK is None:return False
    key=(str(Path(root).resolve()),day)
    with _LOCK:
        if advance:_VERSIONS[key]=_VERSIONS.get(key,0)+1
        if key in _PENDING:return True
        _PENDING.add(key)
    def write():
        try:
            for _ in range(2):
                with _LOCK:version=_VERSIONS.get(key,0)
                with owner._LOCK:
                    anchors={k:list(v) for k,v in owner._ANCHORS.items() if k[4]==day}
                    cursors=dict(owner._ANCHOR_CURSORS.get(day,{}))
                    gaps=set(getattr(owner,'_ANCHOR_GAPS',set()))
                receipt=save(root,day,anchors,cursors,unobservable_streams=gaps)
                with _LOCK:
                    if version==_VERSIONS.get(key,0):
                        _PENDING.discard(key);return receipt
            # Yield back to the existing FIFO after at most two writes. New
            # anchors during a write need a catch-up, never an unbounded drain.
            with _LOCK:_PENDING.discard(key)
            enqueue(root,day,owner,advance=False)
            return receipt
        except Exception:
            with _LOCK:_PENDING.discard(key)
            raise
    try:receipt=_SINK(write,observation_category='default')
    except Exception:receipt=None
    accepted=isinstance(receipt,dict) and receipt.get('status')=='queued'
    if not accepted:
        with _LOCK:_PENDING.discard(key)
    return accepted
