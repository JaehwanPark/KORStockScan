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
    assert counts([event,event]) == dict(pass_count=1, accepted=0, rejected=0, pending=1, unobservable=0)
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
