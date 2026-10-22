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
DEFAULT_START_DATE = '2026-09-29'
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
_READERS = ContextVar('trailing_source_read_connections', default=None)


def _after_fork():
    global _WRITERS, _WRITER_LOCK, _MAINTENANCE_THREAD, _MAINTENANCE_LOCK, _PENDING_LOCK, _PENDING_BYTES
    _WRITERS = OrderedDict()
    _WRITER_LOCK = threading.RLock()
    _MAINTENANCE_THREAD = None
    _MAINTENANCE_LOCK = threading.Lock()
    _MAINTENANCE.clear();_CHECKPOINTS.clear();_VOTE_BACKFILL.clear()
    _PENDING_LOCK=threading.RLock();_PENDING_APPENDS.clear();_PENDING_BYTES=0
    _READERS.set(None)


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
                log_error('[TRAILING_SOURCE_INDEX_GAP] source='+str(path)+' reason='+type(exc).__name__+' detail='+str(exc)[:160])
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
    """Retry resident bytes; an explicit prefix migration owns earlier bytes."""
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
                with _database(root, name, readonly=True) as (db, _, _):
                    prefix = db.execute('SELECT signature,catchup_end,invalid FROM sources WHERE path=?', (name,)).fetchone()
                covered_prefix = (prefix and not prefix[2] and json.loads(prefix[0])[:2] == list(after)[:2]
                                  and after[2] <= prefix[1])
                rows=[json.loads(line) for line in raw.splitlines()]
                if not covered_prefix and not record_append(root,name,before=before,after=after,
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


def _recover_append_gap(data_root, path):
    """Preserve a stuck cache, then restart bounded full-prefix verification.

    Snapshot I/O happens outside the native writer locks. The short reset is
    source-only; build_step must verify every prefix byte before consumption.
    """
    import fcntl
    path, namespace, target = _location(data_root, path)
    if namespace != 'pipeline_events' or not target.is_file():
        return False
    snapshot_deadline = time.monotonic() + .5
    with _database(data_root, path, readonly=True) as (db, _, _):
        state = db.execute('SELECT * FROM sources WHERE path=?', (str(path),)).fetchone()
        if state is None or state[6] != 'append_chain_gap':
            return False
        current = source_signature(data_root, path)
        if current[:2] != json.loads(state[1])[:2] or current[2] < state[4]:
            return False
        if db.execute('PRAGMA page_count').fetchone()[0] * db.execute('PRAGMA page_size').fetchone()[0] > 64*1024*1024:
            raise InputPending('trailing_index_recovery_snapshot_budget_exceeded')
        archive = target.with_name(target.stem+'.append-gap-'+hashlib.sha256(encode(state)).hexdigest()[:24]+'.sqlite')
        if archive.is_symlink():
            raise InputPending('trailing_index_recovery_archive_untrusted')
        if not archive.exists():
            temporary = archive.with_name(archive.name+'.'+str(os.getpid())+'.tmp')
            fd = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
            os.close(fd)
            snapshot = None
            try:
                snapshot = sqlite3.connect(temporary)
                def progress(*_):
                    if time.monotonic() >= snapshot_deadline:
                        raise InputPending('trailing_index_recovery_snapshot_pending')
                db.backup(snapshot, pages=64, progress=progress, sleep=0)
                snapshot.close(); snapshot = None
                try: os.link(temporary, archive, follow_symlinks=False)
                except FileExistsError: pass
            finally:
                if snapshot is not None: snapshot.close()
                temporary.unlink(missing_ok=True)
    metadata = archive.lstat()
    if (not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != os.getuid() or metadata.st_mode & 0o077):
        raise InputPending('trailing_index_recovery_archive_untrusted')
    saved = sqlite3.connect('file:'+str(archive)+'?mode=ro', uri=True, timeout=0)
    try:
        saved.set_progress_handler(lambda: int(time.monotonic() >= snapshot_deadline), 1000)
        if (saved.execute('PRAGMA quick_check').fetchone()[0] != 'ok'
                or saved.execute('SELECT * FROM sources WHERE path=?', (str(path),)).fetchone() != state):
            raise InputPending('trailing_index_recovery_archive_invalid')
    finally:
        saved.close()
    from src.utils.pipeline_event_logger import _pipeline_event_partition_lock_path
    descriptor = os.open(_pipeline_event_partition_lock_path(path),
        os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    source_descriptor = None
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise InputPending('trailing_index_recovery_partition_lock_invalid')
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            source_descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
            if not stat.S_ISREG(os.fstat(source_descriptor).st_mode):
                raise InputPending('trailing_index_source_not_regular')
            fcntl.flock(source_descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return False
        deadline = time.monotonic() + .05
        with _database(data_root, path, writer=True, existing_only=True) as (db, _, _):
            name = str(path)
            if (db.execute('SELECT * FROM sources WHERE path=?', (name,)).fetchone() != state
                    or signature(archive.lstat()) != signature(metadata)):
                raise InputPending('trailing_index_recovery_generation_changed')
            current = source_signature(data_root, path)
            if current[:2] != json.loads(state[1])[:2] or current[2] < state[4]:
                return False
            db.set_progress_handler(lambda: int(time.monotonic() >= deadline), 1000)
            try:
                with db:
                    db.execute('DELETE FROM rows WHERE source=?', (name,))
                    db.execute('DELETE FROM minutes WHERE source=?', (name,))
                    db.execute('DELETE FROM sources WHERE path=?', (name,))
                    db.execute('INSERT INTO sources VALUES(?,?,?,?,?,?,?,?,?,?)',
                        (name, encode(current).decode(), current[2], 0, current[2], 0, None, ZERO_SHA, ZERO_SHA, 0))
            finally:
                db.set_progress_handler(None, 0)
            global _PENDING_BYTES
            with _PENDING_LOCK:
                old = _PENDING_APPENDS.pop(name, [])
                _PENDING_BYTES -= sum(len(receipt[2]) for receipt in old)
        result = dict(status='rebuild_pending', archive=str(archive), catchup_end=current[2])
    finally:
        if source_descriptor is not None: os.close(source_descriptor)
        os.close(descriptor)
    from src.utils.logger import log_info
    log_info('[TRAILING_SOURCE_INDEX_RECOVERY] source='+name+' status=rebuild_pending archive='+str(archive))
    return result


def prepare_for_day(data_root,day):
    """Fixed-size preparation before Main starts collecting/evaluating."""
    for namespace in STREAM_NAMESPACES:
        path=Path(data_root)/namespace/(namespace+'_'+day+'.jsonl')
        with _database(data_root,path,writer=True):
            pass
    target=_index_path(Path(data_root).resolve(),'holding_path_votes',None)
    if target.is_file():
        with _connection(target,writer=True,existing_only=True):
            pass
    maintain(data_root,day)


def _maintain_once(data_root, day, turn=0):
    """No broker/provider/strategy authority; at most one 8 MiB catch-up."""
    if not Path(data_root).is_dir():
        return
    _index_path(Path(data_root).resolve(),'pipeline_events',day)
    _drain_pending(data_root)
    key=(str(data_root), day)
    now=time.monotonic()
    if now-_MAINTENANCE.get(key,float('-inf'))<.5:
        return
    _MAINTENANCE[key]=now
    while len(_MAINTENANCE)>3:
        _MAINTENANCE.pop(next(iter(_MAINTENANCE)))
    for namespace in NAMESPACES:
        target=_index_path(Path(data_root).resolve(),namespace,day)
        name=str(target)
        # The vote DB is global, including across day rollover. Never create
        # an empty vote DB on behalf of a report reader or maintenance turn.
        if namespace=='holding_path_votes' and not target.is_file():
            continue
        due=now-_CHECKPOINTS.get(name,float('-inf'))>=60
        if not due and namespace!='holding_path_votes':
            continue
        if due:
            _CHECKPOINTS[name]=now
            while len(_CHECKPOINTS)>12:_CHECKPOINTS.pop(next(iter(_CHECKPOINTS)))
        started=time.monotonic()
        try:
            with _connection(target,writer=True,existing_only=target.is_file()):
                pass
            if not due:
                continue  # Re-pin a vote connection evicted by other-day preparation.
            # Separate background connection: no native append mutex, schema
            # writes or blocking FULL/RESTART/TRUNCATE checkpoint.
            with _connection(target,existing_only=True) as db:
                busy,frames,copied=db.execute('PRAGMA wal_checkpoint(PASSIVE)').fetchone()
            progress=dict(complete=busy==0 and frames==copied,
                busy=busy,wal_frames=frames,checkpointed_frames=copied)
        except (InputPending,sqlite3.OperationalError) as exc:
            progress=dict(complete=False,reason=str(exc)[:160],
                **getattr(exc,'sqlite_context',{}))
        _MAINTENANCE_STATUS[name]=dict(progress,wall_seconds=time.monotonic()-started,
            observed_epoch=time.time())
        while len(_MAINTENANCE_STATUS)>12:_MAINTENANCE_STATUS.popitem(last=False)
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
            recovery = None
            if isinstance(exc, InputPending) and str(exc) == 'trailing_index_source_generation_changed':
                try:
                    recovery = _recover_append_gap(data_root, path)
                except (InputPending, OSError, sqlite3.Error) as pending:
                    recovery = dict(status='pending', reason=str(pending)[:160])
            _MAINTENANCE_STATUS[str(path)]=dict(complete=False,reason=str(exc)[:160],
                recovery=recovery,observed_epoch=time.time())
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
    'machine_bundle_sha256', 'entry_mechanistic_action', 'machine_observation_sha256',
    # Existing report-only provider lineage consumes this bounded projection.
    'async_request_id', 'async_producer_pid', 'async_producer_start_ticks',
    'request_id', 'prompt_sha256', 'request_envelope_sha256', 'payload_semantic_sha256',
    'provider_response_id', 'response_sha256', 'timeout', 'transport_timing',
    'entry_ai_contract_errors', 'entry_ai_raw_risk_verdict', 'entry_ai_raw_fields_invalid_shape',
    'entry_ai_raw_fields_present', 'entry_ai_raw_fields_source', 'entry_ai_raw_fields_truncated',
    'entry_ai_raw_response_sha256', 'entry_ai_raw_risk_codes', 'entry_ai_raw_supporting_fact_ids',
    'entry_ai_raw_contradicting_fact_ids', 'entry_ai_screen_status',
    'entry_auxiliary_response_contract_valid', 'entry_post_response_execution_valid',
    'entry_source_invalid_primary_blocker', 'machine_contract_error', 'reason',
    'effective_venue', 'continuous_reversal_rejected_claim_receipt', 'actual_order_submitted')


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
                     lineage_projection_version=1,
                     row={key: row[key] for key in TRACE_FIELDS if key in row})
    elif namespace == 'pipeline_events':
        if (row.get('pipeline') == 'HOLDING_PIPELINE'
                and row.get('stage') in {'position_rebased_after_fill', 'scale_in_executed'}):
            # The cost producer needs original broker BUY observations, not
            # only the preceding order intent. Keep the native envelope.
            value = dict(kind='pipeline_fill_receipt', identity=str(row.get('record_id')), row=row)
            if len(encode(value)) > MAX_ROW_BYTES:
                return dict(kind='source_gap', reason='projection_record_budget_exceeded',
                            identity=value['identity'])
            return value
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


def _index_path(root,namespace,day):
    directory=root/'report/main_trailing_source_index'
    if namespace=='holding_path_votes':return directory/'holding_path_votes.sqlite'
    from datetime import date
    if (namespace not in STREAM_NAMESPACES or not isinstance(day,str)
            or date.fromisoformat(day).isoformat()!=day):
        raise ValueError('trailing_index_source_date_invalid')
    return directory/day/(namespace+'.sqlite')


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
        return path,namespace,_index_path(root,namespace,None)
    day=path.name[len(namespace)+1:len(namespace)+11]
    if not path.name.startswith(namespace+'_'):
        raise ValueError('trailing_index_source_date_invalid')
    return path,namespace,_index_path(root,namespace,day)


def _close_reader(entry):
    try:entry['db'].close()
    finally:entry['claim'].close()


@contextmanager
def read_session(data_root):
    """Reuse bounded connections, never rows/verdicts or read transactions."""
    root=Path(data_root).resolve()
    owner=(os.getpid(),threading.get_ident())
    active=_READERS.get()
    if active is not None and active['root']==root and active['owner']==owner:
        yield
        return
    session=dict(root=root,owner=owner,entries=OrderedDict())
    token=_READERS.set(session)
    try:
        yield
    finally:
        _READERS.reset(token)
        if session['owner']==(os.getpid(),threading.get_ident()):
            for entry in session['entries'].values():_close_reader(entry)


def _sqlite_context(exc,target,phase):
    if not hasattr(exc,'sqlite_context'):
        exc.sqlite_context=dict(database=str(target),database_phase=phase,
            sqlite_errorcode=getattr(exc,'sqlite_errorcode',None),
            sqlite_errorname=getattr(exc,'sqlite_errorname',None))
        exc.add_note('trailing_source_database='+str(target)+' phase='+phase)


@contextmanager
def _database(data_root, path, *, readonly=False, writer=False, existing_only=False):
    path, namespace, target = _location(data_root, path)
    with _connection(target,readonly=readonly,writer=writer,existing_only=existing_only) as db:
        yield db,path,namespace


@contextmanager
def _connection(target, *, readonly=False, writer=False, existing_only=False):
    if (readonly or existing_only) and not target.is_file():
        raise InputPending('trailing_index_coverage_incomplete')
    if not readonly and not existing_only and not target.parent.is_dir():
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if target.is_file():
        owner=target.stat()
        if not stat.S_ISREG(owner.st_mode) or owner.st_uid!=os.getuid() or owner.st_mode&0o077:
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
    cached=None;borrowed=False
    try:
        session=_READERS.get() if readonly else None
        if (session is not None and session['owner']==(os.getpid(),threading.get_ident())
                and target.is_relative_to(session['root'])):
            entries=session['entries']
            cached=entries.get(str(target))
            identity=(target.stat().st_dev,target.stat().st_ino)
            if cached is not None and cached['identity']!=identity:
                raise InputPending('trailing_index_database_generation_changed')
            if cached is None:
                if len(entries)>=6:
                    old=next((name for name,value in entries.items() if not value['users']),None)
                    if old is None:raise InputPending('trailing_index_read_session_partition_required')
                    _close_reader(entries.pop(old))
                from src.engine.lifecycle.research_input_budget import Claim
                claim=Claim(2*1024*1024)
                try:db=_open_database(target,readonly=True,writer=False)
                except BaseException:
                    claim.close();raise
                cached=dict(db=db,identity=identity,users=0,claim=claim)
                entries[str(target)]=cached
            db=cached['db'];cached['users']+=1;borrowed=True
            entries.move_to_end(str(target))
        if db is None:
            db=_open_database(target,readonly=readonly,writer=False,initialize=not existing_only)
        yield db
        if borrowed and (target.is_symlink()
                or (target.stat().st_dev,target.stat().st_ino)!=cached['identity']):
            raise InputPending('trailing_index_database_generation_changed')
    except sqlite3.Error as exc:
        _sqlite_context(exc,target,'read' if readonly else 'write')
        raise
    finally:
        if borrowed:
            cached['users']-=1
            if not cached['users'] and db.in_transaction:
                db.rollback()
        elif db is not None and not writer:
            db.close()
        if lock is not None:
            lock.release()


def _open_database(target, *, readonly, writer, initialize=True):
    db=None;phase='connect'
    try:
        db = (sqlite3.connect('file:'+str(target)+'?mode=ro', uri=True, timeout=.005)
              if readonly else sqlite3.connect('file:'+str(target)+('?mode=rwc' if initialize else '?mode=rw'),uri=True,timeout=.005,check_same_thread=not writer))
        phase='configure'
        db.execute('PRAGMA cache_size=-2048')
        version=db.execute('PRAGMA user_version').fetchone()[0] if not readonly else None
        if not readonly and version!=1:
            if not initialize or version!=0:
                raise InputPending('trailing_index_schema_not_prepared')
            phase='initialize'
            os.chmod(target,0o600)
            db.execute('PRAGMA journal_mode=WAL')
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
        if not readonly:
            phase='configure'
            if db.execute('PRAGMA journal_mode').fetchone()[0]!='wal':
                raise InputPending('trailing_index_schema_not_prepared')
            db.execute('PRAGMA synchronous=NORMAL')
            if writer or not initialize:db.execute('PRAGMA wal_autocheckpoint=0')
        return db
    except BaseException as exc:
        if isinstance(exc,sqlite3.Error):_sqlite_context(exc,target,phase)
        if db is not None:db.close()
        raise


def _encoded_projection(value):
    return encode(dict(value,schema=SCHEMA)) if value is not None else b''


def _leaf(offset, raw, body):
    return hashlib.sha256(encode([offset,len(raw),hashlib.sha256(raw).hexdigest(),
        hashlib.sha256(body).hexdigest() if body else None])).hexdigest()


def _put(db, source, offset, raw, value, *, raw_identity=None):
    body=_encoded_projection(value)
    size,raw_sha=raw_identity or (len(raw),hashlib.sha256(raw).hexdigest())
    leaf=hashlib.sha256(encode([offset,size,raw_sha,
        hashlib.sha256(body).hexdigest() if body else None])).hexdigest()
    if value is None:
        return leaf
    old=db.execute('SELECT raw_sha,body_sha FROM rows WHERE source=? AND offset=?',
        (source,offset)).fetchone()
    pair=(raw_sha,hashlib.sha256(body).hexdigest())
    if old is not None and old!=pair:
        raise ValueError('trailing_index_record_conflict')
    row=value.get('row') or {}
    db.execute('INSERT OR IGNORE INTO rows VALUES(?,?,?,?,?,?,?,?,?,?,?)',
        (source,offset,size,*pair,value['kind'],value.get('identity'),
         row.get('stock_code') or row.get('symbol'),row.get('stage'),
         row.get('emitted_at') or row.get('session_key') or row.get('decision_ts') or row.get('captured_at'),body))
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


def read_rows(data_root, path, *, kinds=None, identities=None, symbols=None, stages=None, after=None,
              snapshot_receipt=None, include_undated=False):
    """Read verified rows; an explicit receipt may admit certified later appends."""
    with read_session(data_root), _database(data_root, path, readonly=True) as (db, path, namespace):
        if snapshot_receipt is not None:
            db.execute('BEGIN')
        name = str(path)
        start_generation=generation(data_root,path)
        state = db.execute('SELECT signature,catchup_end,cursor,producer_end,invalid FROM sources WHERE path=?', (name,)).fetchone()
        observed_signature = (start_generation['source_stat'] if snapshot_receipt is not None
            else source_signature(data_root,path))
        if (state is None or state[4] or state[1] != state[2]
                or json.loads(state[0]) != observed_signature or state[3] != start_generation['size']):
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
            query+=(' AND (emitted_at>=? OR emitted_at IS NULL)' if include_undated
                    else ' AND emitted_at>=?');args.append(after)
        for offset, size, raw_sha, body_sha, body in db.execute(query+' ORDER BY offset', args):
            if len(body)>MAX_ROW_BYTES or hashlib.sha256(body).hexdigest()!=body_sha:
                raise ValueError('trailing_index_projection_changed')
            value=json.loads(body)
            if value.get('schema')!=SCHEMA:
                raise ValueError('trailing_index_projection_schema_invalid')
            yield value, dict(path=name, decoded_offset=offset, size=size, sha256=raw_sha)
        if snapshot_receipt is not None:
            # All pinned rows have been consumed. Validate the live successor
            # outside that read snapshot, including when a session reuses db.
            db.rollback()
        end_generation = generation(data_root,path)
        if end_generation != start_generation and (
                snapshot_receipt is None or not _append_successor(start_generation, end_generation)):
            raise InputPending('trailing_index_source_generation_changed')
        if snapshot_receipt is not None:
            snapshot_receipt.update(generation=start_generation,
                verified_append_after_snapshot=end_generation != start_generation)


def read_order_fill_windows(data_root, path, record_ids, *, expected_generation, consume):
    """Producer-only bounded migration of pre-index BUY fill observations.

    Report readers never call this. Each cost revision is its own durable
    checkpoint; its native source generation prevents unchanged rescans.
    Original order anchors, raw bytes and source identity are all verified.
    """
    import gzip
    from src.engine.lifecycle.research_input_budget import Claim
    wanted = {str(record) for record in record_ids}
    if not wanted or len(wanted) > 6:
        raise ValueError('research_buy_window_population_budget')
    logical = Path(path)
    if generation(data_root, logical) != expected_generation:
        raise ValueError('research_buy_window_generation_changed')
    anchors = []
    for value, reference in read_rows(data_root, logical, kinds=['pipeline_receipt'], stages=['order_leg_sent']):
        if str(value['row'].get('record_id')) in wanted:
            anchors.append((str(value['row']['record_id']), reference))
    intervals = []
    for record in wanted:
        offsets = [ref['decoded_offset'] for rid, ref in anchors if rid == record]
        if offsets:
            start = min(offsets)
            intervals.append((start, min(start + 4 * 1024 * 1024, expected_generation['size'])))
    merged = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1]: merged[-1][1] = max(end, merged[-1][1])
        else: merged.append([start, end])
    physical = logical if logical.exists() else Path(str(logical) + '.gz')
    if (sum(end-start for start,end in merged) > 24 * 1024 * 1024
            or physical.suffix == '.gz' and merged and merged[-1][1] > 3_000_000_000):
        raise ValueError('research_buy_window_byte_budget')
    started = time.monotonic()
    expected_anchors = {ref['decoded_offset']:ref for _,ref in anchors
                        if any(start <= ref['decoded_offset'] < end for start,end in merged)}
    seen, recovered, selected, retained = set(), 0, 0, 0
    row_limit = 256 * 1024
    oversize = 0
    physical_identity = signature(physical.lstat())
    descriptor = os.open(physical, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as packed, Claim(row_limit * 12):
        if (not stat.S_ISREG(os.fstat(packed.fileno()).st_mode)
                or signature(os.fstat(packed.fileno())) != physical_identity):
            raise ValueError('research_buy_window_generation_changed')
        stream = gzip.GzipFile(fileobj=packed) if physical.suffix == '.gz' else packed
        try:
            for start,end in merged:
                if time.monotonic()-started > 90:
                    raise ValueError('research_buy_window_time_budget')
                stream.seek(start)
                offset = start
                while offset < end:
                    line = stream.readline(min(row_limit + 1, end-offset))
                    if not line: break
                    size = len(line); raw_sha = hashlib.sha256(line)
                    complete = line.endswith(b'\n')
                    original = line if size <= row_limit else None
                    while not complete and offset + size < end:
                        chunk = stream.readline(min(row_limit + 1, end-offset-size))
                        if not chunk: break
                        raw_sha.update(chunk); size += len(chunk)
                        complete = chunk.endswith(b'\n')
                        original = None
                    selected += size
                    if not complete: break
                    sha = raw_sha.hexdigest()
                    anchor = expected_anchors.get(offset)
                    if anchor is not None:
                        if size != anchor['size'] or sha != anchor['sha256']:
                            raise ValueError('research_buy_window_anchor_changed')
                        seen.add(offset)
                    if original is not None:
                        row = json.loads(original)
                        if (str(row.get('record_id')) in wanted and row.get('pipeline') == 'HOLDING_PIPELINE'
                                and row.get('stage') in {'position_rebased_after_fill', 'scale_in_executed'}):
                            retained += size
                            if retained > 1024 * 1024:
                                raise ValueError('research_buy_window_retained_budget')
                            # Transfer only admitted retained data to the cost
                            # producer; no cross-date raw event list is kept.
                            consume(row, dict(path=str(logical), decoded_offset=offset,
                                              size=size, sha256=sha))
                            recovered += 1
                    else:
                        oversize += 1
                    offset += size
                if time.monotonic()-started > 90:
                    raise ValueError('research_buy_window_time_budget')
            physical_read = packed.tell()
            if signature(os.fstat(packed.fileno())) != physical_identity:
                raise ValueError('research_buy_window_generation_changed')
        finally:
            if stream is not packed: stream.close()
    if (seen != set(expected_anchors) or signature(physical.lstat()) != physical_identity
            or generation(data_root, logical) != expected_generation):
        raise ValueError('research_buy_window_generation_changed')
    return dict(selected_bytes=selected, physical_bytes_read=physical_read,
                        decoded_prefix_bytes=merged[-1][1] if merged else 0,
                        wall_seconds=time.monotonic()-started, recovered_events=recovered,
                        oversize_rows_skipped=oversize)


def generation(data_root, path):
    """O(1) native coverage/chain identity, explicitly not a full-file SHA."""
    with _database(data_root,path,readonly=True) as (db,path,namespace):
        current=source_signature(data_root,path)
        archived=None if path.is_file() else _archive_generation(data_root,path)
        logical_size=current[2] if archived is None else archived['size']
        state=db.execute('SELECT signature,catchup_end,cursor,producer_end,records,invalid,'
            'prefix_sha,append_sha,selected_records FROM sources WHERE path=?',(str(path),)).fetchone()
        if (state is None or state[5] or state[1]!=state[2] or state[3]!=logical_size
                or json.loads(state[0])!=current):
            raise InputPending('trailing_index_coverage_incomplete')
        body=dict(schema=SCHEMA+':generation',path=path.name,size=logical_size,
            namespace=namespace,source_stat=current,catchup_end=state[1],
            raw_records=state[4],selected_records=state[8],prefix_chain_sha256=state[6],
            append_chain_sha256=state[7],whole_file_sha256=False)
        if source_signature(data_root,path)!=current:
            raise InputPending('trailing_index_source_generation_changed')
        result={**body,'sha256':hashlib.sha256(encode(body)).hexdigest()}
        if archived is not None and _archive_generation(data_root,path)!=result:
            raise ValueError('trailing_index_archive_source_head_changed')
        return result


def _archive_logical_authority(path,*,allow_legacy=False):
    """Keep an existing archiver's full logical seal authoritative."""
    receipt=Path(str(path)+'.gz.archive_receipt.json')
    if not receipt.exists() and not receipt.is_symlink():return None
    metadata=receipt.lstat();before=signature(metadata)
    if (not stat.S_ISREG(metadata.st_mode) or metadata.st_uid!=os.getuid()
            or metadata.st_size>128*1024):
        raise ValueError('trailing_index_native_archive_binding_invalid')
    fd=os.open(receipt,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
    with os.fdopen(fd,'rb') as stream:
        if signature(os.fstat(stream.fileno()))!=before:
            raise ValueError('trailing_index_archive_receipt_changed')
        raw=stream.read(128*1024+1)
        if signature(os.fstat(stream.fileno()))!=before or signature(receipt.lstat())!=before:
            raise ValueError('trailing_index_archive_receipt_changed')
    value=json.loads(raw)
    import re
    if not isinstance(value,dict):raise ValueError('trailing_index_native_archive_binding_invalid')
    legacy=(allow_legacy and value.get('schema')=='pipeline_raw_archive_identity_v1'
        and set(value)<=set(('schema','logical_path','logical_content_sha256','logical_size_bytes',
            'storage_custody','storage_disposition','archive_generation','runtime_effect','allowed_runtime_apply')))
    required=('device','inode','size_bytes','mtime_ns')+(() if legacy else ('ctime_ns',))
    declared=value.get('logical_size_bytes');physical=value.get('archive_generation')
    if (len(raw)!=metadata.st_size
            or value.get('schema') not in {'pipeline_raw_archive_identity_v1','native_raw_archive_identity_v1'}
            or value.get('logical_path')!=str(path)
            or not legacy and (value.get('artifact_content_sha256')!=hashlib.sha256(encode({
                k:v for k,v in value.items() if k!='artifact_content_sha256'})).hexdigest()
                or value.get('verification_contract')!='logical_sha256_size_crc_to_eof_v1')
            or value.get('runtime_effect') is not False or value.get('allowed_runtime_apply') is not False
            or ('logical_size_bytes' in value or not legacy) and (type(declared) is not int or declared<0)
            or not isinstance(physical,dict)
            or any(type(physical.get(k)) is not int or physical[k]<0 for k in required)
            or legacy and (set(physical) not in (set(required),set(required)|{'ctime_ns'})
                or 'ctime_ns' in physical and (type(physical['ctime_ns']) is not int or physical['ctime_ns']<0))
            or not isinstance(value.get('logical_content_sha256'),str)
            or re.fullmatch('[0-9a-f]{64}',value['logical_content_sha256']) is None):
        raise ValueError('trailing_index_native_archive_binding_invalid')
    return value,before


def _archive_generation(data_root,path):
    path,_,target=_location(data_root,path)
    receipt=Path(str(path)+'.gz.archive_receipt.json');physical=Path(str(path)+'.gz')
    # Offline enrollment owns a physical gzip identity, not an invented old
    # plain-file inode. Its SQLite metadata is published only after CRC EOF.
    if target.is_file():
        with _database(data_root,path,readonly=True) as (db,_,_):
            if db.execute("SELECT 1 FROM sqlite_master WHERE name='archive_migrations'").fetchone():
                saved=db.execute('SELECT body FROM archive_migrations WHERE path=?',(str(path),)).fetchone()
                if saved:
                    value=json.loads(saved[0]);bound=value['generation']
                    authority=_archive_logical_authority(path,allow_legacy=True)
                    if authority is not None and (value['logical_content_sha256']!=authority[0]['logical_content_sha256']
                            or 'logical_size_bytes' in authority[0] and value['logical_size_bytes']!=authority[0]['logical_size_bytes']):
                        raise ValueError('trailing_index_archive_logical_authority_changed')
                    if (physical.is_symlink() or path.exists()
                            or signature(physical.stat())!=bound['source_stat']
                            or value.get('schema')!='trailing_archive_migration_v1'
                            or value.get('source_identity_kind')!='physical_gzip'
                            or value.get('verification_contract')!='logical_sha256_size_crc_to_eof_v1'
                            or value.get('runtime_effect') is not False or value.get('allowed_runtime_apply') is not False
                            or any(not isinstance(value.get(key),str) or len(value[key])!=64
                                   for key in ('logical_content_sha256','archive_sha256'))
                            or value.get('logical_size_bytes')!=bound['size']
                            or value.get('artifact_content_sha256')!=hashlib.sha256(encode({
                                k:v for k,v in value.items() if k!='artifact_content_sha256'})).hexdigest()):
                        raise ValueError('trailing_index_archive_migration_changed')
                    return bound
    authority=_archive_logical_authority(path,allow_legacy=True)
    if authority is None or physical.is_symlink():
        raise InputPending('trailing_index_native_archive_binding_missing')
    value,before=authority
    if not value.get('trailing_source_index'):
        raise InputPending('trailing_index_offline_archive_migration_required')
    _archive_logical_authority(path)  # O(1) native index reuse still requires the modern writer proof.
    generation=value.get('trailing_source_index') or {}
    actual=signature(physical.stat());bound=value.get('archive_generation') or {}
    observed=[bound.get(key) for key in ('device','inode','size_bytes','mtime_ns','ctime_ns')]
    if (generation.get('schema')!=SCHEMA+':generation' or generation.get('path')!=path.name
            or generation.get('source_stat')!=value.get('trailing_source_identity')
            or generation.get('size')!=value.get('logical_size_bytes') or observed!=actual
            or signature(receipt.stat())!=before):
        raise ValueError('trailing_index_native_archive_binding_invalid')
    return generation


def migrate_frozen_source(data_root,path):
    """Explicit one-pass frozen enrollment; never called by a report reader.

    Original gzip/receipts remain byte-identical. A private SQLite generation
    retains decoded row offsets, raw hashes and a full logical SHA/CRC proof.
    The logical source is never restored to disk. Failed private builds remain
    available for diagnosis and cannot advertise complete coverage.
    """
    import gzip
    import uuid
    from src.utils.jsonl_io import jsonl_artifact_generation_lock
    from src.engine.lifecycle.research_input_budget import Claim
    logical,namespace,target=_location(data_root,path)
    archived=not logical.exists()
    physical=Path(str(logical)+'.gz') if archived else logical
    with jsonl_artifact_generation_lock(logical,exclusive=True),Claim(MAX_ROW_BYTES*12):
        if logical.is_symlink() or physical.is_symlink() or (archived and logical.exists()):
            raise ValueError('trailing_archive_migration_source_invalid')
        metadata=physical.stat()
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_uid!=os.getuid():
            raise ValueError('trailing_archive_migration_source_invalid')
        if target.is_symlink():raise ValueError('trailing_index_database_path_invalid')
        if target.exists():
            try:return generation(data_root,logical)
            except InputPending:pass
        if any(p.is_symlink() for p in target.parents):
            raise ValueError('trailing_index_database_path_invalid')
        current=signature(metadata);target.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
        authority=_archive_logical_authority(logical,allow_legacy=True) if archived else None
        # A legacy compressor may omit the native archive receipt. Preserve
        # the complete issued index's prefix/append boundary only by replaying
        # both raw-record chains to EOF, never by trusting old metadata alone.
        original_index=None
        if archived and target.exists():
            with _database(data_root,logical,readonly=True) as (existing,_,_):
                saved=existing.execute('SELECT * FROM sources WHERE path=?',(str(logical),)).fetchone()
            if saved and not saved[6] and saved[2]==saved[3]:
                original_index=saved
        temporary=target.with_name(target.name+'.archive-'+uuid.uuid4().hex+'.tmp')
        db=_open_database(temporary,readonly=False,writer=False)
        name=str(logical);offset=records=selected=0;chain=ZERO_SHA;logical_sha=hashlib.sha256()
        prefix_chain=append_chain=ZERO_SHA
        try:
            with physical.open('rb') as raw:
                archive_sha=hashlib.file_digest(raw,'sha256').hexdigest() if archived else None
                if archived:raw.seek(0)
                if signature(os.fstat(raw.fileno()))!=current:
                    raise ValueError('trailing_archive_migration_source_changed')
                from contextlib import nullcontext
                with (gzip.GzipFile(fileobj=raw,mode='rb') if archived else nullcontext(raw)) as handle:
                    while line:=handle.readline(MAX_ROW_BYTES+1):
                        logical_sha.update(line)
                        size=len(line)
                        if size>MAX_ROW_BYTES:
                            raw_digest=hashlib.sha256(line)
                            while not line.endswith(b'\n'):
                                line=handle.readline(MAX_ROW_BYTES+1)
                                if not line:raise InputPending('trailing_archive_migration_partial_record')
                                logical_sha.update(line);raw_digest.update(line);size+=len(line)
                            value=dict(kind='source_gap',reason='source_record_budget_exceeded');summary=None
                            leaf=_put(db,name,offset,b'',value,raw_identity=(size,raw_digest.hexdigest()))
                        else:
                            if not line.endswith(b'\n'):
                                raise InputPending('trailing_archive_migration_partial_record')
                            try:
                                row=json.loads(line);value=project(namespace,row);summary=_summary(namespace,row)
                            except (ValueError,TypeError,KeyError,AttributeError):
                                value=dict(kind='source_gap',reason='source_record_invalid');summary=None
                            leaf=_put(db,name,offset,line,value)
                        chain=hashlib.sha256(encode([chain,leaf])).hexdigest()
                        if original_index is not None:
                            boundary=original_index[2]
                            if offset<boundary<offset+size:
                                raise ValueError('trailing_archive_original_index_boundary_invalid')
                            if offset<boundary:
                                prefix_chain=hashlib.sha256(encode([prefix_chain,leaf])).hexdigest()
                            else:
                                append_chain=hashlib.sha256(encode([append_chain,leaf])).hexdigest()
                        if summary:_summary_merge(db,name,*summary[:2],1,summary[2])
                        offset+=size;records+=1;selected+=value is not None
                        if records%128==0:db.commit()
                if signature(os.fstat(raw.fileno()))!=current or signature(physical.stat())!=current:
                    raise ValueError('trailing_archive_migration_source_changed')
            if archived:
                if _archive_logical_authority(logical,allow_legacy=True)!=authority:
                    raise ValueError('trailing_archive_migration_receipt_changed')
                if authority is not None and (authority[0]['logical_content_sha256']!=logical_sha.hexdigest()
                        or 'logical_size_bytes' in authority[0] and authority[0]['logical_size_bytes']!=offset):
                    raise ValueError('trailing_archive_migration_logical_authority_mismatch')
            boundary=offset;prefix_chain,append_chain=(chain,ZERO_SHA) if original_index is None else (prefix_chain,append_chain)
            if original_index is not None:
                boundary=original_index[2]
                if (offset!=original_index[4] or records!=original_index[5]
                        or selected!=original_index[9] or prefix_chain!=original_index[7]
                        or append_chain!=original_index[8]):
                    raise ValueError('trailing_archive_original_index_mismatch')
            body=dict(schema=SCHEMA+':generation',path=logical.name,size=offset,
                namespace=namespace,source_stat=current,catchup_end=boundary,raw_records=records,
                selected_records=selected,prefix_chain_sha256=prefix_chain,append_chain_sha256=append_chain,
                whole_file_sha256=False)
            bound={**body,'sha256':hashlib.sha256(encode(body)).hexdigest()}
            proof=dict(schema='trailing_archive_migration_v1',generation=bound,
                source_identity_kind='physical_gzip' if archived else 'physical_plain',logical_size_bytes=offset,
                logical_content_sha256=logical_sha.hexdigest(),archive_sha256=archive_sha,
                verification_contract='logical_sha256_size_crc_to_eof_v1',
                runtime_effect=False,allowed_runtime_apply=False)
            proof['artifact_content_sha256']=hashlib.sha256(encode(proof)).hexdigest()
            with db:
                db.execute('INSERT INTO sources VALUES(?,?,?,?,?,?,?,?,?,?)',
                    (name,encode(current).decode(),boundary,boundary,offset,records,None,prefix_chain,append_chain,selected))
                if archived:
                    db.execute('CREATE TABLE archive_migrations(path TEXT PRIMARY KEY,body BLOB)')
                    db.execute('INSERT INTO archive_migrations VALUES(?,?)',(name,encode(proof)))
            db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        finally:
            db.close()
        if (signature(physical.stat())!=current or (archived and logical.exists())
                or archived and _archive_logical_authority(logical,allow_legacy=True)!=authority):
            raise ValueError('trailing_archive_migration_source_changed')
        with temporary.open('rb') as stream:os.fsync(stream.fileno())
        if target.exists():
            # Preserve the complete old cache with SQLite's native backup,
            # including WAL contents. Keep the inode for resident append owners;
            # readers see one atomic replacement of the source's SQL rows.
            with _database(data_root,logical) as (existing,_,_):
                prior=existing.execute('SELECT * FROM sources ORDER BY path').fetchall()
                if original_index is not None and original_index not in prior:
                    raise ValueError('trailing_archive_original_index_changed')
                saved=target.with_name(target.stem+'.before-offline-'+uuid.uuid4().hex+'.sqlite')
                descriptor=os.open(saved,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.close(descriptor)
                saved_db=sqlite3.connect(saved)
                try:existing.backup(saved_db)
                finally:saved_db.close()
                if saved.is_symlink():raise ValueError('trailing_index_recovery_archive_untrusted')
                preserved=sqlite3.connect('file:'+str(saved)+'?mode=ro',uri=True)
                try:
                    if preserved.execute('PRAGMA quick_check').fetchone()[0]!='ok' or preserved.execute(
                            'SELECT * FROM sources ORDER BY path').fetchall()!=prior:
                        raise ValueError('trailing_index_recovery_archive_invalid')
                finally:preserved.close()
                existing.execute('ATTACH DATABASE ? AS migration',(str(temporary),))
                try:
                    with existing:
                        existing.execute('BEGIN IMMEDIATE')
                        if (signature(physical.stat())!=current
                                or archived and _archive_logical_authority(logical,allow_legacy=True)!=authority or existing.execute(
                                'SELECT * FROM sources ORDER BY path').fetchall()!=prior):
                            raise ValueError('trailing_archive_migration_source_changed')
                        for table,column in (('rows','source'),('minutes','source'),('sources','path')):
                            existing.execute('DELETE FROM '+table+' WHERE '+column+'=?',(name,))
                            existing.execute('INSERT INTO '+table+' SELECT * FROM migration.'+table+' WHERE '+column+'=?',(name,))
                        existing.execute('CREATE TABLE IF NOT EXISTS archive_migrations(path TEXT PRIMARY KEY,body BLOB)')
                        existing.execute('DELETE FROM archive_migrations WHERE path=?',(name,))
                        if archived:existing.execute('INSERT INTO archive_migrations SELECT * FROM migration.archive_migrations')
                finally:existing.execute('DETACH DATABASE migration')
        else:
            os.link(temporary,target,follow_symlinks=False)  # Exclusive publication, never overwrite.
        temporary.unlink()
        descriptor=os.open(target.parent,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(descriptor)
        finally:os.close(descriptor)
        return generation(data_root,logical)


def prepare_window(data_root,day,*,start_date=DEFAULT_START_DATE):
    """The postclose predecessor owns enrollment, not holding consumers."""
    from datetime import date,timedelta
    end=date.fromisoformat(day);cursor=date.fromisoformat(max(start_date,DEFAULT_START_DATE));results=[]
    if cursor>end:raise ValueError('trailing_index_window_invalid')
    while cursor<=end:
        for namespace in STREAM_NAMESPACES:
            logical=Path(data_root)/namespace/(namespace+'_'+cursor.isoformat()+'.jsonl')
            if not logical.exists() and not Path(str(logical)+'.gz').exists():continue
            try:
                bound=generation(data_root,logical)
            except InputPending:
                if not logical.exists():bound=migrate_frozen_source(data_root,logical)
                else:
                    try:
                        while not build_step(data_root,logical,seconds=30)['complete']:pass
                    except InputPending as exc:
                        if str(exc)!='trailing_index_source_generation_changed':raise
                        migrate_frozen_source(data_root,logical)
                    bound=generation(data_root,logical)
            results.append(dict(path=str(logical),generation=bound))
        cursor+=timedelta(days=1)
    from .main_trailing_completed_store import prepare_window as prepare_completed_window
    cursor=date.fromisoformat(max(start_date,DEFAULT_START_DATE));days=[]
    while cursor<=end:
        days.append(cursor.isoformat());cursor+=timedelta(days=1)
    results.extend(prepare_completed_window(data_root,days))
    return results


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
            if value['kind'] in {'delay_receipt','holding_payload','holding_prompt','holding_request',
                                 'pipeline_fill_receipt'}:
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
    with read_session(data_root):
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
    with read_session(data_root):
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
        from .main_trailing_completed_store import admit_window
        admit_window(data_root,day)
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
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--source',type=Path)
    group.add_argument('--prepare-window',action='store_true')
    parser.add_argument('--date')
    parser.add_argument('--max-bytes',type=int,default=MAX_STEP_BYTES)
    parser.add_argument('--seconds',type=float,default=1.)
    args=parser.parse_args(argv)
    if args.prepare_window:
        if not args.date:parser.error('--prepare-window requires --date')
        result=prepare_window(args.data_root,args.date)
    else:
        result=build_step(args.data_root,args.source,max_bytes=args.max_bytes,seconds=args.seconds)
    print(json.dumps(result))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
