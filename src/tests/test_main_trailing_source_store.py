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


@pytest.mark.parametrize('historical', [False, True])
@pytest.mark.parametrize('compressed', [False, True])
def test_original_buy_observations_reach_cost_producer_without_entering_trailing_population(tmp_path,monkeypatch,historical,compressed):
    from collections import Counter
    path=tmp_path/'pipeline_events/pipeline_events_2026-10-19.jsonl'
    path.parent.mkdir();path.touch()
    anchor=dict(record_id=1,stock_code='005930',stage='order_leg_sent',
        pipeline='ENTRY_PIPELINE',emitted_at='2026-10-19T10:00:00',fields={})
    fill=dict(anchor,stage='position_rebased_after_fill',pipeline='HOLDING_PIPELINE',
        fields={'order_no':'11','execution_no':'101','fill_qty':2})
    append(tmp_path,path,anchor)
    project=store.project
    if historical:monkeypatch.setattr(store,'project',lambda ns,row:None if row['stage']==fill['stage'] else project(ns,row))
    append(tmp_path,path,fill)
    monkeypatch.setattr(store,'project',project)
    logical_size=path.stat().st_size
    if compressed:
        from src.engine.compress_db_backfilled_files import _gzip_file
        assert _gzip_file(path,dry_run=False)[0]
    generation=store.generation(tmp_path,path)
    if historical:
        events,io=store.read_order_fill_windows(tmp_path,path,['1'],expected_generation=generation)
        assert io['selected_bytes']==logical_size
    else:
        events=list(store.read_rows(tmp_path,path,kinds=['pipeline_fill_receipt'],identities=['1']))
        events=[(value['row'],reference) for value,reference in events]
    assert [payload for payload,_ in events]==[fill]
    with store.IndexedReader(tmp_path,path,Counter()) as reader:
        assert json.loads(reader.readline(1024))['stage']=='order_leg_sent'
        assert reader.readline(1024)==b''
    physical=Path(str(path)+'.gz') if compressed else path
    physical.write_bytes(physical.read_bytes()+b'{}\n')
    with pytest.raises(ValueError,match='trailing_index_|research_buy_window_'):
        store.read_order_fill_windows(tmp_path,path,['1'],expected_generation=generation)


@pytest.mark.parametrize("mode", ["verified_append", "strict_append", "missing_append", "rewrite"])
@pytest.mark.parametrize("reuse_session", [False, True])
def test_pinned_row_snapshot_admits_only_native_append_and_never_new_rows(tmp_path, mode, reuse_session):
    from contextlib import nullcontext
    with store.read_session(tmp_path) if reuse_session else nullcontext():
        path = source(tmp_path)
        append(tmp_path, path, row())
        receipt = {} if mode != "strict_append" else None
        stream = store.read_rows(tmp_path, path, snapshot_receipt=receipt)
        assert next(stream)[0]['row']['decision_trace_id'] == 'trace-1'
        if mode in {"verified_append", "strict_append"}:
            append(tmp_path, path, row('trace-2'))
        elif mode == "missing_append":
            with path.open('ab') as handle:
                handle.write(json.dumps(row('trace-2')).encode()+b'\n')
        else:
            path.write_bytes(path.read_bytes().replace(b'trace-1', b'trace-9'))
        if mode == "verified_append":
            assert list(stream) == []
            assert receipt['verified_append_after_snapshot'] is True
            assert receipt['generation']['selected_records'] == 1
        else:
            with pytest.raises(store.InputPending):
                list(stream)
            assert receipt in (None, {})

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


@pytest.mark.parametrize('damage',[None,'prefix','append','extra','partial'])
def test_legacy_archive_enrollment_preserves_original_prefix_and_append_chains(tmp_path,damage):
    import gzip
    from src.engine.automation.main_trailing_source_assembler import source_generation_matches
    path=source(tmp_path)
    path.write_bytes(json.dumps(row('prefix')).encode()+b'\n')
    assert store.build_step(tmp_path,path,seconds=10)['complete']
    append(tmp_path,path,row('append'))
    original=store.generation(tmp_path,path)
    raw=path.read_bytes()
    if damage in {'prefix','append'}:raw=raw.replace(damage.encode(),b'change')
    elif damage=='extra':raw+=json.dumps(row('extra')).encode()+b'\n'
    elif damage=='partial':raw=raw[:-1]
    archive=Path(str(path)+'.gz');archive.write_bytes(gzip.compress(raw));path.unlink()
    before=archive.read_bytes()
    if damage:
        with pytest.raises((ValueError,store.InputPending),match='original_index|partial_record'):
            store.migrate_frozen_source(tmp_path,path)
        assert not source_generation_matches(tmp_path,'2026-10-20',path,original)
    else:
        current=store.migrate_frozen_source(tmp_path,path)
        assert current['catchup_end']==original['catchup_end']<current['size']
        assert current['prefix_chain_sha256']==original['prefix_chain_sha256']
        assert current['append_chain_sha256']==original['append_chain_sha256']
        assert source_generation_matches(tmp_path,'2026-10-20',path,original)
        assert len(list(store.read_rows(tmp_path,path)))==2
    assert archive.read_bytes()==before and not path.exists()


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


@pytest.mark.parametrize('legacy_kind',['hash_only_four_stat','sized_four_stat','sized_five_stat'])
@pytest.mark.parametrize('damage',[None,'sha','size','partial_modern'])
def test_original_legacy_pipeline_archive_requires_full_crc_enrollment(tmp_path,monkeypatch,legacy_kind,damage):
    from src.engine.compress_db_backfilled_files import _gzip_file
    path=tmp_path/'pipeline_events/pipeline_events_2026-10-19.jsonl';path.parent.mkdir()
    raw=json.dumps(dict(stage='order_leg_sent',stock_code='005930',fields={})).encode()+b'\n'
    path.write_bytes(raw);assert _gzip_file(path,dry_run=False)[0]
    receipt=Path(str(path)+'.gz.archive_receipt.json');value=json.loads(receipt.read_bytes())
    for key in ('artifact_content_sha256','verification_contract'):value.pop(key)
    if legacy_kind!='sized_five_stat':value['archive_generation'].pop('ctime_ns')
    if legacy_kind=='hash_only_four_stat':
        for key in ('logical_size_bytes','storage_custody','storage_disposition'):value.pop(key)
    if damage=='sha':value['logical_content_sha256']='0'*64
    elif damage=='size':value['logical_size_bytes']=(value['logical_size_bytes']+1 if 'logical_size_bytes' in value else None)
    elif damage=='partial_modern':value['verification_contract']='logical_sha256_size_crc_to_eof_v1'
    receipt.write_text(json.dumps(value,indent=3)+'\n');before=receipt.read_bytes()
    with pytest.raises(ValueError):store._archive_logical_authority(path)
    if damage:
        with pytest.raises(ValueError,match='archive.*(invalid|mismatch)'):store.migrate_frozen_source(tmp_path,path)
        assert not store._location(tmp_path,path)[2].exists()
    else:
        bound=store.migrate_frozen_source(tmp_path,path)
        assert bound['size']==len(raw) and bound['raw_records']==1
        original=Path.open
        def guard(self,*args,**kwargs):
            if self==Path(str(path)+'.gz'):pytest.fail('cached legacy source decoded raw gzip')
            return original(self,*args,**kwargs)
        monkeypatch.setattr(Path,'open',guard)
        assert store.generation(tmp_path,path)==bound
        assert len(list(store.read_rows(tmp_path,path)))==1
    assert receipt.read_bytes()==before and not path.exists()


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


@pytest.mark.parametrize('damage', [None, 'content', 'seal', 'append'])
def test_frozen_plain_index_remains_bound_after_verified_gzip_enrollment(tmp_path, damage):
    import gzip
    from src.engine.automation.main_trailing_source_assembler import source_generation_matches
    path=source(tmp_path);raw=json.dumps(row()).encode()+b'\n';path.write_bytes(raw)
    store.build_step(tmp_path,path)
    original=store.generation(tmp_path,path)
    if damage=='content':raw=json.dumps(row('changed')).encode()+b'\n'
    elif damage=='append':raw+=json.dumps(row('added')).encode()+b'\n'
    elif damage=='seal':original=dict(original,sha256='0'*64)
    Path(str(path)+'.gz').write_bytes(gzip.compress(raw));path.unlink()
    if damage in {'content','append'}:
        with pytest.raises(ValueError,match='original_index_mismatch'):
            store.migrate_frozen_source(tmp_path,path)
    else:
        store.migrate_frozen_source(tmp_path,path)
    assert source_generation_matches(tmp_path,'2026-10-19',path,original) is (damage is None)


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


def _original_completed_source(root,monkeypatch,kind,compressed):
    from src.engine.automation import main_trailing_completed_store as completed
    from src.engine import compress_db_backfilled_files as archive
    if kind=='retained':
        from src.tests.test_holding_window_generation import _retained_original_window
        day,raw,_=_retained_original_window(root,monkeypatch)
    else:
        from src.tests.test_strategy_position_performance_report import _native_fact_projection
        day,raw=_native_fact_projection(root,monkeypatch,large=False)
        receipt=Path(str(raw.with_suffix('.completed_projection.json'))+'.dependencies.json')
        dependency=json.loads(receipt.read_bytes());dependency.pop('trailing_completed_index')
        dependency['artifact_sha256']=completed.digest({k:v for k,v in dependency.items()if k!='artifact_sha256'})
        receipt.write_text(json.dumps(dependency))
    sidecar=raw.with_suffix('.completed_projection.json')
    if compressed:
        monkeypatch.setattr(archive,'MONITOR_SNAPSHOT_DIR',sidecar.parent)
        assert archive._gzip_file(sidecar,dry_run=False)[0]
    return day,raw,sidecar


@pytest.mark.parametrize('kind',['native','retained'])
@pytest.mark.parametrize('compressed',[False,True])
def test_explicit_completed_enrollment_preserves_originals_and_warm_reader(kind,compressed,tmp_path,monkeypatch):
    from src.engine.automation import main_trailing_completed_store as completed
    from src.engine.lifecycle import research_json_stream as stream,research_storage as storage
    from src.engine.lifecycle.holding_window_generation import byte_generation,verified_legacy_projection_dependency
    root=tmp_path/'source';day,raw,sidecar=_original_completed_source(root,monkeypatch,kind,compressed)
    originals={p:p.read_bytes()for p in (root/'report/monitor_snapshots').iterdir()if p.is_file()}
    legacy_output=tmp_path/'legacy';expected=list(stream.completed_rows(sidecar,legacy_output))
    result=store.prepare_window(root,day,start_date=day)
    assert any(r.get('status')=='offline_index_prepared'for r in result),result
    generation=byte_generation(sidecar);receipt=Path(str(sidecar)+'.dependencies.json')
    dependency=(completed._metadata(receipt)if receipt.exists()else
        verified_legacy_projection_dependency(root,day,projection_generation=generation)[0])
    assert completed.binding(root,dependency,projection_generation=generation)
    def no_source(*a,**k):pytest.fail('normal completed reader reopened original rows')
    monkeypatch.setattr(stream,'completed_rows',no_source)
    monkeypatch.setattr(store,'claim_legacy_bytes',no_source)
    output=tmp_path/'indexed';actual=list(completed.read(root,dependency,output,projection_generation=generation))
    assert len(actual)==len(expected)==1
    def expanded(trade,base):
        return {k:(list(storage.iter_tree(base,v))if isinstance(v,dict)and v.get('schema')==storage.SCHEMA else v)
            for k,v in trade.items()}
    assert expanded(actual[0][0],output)==expanded(expected[0][0],legacy_output)
    assert list(storage.iter_tree(output,actual[0][1]))==list(storage.iter_tree(legacy_output,expected[0][1]))
    assert completed.vote_store_names(root,[day])==set()
    assert completed.prepare_window(root,[day])[0]['status']=='offline_index_ready'
    assert originals=={p:p.read_bytes()for p in originals}
    # Historical enrollment also gives the existing inventory an exact cohort;
    # an unrelated journal must not force a scan or a larger legacy budget.
    from src.engine.automation import main_trailing_source_assembler as assembly
    unrelated=root/'runtime/holding_path_votes'/('a'*64+'.jsonl')
    unrelated.parent.mkdir(parents=True,exist_ok=True)
    with unrelated.open('wb')as handle:handle.truncate(200*1024**3)
    master=root/'master.json';master.write_text('{}')
    parent=root/'parent.json';parent.write_text('{}')
    original_open=Path.open
    def guarded(path,*args,**kwargs):
        if path==unrelated:pytest.fail('unrelated vote history reopened')
        return original_open(path,*args,**kwargs)
    monkeypatch.setattr(Path,'open',guarded)
    inventory=assembly.input_inventory(root,[day],master,parent)
    assert str(unrelated)not in {r['path']for r in inventory}


@pytest.mark.parametrize('mutation',['projection','dependency','code','manifest'])
def test_completed_offline_cache_refuses_changed_sources_and_code(tmp_path,monkeypatch,mutation):
    from src.engine.automation import main_trailing_completed_store as completed
    from src.engine.lifecycle.holding_window_generation import byte_generation
    root=tmp_path/'source';day,_,sidecar=_original_completed_source(root,monkeypatch,'native',False)
    completed.prepare_window(root,[day]);generation=byte_generation(sidecar)
    receipt=Path(str(sidecar)+'.dependencies.json');dependency=completed._metadata(receipt)
    bound=completed.binding(root,dependency,projection_generation=generation)
    if mutation=='projection':sidecar.write_bytes(sidecar.read_bytes()+b' ')
    elif mutation=='dependency':receipt.write_bytes(receipt.read_bytes()+b' ')
    elif mutation=='code':monkeypatch.setattr(completed,'_offline_code',lambda:'0'*64)
    else:
        path=Path(bound['manifest_path']);body=json.loads(path.read_bytes());body['runtime_effect']=True
        body['artifact_sha256']=completed.digest({k:v for k,v in body.items()if k!='artifact_sha256'})
        path.write_text(json.dumps(body))
    with pytest.raises((ValueError,OSError)):
        list(completed.read(root,dependency,tmp_path/'reader',projection_generation=generation))


def test_completed_enrollment_refuses_source_change_before_publication(tmp_path,monkeypatch):
    from src.engine.automation import main_trailing_completed_store as completed
    from src.engine.lifecycle import research_json_stream as stream
    root=tmp_path/'source';day,_,sidecar=_original_completed_source(root,monkeypatch,'native',False)
    original=stream.completed_rows
    def changed(*args,**kwargs):
        yield from original(*args,**kwargs)
        sidecar.write_bytes(sidecar.read_bytes()+b' ')
    monkeypatch.setattr(stream,'completed_rows',changed)
    with pytest.raises(ValueError,match='offline_source_changed'):
        completed.prepare_window(root,[day])
    assert list((root/'report/main_trailing_completed_source'/day/'generations').glob('offline-*.json'))==[]


def test_completed_enrollment_does_not_promote_invalid_original_receipt(tmp_path,monkeypatch):
    from src.engine.automation import main_trailing_completed_store as completed
    root=tmp_path/'source';day,_,sidecar=_original_completed_source(root,monkeypatch,'native',False)
    path=Path(str(sidecar)+'.dependencies.json');body=json.loads(path.read_bytes());body['completed_count']=-1
    body['artifact_sha256']=completed.digest({k:v for k,v in body.items()if k!='artifact_sha256'})
    path.write_text(json.dumps(body));before=path.read_bytes()
    result=completed.prepare_window(root,[day])
    assert result[0]['status']=='source_gap'
    assert completed.offline_binding(root,day)==(None,None)
    assert path.read_bytes()==before


def test_completed_enrollment_checks_full_gzip_crc_before_publishing(tmp_path,monkeypatch):
    import gzip,hashlib
    from src.engine.automation import main_trailing_completed_store as completed
    from src.engine.lifecycle.snapshot_archive import file_identity
    from src.engine.scalping.micro_reversion.economic_reference import content_sha256
    root=tmp_path/'source';day,_,sidecar=_original_completed_source(root,monkeypatch,'native',True)
    packed=Path(str(sidecar)+'.gz');blob=bytearray(packed.read_bytes());blob[-8]^=1;packed.write_bytes(blob)
    # A negative fixture retains the original logical declaration while making
    # its small physical metadata match a CRC-damaged stream. Parsing to EOF
    # must still reject it; metadata alone cannot enroll the source.
    path=Path(str(packed)+'.archive_receipt.json');receipt=json.loads(path.read_bytes())
    receipt.update(archive_generation=file_identity(packed.stat()),archive_sha256=hashlib.sha256(blob).hexdigest())
    receipt['artifact_content_sha256']=content_sha256({k:v for k,v in receipt.items()if k!='artifact_content_sha256'})
    path.write_text(json.dumps(receipt))
    with pytest.raises((gzip.BadGzipFile,EOFError)):
        completed.prepare_window(root,[day])
    assert list((root/'report/main_trailing_completed_source'/day/'generations').glob('offline-*.json'))==[]


@pytest.mark.parametrize('kind',['native','retained'])
def test_completed_cache_survives_only_verified_lossless_compression(tmp_path,monkeypatch,kind):
    from src.engine.automation import main_trailing_completed_store as completed
    from src.engine import compress_db_backfilled_files as archive
    from src.engine.lifecycle.holding_window_generation import byte_generation,verified_legacy_projection_dependency
    from src.engine.scalping.micro_reversion.economic_reference import content_sha256
    root=tmp_path/'source';day,raw,sidecar=_original_completed_source(root,monkeypatch,kind,False)
    completed.prepare_window(root,[day]);generation=byte_generation(sidecar)
    receipt=Path(str(sidecar)+'.dependencies.json')
    dependency=(completed._metadata(receipt)if receipt.exists()else
        verified_legacy_projection_dependency(root,day,projection_generation=generation)[0])
    before=completed.binding(root,dependency,projection_generation=generation)
    monkeypatch.setattr(archive,'MONITOR_SNAPSHOT_DIR',sidecar.parent)
    assert archive._gzip_file(sidecar,dry_run=False)[0]
    if kind=='native':assert archive._gzip_file(raw,dry_run=False)[0]
    assert byte_generation(sidecar)==generation
    assert completed.binding(root,dependency,projection_generation=generation)==before
    assert len(list(completed.read(root,dependency,tmp_path/'read',projection_generation=generation)))==1
    assert completed.prepare_window(root,[day])[0]['status']=='offline_index_ready'
    # An apparently well-formed archive cannot bind a different logical source.
    path=Path(str(sidecar)+'.gz.archive_receipt.json');body=json.loads(path.read_bytes())
    body['logical_content_sha256']='0'*64
    body['artifact_content_sha256']=content_sha256({k:v for k,v in body.items()if k!='artifact_content_sha256'})
    path.write_text(json.dumps(body))
    with pytest.raises(ValueError,match='logical_source_changed'):
        completed.binding(root,dependency,projection_generation=generation)


def test_completed_enrollment_admits_only_same_epoch_postclose_byte_hashes(tmp_path,monkeypatch):
    from src.engine.automation import main_trailing_completed_store as completed
    from src.engine.lifecycle.holding_window_generation import byte_generation
    from src.engine.infrastructure.validation_digest_session import postclose_session,ValidationDeferred
    root=tmp_path/'source';day,raw,sidecar=_original_completed_source(root,monkeypatch,'native',False)
    completed.prepare_window(root,[day]);expected={p:byte_generation(p)for p in (raw,sidecar)}
    assert completed.admit_window(root,day,start_date=day)==0
    original=Path.open
    def guarded(path,*args,**kwargs):
        if path in expected:pytest.fail('native byte proof reread original snapshot')
        return original(path,*args,**kwargs)
    with postclose_session(root,day)as session:
        assert completed.admit_window(root,day,start_date=day)==2
        before=session.stats['full_bytes']
        monkeypatch.setattr(Path,'open',guarded)
        assert {p:byte_generation(p)for p in expected}==expected
        assert session.stats['full_bytes']==before
        with pytest.raises(ValueError,match='owner_mismatch'):
            completed.admit_window(root,'2026-10-19',start_date=day)
        monkeypatch.setattr(Path,'open',original)
        sidecar.write_bytes(sidecar.read_bytes()+b' ')
        with pytest.raises(ValidationDeferred,match='proof_epoch_changed'):
            byte_generation(sidecar)


@pytest.mark.parametrize('damage', [None, 'source', 'dependency', 'manifest_hash',
                                   'manifest_seal', 'authority', 'symlink', 'foreign_path'])
def test_frozen_replay_uses_exact_original_byte_proofs_without_old_semantic_binding(tmp_path, monkeypatch, damage):
    from src.engine.automation import main_trailing_completed_store as completed
    from src.engine.automation import main_trailing_source_reuse as reuse
    from src.engine.lifecycle import research_storage as storage
    from src.engine.lifecycle.holding_window_generation import byte_generation
    root=tmp_path/'source'
    day,raw,sidecar=_original_completed_source(root,monkeypatch,'native',False)
    completed.prepare_window(root,[day])
    binding,body=completed.offline_binding(root,day)
    issuer=Path(binding['manifest_path'])
    expected={p:byte_generation(p) for p in (raw,sidecar,issuer)}
    original={p:p.read_bytes() for p in expected}
    from src.engine.infrastructure.validation_digest_session import _native_proof_path
    for path in (raw,sidecar):
        _native_proof_path(root,path).unlink(missing_ok=True)
    # New code must not consume old extraction rows as a current native index.
    monkeypatch.setattr(completed,'_offline_code',lambda:'0'*64)
    assert completed.offline_binding(root,day)==(None,None)
    if damage=='source':raw.write_bytes(original[raw]+b' ')
    elif damage=='dependency':
        dependency=Path(str(sidecar)+'.dependencies.json')
        dependency.write_bytes(dependency.read_bytes()+b' ')
    elif damage=='manifest_hash':expected[issuer]['sha256']='0'*64
    elif damage in {'manifest_seal','authority'}:
        body['runtime_effect']=True
        if damage=='authority':body['artifact_sha256']=completed.digest({k:v for k,v in body.items() if k!='artifact_sha256'})
        issuer.write_text(json.dumps(body))
    elif damage=='symlink':
        target=tmp_path/'original.json';issuer.rename(target);issuer.symlink_to(target)
    elif damage=='foreign_path':
        foreign=tmp_path/issuer.name;foreign.write_bytes(original[issuer])
        with pytest.raises(ValueError):
            completed.original_byte_observations(root,foreign,expected[issuer])
        return
    assembly=tmp_path/'assembly';assembly.mkdir()
    manifest=dict(schema='main_all_scope_exit_input_manifest_v2',source_date=day,target_date='2026-10-22',
        consumed_dates=[day],assembly_inventory_ref=storage.write_tree(assembly,[]),
        source_generations_ref=storage.write_tree(assembly,
            (dict(path=str(p),generation=gen) for p,gen in expected.items())))
    manifest['artifact_sha256']=completed.digest(manifest)
    origin=assembly/'manifest.json';origin.write_text(json.dumps(manifest))
    original_open=Path.open
    def guarded(path,*args,**kwargs):
        if path in {raw,sidecar}:pytest.fail('byte proof reopened original rows')
        return original_open(path,*args,**kwargs)
    monkeypatch.setattr(Path,'open',guarded)
    if damage not in {None,'source','dependency'}:
        with pytest.raises(ValueError):reuse.collect_proofs(root,origin)
        return
    catalog=reuse.collect_proofs(root,origin)
    for p in (raw,sidecar):
        if damage is None:
            assert catalog['proofs'][str(p)]['kind']=='native_completed_source_enrollment'
            assert catalog['proofs'][str(p)]['generation']==expected[p]
        else:assert str(p) not in catalog['proofs']
    assert completed.offline_binding(root,day)==(None,None)
    if damage is None:
        monkeypatch.setattr(Path,'open',original_open)
        assert all(p.read_bytes()==value for p,value in original.items())


def test_completed_enrollment_refuses_crc_valid_changed_logical_gzip(tmp_path,monkeypatch):
    import gzip,hashlib
    from src.engine.automation import main_trailing_completed_store as completed
    from src.engine.lifecycle.snapshot_archive import file_identity
    from src.engine.scalping.micro_reversion.economic_reference import content_sha256
    root=tmp_path/'source';day,_,sidecar=_original_completed_source(root,monkeypatch,'native',True)
    packed=Path(str(sidecar)+'.gz');original=gzip.decompress(packed.read_bytes())
    # Keep valid JSON, row count and CRC; the original logical SHA is still
    # authoritative even if changed packed bytes have matching metadata.
    packed.write_bytes(gzip.compress(original+b' '))
    path=Path(str(packed)+'.archive_receipt.json');body=json.loads(path.read_bytes())
    body.update(archive_generation=file_identity(packed.stat()),archive_sha256=hashlib.sha256(packed.read_bytes()).hexdigest())
    body['artifact_content_sha256']=content_sha256({k:v for k,v in body.items()if k!='artifact_content_sha256'})
    path.write_text(json.dumps(body))
    with pytest.raises(ValueError,match='logical_generation_changed'):
        completed.prepare_window(root,[day])
    assert list((root/'report/main_trailing_completed_source'/day/'generations').glob('offline-*.json'))==[]


@pytest.mark.parametrize('legacy,native_window',[(True,False),(False,False),(False,True)])
def test_preparation_reuses_original_verified_empty_gzip_without_new_archive_receipt(tmp_path,monkeypatch,legacy,native_window):
    from src.tests.test_holding_window_generation import _archived_empty_original
    from src.engine.lifecycle import research_json_stream as stream
    from src.engine.automation import main_trailing_completed_store as completed
    day='2026-10-01';raw,physical,sidecar,manifest,_=_archived_empty_original(tmp_path,day=day,legacy=legacy,native_window=native_window)
    originals={p:p.read_bytes()for p in(physical,sidecar,manifest)}
    monkeypatch.setattr(stream,'completed_rows',lambda *a,**k:pytest.fail('empty cohort must retain its existing reader'))
    result=store.prepare_window(tmp_path,day,start_date=day)
    assert result[0]['status']=='original_empty_verified'
    assert result[0]['generation']['source_basis']=='current_native_gzip_empty_postclose'
    assert completed.offline_binding(tmp_path,day)==(None,None)
    assert not raw.exists()and not Path(str(physical)+'.archive_receipt.json').exists()
    assert {p:p.read_bytes()for p in originals}==originals


@pytest.mark.parametrize('fault',['manifest_missing','manifest_hash','corrupt_gzip'])
def test_empty_gzip_preparation_preserves_identifiable_contract_gap(tmp_path,fault):
    from src.tests.test_holding_window_generation import _archived_empty_original
    from src.engine.automation import main_trailing_completed_store as completed
    day='2026-10-01';_,physical,_,manifest,_=_archived_empty_original(tmp_path,day=day)
    if fault=='manifest_missing':manifest.unlink()
    elif fault=='manifest_hash':
        body=json.loads(manifest.read_bytes());body['snapshot_sha256']['trade_review']='0'*64;manifest.write_text(json.dumps(body))
    else:physical.write_bytes(b'not a gzip')
    result=completed.prepare_window(tmp_path,[day])
    assert result[0]['status']=='source_gap'
    assert completed.offline_binding(tmp_path,day)==(None,None)
    assert not Path(str(physical)+'.archive_receipt.json').exists()


def test_empty_archive_does_not_abort_normal_original_cohort_enrollment(tmp_path,monkeypatch):
    from datetime import date,timedelta
    from src.tests.test_holding_window_generation import _archived_empty_original
    from src.engine.automation import main_trailing_completed_store as completed
    root=tmp_path/'source';empty='2026-10-01';_archived_empty_original(root,day=empty)
    day,_,_=_original_completed_source(root,monkeypatch,'native',False)
    days=[];cursor=date.fromisoformat(empty)
    while cursor<=date.fromisoformat(day):days.append(cursor.isoformat());cursor+=timedelta(days=1)
    result=completed.prepare_window(root,days)
    assert result[0]['status']=='original_empty_verified'
    assert result[-1]['status']=='offline_index_prepared'
    assert completed.offline_binding(root,day)[0]is not None


def test_native_plain_empty_sidecar_does_not_require_large_legacy_fact_migration(tmp_path):
    from src.tests.test_holding_window_generation import _old_empty_projection
    from src.engine.automation import main_trailing_completed_store as completed
    from src.engine.lifecycle.holding_window_generation import capture_window
    day='2026-10-02';raw,sidecar,_=_old_empty_projection(tmp_path,day)
    originals={p:p.read_bytes()for p in(raw,sidecar)}
    assert capture_window(tmp_path,[day])['dependencies'][day]['status']=='valid_empty'
    result=completed.prepare_window(tmp_path,[day])
    assert result[0]['status']=='original_empty_verified'
    assert completed.offline_binding(tmp_path,day)==(None,None)
    assert {p:p.read_bytes()for p in originals}==originals


def test_empty_unsealed_raw_claim_is_isolated_without_ready_cache(tmp_path):
    from src.tests.test_holding_window_generation import _old_empty_projection
    from src.engine.automation import main_trailing_completed_store as completed
    day='2026-10-02';raw,sidecar,value=_old_empty_projection(tmp_path,day)
    sidecar.unlink();raw.write_text(json.dumps(value));original=raw.read_bytes()
    result=completed.prepare_window(tmp_path,[day])
    assert result[0]['status']=='source_gap'
    assert result[0]['reason']=='trailing_completed_empty_original_contract_unverified'
    assert completed.offline_binding(tmp_path,day)==(None,None)
    assert raw.read_bytes()==original


def test_empty_native_sidecar_identity_mismatch_remains_source_gap(tmp_path):
    from src.tests.test_holding_window_generation import _old_empty_projection
    from src.engine.automation import main_trailing_completed_store as completed
    day='2026-10-02';_,sidecar,value=_old_empty_projection(tmp_path,day)
    value['snapshot_identity']['inode']+=1
    value['artifact_sha256']=completed.digest({k:v for k,v in value.items()if k!='artifact_sha256'})
    sidecar.write_text(json.dumps(value))
    assert completed.prepare_window(tmp_path,[day])[0]['status']=='source_gap'
    assert completed.offline_binding(tmp_path,day)==(None,None)


@pytest.mark.parametrize('pinned_reader', [False, True])
def test_background_checkpoints_shared_vote_database_and_retains_partial_progress(tmp_path, pinned_reader):
    import sqlite3
    from src.engine.ai.holding_exit_vote import path_vote_store_path
    path = path_vote_store_path(tmp_path, 'record:7')
    with store._database(tmp_path, path, writer=True) as (writer, _, _):
        with writer:
            writer.execute('CREATE TABLE sample(body BLOB)')
            writer.execute('INSERT INTO sample VALUES(zeroblob(65536))')
    target = store._location(tmp_path, path)[2]
    reader = sqlite3.connect('file:'+str(target)+'?mode=ro', uri=True)
    try:
        if pinned_reader:
            reader.execute('BEGIN')
            reader.execute('SELECT count(*) FROM sample').fetchone()
        with writer:
            writer.execute('INSERT INTO sample VALUES(zeroblob(65536))')
        store._maintain_once(tmp_path, '2026-10-20', turn=5)
        state = store._MAINTENANCE_STATUS[str(target)]
        assert state['complete'] is (not pinned_reader)
        assert state['wal_frames'] >= state['checkpointed_frames'] >= 0
        assert state['wal_frames'] > state['checkpointed_frames'] if pinned_reader else True
        # The global DB must not be checkpointed again for another day.
        store._maintain_once(tmp_path, '2026-10-19', turn=5)
        assert store._MAINTENANCE_STATUS[str(target)] is state
        assert (__import__('os').getpid(),str(target)) in store._WRITERS
    finally:
        reader.close()
    store._CHECKPOINTS[str(target)]-=61
    store._MAINTENANCE[(str(tmp_path),'2026-10-20')]-=1
    store._maintain_once(tmp_path,'2026-10-20',turn=5)
    assert store._MAINTENANCE_STATUS[str(target)]['complete']
    with store._database(tmp_path,path,readonly=True) as (current,_,_):
        assert current.execute('SELECT count(*) FROM sample').fetchone()[0]==2


def test_validation_session_reuses_sqlite_connections_but_checks_each_new_source_generation(tmp_path, monkeypatch):
    import sqlite3
    from src.engine.infrastructure.validation_digest_session import postclose_session
    path = source(tmp_path); append(tmp_path, path, row('before'))
    native = store._open_database; opened = []
    def observe(*args, **kwargs):
        db = native(*args, **kwargs)
        if kwargs.get('readonly'): opened.append(db)
        return db
    monkeypatch.setattr(store, '_open_database', observe)
    with postclose_session(tmp_path, '2026-10-19'):
        original = store.generation(tmp_path, path)
        assert len(list(store.read_rows(tmp_path, path))) == 1
        append(tmp_path, path, row('after'))
        assert store.generation(tmp_path, path) != original
        assert len(list(store.read_rows(tmp_path, path))) == 2
        assert len(opened) == 1
    with pytest.raises(sqlite3.ProgrammingError, match='closed'):
        opened[0].execute('SELECT 1')


def test_open_prepared_database_never_repeats_schema_writes_under_another_writer(tmp_path):
    import sqlite3
    path = source(tmp_path)
    with store._database(tmp_path, path, writer=True): pass
    target = store._location(tmp_path, path)[2]
    locker = sqlite3.connect(target)
    db = None
    try:
        locker.execute('BEGIN IMMEDIATE')
        db = store._open_database(target, readonly=False, writer=True)
        assert db.execute('PRAGMA user_version').fetchone()[0] == 1
        assert not db.in_transaction
        with pytest.raises(sqlite3.OperationalError, match='locked'):
            db.execute('PRAGMA user_version=1')
    finally:
        if db is not None: db.close()
        locker.close()


@pytest.mark.parametrize('fault', ['none', 'exception', 'replaced_before', 'replaced_during', 'changed_body'])
def test_reader_session_cleanup_and_database_identity_fail_closed(tmp_path, fault):
    import sqlite3
    from src.engine.lifecycle.research_input_budget import health
    path = source(tmp_path); append(tmp_path, path, row())
    target = store._location(tmp_path, path)[2]
    prior = health()['used_bytes']
    db = None
    expected = RuntimeError if fault == 'exception' else (store.InputPending if fault.startswith('replaced') else ValueError)
    def replace():
        copied = target.with_suffix('.replacement')
        saved = sqlite3.connect(copied)
        try:db.backup(saved)
        finally:saved.close()
        copied.chmod(0o600);copied.replace(target)
    def run():
        nonlocal db
        with store.read_session(tmp_path):
            with store._database(tmp_path, path, readonly=True) as (db, _, _):
                if fault == 'replaced_during': replace()
            if fault == 'exception': raise RuntimeError('consumer failed')
            if fault == 'replaced_before': replace()
            if fault == 'changed_body':
                with store._database(tmp_path, path, writer=True) as (writer, _, _), writer:
                    writer.execute('UPDATE rows SET body=?', (b'{}',))
                list(store.read_rows(tmp_path, path))
            store.generation(tmp_path, path)
    if fault == 'none': run()
    else:
        with pytest.raises(expected): run()
    assert health()['used_bytes'] == prior
    with pytest.raises(sqlite3.ProgrammingError, match='closed'):db.execute('SELECT 1')


def test_reader_pool_bounds_eviction_and_keeps_borrowed_connections(tmp_path):
    from contextlib import ExitStack
    from src.engine.lifecycle.research_input_budget import health
    paths = [tmp_path/'ai_decision_trace'/f'ai_decision_trace_2026-10-{day:02d}.jsonl' for day in range(12, 20)]
    for path in paths:
        path.parent.mkdir(exist_ok=True);path.touch();append(tmp_path, path, row())
    prior = health()['used_bytes']
    with store.read_session(tmp_path):
        for path in paths: assert store.generation(tmp_path, path)['raw_records'] == 1
        assert len(store._READERS.get()['entries']) == 6
        with ExitStack() as stack:
            for path in paths[-6:]:stack.enter_context(store._database(tmp_path, path, readonly=True))
            with pytest.raises(store.InputPending, match='read_session_partition_required'):
                store.generation(tmp_path, paths[0])
        assert store.generation(tmp_path, paths[0])['raw_records'] == 1
    assert health()['used_bytes'] == prior


def test_reader_connections_never_cross_inherited_thread_or_fork_context(tmp_path):
    import os, threading
    from contextvars import copy_context
    path = source(tmp_path);append(tmp_path, path, row())
    with store.read_session(tmp_path):
        before = store.generation(tmp_path, path)
        entries = store._READERS.get()['entries'];db = next(iter(entries.values()))['db']
        results = []
        thread = threading.Thread(target=copy_context().run, args=(lambda: results.append(store.generation(tmp_path, path)),))
        thread.start();thread.join(timeout=5);assert not thread.is_alive()
        assert results == [before] and next(iter(entries.values()))['db'] is db
        child = os.fork()
        if child == 0:
            try:
                assert store._READERS.get() is None
                assert store.generation(tmp_path, path) == before
            except BaseException:os._exit(2)
            os._exit(0)
        assert os.waitpid(child, 0)[1] == 0
        assert store.generation(tmp_path, path) == before


def test_startup_prepares_existing_global_vote_index_before_first_reader(tmp_path):
    from src.engine.ai.holding_exit_vote import path_vote_store_path
    path = path_vote_store_path(tmp_path, 'record:7')
    with store._database(tmp_path, path, writer=True): pass
    # Force that cached connection out, as happens during other-day preparation.
    for day in range(12, 19):
        stream = tmp_path/'ai_decision_trace'/f'ai_decision_trace_2026-10-{day:02d}.jsonl'
        with store._database(tmp_path, stream, writer=True): pass
    key = (__import__('os').getpid(), str(store._location(tmp_path, path)[2]))
    assert key not in store._WRITERS
    store.prepare_for_day(tmp_path, '2026-10-20')
    assert key in store._WRITERS
    # No fabricated vote DB is created when this source family is absent.
    empty = tmp_path/'empty';empty.mkdir()
    store.prepare_for_day(empty, '2026-10-20')
    assert not store._index_path(empty, 'holding_path_votes', None).exists()


def test_failed_read_transaction_releases_snapshot_before_connection_reuse(tmp_path):
    path = source(tmp_path);append(tmp_path, path, row('before'))
    with store.read_session(tmp_path):
        with pytest.raises(store.InputPending, match='original_failure'):
            with store._database(tmp_path, path, readonly=True) as (db, _, _):
                db.execute('BEGIN')
                db.execute('SELECT count(*) FROM rows').fetchone()
                raise store.InputPending('original_failure')
        assert not db.in_transaction
        append(tmp_path, path, row('after'))
        assert len(list(store.read_rows(tmp_path, path))) == 2


@pytest.mark.parametrize('day', ['2026-10-20/../../escape', '20261020', '2026-W43-2', None])
def test_maintenance_rejects_noncanonical_dates_before_preparing_any_database(tmp_path, day):
    with pytest.raises(ValueError):store._maintain_once(tmp_path, day)
    assert not (tmp_path/'report').exists()


@pytest.mark.parametrize('pinned', [False, True])
def test_snapshot_generation_and_first_row_use_the_same_database_view(tmp_path, monkeypatch, pinned):
    path=source(tmp_path);append(tmp_path,path,row('before'))
    original=store.generation
    calls=[]
    def generation(root, source_path):
        value=original(root,source_path)
        if not calls:
            calls.append(True)
            append(tmp_path,path,row('after'))
        return value
    monkeypatch.setattr(store,'generation',generation)
    receipt={} if pinned else None
    stream=store.read_rows(tmp_path,path,snapshot_receipt=receipt)
    if pinned:
        rows=list(stream)
        assert [v['row']['decision_trace_id'] for v,_ in rows]==['before']
        assert receipt['generation']['selected_records']==1
        assert receipt['verified_append_after_snapshot'] is True
    else:
        with pytest.raises(store.InputPending):list(stream)
    assert len(list(store.read_rows(tmp_path,path)))==2
