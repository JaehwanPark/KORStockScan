"""Writer-owned trailing input index; readers never rebuild it from raw logs.

Owns report inputs only. Native append owners supply before/after identities.
Missing historical coverage is explicit and is filled by bounded offline steps.
"""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import stat
import time
import threading
from collections import OrderedDict
from contextvars import ContextVar

SCHEMA = 'main_trailing_indexed_source_v1'
ZERO_SHA = '0' * 64
MAX_ROW_BYTES = 2 * 1024 * 1024
MAX_STEP_BYTES = 8 * 1024 * 1024
STREAM_NAMESPACES = ('ai_decision_payloads','ai_decision_trace','pipeline_events',
    'ai_decision_prompts','ai_decision_requests')
NAMESPACES = STREAM_NAMESPACES+('holding_path_votes',)
_WRITERS = OrderedDict()
_WRITER_LOCK = threading.RLock()
APPEND_RECORD = ContextVar('native_trailing_projection_append_record', default=None)
_COMPAT_DECODE=ContextVar('native_trailing_legacy_decode_budget',default=None)
_REPORTED_FAILURES = {}
_MAINTENANCE = {}
_CHECKPOINTS = {}
_MAINTENANCE_STATUS = OrderedDict()
_MAINTENANCE_REQUEST = None
_MAINTENANCE_THREAD = None
_MAINTENANCE_LOCK = threading.Lock()
_VOTE_BACKFILL = OrderedDict()
_PENDING_APPENDS = OrderedDict()
_PENDING_LOCK = threading.RLock()
_PENDING_BYTES = 0


def _after_fork():
    global _WRITERS, _WRITER_LOCK, _MAINTENANCE_THREAD, _MAINTENANCE_LOCK, _PENDING_LOCK, _PENDING_BYTES
    _WRITERS = OrderedDict()
    _WRITER_LOCK = threading.RLock()
    _MAINTENANCE_THREAD = None
    _MAINTENANCE_LOCK = threading.Lock()
    _MAINTENANCE.clear();_CHECKPOINTS.clear();_VOTE_BACKFILL.clear()
    _PENDING_LOCK=threading.RLock();_PENDING_APPENDS.clear();_PENDING_BYTES=0


os.register_at_fork(after_in_child=_after_fork)


@contextmanager
def append_record(row):
    """The existing pipeline writer owns the parsed row and append lock."""
    token=APPEND_RECORD.set(row)
    try:
        yield
    finally:
        APPEND_RECORD.reset(token)


def capture_native_append(path, *, before, after, raw, row=None):
    """Source-only failure cannot change the original writer/order outcome."""
    path=Path(path)
    if path.parent.name not in NAMESPACES:
        return
    data_root=path.parent.parent.parent if path.parent.name=='holding_path_votes' else path.parent.parent
    try:
        with _PENDING_LOCK:
            queued=str(path.resolve()) in _PENDING_APPENDS
        if queued:
            if not _queue_append(data_root,path,before,after,raw):
                raise InputPending('trailing_index_append_queue_budget_exceeded')
            return
        _,_,target=_location(data_root,path)
        if (os.getpid(),str(target)) not in _WRITERS and not target.is_file():
            if before.st_size:
                # Existing history is migrated outside the native append path.
                if path.parent.name!='holding_path_votes':
                    maintain(data_root,path.name[len(path.parent.name)+1:len(path.parent.name)+11])
                    return
                with _database(data_root,path,writer=True):
                    pass
                with _MAINTENANCE_LOCK:
                    _VOTE_BACKFILL[str(path.resolve())]=True
                    while len(_VOTE_BACKFILL)>64:_VOTE_BACKFILL.popitem(last=False)
                first=row[0] if isinstance(row,list) else row
                maintain(data_root,str((first or {}).get('session_key')))
            # A genuinely new source has no history to scan. Preserve its very
            # first append even if it precedes Main's normal preparation.
            with _database(data_root,path,writer=True):
                pass
        value=row if row is not None else APPEND_RECORD.get()
        if value is None:
            if len(raw)>MAX_ROW_BYTES:
                value=dict(schema='unindexed_oversize_native_record')
            else:
                value=json.loads(raw)
        ok=record_append(data_root,path,before=signature(before),
            after=signature(after),raw=raw,row=value,existing_only=True)
        if not ok:
            raise InputPending('trailing_index_append_chain_gap')
    except Exception as exc:
        if (isinstance(exc,InputPending) and str(exc) in {
                'trailing_index_writer_busy','trailing_index_preparation_pending'}
                or isinstance(exc,sqlite3.OperationalError) and 'locked' in str(exc).lower()):
            if _queue_append(data_root,path,before,after,raw):return
        # The stale coverage identity makes readers fail closed. This diagnostic
        # is bounded independently from the trading writer's original receipt.
        key=(str(path),type(exc).__name__)
        now=time.monotonic()
        if now-_REPORTED_FAILURES.get(key,float('-inf'))>=60:
            _REPORTED_FAILURES[key]=now
            while len(_REPORTED_FAILURES)>64:
                _REPORTED_FAILURES.pop(next(iter(_REPORTED_FAILURES)))
            try:
                from src.utils.logger import log_error
                log_error('[TRAILING_SOURCE_INDEX_GAP] source='+str(path)+' reason='+type(exc).__name__)
            except Exception:
                pass  # Coverage still fails closed; original native append wins.


def _queue_append(root,path,before,after,raw):
    """Retain a busy native append, never reread its raw file on the caller."""
    global _PENDING_BYTES
    name=str(Path(path).resolve())
    with _PENDING_LOCK:
        rows=_PENDING_APPENDS.get(name,[])
        if len(rows)>=128 or _PENDING_BYTES+len(raw)>16*1024*1024:
            return False  # Physical/index identity remains visibly incomplete.
        rows.append((signature(before),signature(after),raw))
        _PENDING_APPENDS[name]=rows;_PENDING_BYTES+=len(raw)
    from datetime import datetime
    from zoneinfo import ZoneInfo
    maintain(root,datetime.now(ZoneInfo('Asia/Seoul')).date().isoformat())
    return True


def _drain_pending(root):
    """Bounded retry of resident native bytes; source gaps are never repaired."""
    global _PENDING_BYTES
    started=time.monotonic();count=0
    with _PENDING_LOCK:
        names=list(_PENDING_APPENDS)
    for name in names:
        if not Path(name).is_relative_to(Path(root).resolve()):continue
        while count<128 and time.monotonic()-started<.05:
            with _PENDING_LOCK:
                pending=_PENDING_APPENDS.get(name)
                if not pending:break
                receipt=pending[0]
            before,after,raw=receipt
            try:
                rows=[json.loads(line) for line in raw.splitlines()]
                if not record_append(root,name,before=before,after=after,
                        raw=raw,row=rows,existing_only=True):return
            except (InputPending,OSError,ValueError,sqlite3.Error):
                return
            with _PENDING_LOCK:
                pending.pop(0);_PENDING_BYTES-=len(raw);count+=1
                if not pending:_PENDING_APPENDS.pop(name,None)


def capture_native_rotation(path,segment,*,before,after):
    """The existing native journal lock owns this exact rename, no raw read."""
    try:
        data_root=Path(path).parent.parent.parent
        original,namespace,target=_location(data_root,path)
        if namespace!='holding_path_votes' or not target.is_file():return
        segment,_,_=_location(data_root,segment)
        old,new=signature(before),signature(after)
        if old[:4]!=new[:4] or source_signature(data_root,segment)!=new:
            raise ValueError('trailing_index_rotation_identity_invalid')
        with _database(data_root,original,writer=True,existing_only=True) as (db,_,_),db:
            state=db.execute('SELECT signature FROM sources WHERE path=?',(str(original),)).fetchone()
            if state is None or json.loads(state[0])!=old:
                raise InputPending('trailing_index_rotation_prefix_unverified')
            db.execute('UPDATE sources SET path=?,signature=? WHERE path=?',
                (str(segment),encode(new).decode(),str(original)))
            db.execute('UPDATE rows SET source=? WHERE source=?',(str(segment),str(original)))
            db.execute('UPDATE minutes SET source=? WHERE source=?',(str(segment),str(original)))
    except Exception as exc:
        try:
            from src.utils.logger import log_error
            log_error('[TRAILING_SOURCE_INDEX_ROTATION_GAP] '+type(exc).__name__)
        except Exception:
            pass


def prepare_for_day(data_root,day):
    """Fixed-size preparation before Main starts collecting/evaluating."""
    for namespace in STREAM_NAMESPACES:
        path=Path(data_root)/namespace/(namespace+'_'+day+'.jsonl')
        with _database(data_root,path,writer=True):
            pass
    maintain(data_root,day)


def _maintain_once(data_root, day, turn=0):
    """No broker/provider/strategy authority; at most one 8 MiB catch-up."""
    if not Path(data_root).is_dir():
        return
    _drain_pending(data_root)
    key=(str(data_root), day)
    now=time.monotonic()
    if now-_MAINTENANCE.get(key,float('-inf'))<.5:
        return
    _MAINTENANCE[key]=now
    while len(_MAINTENANCE)>3:
        _MAINTENANCE.pop(next(iter(_MAINTENANCE)))
    if now-_CHECKPOINTS.get(key,float('-inf'))>=60:
        _CHECKPOINTS.clear();_CHECKPOINTS[key]=now
        for namespace in STREAM_NAMESPACES:
            path=Path(data_root)/namespace/(namespace+'_'+day+'.jsonl')
            try:
                with _database(data_root,path,writer=True):
                    pass
                # Checkpoint outside the native append lock, at most once per
                # minute. Catch-up turns are independent from this disk work.
                with _database(data_root,path) as (db,_,_):
                    db.execute('PRAGMA wal_checkpoint(PASSIVE)').fetchone()
            except (InputPending,sqlite3.OperationalError):
                continue
    path=None
    if turn % (len(STREAM_NAMESPACES)+1)==len(STREAM_NAMESPACES):
        with _MAINTENANCE_LOCK:
            path=next((Path(name) for name in _VOTE_BACKFILL
                if Path(name).is_relative_to(Path(data_root).resolve())),None)
    else:
        namespace=STREAM_NAMESPACES[turn % (len(STREAM_NAMESPACES)+1)]
        path=Path(data_root)/namespace/(namespace+'_'+day+'.jsonl')
    if path is not None and path.is_file():
        try:
            progress=build_step(data_root,path,max_bytes=MAX_STEP_BYTES,seconds=.05)
            _MAINTENANCE_STATUS[str(path)]={**progress,'observed_epoch':time.time()}
            while len(_MAINTENANCE_STATUS)>12:_MAINTENANCE_STATUS.popitem(last=False)
            if progress['complete']:
                with _MAINTENANCE_LOCK:_VOTE_BACKFILL.pop(str(path),None)
        except (InputPending,sqlite3.OperationalError) as exc:
            _MAINTENANCE_STATUS[str(path)]=dict(complete=False,reason=str(exc)[:160],observed_epoch=time.time())
            while len(_MAINTENANCE_STATUS)>12:_MAINTENANCE_STATUS.popitem(last=False)


def maintain(data_root, day):
    """Kick a source-only worker; never checkpoint or backfill on the caller."""
    global _MAINTENANCE_REQUEST, _MAINTENANCE_THREAD
    if not _MAINTENANCE_LOCK.acquire(blocking=False):
        return
    try:
        _MAINTENANCE_REQUEST=(str(data_root),day)
        if _MAINTENANCE_THREAD is not None and _MAINTENANCE_THREAD.is_alive():
            return
        def run():
            turn=0
            while True:
                request=_MAINTENANCE_REQUEST
                if request is not None:
                    try:
                        _maintain_once(*request,turn=turn)
                    except (OSError,ValueError,sqlite3.Error):
                        pass  # Missing/invalid coverage remains visible to readers.
                turn+=1
                time.sleep(.5)
        _MAINTENANCE_THREAD=threading.Thread(target=run,name='trailing-source-index',daemon=True)
        _MAINTENANCE_THREAD.start()
    finally:
        _MAINTENANCE_LOCK.release()
TRACE_FIELDS = ('schema', 'decision_stage', 'decision_ts', 'stock_code',
    'continuous_reversal_consumption', 'entry_mechanistic_policy_decision',
    'decision_trace_id', 'evaluation_attempt_id', 'source_event_stage',
    'entry_ai_risk_verdict', 'provider_called', 'decision_evaluation_status',
    'result_source', 'prompt_version', 'entry_ai_component_sha256',
    'response_completed_at', 'session_bucket', 'market_data_route',
    'machine_bundle_sha256', 'entry_mechanistic_action', 'machine_observation_sha256')


class InputPending(ValueError):
    pass


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode()


def signature(metadata):
    if not stat.S_ISREG(metadata.st_mode):
        raise ValueError('trailing_index_source_not_regular')
    return [metadata.st_dev, metadata.st_ino, metadata.st_size,
            metadata.st_mtime_ns, metadata.st_ctime_ns]


def project(namespace, row):
    """Keep original eligible envelopes and an explicit identified gap."""
    if not isinstance(row, dict):
        return dict(kind='source_gap', reason='source_record_not_object')
    if row.get('schema')=='unindexed_oversize_native_record':
        return dict(kind='source_gap',reason='source_record_budget_exceeded')
    if namespace=='holding_path_votes':
        from src.engine.ai.holding_exit_vote import validate_path_event
        from datetime import datetime
        from zoneinfo import ZoneInfo
        row=validate_path_event(row,row.get('position_key'))
        if row is None:return None
        day=datetime.fromtimestamp(row['requested_at'],ZoneInfo('Asia/Seoul')).date().isoformat()
        if row.get('session_key')!=day:
            return dict(kind='source_gap',reason='holding_vote_session_invalid')
        value=dict(kind='holding_vote',identity=row['position_key'],row=row)
    elif namespace in {'ai_decision_payloads','ai_decision_prompts','ai_decision_requests'} and row.get('endpoint')=='holding_path_vote':
        kind,key={'ai_decision_payloads':('holding_payload','request_envelope_sha256'),
            'ai_decision_prompts':('holding_prompt','prompt_sha256'),
            'ai_decision_requests':('holding_request','request_id')}[namespace]
        value=dict(kind=kind,identity=row.get(key),row=row)
    elif namespace in {'ai_decision_prompts','ai_decision_requests'}:
        return None
    elif namespace == 'ai_decision_payloads':
        if (row.get('schema') != 'mechanistic_entry_observation_v1'
                or ((row.get('source') or {}).get('assessment') or {}).get('action') != 'ENTER_NOW'):
            return None
        from src.engine.scalping.ai_decision_trace import _json_bytes
        identity=row.get('machine_observation_sha256')
        if hashlib.sha256(_json_bytes({k:v for k,v in row.items() if k!='machine_observation_sha256'})).hexdigest()!=identity:
            return dict(kind='source_gap',reason='native_observation_hash_invalid')
        assessment=row['source']['assessment'];event=assessment.get('event') or {}
        fields={key:event[key] for key in ('at','event_id','native_epoch','entry_ask','planned_qty',
            'buy_basis_krw','entry_cost_model','item','source_item','execution_plan_sha256',
            'entry_depth_verified','trailing_entry_context','universal_trailing_quote') if key in event}
        projected={key:row[key] for key in ('schema','machine_observation_sha256','label_context',
            'bundle_sha256','captured_at') if key in row}
        projected['source']={'assessment':{'action':assessment['action'],
            'canonical_opportunity_id':assessment.get('canonical_opportunity_id'),'event':fields}}
        value=dict(kind='machine_capture_projection',identity=identity,row=projected,
            original_native_observation_verified=True)
    elif namespace == 'ai_decision_trace':
        if row.get('schema') != 'ai_decision_trace_v1' or row.get('decision_stage') != 'entry_screen':
            return None
        # Keep all entry dispositions so missing/invalid AI is never recast as
        # an empty population. The consumer selects PASS by its native rules.
        value = dict(kind='entry_trace', identity=row.get('decision_trace_id'),
                     row={key: row[key] for key in TRACE_FIELDS if key in row})
    elif namespace == 'pipeline_events':
        delay=row.get('stage') in {'pre_submit_delay_committed','pre_submit_delay_quote_observed',
            'pre_submit_delay_intent_terminal','pre_submit_delay_recheck_observed'}
        if not delay and row.get('stage') not in {'order_leg_sent', 'entry_execution_sizing_plan',
                                   'scalp_trailing_input_transition'}:
            return None
        fields = row.get('fields') or {}
        if row.get('stage') == 'scalp_trailing_input_transition' and not fields.get('trailing_entry_plan_receipt_sha256'):
            return None
        if not delay:
            fields={key:fields[key] for key in (
                'trailing_entry_plan_receipt','trailing_entry_plan_receipt_sha256','universal_trailing_quote',
                'trailing_entry_plan_holding_link','buy_account_key','order_no','buy_owner_type','buy_owner_id',
                'buy_registry_mode','owner_registry_intent_id','pipeline_lifecycle_population_scope',
                'actual_order_submitted','broker_order_forbidden','broker_route','qty','entry_split_submitted_at') if key in fields}
        projected={key:row[key] for key in ('stock_code','record_id','emitted_at','stage','event_type','pipeline','emitted_date') if key in row}
        projected['fields']=fields
        if delay:
            projected=row
        value = dict(kind='delay_receipt' if delay else 'pipeline_receipt',
            identity=fields.get('delay_intent_id') if delay else fields.get('trailing_entry_plan_receipt_sha256'),row=projected)
    else:
        raise ValueError('trailing_index_namespace_invalid')
    if len(encode(value)) > MAX_ROW_BYTES:
        return dict(kind='source_gap', reason='projection_record_budget_exceeded',
                    identity=value.get('identity'))
    return value


def _location(data_root, path):
    lexical=Path(data_root).absolute();root=lexical.resolve(strict=True);path=Path(path).absolute()
    if path.is_relative_to(lexical):
        relative=path.relative_to(lexical)
    elif path.is_relative_to(root):
        relative=path.relative_to(root)
    else:
        raise ValueError('trailing_index_source_path_invalid')
    if '..' in relative.parts:
        raise ValueError('trailing_index_source_path_invalid')
    path=root/relative
    if path.name.endswith('.jsonl.gz'):
        path=path.with_suffix('')
    if (path.is_symlink() or any(p.is_symlink() for p in path.parents)
            or path.parent.name not in NAMESPACES):
        raise ValueError('trailing_index_source_path_invalid')
    namespace=path.parent.name
    if namespace=='holding_path_votes':
        import re
        if re.fullmatch(r'[0-9a-f]{64}\.jsonl(?:\.segment-[0-9]+)?',path.name) is None:
            raise ValueError('trailing_index_vote_path_invalid')
        return path,namespace,root/'report/main_trailing_source_index/holding_path_votes.sqlite'
    day=path.name[len(namespace)+1:len(namespace)+11]
    from datetime import date
    if date.fromisoformat(day).isoformat()!=day or not path.name.startswith(namespace+'_'):
        raise ValueError('trailing_index_source_date_invalid')
    directory=root/'report/main_trailing_source_index'/day
    return path,namespace,directory/(namespace+'.sqlite')


@contextmanager
def _database(data_root, path, *, readonly=False, writer=False, existing_only=False):
    path, namespace, target = _location(data_root, path)
    if (readonly or existing_only) and not target.is_file():
        raise InputPending('trailing_index_coverage_incomplete')
    if not readonly and not existing_only and not target.parent.is_dir():
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if target.is_file():
        owner=target.stat()
        if owner.st_uid!=os.getuid() or owner.st_mode&0o077:
            raise InputPending('trailing_index_database_untrusted')
    if target.is_symlink() or any(p.is_symlink() for p in target.parents):
        raise ValueError('trailing_index_database_path_invalid')
    key=(os.getpid(), str(target))
    entry = _WRITERS.get(key) if writer else None
    if writer and entry is None:
        if not _WRITER_LOCK.acquire(blocking=False):
            raise InputPending('trailing_index_preparation_pending')
        try:
            entry=_WRITERS.get(key)
            if entry is None:
                db=_open_database(target,readonly=False,writer=True,initialize=not existing_only)
                entry=(db,threading.RLock());_WRITERS[key]=entry
                # Only preparation performs eviction/checkpoint work. Native
                # callbacks use already prepared connections exclusively.
                for old in list(_WRITERS):
                    if len(_WRITERS)<=6:
                        break
                    if old==key:
                        continue
                    connection,lock=_WRITERS[old]
                    if lock.acquire(blocking=False):
                        try:
                            _WRITERS.pop(old);connection.close()
                        finally:
                            lock.release()
        finally:
            _WRITER_LOCK.release()
    lock=entry[1] if entry is not None else None
    if lock is not None and not lock.acquire(blocking=False):
        raise InputPending('trailing_index_writer_busy')
    db=entry[0] if entry is not None else None
    try:
        if db is None:
            db=_open_database(target,readonly=readonly,writer=False)
        yield db, path, namespace
    finally:
        if db is not None and not writer:
            db.close()
        if lock is not None:
            lock.release()


def _open_database(target, *, readonly, writer, initialize=True):
    db = (sqlite3.connect('file:'+str(target)+'?mode=ro', uri=True, timeout=.005)
          if readonly else sqlite3.connect('file:'+str(target)+('?mode=rwc' if initialize else '?mode=rw'),uri=True,timeout=.005,check_same_thread=not writer))
    try:
        db.execute('PRAGMA cache_size=-2048')
        if not readonly and not initialize:
            if db.execute('PRAGMA user_version').fetchone()[0] != 1:
                raise InputPending('trailing_index_schema_not_prepared')
            db.execute('PRAGMA synchronous=NORMAL')
            db.execute('PRAGMA wal_autocheckpoint=0')
        if not readonly and initialize:
            os.chmod(target,0o600)
            db.execute('PRAGMA journal_mode=WAL')
            db.execute('PRAGMA synchronous=NORMAL')
            if writer:
                db.execute('PRAGMA wal_autocheckpoint=0')
            db.execute('CREATE TABLE IF NOT EXISTS sources(path TEXT PRIMARY KEY, signature TEXT, '
                'catchup_end INTEGER, cursor INTEGER, producer_end INTEGER, records INTEGER, invalid TEXT, '
                'prefix_sha TEXT, append_sha TEXT, selected_records INTEGER)')
            db.execute('CREATE TABLE IF NOT EXISTS rows(source TEXT, offset INTEGER, size INTEGER, '
                'raw_sha TEXT, body_sha TEXT, kind TEXT, identity TEXT, symbol TEXT, stage TEXT, emitted_at TEXT, body BLOB, PRIMARY KEY(source,offset))')
            db.execute('CREATE INDEX IF NOT EXISTS selected_identity ON rows(kind,identity)')
            db.execute('CREATE INDEX IF NOT EXISTS selected_symbol ON rows(symbol,kind)')
            db.execute('CREATE INDEX IF NOT EXISTS selected_window ON rows(source,kind,emitted_at)')
            db.execute('CREATE TABLE IF NOT EXISTS minutes(source TEXT, minute TEXT, stage TEXT, records INTEGER, identity_sum TEXT, PRIMARY KEY(source,minute,stage))')
            db.execute('PRAGMA user_version=1')
        return db
    except BaseException:
        db.close()
        raise


def _encoded_projection(value):
    return encode(dict(value,schema=SCHEMA)) if value is not None else b''


def _leaf(offset, raw, body):
    return hashlib.sha256(encode([offset,len(raw),hashlib.sha256(raw).hexdigest(),
        hashlib.sha256(body).hexdigest() if body else None])).hexdigest()


def _put(db, source, offset, raw, value):
    body=_encoded_projection(value)
    leaf=_leaf(offset,raw,body)
    if value is None:
        return leaf
    old=db.execute('SELECT raw_sha,body_sha FROM rows WHERE source=? AND offset=?',
        (source,offset)).fetchone()
    pair=(hashlib.sha256(raw).hexdigest(),hashlib.sha256(body).hexdigest())
    if old is not None and old!=pair:
        raise ValueError('trailing_index_record_conflict')
    row=value.get('row') or {}
    db.execute('INSERT OR IGNORE INTO rows VALUES(?,?,?,?,?,?,?,?,?,?,?)',
        (source,offset,len(raw),*pair,value['kind'],value.get('identity'),
         row.get('stock_code') or row.get('symbol'),row.get('stage'),row.get('emitted_at') or row.get('session_key'),body))
    return leaf


def _summary(namespace, row):
    if namespace!='pipeline_events' or not isinstance(row,dict):
        return None
    from src.engine.pipeline_event_summary import summary_event_from_payload, PRODUCER_SUMMARY_STAGES
    event=summary_event_from_payload(row,summary_stages=PRODUCER_SUMMARY_STAGES)
    if event is None:
        return None
    return event.emitted_at.replace(second=0,microsecond=0).isoformat(),event.stage,event.evidence_hash


def _summary_put(db, name, namespace, row):
    summary=_summary(namespace,row)
    if summary is not None:
        minute,stage,identity=summary
        _summary_merge(db,name,minute,stage,1,identity)


def _summary_merge(db,name,minute,stage,count,total):
    from src.engine.pipeline_event_summary import IDENTITY_MODULUS
    old=db.execute('SELECT records,identity_sum FROM minutes WHERE source=? AND minute=? AND stage=?',
        (name,minute,stage)).fetchone()
    if old:
        count+=old[0];total+=int(old[1],16)
    db.execute('INSERT OR REPLACE INTO minutes VALUES(?,?,?,?,?)',
        (name,minute,stage,count,f'{total % IDENTITY_MODULUS:064x}'))


def record_append(data_root, path, *, before, after, raw, row, existing_only=False):
    """Called after the native durable append, under its existing writer lock.

    This function performs no raw reads. A skipped/failed append receipt leaves
    coverage invalid; readers have no inline raw-scan fallback.
    """
    before, after = list(before), list(after)
    if before[:2] != after[:2] or after[2] != before[2] + len(raw):
        raise ValueError('trailing_index_append_identity_invalid')
    with _database(data_root, path, writer=True,existing_only=existing_only) as (db, path, namespace), db:
        name = str(path)
        state = db.execute('SELECT signature,producer_end,invalid,append_sha FROM sources WHERE path=?', (name,)).fetchone()
        if state is None:
            db.execute('INSERT INTO sources VALUES(?,?,?,?,?,?,?,?,?,?)',
                (name, encode(before).decode(), before[2], 0, before[2], 0, None, ZERO_SHA, ZERO_SHA, 0))
        elif json.loads(state[0]) != before or state[1] != before[2] or state[2]:
            db.execute('UPDATE sources SET invalid=? WHERE path=?', ('append_chain_gap', name))
            return False
        rows=row if isinstance(row,list) else [row]
        raw_rows=raw.splitlines(keepends=True)
        if len(rows)!=len(raw_rows) or any(not line.endswith(b'\n') for line in raw_rows):
            raise ValueError('trailing_index_append_batch_invalid')
        offset=before[2];chain=state[3] if state else ZERO_SHA;selected=0
        for item,line in zip(rows,raw_rows):
            if namespace=='holding_path_votes':
                from src.engine.ai.holding_exit_vote import path_vote_store_path
                base=path_vote_store_path(data_root,item.get('position_key')).name
                if path.name!=base and not path.name.startswith(base+'.segment-'):
                    raise ValueError('trailing_index_vote_position_mismatch')
            value=project(namespace,item)
            leaf=_put(db,name,offset,line,value);_summary_put(db,name,namespace,item)
            chain=hashlib.sha256(encode([chain,leaf])).hexdigest()
            selected+=int(value is not None);offset+=len(line)
        db.execute('UPDATE sources SET signature=?,producer_end=?,records=records+?,append_sha=?,selected_records=selected_records+? WHERE path=?',
            (encode(after).decode(),after[2],len(rows),chain,selected,name))

    return True


def build_step(data_root, path, *, max_bytes=MAX_STEP_BYTES, seconds=1):
    """Explicit resumable migration, never run by a report reader.

    Parse outside the write transaction. Each call reads at most8MiB and
    commits a bounded set of selected projections and minute aggregates.
    Native appends may advance the verified tail while this old prefix parses.
    """
    from src.engine.lifecycle.research_input_budget import Claim
    if type(max_bytes) is not int or not MAX_ROW_BYTES <= max_bytes <= MAX_STEP_BYTES:
        raise ValueError('trailing_index_step_budget_invalid')
    if type(seconds) not in (int,float) or not 0<seconds<=30:
        raise ValueError('trailing_index_step_time_invalid')
    path=Path(path)
    if path.suffix=='.gz' or not path.is_file():
        raise InputPending('trailing_index_offline_archive_migration_required')
    started=time.monotonic()
    with _database(data_root,path) as (db,path,namespace),Claim(max_bytes*8):
        current=source_signature(data_root,path);name=str(path)
        with db:
            db.execute('INSERT OR IGNORE INTO sources VALUES(?,?,?,?,?,?,?,?,?,?)',
                (name,encode(current).decode(),current[2],0,current[2],0,None,ZERO_SHA,ZERO_SHA,0))
        state=db.execute('SELECT signature,catchup_end,cursor,invalid,prefix_sha FROM sources WHERE path=?',
            (name,)).fetchone()
        if json.loads(state[0])!=current or state[3]:
            raise InputPending('trailing_index_source_generation_changed')
        end,cursor=state[1:3]
        with path.open('rb') as handle:
            handle.seek(cursor);raw=handle.read(min(max_bytes,end-cursor))
        complete=raw.rfind(b'\n')+1
        if raw and not complete:
            raise InputPending('trailing_index_oversize_or_partial_record')
        pending=[];minutes={};offset=cursor;records=0;selected=0;chain=state[4]
        for line in raw[:complete].splitlines(keepends=True):
            if time.monotonic()-started>=seconds:
                break
            try:
                row=json.loads(line) if len(line)<=MAX_ROW_BYTES else None
                value=(project(namespace,row) if row is not None else
                    dict(kind='source_gap',reason='source_record_budget_exceeded'))
                summary=_summary(namespace,row)
            except (ValueError,TypeError,KeyError,AttributeError):
                value=dict(kind='source_gap',reason='source_record_invalid');summary=None
            if value is not None:
                size=len(_encoded_projection(value))
                if pending and (selected+size>256*1024 or len(pending)>=128):
                    break
                pending.append((offset,line,value));selected+=size
            if summary:
                key=summary[:2];count,total=minutes.get(key,(0,0))
                minutes[key]=(count+1,total+summary[2])
            chain=hashlib.sha256(encode([chain,_leaf(offset,line,_encoded_projection(value))])).hexdigest()
            offset+=len(line);records+=1
        # Only a native contiguous append may change metadata during parsing.
        # Unknown rewrites, missing append receipts and competing cursor steps
        # cannot be silently repaired by this migration.
        with db:
            latest=db.execute('SELECT signature,catchup_end,cursor,invalid,prefix_sha FROM sources WHERE path=?',
                (name,)).fetchone()
            disk=source_signature(data_root,path)
            if (latest[1:]!=state[1:] or latest[3] or json.loads(latest[0])!=disk
                    or disk[:2]!=current[:2] or disk[2]<current[2]):
                raise InputPending('trailing_index_source_generation_changed')
            for at,line,value in pending:
                _put(db,name,at,line,value)
            for (minute,stage),(count,total) in minutes.items():
                _summary_merge(db,name,minute,stage,count,total)
            db.execute('UPDATE sources SET cursor=?,records=records+?,prefix_sha=?,selected_records=selected_records+? WHERE path=?',
                (offset,records,chain,len(pending),name))
        return dict(schema=SCHEMA,raw_bytes_read=len(raw),cursor=offset,catchup_end=end,
            complete=offset==end,selected_records=len(pending),wall_seconds=time.monotonic()-started)


def read_rows(data_root, path, *, kinds=None, identities=None, symbols=None, stages=None, after=None):
    """Read verified index rows only; missing coverage never scans the source."""
    with _database(data_root, path, readonly=True) as (db, path, namespace):
        name = str(path)
        start_generation=generation(data_root,path)
        state = db.execute('SELECT signature,catchup_end,cursor,producer_end,invalid FROM sources WHERE path=?', (name,)).fetchone()
        if (state is None or state[4] or state[1] != state[2]
                or json.loads(state[0]) != source_signature(data_root,path) or state[3] != source_signature(data_root,path)[2]):
            raise InputPending('trailing_index_coverage_incomplete')
        query, args = 'SELECT offset,size,raw_sha,body_sha,body FROM rows WHERE source=?', [name]
        for column, values in (('kind', kinds), ('identity', identities), ('symbol', symbols), ('stage', stages)):
            if values is not None:
                values = tuple(values)
                if not values:
                    return
                if len(values)>256:
                    raise ValueError('trailing_index_query_partition_required')
                query += ' AND '+column+' IN ('+','.join('?' for _ in values)+')';args.extend(values)
        if after is not None:
            query+=' AND emitted_at>=?';args.append(after)
        for offset, size, raw_sha, body_sha, body in db.execute(query+' ORDER BY offset', args):
            if len(body)>MAX_ROW_BYTES or hashlib.sha256(body).hexdigest()!=body_sha:
                raise ValueError('trailing_index_projection_changed')
            value=json.loads(body)
            if value.get('schema')!=SCHEMA:
                raise ValueError('trailing_index_projection_schema_invalid')
            yield value, dict(path=name, decoded_offset=offset, size=size, sha256=raw_sha)
        if generation(data_root,path)!=start_generation:
            raise InputPending('trailing_index_source_generation_changed')


def generation(data_root, path):
    """O(1) native coverage/chain identity, explicitly not a full-file SHA."""
    with _database(data_root,path,readonly=True) as (db,path,namespace):
        current=source_signature(data_root,path)
        state=db.execute('SELECT signature,catchup_end,cursor,producer_end,records,invalid,'
            'prefix_sha,append_sha,selected_records FROM sources WHERE path=?',(str(path),)).fetchone()
        if (state is None or state[5] or state[1]!=state[2] or state[3]!=current[2]
                or json.loads(state[0])!=current):
            raise InputPending('trailing_index_coverage_incomplete')
        body=dict(schema=SCHEMA+':generation',path=path.name,size=current[2],
            namespace=namespace,source_stat=current,catchup_end=state[1],
            raw_records=state[4],selected_records=state[8],prefix_chain_sha256=state[6],
            append_chain_sha256=state[7],whole_file_sha256=False)
        if source_signature(data_root,path)!=current:
            raise InputPending('trailing_index_source_generation_changed')
        result={**body,'sha256':hashlib.sha256(encode(body)).hexdigest()}
        if not path.is_file() and _archive_generation(data_root,path)!=result:
            raise ValueError('trailing_index_archive_source_head_changed')
        return result


def _archive_generation(data_root,path):
    path,_,_=_location(data_root,path)
    receipt=Path(str(path)+'.gz.archive_receipt.json');physical=Path(str(path)+'.gz')
    if (not receipt.is_file() or receipt.is_symlink() or receipt.stat().st_size>128*1024
            or physical.is_symlink()):
        raise InputPending('trailing_index_native_archive_binding_missing')
    before=signature(receipt.stat());raw=receipt.read_bytes();value=json.loads(raw)
    generation=value.get('trailing_source_index') or {}
    actual=signature(physical.stat());bound=value.get('archive_generation') or {}
    observed=[bound.get(key) for key in ('device','inode','size_bytes','mtime_ns','ctime_ns')]
    if (value.get('schema') not in {'pipeline_raw_archive_identity_v1','native_raw_archive_identity_v1'}
            or value.get('logical_path')!=str(path) or value.get('artifact_content_sha256')!=hashlib.sha256(
                encode({k:v for k,v in value.items() if k!='artifact_content_sha256'})).hexdigest()
            or value.get('verification_contract')!='logical_sha256_size_crc_to_eof_v1'
            or value.get('runtime_effect') is not False or value.get('allowed_runtime_apply') is not False
            or generation.get('schema')!=SCHEMA+':generation' or generation.get('path')!=path.name
            or generation.get('source_stat')!=value.get('trailing_source_identity')
            or generation.get('size')!=value.get('logical_size_bytes') or observed!=actual
            or signature(receipt.stat())!=before):
        raise ValueError('trailing_index_native_archive_binding_invalid')
    return generation


def source_signature(data_root,path):
    path,_,_=_location(data_root,path)
    if path.is_file():
        return signature(path.stat())
    return _archive_generation(data_root,path)['source_stat']


def input_generation(data_root, path):
    """Prefer native index coverage; large unindexed raw never scans inline."""
    path=Path(path)
    from src.engine.infrastructure.validation_digest_session import ACTIVE
    from src.engine.lifecycle.holding_window_generation import byte_generation
    active=ACTIVE.get()
    entry=active.entries.get(str(path.absolute()),{}) if active is not None else {}
    # An approved frozen input retains its original physical generation.
    if entry.get('native_generation_proof'):
        return byte_generation(path)
    logical,_,target=_location(data_root,path)
    if target.is_file():
        try:
            value=generation(data_root,logical)
        except InputPending:
            if path.is_file() and not path.name.endswith('.gz') and path.stat().st_size<=4*1024*1024:
                return byte_generation(path)
            raise
        if path.name.endswith('.jsonl.gz') and _archive_generation(data_root,logical)!=value:
            raise ValueError('trailing_index_archive_source_head_changed')
        return value
    if not path.is_file():
        raise InputPending('trailing_index_offline_archive_migration_required')
    if path.stat().st_size>4*1024*1024:
        raise InputPending('trailing_index_offline_migration_required:'+str(path))
    return byte_generation(path)


class IndexedReader:
    """A bounded projection stream retaining original physical row receipts."""
    def __init__(self,data_root,path,gaps):
        self.path=Path(path);self.gaps=gaps
        self.iterator=iter(read_rows(data_root,path))
        self.reference=None;self.native_capture_verified=False;self.offset=0
    def __enter__(self):return self
    def __exit__(self,*args):
        self.iterator.close()
    def tell(self):return self.offset
    def readline(self,limit):
        for value,reference in self.iterator:
            if value['kind']=='source_gap':
                self.gaps[value['reason']]+=1
                continue
            if value['kind'] in {'delay_receipt','holding_payload','holding_prompt','holding_request'}:
                continue
            raw=encode(value['row'])+b'\n'
            if len(raw)>limit:
                self.gaps['indexed_projection_budget_exceeded']+=1
                continue
            self.reference={**reference,'encoding':'plain',
                'native_source_index_schema':SCHEMA}
            self.native_capture_verified=(value['kind']=='machine_capture_projection'
                and value.get('original_native_observation_verified') is True
                and value.get('identity')==value['row'].get('machine_observation_sha256'))
            self.offset=reference['decoded_offset']+reference['size']
            return raw
        return b''


def open_input(data_root,path,generation,gaps):
    if generation.get('schema')==SCHEMA+':generation':
        return IndexedReader(data_root,path,gaps)
    import gzip
    claim_legacy_bytes(generation['size'])
    return gzip.open(path,'rb') if Path(path).suffix=='.gz' else Path(path).open('rb')


def row_reference(handle,path,offset,raw):
    if isinstance(handle,IndexedReader):
        return dict(handle.reference)
    return dict(path=str(path),decoded_offset=offset,size=len(raw),
        sha256=hashlib.sha256(raw).hexdigest(),encoding='gzip' if Path(path).suffix=='.gz' else 'plain')


def read_at(data_root,path,offset,expected_generation):
    """Exact native row lookup, never a raw seek or gzip rewind."""
    if generation(data_root,path)!=expected_generation:
        raise ValueError('trailing_index_reference_generation_changed')
    with _database(data_root,path,readonly=True) as (db,path,_):
        row=db.execute('SELECT body_sha,body,raw_sha FROM rows WHERE source=? AND offset=?',
            (str(path),offset)).fetchone()
        if row is None or hashlib.sha256(row[1]).hexdigest()!=row[0]:
            raise ValueError('trailing_index_reference_row_changed')
        value=json.loads(row[1])
        if value.get('schema')!=SCHEMA:
            raise ValueError('trailing_index_projection_schema_invalid')
        result=value.get('row');raw_sha=row[2]
    if generation(data_root,path)!=expected_generation:
        raise ValueError('trailing_index_reference_generation_changed')
    return result,raw_sha


def vote_rows(data_root,path,position_key,*,source_date=None,segments=True):
    """Exact position/date lookup; validates native coverage of each segment."""
    from src.engine.ai.holding_exit_vote import path_vote_store_path,validate_path_event
    base=path_vote_store_path(Path(data_root).resolve(),position_key)
    path=Path(path).resolve()
    if path.name!=base.name and not path.name.startswith(base.name+'.segment-'):
        raise ValueError('trailing_index_vote_position_mismatch')
    paths=(sorted(base.parent.glob(base.name+'.segment-*'))+([base] if base.is_file() else [])
        if segments else [path])
    if not paths:return
    for part in paths:
        before=generation(data_root,part)
        with _database(data_root,part,readonly=True) as (db,part,_):
            gaps=db.execute("SELECT count(*) FROM rows WHERE source=? AND kind='source_gap'",
                (str(part),)).fetchone()[0]
            if gaps:raise InputPending('trailing_index_vote_native_contract_gap')
            query="SELECT body_sha,body FROM rows WHERE source=? AND kind='holding_vote'"
            args=[str(part)]
            if source_date is not None:
                query+=' AND emitted_at<=?';args.append(source_date)
            for body_sha,body in db.execute(query+' ORDER BY offset',args):
                if len(body)>MAX_ROW_BYTES or hashlib.sha256(body).hexdigest()!=body_sha:
                    raise ValueError('trailing_index_projection_changed')
                value=json.loads(body)
                if value.get('schema')!=SCHEMA or value.get('kind')!='holding_vote':
                    raise ValueError('trailing_index_projection_schema_invalid')
                event=validate_path_event(value['row'],position_key)
                if event is not None:yield event
        if generation(data_root,part)!=before:
            raise InputPending('trailing_index_vote_generation_changed')


def scoped_vote_generation(data_root,path,source_date):
    """A logical position journal remains stable across later-session appends."""
    from src.engine.ai.holding_exit_vote import path_vote_store_path
    from src.engine.lifecycle import research_storage
    with _database(data_root,path,readonly=True) as (db,path,_):
        first=db.execute("SELECT body FROM rows WHERE source=? AND kind='holding_vote' ORDER BY offset LIMIT 1",
            (str(path),)).fetchone()
    if first is None:
        raise InputPending('trailing_index_vote_position_unobserved')
    position=json.loads(first[0])['row']['position_key']
    base=path_vote_store_path(Path(data_root).resolve(),position)
    sha=hashlib.sha256();count=size=0
    for row in vote_rows(data_root,path,position,source_date=source_date):
        raw=research_storage.encoded(row)+b'\n';sha.update(raw);count+=1;size+=len(raw)
    if not count:return None
    return dict(schema='main_trailing_historical_vote_inventory_v1',path=base.name,
        source_date=source_date,event_count=count,size=size,sha256=sha.hexdigest())


def _append_successor(before,after):
    return (before['source_stat'][:2]==after['source_stat'][:2]
        and before['size']<=after['size'] and before['raw_records']<after['raw_records']
        and before['catchup_end']==after['catchup_end']
        and before['prefix_chain_sha256']==after['prefix_chain_sha256']
        and before['selected_records']<=after['selected_records'])


def window(data_root,path,*,cutoff):
    """Pinned native raw-owned minutes/IDs, allowing certified later appends."""
    with _database(data_root,path,readonly=True) as (db,path,namespace):
        db.execute('BEGIN')
        current=source_signature(data_root,path)
        state=db.execute('SELECT signature,catchup_end,cursor,producer_end,records,invalid,'
            'prefix_sha,append_sha,selected_records FROM sources WHERE path=?',(str(path),)).fetchone()
        if (state is None or state[5] or state[1]!=state[2] or state[3]!=current[2]
                or json.loads(state[0])!=current):
            raise InputPending('trailing_index_coverage_incomplete')
        body=dict(schema=SCHEMA+':generation',path=path.name,size=current[2],
            namespace=namespace,source_stat=current,catchup_end=state[1],raw_records=state[4],
            selected_records=state[8],prefix_chain_sha256=state[6],append_chain_sha256=state[7],
            whole_file_sha256=False)
        before={**body,'sha256':hashlib.sha256(encode(body)).hexdigest()}
        minutes={minute+'|'+stage:dict(count=count,identity_sum=identity)
            for minute,stage,count,identity in db.execute('SELECT minute,stage,records,identity_sum '
                'FROM minutes WHERE source=? AND minute>=?',(str(path),cutoff))}
        gaps=db.execute("SELECT count(*) FROM rows WHERE source=? AND kind='source_gap' "
            'AND (emitted_at IS NULL OR emitted_at>=?)',(str(path),cutoff)).fetchone()[0]
        rows=[];retained_bytes=0
        for body_sha,body in db.execute("SELECT body_sha,body FROM rows WHERE source=? "
                "AND kind='delay_receipt' AND emitted_at>=? ORDER BY offset",(str(path),cutoff)):
            if len(body)>MAX_ROW_BYTES or hashlib.sha256(body).hexdigest()!=body_sha:
                raise ValueError('trailing_index_projection_changed')
            value=json.loads(body)
            if value.get('schema')!=SCHEMA or value.get('kind')!='delay_receipt':
                raise ValueError('trailing_index_projection_schema_invalid')
            if len(rows)>=8192 or retained_bytes+len(body)>16*1024*1024:
                raise InputPending('trailing_index_window_partition_required')
            retained_bytes+=len(body);rows.append(value['row'])
        db.rollback()
    after=generation(data_root,path)
    if after!=before and not _append_successor(before,after):
        raise InputPending('trailing_index_source_generation_changed')
    return dict(generation=before,minutes=minutes,rows=rows,source_gaps=gaps,
        verified_append_after_snapshot=after!=before,
        coverage_started_at=path.name[len(path.parent.name)+1:len(path.parent.name)+11]+'T00:00:00+09:00')


def claim_legacy_bytes(size):
    budget=_COMPAT_DECODE.get()
    if type(size) is not int or size>32*1024*1024:
        raise InputPending('trailing_index_offline_migration_required')
    if budget is not None:
        if size>budget['remaining']:
            raise InputPending('trailing_legacy_decode_budget_exceeded')
        budget['remaining']-=size


@contextmanager
def native_input_session(data_root,day):
    """Bound normal indexed research; native writer proofs admit large files."""
    from src.engine.infrastructure.validation_digest_session import postclose_session
    with postclose_session(data_root,day) as session:
        token=None
        if _COMPAT_DECODE.get() is None:
            token=_COMPAT_DECODE.set(dict(remaining=32*1024*1024))
        previous=session.native_read_budget
        if previous is None:
            session.native_read_budget=dict(remaining=32*1024*1024)
        try:
            yield session
        finally:
            session.native_read_budget=previous
            if token is not None:_COMPAT_DECODE.reset(token)


def main(argv=None):
    """One bounded offline migration step; never loop over the whole source."""
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root',type=Path,required=True)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--max-bytes',type=int,default=MAX_STEP_BYTES)
    parser.add_argument('--seconds',type=float,default=1.)
    args=parser.parse_args(argv)
    print(json.dumps(build_step(args.data_root,args.source,max_bytes=args.max_bytes,seconds=args.seconds)))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
