"""Indexed input coverage and fixed raw-read budgets at large source sizes."""
import json
from pathlib import Path
import pytest
from src.engine.automation import main_trailing_source_store as store


def source(root):
    path=root/'ai_decision_trace/ai_decision_trace_2026-10-19.jsonl'
    path.parent.mkdir(parents=True);path.touch()
    return path


def row(identity='trace-1', **extra):
    return dict(schema='ai_decision_trace_v1',decision_stage='entry_screen',
        decision_trace_id=identity,stock_code='005930',entry_ai_risk_verdict='PASS',
        **extra)


def append(root,path,value):
    before=store.signature(path.stat());raw=json.dumps(value).encode()+b'\n'
    with path.open('ab') as handle:handle.write(raw)
    after=store.signature(path.stat())
    assert store.record_append(root,path,before=before,after=after,raw=raw,row=value)


def test_native_append_index_consumption_never_reads_the_raw_source(tmp_path,monkeypatch):
    path=source(tmp_path);append(tmp_path,path,row())
    original=Path.open
    def guarded(self,*args,**kwargs):
        if self==path:pytest.fail('indexed report attempted a raw source read')
        return original(self,*args,**kwargs)
    monkeypatch.setattr(Path,'open',guarded)
    values=list(store.read_rows(tmp_path,path,kinds=['entry_trace'],identities=['trace-1']))
    assert len(values)==1
    assert values[0][0]['row']['decision_trace_id']=='trace-1'
    assert values[0][1]['decoded_offset']==0
    assert len(values[0][1]['sha256'])==64


def test_200_gib_unindexed_history_is_pending_without_a_raw_read(tmp_path,monkeypatch):
    path=source(tmp_path)
    with path.open('r+b') as handle:handle.truncate(200*1024**3)
    append(tmp_path,path,row())
    original=Path.open
    def guarded(self,*args,**kwargs):
        if self==path:pytest.fail('pending coverage attempted a full historical scan')
        return original(self,*args,**kwargs)
    monkeypatch.setattr(Path,'open',guarded)
    with pytest.raises(store.InputPending,match='coverage_incomplete'):
        list(store.read_rows(tmp_path,path))


def test_historical_catchup_joins_exactly_with_new_producer_appends(tmp_path):
    path=source(tmp_path)
    with path.open('ab') as handle:handle.write(json.dumps(row('old')).encode()+b'\n')
    append(tmp_path,path,row('new'))
    with pytest.raises(store.InputPending):list(store.read_rows(tmp_path,path))
    receipt=store.build_step(tmp_path,path)
    assert receipt['complete']
    assert [v['row']['decision_trace_id'] for v,_ in store.read_rows(tmp_path,path)]==['old','new']
    again=store.build_step(tmp_path,path)
    assert again['raw_bytes_read']==0


def test_changed_source_cannot_reuse_old_index(tmp_path):
    path=source(tmp_path);append(tmp_path,path,row())
    raw=path.read_bytes();path.write_bytes(raw.replace(b'trace-1',b'trace-2'))
    with pytest.raises(store.InputPending):list(store.read_rows(tmp_path,path))
    with pytest.raises(store.InputPending):store.build_step(tmp_path,path)


def test_missed_append_does_not_silently_restore_coverage(tmp_path):
    path=source(tmp_path);append(tmp_path,path,row())
    with path.open('ab') as handle:handle.write(b'{}\n')
    before=store.signature(path.stat());raw=json.dumps(row('later')).encode()+b'\n'
    with path.open('ab') as handle:handle.write(raw)
    assert not store.record_append(tmp_path,path,before=before,
        after=store.signature(path.stat()),raw=raw,row=row('later'))
    with pytest.raises(store.InputPending):list(store.read_rows(tmp_path,path))


def test_backfill_read_is_capped_and_resumes_from_committed_cursor(tmp_path):
    path=source(tmp_path)
    raw=json.dumps(dict(schema='irrelevant',padding='x'*1024)).encode()+b'\n'
    with path.open('ab') as handle:
        for _ in range(12000):handle.write(raw)
    first=store.build_step(tmp_path,path,max_bytes=store.MAX_STEP_BYTES,seconds=10)
    assert first['raw_bytes_read']<=store.MAX_STEP_BYTES and not first['complete']
    second=store.build_step(tmp_path,path,max_bytes=store.MAX_STEP_BYTES,seconds=10)
    assert second['raw_bytes_read']<=store.MAX_STEP_BYTES and second['complete']
    assert list(store.read_rows(tmp_path,path))==[]


def test_archive_backfill_requires_a_separate_offline_worker(tmp_path):
    path=source(tmp_path).with_suffix('.jsonl.gz')
    with pytest.raises(store.InputPending,match='offline_archive_migration_required'):
        store.build_step(tmp_path,path)


def test_selected_projection_tamper_is_not_native_success(tmp_path):
    path=source(tmp_path);append(tmp_path,path,row())
    with store._database(tmp_path,path) as (db,_,_),db:
        db.execute('UPDATE rows SET body=?',(b'{}',))
    with pytest.raises(ValueError,match='projection_changed'):
        list(store.read_rows(tmp_path,path))


def test_native_indexes_feed_full_assembly_replay_and_handoff_without_raw_reads(tmp_path,monkeypatch):
    from src.tests.test_main_trailing_source_assembler import fixture,DAY,TARGET
    from src.engine.automation import main_trailing_source_assembler as source
    from src.engine.automation import main_trailing_all_scope_research as research
    from src.engine.automation.main_trailing_research_handoff import verify_report
    data=tmp_path/'data';fixture(data)
    plain=source.assemble(data,tmp_path/'plain',source_date=DAY,target_date=TARGET,start_date=DAY)
    baseline=research.run(plain,input_root=plain.parent,output_root=tmp_path/'baseline',dry_run=False)
    raw_paths=list(data.glob('*/*.jsonl'))
    for path in raw_paths:
        assert store.build_step(data,path)['complete']
    original=Path.open
    def guard(self,*args,**kwargs):
        if self in raw_paths:pytest.fail('indexed normal report opened a raw stream')
        return original(self,*args,**kwargs)
    monkeypatch.setattr(Path,'open',guard)
    manifest=source.assemble(data,tmp_path/'indexed',source_date=DAY,target_date=TARGET,start_date=DAY)
    result=research.run(manifest,input_root=manifest.parent,output_root=tmp_path/'indexed-report',dry_run=False)
    assert verify_report(tmp_path/'indexed-report'/f'research_{DAY}.json',target_date=TARGET)[0]==result
    assert result['initial_policy']==baseline['initial_policy']
    assert result['common_population_evaluation']==baseline['common_population_evaluation']
    assert result['assembly_census']==baseline['assembly_census']


def test_raw_owned_window_identity_exceeds_legacy_budget_without_reading_raw(tmp_path,monkeypatch):
    from datetime import datetime
    from src.engine.monitoring import submission_bottleneck_monitor as monitor
    path=tmp_path/'pipeline_events/pipeline_events_2026-10-19.jsonl'
    path.parent.mkdir();path.touch()
    # Native coverage includes irrelevant raw bytes, without projecting their
    # payload into the report. No synthetic full SHA or skipped prefix.
    for number in range(40):
        append(tmp_path,path,dict(event_type='pipeline_event',pipeline='ENTRY_PIPELINE',
            stage='irrelevant_native_event',stock_code='005930',stock_name='fixture',
            emitted_at='2026-10-19T10:00:00',emitted_date='2026-10-19',
            fields={'padding':'x'*(1024*1024),'ordinal':number}))
    assert path.stat().st_size>monitor.DELAY_RAW_BUDGET
    original=Path.open
    def guard(self,*args,**kwargs):
        if self==path:pytest.fail('native observer fell back to large raw cursor scan')
        return original(self,*args,**kwargs)
    monkeypatch.setattr(Path,'open',guard)
    observed=monitor.pre_submit_delay_source_semantics(tmp_path,datetime(2026,10,19,10,5))
    assert observed['sources']['raw']=='complete'
    assert observed['cursor']['offset']==path.stat().st_size
    assert observed['diagnostics']['raw_native_index_used']==1
    assert 'raw_cursor_backlog' not in observed['issues']


def test_prepared_database_works_through_the_selected_release_data_mount(tmp_path):
    data=tmp_path/'data';data.mkdir();path=source(data)
    with store._database(data,path,writer=True):pass
    release=tmp_path/'release';release.mkdir();(release/'data').symlink_to(data,target_is_directory=True)
    alias=release/'data'/path.relative_to(data)
    value=row();before=alias.stat();raw=json.dumps(value).encode()+b'\n'
    with alias.open('ab') as handle:handle.write(raw)
    store.capture_native_append(alias,before=before,after=alias.stat(),raw=raw,row=value)
    assert len(list(store.read_rows(data,path)))==1


def test_native_first_vote_batch_and_rotation_preserve_scoped_history_without_raw_reads(tmp_path,monkeypatch):
    from datetime import datetime
    from src.tests.test_holding_path_vote_replay import _events
    from src.engine.ai import holding_exit_vote as votes
    at=datetime.fromisoformat('2026-10-16T09:00:00+09:00').timestamp()
    values=_events('EXIT_TRAILING_TP','REGULAR',base_at=at,session_key='2026-10-16')
    path=votes.path_vote_store_path(tmp_path,'record:7')
    monkeypatch.setattr(votes.time,'time',lambda:at+20)
    assert votes.append_path_events_file(path,'record:7',values)[1]=='appended'
    old=store.scoped_vote_generation(tmp_path,path,'2026-10-16')
    first=list(store.vote_rows(tmp_path,path,'record:7'))
    assert len(first)==2
    later=datetime.fromisoformat('2026-10-19T09:00:00+09:00').timestamp()
    future=_events('EXIT_TRAILING_TP','REGULAR',base_at=later,session_key='2026-10-19')
    monkeypatch.setattr(votes.time,'time',lambda:later+20)
    monkeypatch.setattr(votes,'PATH_MAX_STORE_BYTES',path.stat().st_size+100)
    assert votes.append_path_events_file(path,'record:7',future)[1]=='appended'
    assert len(list(path.parent.glob(path.name+'.segment-*')))==1
    original=Path.open
    def guard(self,*a,**kw):
        if self.parent==path.parent and '.jsonl' in self.name:pytest.fail('indexed vote read opened native raw')
        return original(self,*a,**kw)
    monkeypatch.setattr(Path,'open',guard)
    monkeypatch.setattr(votes,'_iter_path_events',lambda *a:pytest.fail('indexed live vote reader scanned raw'))
    assert store.scoped_vote_generation(tmp_path,path,'2026-10-16')==old
    assert list(store.vote_rows(tmp_path,path,'record:7',source_date='2026-10-16'))==first
    assert len(votes.load_path_events_file(path,'record:7',tail=True))==4


def test_indexed_archive_consumer_never_reopens_compressed_raw(tmp_path,monkeypatch):
    from src.engine.compress_db_backfilled_files import _gzip_file
    path=source(tmp_path);append(tmp_path,path,row())
    before=store.generation(tmp_path,path)
    assert _gzip_file(path,dry_run=False)[0]
    assert not path.exists()
    original=Path.open
    def guard(self,*a,**kw):
        if self==Path(str(path)+'.gz'):pytest.fail('indexed report reopened gzip stream')
        return original(self,*a,**kw)
    monkeypatch.setattr(Path,'open',guard)
    assert store.generation(tmp_path,path)==before
    assert len(list(store.read_rows(tmp_path,path)))==1


def test_native_cursor_source_gaps_and_future_rows_remain_explicit(tmp_path):
    path=tmp_path/'pipeline_events/pipeline_events_2026-10-19.jsonl'
    path.parent.mkdir();path.touch()
    value=dict(event_type='pipeline_event',pipeline='ENTRY_PIPELINE',stock_code='005930',
        emitted_at='2026-10-19T10:07:00',emitted_date='2026-10-19',
        stage='pre_submit_delay_committed',fields={'delay_intent_id':'future'})
    append(tmp_path,path,value)
    result=store.window(tmp_path,path,cutoff='2026-10-19T10:00:00')
    assert result['rows']==[value]
    assert result['source_gaps']==0
    append(tmp_path,path,['malformed_native_row'])
    result=store.window(tmp_path,path,cutoff='2026-10-19T10:00:00')
    assert result['source_gaps']==1


def test_native_completed_cohort_excludes_unrelated_200_gib_vote_history(tmp_path,monkeypatch):
    from src.engine import log_archive_service as archive
    from src.engine.sniper_trade_review_report import completed_census_manifest
    from src.engine.automation import main_trailing_source_assembler as assembly
    from src.engine.automation.main_trailing_completed_store import vote_store_names
    day='2026-10-19';directory=tmp_path/'report/monitor_snapshots'
    directory.mkdir(parents=True)
    monkeypatch.setattr(archive,'DATA_DIR',tmp_path)
    monkeypatch.setattr(archive,'MONITOR_SNAPSHOT_DIR',directory)
    monkeypatch.setattr(archive,'MONITOR_SNAPSHOT_MANIFEST_DIR',directory/'manifests')
    payload=dict(date=day,code=None,since=None,
        meta=dict(warnings=[],snapshot_profile='postclose_exit',sell_completed_event_ids=[],trailing_event_source_receipts=[]),
        metrics=dict(canonical_completed_trades=0,completed_trades=0,open_scalp_position_projection_count=0,
            open_scalp_position_projection_status='current_db_census'),
        sections=dict(completed_trade_projection=[],open_scalp_position_projection=[]))
    payload['meta']['completed_census_manifest']=completed_census_manifest(payload)
    archive.save_monitor_snapshot('trade_review',day,payload)
    assert vote_store_names(tmp_path,[day])==set()
    path=tmp_path/'runtime/holding_path_votes'/('a'*64+'.jsonl');path.parent.mkdir(parents=True)
    with path.open('wb') as handle:handle.truncate(200*1024**3)
    original=Path.open
    def guard(self,*a,**kw):
        if self==path:pytest.fail('unrelated position history was read')
        return original(self,*a,**kw)
    monkeypatch.setattr(Path,'open',guard)
    with store.native_input_session(tmp_path,day):
        result=assembly.input_inventory(tmp_path,[day],tmp_path/'master',tmp_path/'parent')
    assert str(path) not in [r['path'] for r in result]


def test_busy_native_writer_retries_original_resident_bytes_in_order_without_raw_read(tmp_path,monkeypatch):
    path=source(tmp_path)
    with store._database(tmp_path,path,writer=True):pass
    native=store.record_append
    monkeypatch.setattr(store,'maintain',lambda *a:None)
    monkeypatch.setattr(store,'record_append',lambda *a,**kw:(_ for _ in ()).throw(
        store.InputPending('trailing_index_writer_busy')))
    for name in ('first','second'):
        value=row(name);before=path.stat();raw=json.dumps(value).encode()+b'\n'
        with path.open('ab') as handle:handle.write(raw)
        store.capture_native_append(path,before=before,after=path.stat(),raw=raw,row=value)
    with pytest.raises(store.InputPending):store.generation(tmp_path,path)
    monkeypatch.setattr(store,'record_append',native)
    original=Path.open
    def guard(self,*a,**kw):
        if self==path:pytest.fail('busy native append retry reread raw')
        return original(self,*a,**kw)
    monkeypatch.setattr(Path,'open',guard)
    store._drain_pending(tmp_path)
    assert [v['row']['decision_trace_id'] for v,_ in store.read_rows(tmp_path,path)]==['first','second']
    assert str(path) not in store._PENDING_APPENDS


def test_native_writer_reopens_its_own_connection_after_fork(tmp_path):
    import os
    path=source(tmp_path);append(tmp_path,path,row('parent-before'))
    child=os.fork()
    if child==0:
        try:append(tmp_path,path,row('child'))
        except BaseException:os._exit(2)
        os._exit(0)
    assert os.waitpid(child,0)[1]==0
    append(tmp_path,path,row('parent-after'))
    assert [v['row']['decision_trace_id'] for v,_ in store.read_rows(tmp_path,path)]==[
        'parent-before','child','parent-after']
