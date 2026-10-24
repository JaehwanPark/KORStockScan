import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.engine import buy_funnel_sentinel as buy
from src.engine.sentinel_event_cache import update_and_load_cached_event_rows
from src.engine.monitoring import sentinel_source_window as window


AT = datetime(2026,10,14,10,tzinfo=window.KST)


def _event(seconds, stage='zero_base_probe_result', **fields):
    return dict(event_type='pipeline_event',pipeline='ENTRY_PIPELINE',stage=stage,
        emitted_at=(AT+timedelta(seconds=seconds)).isoformat(),stock_code='005930',
        stock_name='Example',fields=fields)


def _append(path, *rows):
    with path.open('a') as stream:
        for row in rows:
            stream.write(json.dumps(row)+'\n')


def _prepared(tmp_path, monkeypatch):
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return AT if tz else AT.replace(tzinfo=None)
    monkeypatch.setattr(window,'datetime',Clock)
    raw = tmp_path/'pipeline_events/pipeline_events_2026-10-14.jsonl'
    raw.parent.mkdir()
    _append(raw,_event(-60,'ai_confirmed'))
    args = dict(raw_path=raw,cache_dir=tmp_path/'runtime/sentinel_event_cache',
        cache_name=buy.EVENT_CACHE_NAME,target_date='2026-10-14',schema_version=18,
        parse_payload=lambda row:buy._payload_to_cache_row(row,exclude_summary_stages=True),
        project_loaded_payload=buy._slim_economic_cache_row,
        cache_projection_version='economic_source_refs_v1',compact_index=True,load_rows=True)
    _, before = update_and_load_cached_event_rows(**args)
    receipt = window.prepare(tmp_path)
    assert receipt['prior_raw_offset']==receipt['raw_offset']==before['raw_offset']
    assert receipt['prior_cache_generation']==receipt['cache_generation']
    assert receipt['projection']['coverage_started_epoch']==AT.timestamp()
    assert receipt['historical_stage_coverage']=='not_backfilled_before_cache_offset'
    args['schema_version']=buy.LOSSLESS_EVENT_CACHE_SCHEMA_VERSION
    return raw,args,Path(before['cache_path'])


def test_forward_window_exact_clock_census_raw_delta_and_original_types(tmp_path, monkeypatch):
    raw,args,cache = _prepared(tmp_path,monkeypatch)
    events = [_event(240,zero_base_probe_result='assessed', nested={'valid':True}),
              _event(180,'main_fixed_watch_observation_wait',reason='missing'),
              _event(720),_event(120,'entry_async_disposition',async_provider_called=True)]
    _append(raw,*events)
    update_and_load_cached_event_rows(**args)
    delta = _event(550,zero_base_probe_result='source_unavailable')
    _append(raw,delta)
    rows,receipt = window.read(tmp_path,AT+timedelta(seconds=600),lower_epoch=AT.timestamp())
    assert [row['stage'] for row in rows]==[row['stage'] for row in events[:2]+events[3:]+[delta]]
    assert rows[0]['fields']['nested']=={'valid':True}
    assert rows[2]['fields']['async_provider_called']=='True'  # Existing cache's native wire.
    assert receipt['window_covered'] and receipt['indexed_bytes_read']>0 and receipt['bytes_read']>0
    monkeypatch.setattr(buy,'DATA_DIR',tmp_path)
    # Source-only stages cannot change the scanner/fixed-watch funnel population.
    assert all(event.stage not in {'zero_base_probe_result','main_fixed_watch_observation_wait'}
               for event in buy.load_pipeline_events('2026-10-14',use_cache=True,exclude_summary_stages=True))


def test_preparation_does_not_backfill_and_pid_birth_may_bound_first_window(tmp_path,monkeypatch):
    raw,args,cache = _prepared(tmp_path,monkeypatch)
    _append(raw,_event(10))
    update_and_load_cached_event_rows(**args)
    with pytest.raises(ValueError,match='stage_coverage_incomplete'):
        window.read(tmp_path,AT+timedelta(seconds=30),lower_epoch=AT.timestamp()-570)
    rows,receipt=window.read(tmp_path,AT+timedelta(seconds=30),lower_epoch=AT.timestamp()+1)
    assert len(rows)==1 and receipt['coverage_started_at']==AT.isoformat()


def test_immutable_release_data_mount_uses_canonical_source_owner(tmp_path,monkeypatch):
    raw,args,cache=_prepared(tmp_path,monkeypatch)
    routed=tmp_path/'release-data'
    routed.symlink_to(tmp_path,target_is_directory=True)
    _append(raw,_event(1))
    update_and_load_cached_event_rows(**args)
    assert len(window.read(routed,AT+timedelta(seconds=600),lower_epoch=AT.timestamp())[0])==1
    assert window.prepare(routed)['raw_offset']==raw.stat().st_size


def test_monitor_keeps_ten_minute_gap_but_verifies_covered_current_pid_lifetime(tmp_path,monkeypatch):
    from src.engine.monitoring import submission_bottleneck_monitor as monitor
    from src.tests.test_submission_bottleneck_monitor import _health_birth_fixture
    raw,args,cache=_prepared(tmp_path,monkeypatch)
    _append(raw,_event(30,zero_base_producer_pid='9',zero_base_producer_start_ticks='900'))
    update_and_load_cached_event_rows(**args)
    now=AT+timedelta(seconds=190)
    proof,generation=_health_birth_fixture(now)
    with monitor._health_actor_scope(generation):
        result=monitor.source_gap_semantics(tmp_path,now)
    original=result['sources']['probe']
    current=result['current_health_cohort']['view']['sources']['probe']
    assert original['status']=='partial' and original['window_covered'] is False
    assert current['status']=='complete' and current['window_covered'] is True
    assert current['coverage_basis']=='verified_forward_sentinel_source_window_v1'
    assert current['actor_lifetime_bound'] is True
    assert current['current_window_start_at']==proof['birth_lower_bound_at']


@pytest.mark.parametrize('damage',['delete','row','clock','offset','body_and_sha','state','cache',
                                  'raw_truncate','raw_partial','raw_malformed','raw_array','meta_array','state_array'])
def test_projection_cannot_mask_changed_or_incomplete_source(tmp_path,monkeypatch,damage):
    raw,args,cache=_prepared(tmp_path,monkeypatch)
    _append(raw,_event(1))
    update_and_load_cached_event_rows(**args)
    index=cache.with_suffix('.compact.sqlite')
    if damage in {'delete','row','clock','offset','body_and_sha','state','state_array'}:
        with sqlite3.connect(index) as conn:
            conn.execute({'delete':'DELETE FROM source_window_rows',
                          'row':"UPDATE source_window_rows SET body=X'6162'",
                          'clock':"UPDATE source_window_rows SET emitted_epoch=0",
                          'offset':"UPDATE source_window_rows SET offset=offset+1",
                          'body_and_sha':"UPDATE source_window_rows SET body=X'6162',sha='fake'",
                          'state':"UPDATE source_window_state SET body='{}'",
                          'state_array':"UPDATE source_window_state SET body='[]'"}[damage])
    elif damage=='cache':
        with cache.open('a') as stream:stream.write('{}\n')
    elif damage=='raw_truncate':raw.write_text('')
    elif damage=='raw_partial':
        with raw.open('a') as stream:stream.write('{')
    elif damage=='raw_malformed':
        with raw.open('a') as stream:stream.write('{\n')
    elif damage=='raw_array':
        with raw.open('a') as stream:stream.write('[]\n')
    elif damage=='meta_array':cache.with_suffix('.meta.json').write_text('[]')
    with pytest.raises((ValueError,KeyError)):
        window.read(tmp_path,AT+timedelta(seconds=600),lower_epoch=AT.timestamp())


def test_window_budget_is_bounded_and_missing_index_never_rebuilds_history(tmp_path,monkeypatch):
    raw,args,cache=_prepared(tmp_path,monkeypatch)
    _append(raw,_event(1,large='x'*1000))
    update_and_load_cached_event_rows(**args)
    with pytest.raises(ValueError,match='budget_exceeded'):
        window.read(tmp_path,AT+timedelta(seconds=600),lower_epoch=AT.timestamp(),limit=64)
    cache.with_suffix('.compact.sqlite').unlink()
    with pytest.raises(sqlite3.OperationalError):
        window.read(tmp_path,AT+timedelta(seconds=600),lower_epoch=AT.timestamp())
    assert not cache.with_suffix('.compact.sqlite').exists()


def test_unavailable_preparation_preserves_existing_cursor(tmp_path,monkeypatch):
    raw,args,cache=_prepared(tmp_path,monkeypatch)
    meta_path=cache.with_suffix('.meta.json')
    original=meta_path.read_bytes()
    raw.write_bytes(raw.read_bytes()[:1])
    with pytest.raises(ValueError,match='existing_cursor_unverified'):
        window.prepare(tmp_path)
    assert meta_path.read_bytes()==original


def test_preparation_catches_up_in_bounded_owned_batches(tmp_path,monkeypatch):
    raw,args,cache=_prepared(tmp_path,monkeypatch)
    monkeypatch.setattr(window,'LIMIT',2048)
    _append(raw,*[_event(i+1,padding='x'*900) for i in range(3)])
    before=json.loads(cache.with_suffix('.meta.json').read_bytes())
    result=window.prepare(tmp_path)
    assert 1 < result['batches'] <= 4
    assert result['prior_raw_offset']==before['raw_offset']
    assert len(result['native_index_batches']) == result['batches']
    assert all(0 < row['appended_cache_bytes'] <= 2048
               for row in result['native_index_batches'])
    assert result['raw_offset']==raw.stat().st_size
    rows,_=window.read(tmp_path,AT+timedelta(seconds=600),lower_epoch=AT.timestamp())
    assert len(rows)==3


def _native_state(cache):
    with sqlite3.connect(f'file:{cache.with_suffix(".compact.sqlite")}?mode=ro', uri=True) as conn:
        return json.loads(conn.execute('SELECT body FROM state WHERE id=1').fetchone()[0])


def test_preparation_keeps_native_index_current_without_repacking_history(tmp_path, monkeypatch):
    from src.engine.monitoring import sentinel_compact_store as compact
    raw, args, cache = _prepared(tmp_path, monkeypatch)
    packed = []
    original = compact._pack
    def track(row):
        packed.append(row['stage'])
        return original(row)
    monkeypatch.setattr(compact, '_pack', track)
    _append(raw, _event(1), _event(2, 'entry_async_disposition'))
    receipt = window.prepare(tmp_path)
    meta = json.loads(cache.with_suffix('.meta.json').read_bytes())
    assert _native_state(cache)['generation'] == meta['cache_generation']
    assert _native_state(cache)['count'] == meta['cache_event_count']
    assert packed == ['zero_base_probe_result', 'entry_async_disposition']
    assert receipt['native_index_batches'][0]['count'] == meta['cache_event_count']
    _append(raw, _event(3))
    update_and_load_cached_event_rows(**args)
    assert packed == ['zero_base_probe_result', 'entry_async_disposition', 'zero_base_probe_result']


@pytest.mark.parametrize('damage', ['missing_file', 'missing_state', 'contract', 'generation',
                                    'offset', 'count', 'boolean_count', 'array', 'oversized'])
def test_preparation_rejects_unverified_native_index_before_cache_mutation(tmp_path, monkeypatch, damage):
    raw, args, cache = _prepared(tmp_path, monkeypatch)
    index = cache.with_suffix('.compact.sqlite')
    if damage == 'missing_file':
        index.unlink()
    else:
        state = _native_state(cache)
        if damage in {'contract', 'generation', 'offset', 'count', 'boolean_count'}:
            key = 'count' if damage == 'boolean_count' else damage
            state[key] = {'contract':'bad', 'generation':[], 'offset':-1,
                          'count':-1, 'boolean_count':True}[damage]
        body = ('[]' if damage == 'array' else 'x' * (1024 * 1024 + 1)
                if damage == 'oversized' else json.dumps(state))
        with sqlite3.connect(index) as conn:
            if damage == 'missing_state':
                conn.execute('DELETE FROM state')
            else:
                conn.execute('UPDATE state SET body=? WHERE id=1', (body,))
    _append(raw, _event(1))
    meta = cache.with_suffix('.meta.json')
    before = (cache.read_bytes(), meta.read_bytes())
    with pytest.raises(ValueError, match='native_index_unverified'):
        window.prepare(tmp_path)
    assert (cache.read_bytes(), meta.read_bytes()) == before
    if damage == 'missing_file':
        assert not index.exists()


def test_preparation_closes_native_iterator_after_first_row(tmp_path, monkeypatch):
    from src.engine.monitoring import sentinel_compact_store as compact
    raw, args, cache = _prepared(tmp_path, monkeypatch)
    original = compact.indexed_rows
    seen, closed = [], []
    def tracked(*args, **kwargs):
        iterator = original(*args, **kwargs)
        try:
            for row in iterator:
                seen.append(row)
                yield row
        finally:
            iterator.close()
            closed.append(True)
    monkeypatch.setattr(compact, 'indexed_rows', tracked)
    _append(raw, _event(1), _event(2))
    window.prepare(tmp_path)
    assert len(seen) == 1 and closed == [True]


def test_preparation_requires_native_owner_commit_before_success(tmp_path, monkeypatch):
    from src.engine.monitoring import sentinel_compact_store as compact
    raw, args, cache = _prepared(tmp_path, monkeypatch)
    _append(raw, _event(1))
    def omitted(*args, **kwargs):
        yield from ()
    monkeypatch.setattr(compact, 'indexed_rows', omitted)
    with pytest.raises(ValueError, match='native_index_unverified'):
        window.prepare(tmp_path)


def test_native_commit_failure_leaves_gap_fail_closed_on_preparation_retry(tmp_path, monkeypatch):
    from src.engine.monitoring import sentinel_compact_store as compact
    raw, args, cache = _prepared(tmp_path, monkeypatch)
    prior = _native_state(cache)
    _append(raw, _event(1))
    def interrupted(*args, **kwargs):
        raise OSError('fixture interrupted before native commit')
        yield
    monkeypatch.setattr(compact, 'indexed_rows', interrupted)
    with pytest.raises(OSError, match='fixture interrupted'):
        window.prepare(tmp_path)
    meta = cache.with_suffix('.meta.json')
    before_retry = (cache.read_bytes(), meta.read_bytes())
    assert _native_state(cache) == prior
    assert prior['generation'] != json.loads(meta.read_bytes())['cache_generation']
    with pytest.raises(ValueError, match='native_index_unverified'):
        window.prepare(tmp_path)
    assert (cache.read_bytes(), meta.read_bytes()) == before_retry


def test_preparation_bounds_actual_cache_append_before_native_owner(tmp_path, monkeypatch):
    from src.engine import sentinel_event_cache as event_cache
    from src.engine.monitoring import sentinel_compact_store as compact
    raw, args, cache = _prepared(tmp_path, monkeypatch)
    original = event_cache._update_and_load_cached_event_rows
    monkeypatch.setattr(window, 'LIMIT', 1024)
    def oversized(**kwargs):
        rows, meta = original(**kwargs)
        with cache.open('ab') as stream:
            stream.write(b' ' * 1025)
        meta['cache_generation'] = compact.stamp(cache)
        return rows, meta
    monkeypatch.setattr(event_cache, '_update_and_load_cached_event_rows', oversized)
    monkeypatch.setattr(compact, 'indexed_rows', lambda *a, **k: pytest.fail('native owner exceeds append budget'))
    with pytest.raises(ValueError, match='native_append_budget_invalid'):
        window.prepare(tmp_path)


def test_preparation_never_advances_past_an_incomplete_raw_line(tmp_path,monkeypatch):
    raw,args,cache=_prepared(tmp_path,monkeypatch)
    before=json.loads(cache.with_suffix('.meta.json').read_bytes())['raw_offset']
    with raw.open('a') as stream:stream.write('{')
    with pytest.raises(ValueError,match='incomplete_or_oversized_raw_line'):
        window.prepare(tmp_path)
    assert json.loads(cache.with_suffix('.meta.json').read_bytes())['raw_offset']==before


def test_decode_error_counter_is_per_append_and_metadata_retry_is_not_counted(tmp_path,monkeypatch):
    from src.engine.monitoring.sentinel_source_window import maintain
    raw,args,cache=_prepared(tmp_path,monkeypatch)
    with raw.open('a') as stream:stream.write('{\n')
    _,meta=update_and_load_cached_event_rows(**args)
    assert meta['source_window_projection']['invalid_rows']==1
    repeated=maintain(cache,meta['cache_generation'],meta,
                      previous_state=meta['source_window_projection'])
    assert repeated['invalid_rows']==1
    _,following=update_and_load_cached_event_rows(**args)
    assert following['source_window_projection']['invalid_rows']==1


@pytest.mark.parametrize('bad',[[],None,{'stage':'unrelated'},
    {'stage':'zero_base_probe_result','pipeline':'ENTRY_PIPELINE','emitted_at':'invalid'}])
def test_cache_writer_retains_unclassified_rows_and_missing_clocks_as_source_gaps(tmp_path,monkeypatch,bad):
    raw,args,cache=_prepared(tmp_path,monkeypatch)
    _append(raw,bad)
    _,meta=update_and_load_cached_event_rows(**args)
    assert meta['source_window_projection']['invalid_rows']==1
    with pytest.raises(ValueError,match='stage_coverage_incomplete'):
        window.read(tmp_path,AT+timedelta(seconds=600),lower_epoch=AT.timestamp())


@pytest.mark.parametrize('change',['append','rotate','same_size_rewrite'])
def test_concurrent_raw_change_uses_captured_prefix_or_rejects_rotation(tmp_path,monkeypatch,change):
    raw,args,cache=_prepared(tmp_path,monkeypatch)
    _append(raw,_event(1))
    original_stat=Path.stat
    changed=False
    def stat(path,*a,**kwargs):
        nonlocal changed
        if path==raw and not changed:
            changed=True
            if change=='append':_append(raw,_event(2))
            elif change=='same_size_rewrite':raw.write_bytes(raw.read_bytes().replace(b'005930',b'036930'))
            else:
                raw.rename(raw.with_suffix('.old'))
                _append(raw,_event(2))
        return original_stat(path,*a,**kwargs)
    monkeypatch.setattr(Path,'stat',stat)
    if change in {'rotate','same_size_rewrite'}:
        with pytest.raises(ValueError,match='generation_changed_during_read'):
            window.read(tmp_path,AT+timedelta(seconds=600),lower_epoch=AT.timestamp())
    else:
        rows,_=window.read(tmp_path,AT+timedelta(seconds=600),lower_epoch=AT.timestamp())
        assert len(rows)==1  # Captured source prefix; the next read consumes the append.
        assert len(window.read(tmp_path,AT+timedelta(seconds=600),lower_epoch=AT.timestamp())[0])==2
