"""Source-only migration tests; every writable source is an isolated fixture."""
import builtins
import hashlib
import inspect
import json
from pathlib import Path

import pytest

from src.engine import buy_funnel_sentinel as B
from src.engine import pipeline_event_summary as P
from src.engine.monitoring import sentinel_summary_contract as C


def event(second):
    return dict(event_type='pipeline_event', emitted_at=f'2026-10-13T10:00:{second:02}',
        pipeline='ENTRY_PIPELINE', stage='blocked_overbought', stock_name='Alpha',
        stock_code='123456', record_id=second, fields={'reason': 'stretched'})


def predecessor(tmp_path, *, parser_callback=False):
    raw = tmp_path/'raw.jsonl'
    raw.write_text(json.dumps(event(1))+'\n')
    callbacks = (P.default_reason_label, None) if parser_callback else (
        B._blocker_label_from_stage_fields, B._is_ignored_event)
    options = dict(raw_path=raw, summary_dir=tmp_path/'summaries', target_date='2026-10-13',
        reason_labeler=callbacks[0], ignore_payload=callbacks[1], include_samples=False)
    rows, meta = P.update_and_load_pipeline_event_summaries(**options)
    manifest = Path(meta['manifest_path'])
    source = json.loads(manifest.read_text())
    parts = []
    for callback in callbacks:
        if callback is not None:
            parts.extend((inspect.getsource(callback), C.PREVIOUS_PARSER if parser_callback else C.PREVIOUS_BUY_OWNER))
    source['callback_contract'] = hashlib.sha256('\n'.join(parts).encode()).hexdigest()
    source['parser_contract'] = C.PREVIOUS_PARSER
    source['checkpoint_digest'] = P.checkpoint_digest(source)
    manifest.write_text(json.dumps(source))
    return raw, options, manifest, manifest.read_bytes(), rows


def revise(manifest, **changes):
    source=json.loads(manifest.read_text());source.update(changes)
    source['checkpoint_digest']=P.checkpoint_digest(source)
    manifest.write_text(json.dumps(source))


@pytest.mark.parametrize('parser_callback', [False, True])
@pytest.mark.parametrize('append', [False, True])
def test_migration_preserves_original_and_reads_only_new_suffix(tmp_path, monkeypatch, parser_callback, append):
    raw, options, manifest, original, rows = predecessor(tmp_path, parser_callback=parser_callback)
    start=raw.stat().st_size
    if append:
        with raw.open('a') as f:f.write(json.dumps(event(2))+'\n')
    real_open=builtins.open; reads=[]
    class Tracked:
        def __init__(self, f):self.f=f
        def __getattr__(self, name):return getattr(self.f,name)
        def __enter__(self):return self
        def __exit__(self,*args):return self.f.__exit__(*args)
        def readline(self,*args):
            assert self.f.tell()>=start
            value=self.f.readline(*args);reads.append(len(value));return value
    def guarded(path,*args,**kwargs):
        f=real_open(path,*args,**kwargs)
        return Tracked(f) if Path(path)==raw and args and args[0]=='rb' else f
    monkeypatch.setattr(builtins,'open',guarded)
    result, meta=P.update_and_load_pipeline_event_summaries(**options)
    receipt=meta['contract_migration']
    assert not meta['rebuilt'] and meta['start_raw_offset']==start
    assert sum(row['event_count'] for row in result)==(2 if append else 1)
    assert sum(reads)==raw.stat().st_size-start
    assert Path(receipt['original_manifest_archive']).read_bytes()==original
    assert receipt['original_manifest_sha256']==hashlib.sha256(original).hexdigest()
    assert receipt['original_checkpoint']==json.loads(original)['checkpoint_digest']
    assert receipt['from_parser']==C.PREVIOUS_PARSER and receipt['to_parser']==C.CURRENT_PARSER
    committed=json.loads(manifest.read_text())
    assert committed['checkpoint_digest']==P.checkpoint_digest(committed)
    unchanged=manifest.read_bytes()
    _, again=P.update_and_load_pipeline_event_summaries(**options)
    assert again['contract_migration']==receipt
    assert Path(receipt['original_manifest_archive']).read_bytes()==original


@pytest.mark.parametrize('change,reason', [
    ({'parser_contract':'unknown'},'parser_predecessor_unverified'),
    ({'callback_contract':'unknown'},'callback_predecessor_unverified'),
    ({'complete_through_raw_offset':0},'source_prefix_unverified'),
    ({'incomplete_tail':True},'source_prefix_unverified'),
    ({'decode_errors':1},'source_prefix_unverified'),
    ({'summary_detail_level':'changed'},'source_guard_failed'),
])
def test_invalid_predecessor_does_not_advance_or_archive(tmp_path, change, reason):
    raw, options, manifest, _, _=predecessor(tmp_path)
    revise(manifest, **change); original=manifest.read_bytes();summary=Path(json.loads(original)['summary_path']).read_bytes()
    with pytest.raises(RuntimeError,match=reason):P.update_and_load_pipeline_event_summaries(**options)
    assert manifest.read_bytes()==original
    assert Path(json.loads(original)['summary_path']).read_bytes()==summary
    assert not (manifest.parent/'contract_migrations').exists()


def test_mutated_runtime_callback_dependency_is_rejected(tmp_path, monkeypatch):
    _,options,manifest,original,_=predecessor(tmp_path)
    monkeypatch.setattr(B,'IGNORED_STOCK_NAMES',{'TEST'})
    with pytest.raises(RuntimeError,match='dependency_changed'):P.update_and_load_pipeline_event_summaries(**options)
    assert manifest.read_bytes()==original


def test_exact_current_parser_pin_rejects_unreviewed_source(tmp_path, monkeypatch):
    _,options,manifest,original,_=predecessor(tmp_path)
    monkeypatch.setattr(C,'CURRENT_PARSER','unreviewed')
    with pytest.raises(RuntimeError,match='parser_predecessor_unverified'):P.update_and_load_pipeline_event_summaries(**options)
    assert manifest.read_bytes()==original


@pytest.mark.parametrize('kind',['truncate','same_size_rewrite','oversized_append'])
def test_raw_generation_and_migration_append_budget(tmp_path, kind):
    raw, options, manifest, original, _=predecessor(tmp_path)
    if kind=='truncate':raw.write_bytes(b'')
    elif kind=='same_size_rewrite':raw.write_bytes(raw.read_bytes().replace(b'Alpha',b'Bravo'))
    else:
        with raw.open('ab') as f:f.truncate(raw.stat().st_size+C.LIMIT+1)
    with pytest.raises(RuntimeError,match='source_prefix_unverified|append_budget_exceeded'):
        P.update_and_load_pipeline_event_summaries(**options)
    assert manifest.read_bytes()==original


def test_archive_conflict_is_fatal_before_source_append(tmp_path):
    raw,options,manifest,original,_=predecessor(tmp_path)
    directory=manifest.parent/'contract_migrations';directory.mkdir()
    archive=directory/(manifest.name+'.'+hashlib.sha256(original).hexdigest()+'.json')
    archive.write_bytes(b'conflict')
    with pytest.raises(RuntimeError,match='archive_conflict'):P.update_and_load_pipeline_event_summaries(**options)
    assert manifest.read_bytes()==original and archive.read_bytes()==b'conflict'


def test_incomplete_append_never_publishes_successor(tmp_path):
    raw,options,manifest,original,_=predecessor(tmp_path)
    with raw.open('a') as f:f.write('{"unfinished":')
    with pytest.raises(RuntimeError,match='incomplete_source_prefix'):P.update_and_load_pipeline_event_summaries(**options)
    assert manifest.read_bytes()==original
    assert len(list((manifest.parent/'contract_migrations').glob('*.json')))==1


def test_prepublication_same_size_raw_rewrite_is_rejected(tmp_path, monkeypatch):
    raw,options,manifest,original,_=predecessor(tmp_path)
    real=C.archive_predecessor
    def alter(receipt,path):
        value=real(receipt,path);raw.write_bytes(raw.read_bytes().replace(b'Alpha',b'Bravo'));return value
    monkeypatch.setattr(C,'archive_predecessor',alter)
    with pytest.raises(RuntimeError,match='source_changed_before_publication'):P.update_and_load_pipeline_event_summaries(**options)
    assert manifest.read_bytes()==original


def test_parser_only_migration_keeps_unchanged_external_callback(tmp_path):
    _,options,manifest,_,_=predecessor(tmp_path)
    parts=[]
    for cb in (options['reason_labeler'],options['ignore_payload']):
        parts.extend((inspect.getsource(cb),C.CURRENT_BUY_OWNER))
    revise(manifest,callback_contract=hashlib.sha256('\n'.join(parts).encode()).hexdigest())
    _,meta=P.update_and_load_pipeline_event_summaries(**options)
    assert meta['contract_migration']['from_callback']==meta['callback_contract']
    assert not meta['rebuilt']


def test_archive_io_failure_cannot_fall_back_to_raw_report(tmp_path, monkeypatch):
    _,options,manifest,original,_=predecessor(tmp_path)
    def fail(*args,**kwargs):raise OSError('archive disk failure')
    monkeypatch.setattr(C.os,'open',fail)
    with pytest.raises(RuntimeError,match='archive_failed'):
        P.update_and_load_pipeline_event_summaries(**options)
    assert manifest.read_bytes()==original


def test_explicit_bootstrap_preserves_existing_revalidation_authority(tmp_path):
    _,options,manifest,_,_=predecessor(tmp_path)
    revise(manifest,parser_contract=C.CURRENT_PARSER,callback_contract='changed_semantics')
    original=manifest.read_bytes()
    with pytest.raises(RuntimeError,match='parser_predecessor_unverified'):
        P.update_and_load_pipeline_event_summaries(**options)
    assert manifest.read_bytes()==original
    rows,meta=P.update_and_load_pipeline_event_summaries(**options,allow_bootstrap=True)
    assert meta['rebuilt'] and 'contract_migration' not in meta
    assert sum(row['event_count'] for row in rows)==1


def test_concurrent_append_is_left_for_next_owned_cursor(tmp_path,monkeypatch):
    raw,options,manifest,_,_=predecessor(tmp_path)
    with raw.open('a') as f:f.write(json.dumps(event(2))+'\n')
    end=raw.stat().st_size
    real=C.archive_predecessor
    def append(receipt,path):
        value=real(receipt,path)
        with raw.open('a') as f:f.write(json.dumps(event(3))+'\n')
        return value
    monkeypatch.setattr(C,'archive_predecessor',append)
    rows,meta=P.update_and_load_pipeline_event_summaries(**options)
    assert meta['raw_offset']==end<raw.stat().st_size
    assert sum(row['event_count'] for row in rows)==2
    rows,meta=P.update_and_load_pipeline_event_summaries(**options)
    assert meta['raw_offset']==raw.stat().st_size
    assert sum(row['event_count'] for row in rows)==3


@pytest.mark.parametrize('target',['archive','directory'])
def test_predecessor_archive_rejects_symlink_without_publishing(tmp_path,target):
    _,options,manifest,original,_=predecessor(tmp_path)
    directory=manifest.parent/'contract_migrations'
    if target=='directory':
        outside=tmp_path/'outside';outside.mkdir();directory.symlink_to(outside,target_is_directory=True)
    else:
        directory.mkdir()
        archive=directory/(manifest.name+'.'+hashlib.sha256(original).hexdigest()+'.json')
        archive.symlink_to(manifest)
    summary=Path(json.loads(original)['summary_path']);prior_summary=summary.read_bytes()
    with pytest.raises(RuntimeError,match='archive_failed'):
        P.update_and_load_pipeline_event_summaries(**options)
    assert manifest.read_bytes()==original and summary.read_bytes()==prior_summary
