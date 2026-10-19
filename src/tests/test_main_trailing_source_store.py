"""Indexed input coverage and fixed raw-read budgets at large source sizes."""
import json
from pathlib import Path
import pytest
from src.engine.automation import main_trailing_source_store as store


@pytest.fixture(autouse=True)
def explicit_migration_only(monkeypatch):
    # Tests drive catch-up and resident retries explicitly; a daemon from a
    # temporary writer must not prepare another test's cache concurrently.
    monkeypatch.setattr(store, 'maintain', lambda *a: None)
    monkeypatch.setattr(store, '_MAINTENANCE_REQUEST', None)


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


def test_offline_archive_enrollment_preserves_source_and_never_restores_plain(tmp_path,monkeypatch):
    import hashlib
    from src.engine.compress_db_backfilled_files import _gzip_file
    path=source(tmp_path);raw=json.dumps(row()).encode()+b'\n';path.write_bytes(raw)
    assert _gzip_file(path,dry_run=False)[0]
    archive=Path(str(path)+'.gz')
    receipt=Path(str(archive)+'.archive_receipt.json');original_receipt=receipt.read_bytes()
    before=archive.read_bytes();identity=store.signature(archive.stat())
    with pytest.raises(store.InputPending):store.generation(tmp_path,path)
    bound=store.migrate_frozen_source(tmp_path,path)
    assert not path.exists() and archive.read_bytes()==before
    assert store.signature(archive.stat())==identity and receipt.read_bytes()==original_receipt
    assert bound['source_stat']==identity and bound['size']==len(raw)
    assert store.input_generation(tmp_path,archive)==bound
    original=Path.open
    def no_raw(self,*args,**kwargs):
        if self in (path,archive):pytest.fail('indexed reader reopened compressed source')
        return original(self,*args,**kwargs)
    monkeypatch.setattr(Path,'open',no_raw)
    values=list(store.read_rows(tmp_path,path))
    assert values[0][0]['row']['decision_trace_id']=='trace-1'
    assert values[0][1]['sha256']==hashlib.sha256(raw).hexdigest()
    assert store.migrate_frozen_source(tmp_path,path)==bound


@pytest.mark.parametrize('damage',['seal','logical_sha','logical_size','path','authority','generation','concurrent'])
def test_archive_enrollment_cannot_discard_existing_native_logical_authority(tmp_path,monkeypatch,damage):
    import hashlib
    from src.engine.compress_db_backfilled_files import _gzip_file
    path=source(tmp_path);path.write_bytes(json.dumps(row()).encode()+b'\n')
    assert _gzip_file(path,dry_run=False)[0]
    receipt=Path(str(path)+'.gz.archive_receipt.json');value=json.loads(receipt.read_bytes())
    if damage in {'seal','logical_sha'}:value['logical_content_sha256']='0'*64
    elif damage=='logical_size':value['logical_size_bytes']+=1
    elif damage=='path':value['logical_path']=str(path.with_name('foreign.jsonl'))
    elif damage=='authority':value['allowed_runtime_apply']=True
    elif damage=='generation':value['archive_generation']={}
    if damage!='seal':
        value['artifact_content_sha256']=hashlib.sha256(store.encode({
            k:v for k,v in value.items() if k!='artifact_content_sha256'})).hexdigest()
    receipt.write_bytes(store.encode(value));before=receipt.read_bytes()
    if damage=='concurrent':
        original=store._put
        def change(*args,**kwargs):
            result=original(*args,**kwargs);receipt.write_bytes(before);return result
        monkeypatch.setattr(store,'_put',change)
    with pytest.raises(ValueError,match='archive.*(invalid|mismatch|changed)'):
        store.migrate_frozen_source(tmp_path,path)
    assert not store._location(tmp_path,path)[2].exists() and not path.exists()
    assert receipt.read_bytes()==before


@pytest.mark.parametrize('present_at_enrollment',[False,True])
def test_indexed_gzip_rechecks_declared_logical_seal_without_raw_decode(tmp_path,monkeypatch,present_at_enrollment):
    import hashlib
    from src.engine.compress_db_backfilled_files import _gzip_file
    path=source(tmp_path);path.write_bytes(json.dumps(row()).encode()+b'\n')
    assert _gzip_file(path,dry_run=False)[0]
    receipt=Path(str(path)+'.gz.archive_receipt.json');original=receipt.read_bytes()
    if not present_at_enrollment:receipt.unlink()
    bound=store.migrate_frozen_source(tmp_path,path)
    if not present_at_enrollment:receipt.write_bytes(original)
    opened=Path.open
    def guard(self,*args,**kwargs):
        if self==Path(str(path)+'.gz'):pytest.fail('indexed authority check decoded the archive')
        return opened(self,*args,**kwargs)
    monkeypatch.setattr(Path,'open',guard)
    assert store.generation(tmp_path,path)==bound
    value=json.loads(original);value['logical_content_sha256']='0'*64
    value['artifact_content_sha256']=hashlib.sha256(store.encode({
        k:v for k,v in value.items() if k!='artifact_content_sha256'})).hexdigest()
    receipt.write_bytes(store.encode(value))
    with pytest.raises(ValueError,match='logical_authority_changed'):store.generation(tmp_path,path)


@pytest.mark.parametrize('corruption',['crc','partial','changed','symlink'])
def test_archive_enrollment_does_not_publish_failed_or_foreign_sources(tmp_path,monkeypatch,corruption):
    import gzip
    path=source(tmp_path);path.unlink();archive=Path(str(path)+'.gz')
    raw=json.dumps(row()).encode()+ (b'' if corruption=='partial' else b'\n')
    packed=gzip.compress(raw)
    archive.write_bytes(packed[:-5] if corruption=='crc' else packed)
    if corruption=='symlink':
        other=archive.with_name('foreign.gz');archive.rename(other);archive.symlink_to(other)
    if corruption=='changed':
        original=store._put
        def change(*args):
            result=original(*args);archive.write_bytes(packed);return result
        monkeypatch.setattr(store,'_put',change)
    with pytest.raises((ValueError,EOFError,store.InputPending)):
        store.migrate_frozen_source(tmp_path,path)
    assert not store._location(tmp_path,path)[2].exists() and not path.exists()


def test_window_preparation_enrolls_once_and_keeps_future_sources_out(tmp_path,monkeypatch):
    import gzip
    path=source(tmp_path);path.write_bytes(json.dumps(row()).encode()+b'\n')
    old=path.with_name('ai_decision_trace_2026-10-16.jsonl.gz')
    old.write_bytes(gzip.compress(json.dumps(row('old')).encode()+b'\n'))
    path.with_name('ai_decision_trace_2026-10-20.jsonl.gz').write_bytes(b'invalid future source')
    result=store.prepare_window(tmp_path,'2026-10-19')
    assert len(result)==2
    monkeypatch.setattr(store,'build_step',lambda *a,**k:pytest.fail('repeated migration'))
    monkeypatch.setattr(store,'migrate_frozen_source',lambda *a,**k:pytest.fail('repeated migration'))
    assert store.prepare_window(tmp_path,'2026-10-19')==result


def test_frozen_generation_replacement_preserves_prior_cache_and_append_inode(tmp_path):
    import sqlite3
    path=source(tmp_path);append(tmp_path,path,row('old'))
    target=store._location(tmp_path,path)[2];inode=target.stat().st_ino
    path.write_bytes(json.dumps(row('new')).encode()+b'\n')
    result=store.prepare_window(tmp_path,'2026-10-19')
    assert result[0]['generation']==store.generation(tmp_path,path)
    assert target.stat().st_ino==inode
    assert [v['row']['decision_trace_id'] for v,_ in store.read_rows(tmp_path,path)]==['new']
    saved=list(target.parent.glob('*.before-offline-*.sqlite'));assert len(saved)==1
    with sqlite3.connect(saved[0]) as db:
        assert json.loads(db.execute('SELECT body FROM rows').fetchone()[0])['row']['decision_trace_id']=='old'
    append(tmp_path,path,row('later'))
    assert [v['row']['decision_trace_id'] for v,_ in store.read_rows(tmp_path,path)]==['new','later']


def test_archive_oversize_row_is_identified_without_blocking_other_rows(tmp_path):
    import gzip,hashlib
    path=source(tmp_path);path.unlink()
    huge=json.dumps(dict(padding='x'*(store.MAX_ROW_BYTES+100))).encode()+b'\n'
    raw=huge+json.dumps(row()).encode()+b'\n'
    Path(str(path)+'.gz').write_bytes(gzip.compress(raw))
    store.migrate_frozen_source(tmp_path,path)
    values=list(store.read_rows(tmp_path,path))
    assert values[0][0]['reason']=='source_record_budget_exceeded'
    assert values[0][1]['size']==len(huge) and values[0][1]['sha256']==hashlib.sha256(huge).hexdigest()
    assert values[1][1]['decoded_offset']==len(huge)
    assert values[1][0]['row']['decision_trace_id']=='trace-1'


def test_selected_projection_tamper_is_not_native_success(tmp_path):
    path=source(tmp_path);append(tmp_path,path,row())
    with store._database(tmp_path,path) as (db,_,_),db:
        db.execute('UPDATE rows SET body=?',(b'{}',))
    with pytest.raises(ValueError,match='projection_changed'):
        list(store.read_rows(tmp_path,path))


@pytest.mark.parametrize('offline_archives',[False,True])
def test_native_indexes_feed_full_assembly_replay_and_handoff_without_raw_reads(tmp_path,monkeypatch,offline_archives):
    from src.tests.test_main_trailing_source_assembler import fixture,DAY,TARGET
    from src.engine.automation import main_trailing_source_assembler as source
    from src.engine.automation import main_trailing_all_scope_research as research
    from src.engine.automation.main_trailing_research_handoff import verify_report
    data=tmp_path/'data';fixture(data)
    plain=source.assemble(data,tmp_path/'plain',source_date=DAY,target_date=TARGET,start_date=DAY)
    baseline=research.run(plain,input_root=plain.parent,output_root=tmp_path/'baseline',dry_run=False)
    raw_paths=list(data.glob('*/*.jsonl'))
    for path in raw_paths:
        if offline_archives:
            import gzip
            Path(str(path)+'.gz').write_bytes(gzip.compress(path.read_bytes()));path.unlink()
            store.migrate_frozen_source(data,path)
        else:
            assert store.build_step(data,path)['complete']
    original=Path.open
    def guard(self,*args,**kwargs):
        if self in raw_paths or self in [Path(str(p)+'.gz') for p in raw_paths]:
            pytest.fail('indexed normal report opened a raw stream')
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



def _broken_pipeline_index(root):
    path = root/'pipeline_events/pipeline_events_2026-10-19.jsonl'
    path.parent.mkdir(parents=True); path.touch()
    from src.utils.pipeline_event_logger import _pipeline_event_partition_lock_path
    _pipeline_event_partition_lock_path(path).touch()
    def event(qty):
        return dict(stage='order_leg_sent',stock_code='005930',emitted_at='2026-10-19T18:37:00+09:00',
                    fields=dict(qty=qty,actual_order_submitted=True))
    append(root, path, event(1))
    for qty in (2, 3):
        before=store.signature(path.stat()); raw=json.dumps(event(qty)).encode()+b'\n'
        with path.open('ab') as handle:handle.write(raw)
        if qty == 3:
            assert not store.record_append(root,path,before=before,after=store.signature(path.stat()),raw=raw,row=event(qty))
    return path, event


@pytest.mark.parametrize('queued_retry', [False, True])
def test_pipeline_gap_archives_failed_cache_then_verifies_whole_raw_prefix(tmp_path, monkeypatch, queued_retry):
    import sqlite3
    path, event = _broken_pipeline_index(tmp_path)
    before_bytes = path.read_bytes()
    if queued_retry:
        from types import SimpleNamespace
        signature=path.stat(); raw=json.dumps(event(3)).encode()+b'\n'
        prior=SimpleNamespace(**{key:getattr(signature,key) for key in (
            'st_dev','st_ino','st_mode','st_mtime_ns','st_ctime_ns')},st_size=signature.st_size-len(raw))
        assert store._queue_append(tmp_path,path,prior,signature,raw)
    original=Path.open
    def guard(self,*a,**kw):
        if self==path:pytest.fail('cache recovery scanned the raw source')
        return original(self,*a,**kw)
    with monkeypatch.context() as local:
        local.setattr(Path,'open',guard)
        recovered=store._recover_append_gap(tmp_path,path)
    assert recovered['status']=='rebuild_pending'
    assert path.read_bytes()==before_bytes
    with sqlite3.connect(recovered['archive']) as archive:
        assert archive.execute('SELECT invalid FROM sources WHERE path=?',(str(path),)).fetchone()[0]=='append_chain_gap'
        assert archive.execute('SELECT COUNT(*) FROM rows').fetchone()[0]==1
    with pytest.raises(store.InputPending):list(store.read_rows(tmp_path,path))
    assert str(path) not in store._PENDING_APPENDS
    # A late retry from another writer is covered by the explicit raw prefix;
    # it must not invalidate the new generation or duplicate its minute rows.
    if queued_retry:
        assert store._queue_append(tmp_path,path,prior,signature,raw)
        store._drain_pending(tmp_path)
    append(tmp_path,path,event(4))
    assert store.build_step(tmp_path,path)['complete']
    rows=list(store.read_rows(tmp_path,path))
    assert [value['row']['fields']['qty'] for value,_ in rows]==[1,2,3,4]


@pytest.mark.parametrize('fault',['partition_busy','source_busy','source_replaced','archive_failure','archive_untrusted'])
def test_pipeline_gap_recovery_preserves_invalid_cache_when_custody_fails(tmp_path, monkeypatch, fault):
    import os,fcntl
    from src.utils.pipeline_event_logger import _pipeline_event_partition_lock_path
    path,_=_broken_pipeline_index(tmp_path); lock=None
    if fault=='partition_busy':
        lock=os.open(_pipeline_event_partition_lock_path(path),os.O_RDWR)
        fcntl.flock(lock,fcntl.LOCK_EX)
    elif fault=='source_busy':
        lock=os.open(path,os.O_RDONLY);fcntl.flock(lock,fcntl.LOCK_EX)
    elif fault=='archive_untrusted':
        import hashlib
        with store._database(tmp_path,path,readonly=True) as (db,_,_):
            state=db.execute('SELECT * FROM sources WHERE path=?',(str(path),)).fetchone()
        target=store._location(tmp_path,path)[2]
        archive=target.with_name(target.stem+'.append-gap-'+hashlib.sha256(store.encode(state)).hexdigest()[:24]+'.sqlite')
        archive.symlink_to(target)
    elif fault=='source_replaced':
        replacement=path.with_suffix('.replacement');replacement.write_bytes(path.read_bytes());replacement.replace(path)
    else:
        monkeypatch.setattr(store.os,'link',lambda *a,**kw:(_ for _ in ()).throw(OSError('archive_write_failed')))
    try:
        if fault=='archive_failure':
            with pytest.raises(OSError,match='archive_write_failed'):store._recover_append_gap(tmp_path,path)
        elif fault=='archive_untrusted':
            with pytest.raises(store.InputPending,match='archive_untrusted'):store._recover_append_gap(tmp_path,path)
        else:assert store._recover_append_gap(tmp_path,path) is False
    finally:
        if lock is not None:os.close(lock)
    with store._database(tmp_path,path,readonly=True) as (db,_,_):
        assert db.execute('SELECT invalid FROM sources WHERE path=?',(str(path),)).fetchone()[0]=='append_chain_gap'
    with pytest.raises(store.InputPending):list(store.read_rows(tmp_path,path))



def test_background_maintenance_restarts_invalid_pipeline_as_pending(tmp_path):
    path,_=_broken_pipeline_index(tmp_path)
    turn=store.STREAM_NAMESPACES.index('pipeline_events')
    store._maintain_once(tmp_path,'2026-10-19',turn=turn)
    observed=store._MAINTENANCE_STATUS[str(path)]
    assert observed['complete'] is False
    assert observed['recovery']['status']=='rebuild_pending'
    assert Path(observed['recovery']['archive']).is_file()
    with pytest.raises(store.InputPending):list(store.read_rows(tmp_path,path))
