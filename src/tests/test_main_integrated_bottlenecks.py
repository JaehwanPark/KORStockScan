"""Offline concurrency, source-identity and deadline regression for Main repairs."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timedelta
import json
import os
import sqlite3
import threading
import time
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

from src.trading.market import completed_history as H
from src.engine.scalping import trace_dedup as D
from src.engine.scalping import ai_decision_trace as T
from src.utils.jsonl_io import jsonl_artifact_generation_lock

KST = ZoneInfo('Asia/Seoul')
NOW = datetime(2026, 10, 8, 10, 0, 1, tzinfo=KST).timestamp()


def history_rows(count=61):
    start = datetime.fromtimestamp(NOW, KST).replace(second=0)-timedelta(minutes=count-1)
    return [dict(source_timestamp=(start+timedelta(minutes=i)).strftime('%Y%m%d%H%M%S'),
                 체결시간=(start+timedelta(minutes=i)).strftime('%H:%M:%S'),
                 시가=100, 고가=101, 저가=99, 현재가=100, 거래량=10) for i in range(count)]


def publish(root, rows=None, now=NOW, key=None):
    identity = key or H.key(('real', 'token-hash'), '005930_AL', '20261008', 'REG')
    assert H.publish(root, identity, rows or history_rows(),
                     dict(rest_received_ts_ms=int(now*1000), request_code=identity['item'],
                          request_attempt_count=1), now=now)
    return identity


def test_completed_revision_reuse_does_not_renew_forming_or_provider_clock(tmp_path):
    key = publish(tmp_path)
    assert H.read(tmp_path, key, now=NOW+2.9, limit=20)[1]['rest_received_ts_ms'] == NOW*1000
    assert H.read(tmp_path, key, now=NOW+3, limit=20) is None
    rows, meta = H.read(tmp_path, key, now=NOW+30, limit=60, include_forming=False)
    assert len(rows) == 60 and rows[-1]['source_timestamp'] == '20261008095900'
    assert meta['read_singleflight_caller_http_attempt_count'] == 0
    assert H.read(tmp_path, key, now=NOW+60, limit=60, include_forming=False) is None
    assert H.read(tmp_path, key, now=NOW-.01, limit=10) is None


@pytest.mark.parametrize('change', [dict(item='005930_NX'), dict(session='AFTER'),
                                  dict(date='20261009'), dict(auth_scope=['demo','token-hash']),
                                  dict(adjustment='raw_same_day')])
def test_history_scope_cannot_cross_identity(tmp_path, change):
    key = publish(tmp_path)
    assert H.read(tmp_path, dict(key, **change), now=NOW+1, limit=10) is None


def test_history_correction_is_immutable_deduplicated_and_asof_bound(tmp_path):
    key = publish(tmp_path)
    original, meta = H.read(tmp_path, key, now=NOW, limit=60, include_forming=False)
    old_revision = meta['shared_history_revision_sha256']
    updated = history_rows()
    updated[-2]['현재가'] = 101
    publish(tmp_path, updated, now=NOW+4)
    current, new_meta = H.read(tmp_path, key, now=NOW+4, limit=60, include_forming=False)
    assert current != original and new_meta['shared_history_revision_sha256'] != old_revision
    assert H.read(tmp_path, key, now=NOW+4, limit=60, include_forming=False, revision=old_revision)[0] == original
    assert H.read(tmp_path, key, now=NOW, limit=60, include_forming=False,
                  revision=new_meta['shared_history_revision_sha256']) is None
    assert not H.publish(tmp_path, key, history_rows(), dict(rest_received_ts_ms=int(NOW*1000),
        request_code=key['item']), now=NOW+1)
    # Only one changed completed bar is stored, not another 60-bar payload.
    with sqlite3.connect(H._path(tmp_path, key)) as db:
        assert db.execute('SELECT count(*) FROM bars').fetchone()[0] == 61
        assert db.execute('SELECT count(*) FROM revisions').fetchone()[0] == 2
    updated[-1]['현재가'] = 101
    publish(tmp_path, updated, now=NOW+5)
    with sqlite3.connect(H._path(tmp_path, key)) as db:
        assert db.execute('SELECT count(*) FROM revisions').fetchone()[0] == 2
    assert original[-1]['현재가'] == 100


def test_history_corrupt_bar_not_delivered_and_storage_cap_retains_receipts(tmp_path, monkeypatch):
    key = publish(tmp_path)
    monkeypatch.setattr(H, 'MAX_DATABASE_BYTES', 1)
    assert not H.publish(tmp_path, key, history_rows(), dict(rest_received_ts_ms=int(NOW*1000),
        request_code=key['item']), now=NOW)
    assert H.read(tmp_path, key, now=NOW, limit=10)
    with sqlite3.connect(H._path(tmp_path, key)) as db:
        db.execute("UPDATE bars SET content='{}'")
    assert H.read(tmp_path, key, now=NOW, limit=10) is None


@pytest.mark.parametrize('correction', [dict(현재가=0), dict(고가=98), dict(저가=102)])
def test_invalid_ohlc_cannot_replace_verified_history(tmp_path, correction):
    key = publish(tmp_path)
    original = H.read(tmp_path, key, now=NOW, limit=10)
    bad = history_rows()
    bad[-2].update(correction)
    with pytest.raises(ValueError, match='OHLC'):
        publish(tmp_path, bad, now=NOW+1)
    assert H.read(tmp_path, key, now=NOW, limit=10) == original


def test_original_handoff_clock_does_not_expire_successor_claim():
    from src.engine.sniper_state_handlers import (
        _native_handoff_deadline_perf, _clear_scanner_async_identity)
    expired = time.perf_counter()-10
    stock = dict(_entry_native_deadline_binding=dict(claim_token='old', deadline_perf=expired))
    assert _native_handoff_deadline_perf(stock, {'token': 'old'}) == expired
    assert _native_handoff_deadline_perf(stock, {'token': 'new'}) is None
    assert _native_handoff_deadline_perf(stock, None) is None
    stock['_entry_native_deadline_binding'] = dict(claim_token='new', deadline_perf=expired+100)
    _clear_scanner_async_identity(stock, generation_id='old', cache_key='old', claim={'token': 'old'})
    assert _native_handoff_deadline_perf(stock, {'token': 'new'}) == expired+100
    _clear_scanner_async_identity(stock, generation_id='new', cache_key='new', claim={'token': 'new'})
    assert '_entry_native_deadline_binding' not in stock


def test_trace_cold_preparation_bounded_then_hot_has_no_prefix_scan(tmp_path, monkeypatch):
    path = tmp_path/'ai_decision_requests_2026-10-08.jsonl'
    row = dict(request_id='old', request_envelope_sha256='a', payload_sha256='p', prompt_sha256='q')
    path.write_text(''.join(json.dumps(dict(row, request_id=str(i)))+'\n' for i in range(20000)))
    D._INDEXES.clear()
    with jsonl_artifact_generation_lock(path, exclusive=False) as generation:
        with pytest.raises(D.IndexNotReady):
            D.prepare(path, 'request_id', generation, hot=True, max_bytes=65536)
        first = D.prepare(path, 'request_id', generation, max_bytes=65536)
        assert not first.ready and first.offset <= 65536
        while not first.ready:
            first = D.prepare(path, 'request_id', generation, max_bytes=65536)
    calls = []
    pread = D.os.pread
    monkeypatch.setattr(D.os, 'pread', lambda fd, n, offset: (calls.append((n,offset)), pread(fd,n,offset))[1])
    T._append_jsonl(path, dict(row, request_id='new'))
    assert all(n <= 1024 for n, _ in calls)  # tail fingerprint only
    size = path.stat().st_size
    T._append_jsonl(path, dict(row, request_id='new', captured_at='later'))
    assert path.stat().st_size == size
    with pytest.raises(ValueError, match='identity_conflict'):
        T._append_jsonl(path, dict(row, request_id='new', payload_sha256='conflict'))


def test_trace_two_writers_one_durable_identity_and_partial_tail_not_hidden(tmp_path):
    path = tmp_path/'ai_decision_requests_2026-10-08.jsonl'
    row = dict(request_id='same', request_envelope_sha256='a', payload_sha256='b', prompt_sha256='c')
    with ThreadPoolExecutor(max_workers=2) as executor:
        list(executor.map(lambda _: T._append_jsonl(path, row), range(2)))
    assert len(path.read_text().splitlines()) == 1
    with path.open('ab') as stream:
        stream.write(b'{"request_id":"unfinished"')
    with pytest.raises(D.IndexNotReady):
        T._append_jsonl(path, dict(row, request_id='next'))
    assert 'next' not in path.read_text()


@pytest.mark.parametrize('prepared', [False, True])
def test_machine_first_payload_keeps_request_capture_index_ready(tmp_path, prepared):
    path = tmp_path/'ai_decision_payloads_2026-10-09.jsonl'
    field = 'request_envelope_sha256'
    if prepared:
        with jsonl_artifact_generation_lock(path, exclusive=False) as generation:
            assert D.prepare(path, field, generation).ready
    T._append_jsonl(path, dict(machine_observation_sha256='machine', source={'ask': 100}))
    assert T._load_seen(path, field) == set()
    request = dict(request_envelope_sha256='request', payload_sha256='payload', prompt_sha256='prompt')
    T._append_jsonl(path, request)
    T._append_jsonl(path, request)
    assert T._load_seen(path, field) == {'request'}
    assert len(path.read_text().splitlines()) == 2


def test_large_mixed_payload_append_does_not_rescan_or_lose_existing_keys(tmp_path, monkeypatch):
    path = tmp_path/'ai_decision_payloads_2026-10-09.jsonl'
    first = dict(request_envelope_sha256='first', payload_sha256='a')
    T._append_jsonl(path, first)
    calls = []
    pread = D.os.pread
    monkeypatch.setattr(D.os, 'pread', lambda *a: (calls.append(a[1:]), pread(*a))[1])
    T._append_jsonl(path, dict(machine_observation_sha256='machine', source='x'*150_000))
    T._append_jsonl(path, dict(first, request_envelope_sha256='second'))
    T._append_jsonl(path, first)
    assert calls == []
    assert T._load_seen(path, 'request_envelope_sha256') == {'first', 'second'}
    assert len(path.read_text().splitlines()) == 3


@pytest.mark.parametrize('change', ['cold', 'replacement', 'external_append'])
def test_keyless_append_never_skips_unverified_predecessor(tmp_path, change):
    path = tmp_path/'ai_decision_payloads_2026-10-09.jsonl'
    row = dict(request_envelope_sha256='historical', payload_sha256='a')
    if change != 'cold':
        T._append_jsonl(path, dict(row, request_envelope_sha256='old'))
    if change == 'replacement':
        replaced = path.with_suffix('.replacement')
        replaced.write_text(json.dumps(row)+'\n')
        replaced.replace(path)
    else:
        with path.open('a') as stream:
            stream.write(json.dumps(row)+'\n')
    T._append_jsonl(path, dict(machine_observation_sha256='machine'))
    with pytest.raises(D.IndexNotReady, match='preparation_pending'):
        T._load_seen(path, 'request_envelope_sha256')
    with jsonl_artifact_generation_lock(path, exclusive=False) as generation:
        assert D.prepare(path, 'request_envelope_sha256', generation).ready
    size = path.stat().st_size
    T._append_jsonl(path, row)
    assert path.stat().st_size == size


def test_complete_suffix_before_partial_tail_cannot_admit_request_append(tmp_path):
    path = tmp_path/'ai_decision_requests_2026-10-09.jsonl'
    row = dict(request_id='first', request_envelope_sha256='a')
    T._append_jsonl(path, row)
    with path.open('a') as stream:
        stream.write(json.dumps(dict(row, request_id='external'))+'\n{"request_id":')
    before = path.read_bytes()
    with pytest.raises(D.IndexNotReady, match='partial_or_oversized'):
        T._append_jsonl(path, dict(row, request_id='next'))
    assert path.read_bytes() == before
    with path.open('a') as stream:
        stream.write('"finished"}\n')
    with jsonl_artifact_generation_lock(path, exclusive=False) as generation:
        assert D.prepare(path, 'request_id', generation).ready
    T._append_jsonl(path, dict(row, request_id='next'))
    assert len(path.read_text().splitlines()) == 4


def test_trace_background_releases_generation_before_writer_mutex(tmp_path, monkeypatch):
    paths={}
    for name in ('_payload_path','_prompt_path','_request_path','_trace_path','_outcome_path','_context_candidate_path'):
        paths[name]=tmp_path/(name+'.jsonl')
        monkeypatch.setattr(T,name,lambda day,p=paths[name]:p)
    monkeypatch.setattr(T,'trace_enabled',lambda:True)
    prepared=threading.Event()
    original=D.prepare
    def prepare(*args,**kwargs):
        value=original(*args,**kwargs)
        prepared.set()
        return value
    monkeypatch.setattr(D,'prepare',prepare)
    worker=threading.Thread(target=lambda:T.prepare_ai_request_capture('2026-10-08'),daemon=True)
    acquired=False
    try:
        with T._WRITE_LOCK:
            worker.start()
            assert prepared.wait(1)
            until=time.monotonic()+1
            while time.monotonic()<until:
                try:
                    with jsonl_artifact_generation_lock(paths['_payload_path'],exclusive=True,blocking=False):
                        acquired=True
                        break
                except BlockingIOError:
                    time.sleep(.001)
            assert acquired, 'background cannot hold file lease while waiting on writer mutex'
    finally:
        worker.join(2)
    assert not worker.is_alive()


def test_async_cleanup_retains_successor_identity_and_claim():
    from src.engine.sniper_state_handlers import _clear_scanner_async_identity
    stock = dict(_scanner_async_generation_id='new', _scanner_async_cache_key='new-key',
                 _fixed_watch_async_claim={'token': 'new-token'},
                 _scanner_async_expired_parent_snapshot_id='new-parent')
    original = deepcopy(stock)
    _clear_scanner_async_identity(stock, generation_id='old', cache_key='old-key',
                                  claim={'token': 'old-token'}, clear_recheck=True)
    assert stock == original
    _clear_scanner_async_identity(stock, generation_id='new', cache_key='new-key',
                                  claim={'token': 'new-token'}, clear_recheck=True)
    assert stock == {}


def test_async_disposition_writer_failure_records_health_without_authority(monkeypatch):
    from src.engine.scalping.scanner_async_eval import record_async_disposition
    from src.engine.monitoring import runtime_performance as R
    from src.utils import pipeline_event_logger as P
    failures=[]
    monkeypatch.setattr(R,'failure',lambda *args: failures.append(args))
    monkeypatch.setattr(P,'emit_pipeline_event',lambda *a,**k: dict(structured_append_succeeded=False,
        structured_append_status='raw_append_failed'))
    result=SimpleNamespace(native_claim={},ai_payload={},request_id='id',code='123456',
        generation_id='g',origin_fields={},venue='SOR',deadline_epoch=NOW+5,completed_epoch=NOW)
    assert record_async_disposition(result,'worker_completed','completed') is False
    assert failures == [('async_disposition','raw_append_failed')]


def test_observation_queue_is_finite_and_freezes_producer_arguments():
    from src.utils.pipeline_event_logger import BoundedObservationQueue
    class Executor:
        def submit(self, fn):
            self.drain = fn
    executor = Executor()
    queue = BoundedObservationQueue(executor, max_items=2, max_bytes=100)
    seen = []
    source = {'reason': 'original'}
    assert queue.submit(seen.append, source)['status'] == 'queued'
    source['reason'] = 'successor'
    assert queue.submit(seen.append, {'reason': 'second'})['status'] == 'queued'
    assert queue.submit(seen.append, {})['status'] == 'unavailable'
    assert queue.snapshot()['peak_items'] == 2
    executor.drain()
    assert seen == [{'reason': 'original'}, {'reason': 'second'}]
    assert queue.close(timeout=0)
    assert queue.submit(seen.append, {})['status'] == 'unavailable'


def test_observation_running_job_counts_towards_limit_and_failure_never_blocks():
    from src.utils.pipeline_event_logger import BoundedObservationQueue
    gate = threading.Event()
    started = threading.Event()
    def slow(_):
        started.set()
        gate.wait(2)
        raise OSError('disk')
    with ThreadPoolExecutor(max_workers=1) as executor:
        queue = BoundedObservationQueue(executor, max_items=1)
        assert queue.submit(slow, {})['status'] == 'queued'
        assert started.wait(1)
        assert queue.submit(slow, {})['status'] == 'unavailable'
        assert not queue.close(timeout=0)
        gate.set()
    assert queue.snapshot()['failed'] == 1
    assert queue.snapshot()['pending_bytes'] == 0


def test_big_trace_row_preparation_advances_without_publishing_unverified_keys(tmp_path):
    path = tmp_path/'large.jsonl'
    path.write_text(json.dumps(dict(request_id='large', body='x'*(4*1024*1024)))+'\n')
    with jsonl_artifact_generation_lock(path, exclusive=False, blocking=True) as generation:
        with pytest.raises(D.IndexNotReady, match='preparation_pending'):
            D.prepare(path, 'request_id', generation)
        index = D._INDEXES[D._key(path, 'request_id')]
        assert index.offset == 0 and not index.keys and len(index.pending) == 4*1024*1024
        index = D.prepare(path, 'request_id', generation)
        assert index.ready and index.keys == {'large'}
    # Replacement invalidates externally held ready sets as well as the cursor.
    path.unlink(); path.write_text('{"request_id":"new"}\n')
    with jsonl_artifact_generation_lock(path, exclusive=False, blocking=True) as generation:
        assert D.prepare(path, 'request_id', generation).keys == {'new'}
    assert not index.ready and not index.keys


def test_partial_trace_tail_is_not_reread_until_generation_changes(tmp_path, monkeypatch):
    path = tmp_path/'partial.jsonl'; path.write_text('{"request_id":')
    calls=[]; original=D.os.pread
    monkeypatch.setattr(D.os, 'pread', lambda *a: (calls.append(a) or original(*a)))
    for _ in range(4):
        with jsonl_artifact_generation_lock(path, exclusive=False, blocking=True) as generation:
            with pytest.raises(D.IndexNotReady, match='partial_row'):
                D.prepare(path, 'request_id', generation)
    assert len(calls) == 1
    with path.open('a') as stream: stream.write('"complete"}\n')
    with jsonl_artifact_generation_lock(path, exclusive=False, blocking=True) as generation:
        assert D.prepare(path, 'request_id', generation).keys == {'complete'}


def test_trace_maintenance_continues_other_indexes_after_large_row(tmp_path, monkeypatch):
    monkeypatch.setenv('KORSTOCKSCAN_AI_DECISION_TRACE_ENABLED', '1')
    monkeypatch.setattr(T, 'DATA_DIR', tmp_path)
    # Path owners create these directories, not a second research ledger.
    big = T._payload_path('2026-10-08'); big.parent.mkdir(parents=True, exist_ok=True)
    big.write_text(json.dumps(dict(request_envelope_sha256='big', body='x'*(4*1024*1024)))+'\n')
    small = T._request_path('2026-10-08'); small.parent.mkdir(parents=True, exist_ok=True)
    small.write_text('{"request_id":"small"}\n')
    assert T.prepare_ai_request_capture('2026-10-08')['ai_trace_dedup_preparation_pending']
    assert T._load_seen(small, 'request_id') == {'small'}


def test_partial_assembly_checks_entire_prefix_before_reusing_after_append(tmp_path):
    path = tmp_path/'partial-rewrite.jsonl'
    body=json.dumps(dict(request_id='old', body='x'*(4*1024*1024))).encode()
    path.write_bytes(body[:4*1024*1024])
    with jsonl_artifact_generation_lock(path, exclusive=False, blocking=True) as generation:
        with pytest.raises(D.IndexNotReady, match='partial_row'):
            D.prepare(path,'request_id',generation)
    # Mutate the start while retaining the final 1 KiB of the assembled prefix.
    changed=body.replace(b'"old"',b'"new"',1)+b'\n'
    path.write_bytes(changed)
    with jsonl_artifact_generation_lock(path, exclusive=False, blocking=True) as generation:
        with pytest.raises(D.IndexNotReady, match='prefix_changed'):
            D.prepare(path,'request_id',generation)
    with jsonl_artifact_generation_lock(path, exclusive=False, blocking=True) as generation:
        with pytest.raises(D.IndexNotReady, match='preparation_pending'):
            D.prepare(path,'request_id',generation)
        assert D.prepare(path,'request_id',generation).keys == {'new'}


@pytest.mark.parametrize('clock', ['epoch','perf'])
@pytest.mark.parametrize('elapsed', [4.999,5.000,5.001])
def test_original_five_second_commit_boundary_on_both_clocks(monkeypatch, clock, elapsed):
    from dataclasses import replace
    from src.tests.test_scanner_async_entry_bridge import _retained_fixture
    from src.engine.scalping.scanner_async_eval import validate_scanner_async_commit
    stock=dict(code='005930',status='WATCHING',effective_venue='KRX',source_signature='VALUE_TOP')
    coordinator,generation,result=_retained_fixture(stock)
    result=replace(result, deadline_epoch=NOW+5, deadline_perf=105)
    monkeypatch.setattr(time,'perf_counter',lambda:100+elapsed if clock=='perf' else 100)
    try:
        decision=validate_scanner_async_commit(result,current_generation=generation,
            current_status='WATCHING',current_venue='KRX',current_source_signature='VALUE_TOP',
            venue_resolution_valid=True,current_state_version=result.state_version,quote_fresh=True,
            position_or_pending_order_present=False,cooldown_active=False,
            now_epoch=NOW+elapsed if clock=='epoch' else NOW)
        assert decision.allowed is (elapsed<5)
        assert result.deadline_epoch == NOW+5 and result.deadline_perf == 105
    finally:
        coordinator.shutdown()


def test_finish_publishes_ready_before_slow_diagnostic_and_retains_original_deadline(monkeypatch):
    from src.engine.scalping import scanner_async_eval as A
    from src.tests.test_scanner_async_eval import _generation
    from src.engine.ai.hot_path_ai_dispatcher import HotPathAIDispatcher
    from src.utils.pipeline_event_logger import BoundedObservationQueue
    class Executor:
        def submit(self, fn): self.drain=fn
    executor=Executor();queue=BoundedObservationQueue(executor)
    clock=[NOW];monkeypatch.setattr(time,'time',lambda:clock[0])
    writes=[]
    def slow(code,fields):
        clock[0]+=.2;writes.append(fields)
        return dict(structured_append_succeeded=True,structured_append_status='raw_appended')
    monkeypatch.setattr(A,'_append_async_disposition',slow)
    context=A.ScannerAsyncEvalContext.create(generation=_generation(),cache_key='diagnostic',
        submitted_epoch=NOW-4.9,deadline_epoch=NOW+.1,stock_snapshot={},ws_snapshot={},state_version='v')
    request=A.ScannerAsyncEvalRequest(context=context,prepare=lambda _: {},evaluate=lambda *a: {})
    coordinator=A.ScannerAsyncEvalCoordinator(ai_dispatcher=HotPathAIDispatcher(loaded_key_count=1),
                                             observation_sink=queue.submit)
    coordinator._requests[context.request_id]=request
    try:
        coordinator._finish(request,status='completed',preparation_started_epoch=NOW,
            preparation_completed_epoch=NOW,completed_epoch=NOW,observation_only=False)
        result=coordinator.take_completed(generation_id=context.generation.generation_id,cache_key=context.cache_key)
        assert clock[0] == NOW and writes == []
        assert result.deadline_epoch == NOW+.1
        executor.drain()
        assert clock[0] > result.deadline_epoch
        assert writes[0]['async_disposition_epoch'] == NOW
        assert queue.snapshot()['append_confirmed'] == 1
    finally:
        coordinator.shutdown();queue.close(timeout=0)


def test_delayed_midnight_append_preserves_occurrence_and_request_day(tmp_path, monkeypatch):
    from src.engine.scalping import scanner_async_eval as A
    from src.engine.monitoring import submission_bottleneck_monitor as M
    from src.utils import pipeline_event_logger as P
    from src.tests.test_pipeline_event_logger import _reset_logger_state
    _reset_logger_state(monkeypatch)
    monkeypatch.setattr(P, 'DATA_DIR', tmp_path)
    monkeypatch.setattr(P, 'TRADING_RULES', SimpleNamespace(PIPELINE_EVENT_JSONL_ENABLED=True))
    monkeypatch.setattr(P, 'log_info', lambda *a, **k: None)
    before = datetime(2026,10,10,23,59,59,tzinfo=KST).timestamp()
    physical = datetime(2026,10,11,0,0,3,tzinfo=KST)
    class PhysicalClock(datetime):
        @classmethod
        def now(cls, tz=None): return physical.astimezone(tz) if tz else physical
    monkeypatch.setattr(P, 'datetime', PhysicalClock)
    monkeypatch.setattr(A.time, 'time', lambda: before)
    monkeypatch.setattr(A, '_PROCESS_START', '456')
    class Executor:
        def submit(self, fn): self.drain=fn
    executor=Executor();queue=P.BoundedObservationQueue(executor)
    result=SimpleNamespace(request_id='request', generation_id='original', code='005930',
        native_claim={}, origin_fields={}, venue='SOR', deadline_epoch=before+1,
        submitted_epoch=before-4, completed_epoch=before, observation_sink=queue.submit,
        ai_payload=dict(evaluation_attempt_id='attempt', ai_decision_trace_id='trace',
            entry_mechanistic_action='ENTER_NOW', entry_ai_screen_status='pass',
            entry_ai_risk_verdict='PASS', provider_called=True))
    assert A.record_async_disposition(result,'accepted_to_entry_path','commit_allowed')['status']=='queued'
    executor.drain();assert queue.close(timeout=0)
    raw=next((tmp_path/'pipeline_events').glob('*.jsonl'))
    row=json.loads(raw.read_text().splitlines()[0])
    assert raw.name == 'pipeline_events_2026-10-11.jsonl'
    assert row['fields']['async_request_source_date']=='2026-10-10'
    assert float(row['fields']['async_disposition_epoch'])==before
    event=SimpleNamespace(stage=row['stage'],emitted_at=row['emitted_at'],stock_code=row['stock_code'],fields=row['fields'])
    assert not M.async_disposition_coverage([event], datetime.fromtimestamp(before,KST))['by_producer']
    counts=M.async_disposition_coverage([event],physical)['by_producer']
    assert next(iter(counts.values()))['accepted']==1
    assert not M.async_disposition_coverage([event],datetime.fromtimestamp(before+601,KST))['by_producer']
    P.flush_pipeline_event_producer_summary()


def test_reordered_repeated_transitions_do_not_overflow_bounded_projection():
    from src.engine.monitoring.submission_bottleneck_monitor import async_disposition_coverage
    fields=dict(async_producer_pid=123,async_producer_start_ticks=456,async_request_id='request',
        async_disposition='accepted_to_entry_path',async_disposition_event_id='accepted',
        async_origin_deadline_epoch=NOW+5,async_machine_action='ENTER_NOW',
        async_auxiliary_status='pass',async_auxiliary_verdict='PASS',async_provider_called=True)
    event=SimpleNamespace(stage='entry_async_disposition',stock_code='005930',
                          emitted_at=datetime.fromtimestamp(NOW,KST).isoformat(),fields=fields)
    result=async_disposition_coverage([event]*1100,datetime.fromtimestamp(NOW+6,KST),source_coverage='complete')
    assert result['by_producer']['123:456']['accepted']==1
    assert not result['denominator_partial'] and len(result['attempt_projection'])==1


@pytest.mark.parametrize('field,value', [('ai_decision_trace_id','other'),
    ('evaluation_attempt_id','other'), ('scanner_generation_id','other'),
    ('native_signal_id','other'), ('entry_machine_bundle_sha256','b'*64),
    ('effective_venue','NXT'), ('async_origin_deadline_epoch',NOW+10)])
def test_async_transitions_with_different_identity_never_count_accepted(field, value):
    from src.engine.monitoring.submission_bottleneck_monitor import async_disposition_coverage
    base = dict(async_producer_pid=123, async_producer_start_ticks=456, async_request_id='request',
        async_origin_deadline_epoch=NOW+5, async_disposition_epoch=NOW,
        async_machine_action='ENTER_NOW', async_auxiliary_status='pass', async_auxiliary_verdict='PASS',
        async_provider_called=True, ai_decision_trace_id='trace', evaluation_attempt_id='attempt',
        scanner_generation_id='generation', native_signal_id='signal',
        entry_machine_bundle_sha256='a'*64, effective_venue='KRX')
    def event(kind, updates):
        return SimpleNamespace(stage='entry_async_disposition', stock_code='005930',
            emitted_at=datetime.fromtimestamp(NOW,KST).isoformat(), fields=dict(base,
                async_disposition=kind, async_disposition_event_id=kind, **updates))
    rows = [event('worker_completed',{}),event('accepted_to_entry_path',{field:value})]
    for events in (rows, rows[::-1], rows+rows):
        count=async_disposition_coverage(events, datetime.fromtimestamp(NOW+6,KST))['by_producer']['123:456']
        assert count['pass_count'] == count['unobservable'] == 1 and count['accepted'] == 0


def test_pass_trace_denominator_survives_missing_all_transition_receipts():
    from src.engine.monitoring.submission_bottleneck_monitor import async_disposition_coverage
    row = dict(emitted_at=datetime.fromtimestamp(NOW,KST).isoformat(), stock_code='005930',
        fields=dict(async_producer_pid=123,async_producer_start_ticks=456,async_request_id='request',
            async_disposition='validated_pass_trace', async_disposition_event_id='trace',
            async_origin_deadline_epoch=NOW+5, async_machine_action='ENTER_NOW',
            async_auxiliary_status='pass', async_auxiliary_verdict='PASS', async_provider_called=True))
    outcome=async_disposition_coverage([], datetime.fromtimestamp(NOW+6,KST), pass_projections=[row],
                                      source_coverage='complete')
    assert outcome['by_producer']['123:456']['unobservable'] == 1
    assert outcome['denominator_partial'] is False


@pytest.mark.parametrize('duplicate_id', [False, True])
def test_conflicting_post_entry_physical_facts_are_unobservable(duplicate_id):
    from src.engine.monitoring.submission_bottleneck_monitor import async_disposition_coverage
    base=dict(async_producer_pid=123, async_producer_start_ticks=456, async_request_id='request',
        async_disposition_epoch=NOW, async_origin_deadline_epoch=NOW+5,
        async_machine_action='ENTER_NOW', async_auxiliary_status='pass',
        async_auxiliary_verdict='PASS', async_provider_called=True)
    def event(kind, identity, **facts):
        return SimpleNamespace(stage='entry_async_disposition', stock_code='005930',
            emitted_at=datetime.fromtimestamp(NOW,KST).isoformat(),fields=dict(base,
                async_disposition=kind,async_disposition_event_id=identity,**facts))
    rows=[event('accepted_to_entry_path','accepted'),
        event('entry_path_returned','return',async_entry_broker_attempts=0),
        event('entry_path_returned','return' if duplicate_id else 'another',async_entry_broker_attempts=1)]
    for source in (rows, rows[::-1]):
        count=async_disposition_coverage(source,datetime.fromtimestamp(NOW+6,KST))['by_producer']['123:456']
        assert count['unobservable']==1 and count['accepted']==0


def test_async_disposition_compact_cache_reader_preserves_exact_pass_and_conflicts():
    from src.engine import buy_funnel_sentinel as S
    from src.engine.monitoring import submission_bottleneck_monitor as M
    from src.utils.pipeline_event_logger import _project_fields_for_compact_stream
    fields = dict(async_producer_pid='123', async_producer_start_ticks='456',
                  async_request_id='request', async_disposition_event_id='done',
                  async_disposition='worker_completed', async_machine_action='ENTER_NOW',
                  async_auxiliary_status='pass', async_auxiliary_verdict='PASS',
                  async_provider_called='True', async_origin_deadline_epoch=str(NOW+5))
    fields.update({f'diagnostic_{i}': str(i) for i in range(60)})
    def read(updates=None):
        payload = dict(event_type='pipeline_event', emitted_at=datetime.fromtimestamp(NOW,KST).isoformat(),
            stage='entry_async_disposition', pipeline='ENTRY_PIPELINE', stock_code='123456',
            fields=_project_fields_for_compact_stream('entry_async_disposition', dict(fields, **(updates or {}))))
        return S._event_from_cache_row(S._payload_to_cache_row(payload, exclude_summary_stages=True))
    event = read()
    assert len(event.fields) == len(fields)
    def counts(events, at=NOW+1):
        return M.async_disposition_coverage(events, datetime.fromtimestamp(at,KST))['by_producer']['123:456']
    assert {k: counts([event,event])[k] for k in ('pass_count', 'accepted', 'rejected', 'pending', 'unobservable')} == dict(pass_count=1, accepted=0, rejected=0, pending=1, unobservable=0)
    assert counts([event], NOW+6)['unobservable'] == 1
    final = read(dict(async_disposition_event_id='accepted', async_disposition='accepted_to_entry_path'))
    assert counts([event,final])['accepted'] == 1
    conflicting = read(dict(async_provider_called='False'))
    assert counts([event,conflicting])['unobservable'] == 1
    invalid = SimpleNamespace(stage='entry_async_disposition', emitted_at='broken', fields={})
    assert M.async_disposition_coverage([invalid], datetime.fromtimestamp(NOW,KST))['by_producer'] == {}


def test_history_first_rest_consumer_pins_its_own_revision(tmp_path):
    identity = H.key(('real','token'), '005930_AL', '20261008', 'REG')
    meta = dict(rest_received_ts_ms=int(NOW*1000), request_code='005930_AL', request_attempt_count=1)
    assert H.publish(tmp_path, identity, history_rows(), meta, now=NOW, consumption_receipt=meta)
    assert meta['shared_history_reused'] is False and meta['request_attempt_count'] == 1
    assert H.read(tmp_path, identity, now=NOW, limit=10)[1]['shared_history_revision_sha256'] == meta['shared_history_revision_sha256']


def test_small_history_refresh_preserves_old_prefix_without_filling_overlap_gaps(tmp_path):
    key=publish(tmp_path)
    original=H.read(tmp_path,key,now=NOW,limit=60,include_forming=False)[0]
    tail=history_rows()[-10:]
    tail.pop(2)  # Absence inside a new provider overlap is not a synthetic bar.
    publish(tmp_path,tail,now=NOW+4)
    revised=H.read(tmp_path,key,now=NOW+4,limit=59,include_forming=False)[0]
    assert revised[:51] == original[:51]
    assert len(revised) == 59


def test_selected_ready_denominator_excludes_other_price_bands(monkeypatch):
    from src.engine.monitoring import runtime_performance as R
    from src.engine.scalping.reversal_extended_catalog import cell_key
    monkeypatch.setattr(R, '_READY', __import__('collections').OrderedDict())
    monkeypatch.setattr(R, '_SELECTED_READY', __import__('collections').OrderedDict())
    monkeypatch.setattr(R, '_SELECTED_EVICTED', dict(claimed=0, expired_before_claim=0, unobservable=0))
    monkeypatch.setattr(R, '_COVERAGE', {k: dict(ready=0,claimed=0) for k in ('fixed_watch','other')})
    monkeypatch.setattr(R.time, 'time', lambda: NOW+1)
    band = cell_key('123456', 'KRX_REGULAR', 10000)
    B = SimpleNamespace(_LOCK=threading.RLock(), _STATES={}, _FAMILY={
        'schema':'continuous_reversal_policy_v6', 'family_sha256':'f'*64,
        'machine_cells': {band:{'routes':{'SOR':dict(backend='union_v6',scope_execution_hash='s',
            payload={'branches':[{'branch_id':'selected'}]})}}}})
    for i, scope_band in enumerate((band, 'other-band')):
        event=dict(event_id=f'event{i}', signal_id=f'signal{i}', epoch=NOW, confirmation_price=10000,
            branch_signals={'selected':{}}, native_epoch=1)
        B._STATES[('123456','SOR','123456_AL','KRX_REGULAR','2026-10-08',scope_band)] = SimpleNamespace(
            generation='s', ready=[{'event':event}])
    R.record_native_ready(B,'123456','SOR','123456_AL','KRX_REGULAR',NOW)
    snap=R.snapshot()
    assert snap['ready_coverage']['other']['ready'] == 2
    assert snap['selected_native_coverage']['count'] == 1
    assert snap['selected_native_coverage']['pending'] == 1


def test_completed_wakeup_is_observed_before_sleep():
    from src.engine.scalping.scanner_async_eval import ScannerAsyncEvalCoordinator
    from src.engine.ai.hot_path_ai_dispatcher import HotPathAIDispatcher
    dispatcher = HotPathAIDispatcher(loaded_key_count=1)
    coordinator = ScannerAsyncEvalCoordinator(ai_dispatcher=dispatcher)
    try:
        coordinator.completion_event.set()
        before = time.perf_counter()
        assert coordinator.wait_for_completion(.5)
        assert time.perf_counter()-before < .2
    finally:
        coordinator.shutdown(wait=True)
        dispatcher.shutdown(wait=True)


def test_observation_identity_rejects_nan_renewed_deadline_and_other_process(monkeypatch):
    from src.engine.scalping import reversal_source_diagnostics as S
    item = dict(snapshot=[dict(epoch=NOW)], deadline_epoch=NOW+5,
                deadline_perf=time.perf_counter()+2, observer_pid=os.getpid(),
                observer_start_ticks=S._PROCESS_START_TICKS)
    assert S.observation_binding_valid(item, now=NOW+1)
    for changes in (dict(deadline_epoch=float('nan')), dict(deadline_epoch=NOW+6),
                    dict(observer_pid=os.getpid()+1), dict(observer_start_ticks='old')):
        assert not S.observation_binding_valid(dict(item, **changes), now=NOW+1)
    assert not S.observation_binding_valid(item, now=NOW+5)
