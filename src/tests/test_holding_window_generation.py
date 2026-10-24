"""Cumulative cost revision and immutable input-window regression cases."""
import json
from pathlib import Path
import pytest
from src.engine.lifecycle.holding_window_generation import capture_window, verify_window
from src.engine.lifecycle.broker_cost_reconciliation import receipt_path


def test_past_only_cost_revision_invalidates_window_and_preserves_other_windows(tmp_path):
    prior = capture_window(tmp_path, ["2026-10-07", "2026-10-08"])
    unrelated = capture_window(tmp_path, ["2026-10-08"])
    receipt = receipt_path(tmp_path, "2026-10-07", "1")
    receipt.parent.mkdir(parents=True)
    receipt.write_text('{"revision":1}')
    with pytest.raises(ValueError, match="generation_changed"):
        verify_window(tmp_path, prior)
    verify_window(tmp_path, unrelated)
    current = capture_window(tmp_path, prior["dates"])
    assert current["dependencies"]["2026-10-07"]["status"] == "missing"
    assert current["input_window_generation_sha256"] != prior["input_window_generation_sha256"]


def test_legacy_cannot_be_resealed_and_root_is_bound(tmp_path):
    with pytest.raises(ValueError, match="unverified"):
        verify_window(tmp_path, {})
    window = capture_window(tmp_path, ["2026-10-08"])
    other = tmp_path / "other"
    with pytest.raises(ValueError, match="generation_changed"):
        verify_window(other, window)


def test_missing_date_arrival_and_same_size_revision_are_detected(tmp_path):
    before = capture_window(tmp_path, ["2026-10-08"])
    path = tmp_path / "report/monitor_snapshots/trade_review_2026-10-08.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"date": "2026-10-08", "meta": {"knowledge_cutoff": "a"}}))
    with pytest.raises(ValueError, match="generation_changed"):
        verify_window(tmp_path, before)
    first = capture_window(tmp_path, ["2026-10-08"])
    path.write_text(path.read_text().replace('"a"', '"b"'))
    with pytest.raises(ValueError, match="generation_changed"):
        verify_window(tmp_path, first)


def test_projection_dependency_receipt_avoids_redecoding_timelines_and_detects_tamper(tmp_path, monkeypatch):
    from src.engine import log_archive_service as archive
    from src.engine.sniper_trade_review_report import completed_census_manifest
    from src.engine.lifecycle import holding_window_generation as window
    directory=tmp_path/'report/monitor_snapshots';directory.mkdir(parents=True)
    monkeypatch.setattr(archive,'MONITOR_SNAPSHOT_DIR',directory)
    day='2026-10-08'
    payload={'date':day,'metrics':{'canonical_completed_trades':0},
             'meta':{'snapshot_profile':'postclose_exit','sell_completed_event_ids':[]},
             'sections':{'completed_trade_projection':[],'open_scalp_position_projection':[]}}
    payload['meta']['completed_census_manifest']=completed_census_manifest(payload)
    path=archive.save_monitor_snapshot('trade_review',day,payload)
    original=window.json.loads; decoded=[]
    def once(raw,*a,**k):
        decoded.append(len(raw));return original(raw,*a,**k)
    monkeypatch.setattr(window.json,'loads',once)
    sealed=capture_window(tmp_path,[day])
    assert sealed['dependencies'][day]['status']=='valid_empty'
    assert len(decoded)==1 and max(decoded)<window.MAX_METADATA_BYTES
    sidecar=path.with_suffix('.completed_projection.json')
    sidecar.write_text(sidecar.read_text().replace('postclose_exit','postclose_Exit'))
    with pytest.raises(ValueError,match='generation_changed'):
        verify_window(tmp_path,sealed)


def test_verifier_access_time_cannot_invalidate_same_generation():
    from types import SimpleNamespace
    from src.engine.lifecycle.holding_window_generation import source_stat
    values=dict(st_dev=1,st_ino=2,st_size=3,st_mtime_ns=4,st_ctime_ns=5,st_atime_ns=6)
    assert source_stat(SimpleNamespace(**values))==source_stat(SimpleNamespace(**{**values,'st_atime_ns':7}))
    assert source_stat(SimpleNamespace(**values))!=source_stat(SimpleNamespace(**{**values,'st_ctime_ns':7}))


def _retained_original_window(tmp_path, monkeypatch):
    from src.tests.test_strategy_position_performance_report import (
        _legacy_unreceipted_original, _write_legacy_status, report_mod)
    day, path = _legacy_unreceipted_original(tmp_path, monkeypatch, large=True)
    before = capture_window(tmp_path, [day])
    assert before['dependencies'][day]['reason'] == 'window_dependency_legacy_metadata_required'
    value = report_mod._load_completion_fact_projection(day, path)
    _write_legacy_status(day, value)
    return day, path, report_mod


def test_retained_original_native_window_uses_full_byte_proof_without_rewriting_sources(tmp_path, monkeypatch):
    import hashlib
    from src.engine.lifecycle import holding_window_generation as window
    day, path, fact = _retained_original_window(tmp_path, monkeypatch)
    sidecar = path.with_suffix('.completed_projection.json')
    originals = {p:hashlib.sha256(p.read_bytes()).hexdigest() for p in (path, sidecar)}
    monkeypatch.setattr(fact, '_legacy_original_stream', lambda *a:pytest.fail('full canonical stream repeated'))
    metadata, generation = window.verified_legacy_projection_dependency(tmp_path, day)
    assert metadata['completed_count'] == 1
    assert metadata['meta']['snapshot_profile'] == 'postclose_exit'
    assert 'actual_cost_source_generation' not in metadata['meta']
    assert 'knowledge_cutoff' not in metadata['meta']
    assert generation['sha256'] == originals[sidecar]
    sealed = capture_window(tmp_path, [day])
    dependency = sealed['dependencies'][day]
    assert dependency['status'] == 'observed'
    assert dependency['cost_generation']['count'] == 0
    assert dependency['cost_generation']['status'] == 'cost_source_unavailable'
    assert dependency['knowledge_cutoff'] is None
    assert dependency['census_sha256'] == metadata['census_sha256']
    assert 'legacy_validation' in dependency['projection']
    verify_window(tmp_path, sealed)
    assert {p:hashlib.sha256(p.read_bytes()).hexdigest() for p in originals} == originals
    assert not Path(str(sidecar)+'.dependencies.json').exists()
    assert not path.with_suffix('.fact_projection.json').exists()


def test_retained_original_window_requires_independent_complete_projection_bytes(tmp_path, monkeypatch):
    from src.engine.lifecycle import holding_window_generation as window
    day, path, _ = _retained_original_window(tmp_path, monkeypatch)
    sidecar = path.with_suffix('.completed_projection.json')
    generation = window.byte_generation(sidecar)
    with pytest.raises(ValueError, match='original_generation_changed'):
        window.verified_legacy_projection_dependency(tmp_path, day,
            projection_generation={**generation, 'sha256':'a'*64})


@pytest.mark.parametrize('mutation', ['raw', 'sidecar', 'cost', 'receipt', 'late_race'])
def test_retained_original_window_rejects_changed_source_cost_or_proof(tmp_path, monkeypatch, mutation):
    day, path, fact = _retained_original_window(tmp_path, monkeypatch)
    if mutation in {'raw', 'sidecar'}:
        target = path if mutation == 'raw' else path.with_suffix('.completed_projection.json')
        with target.open('ab') as h:h.write(b' ')
    elif mutation == 'cost':
        target = receipt_path(tmp_path, day, '49013');target.parent.mkdir(parents=True);target.write_text('{}')
    elif mutation == 'receipt':
        value=json.loads(fact._status_path(day).read_bytes());value['completed_census_run_ids']=['f'*24]
        value['artifact_sha256']=fact._canonical_sha256({k:v for k,v in value.items() if k!='artifact_sha256'})
        fact._status_path(day).write_text(json.dumps(value))
    else:
        original=fact._legacy_original_generation_issue;calls=[]
        def change(*a, **k):
            result=original(*a, **k);calls.append(True)
            if len(calls)==2:
                with path.open('ab') as h:h.write(b' ')
            return result
        monkeypatch.setattr(fact, '_legacy_original_generation_issue', change)
    current=capture_window(tmp_path,[day])
    assert current['dependencies'][day]['status']=='source_gap'
    assert not Path(str(path.with_suffix('.completed_projection.json'))+'.dependencies.json').exists()


def test_retained_original_window_preserves_native_logical_compression_contract(tmp_path, monkeypatch):
    from src.engine import compress_db_backfilled_files as archive
    day,path,_ = _retained_original_window(tmp_path,monkeypatch)
    prior=capture_window(tmp_path,[day])
    Path(str(path)+'.gz').unlink()  # An unrelated old fixture archive is not a native transfer.
    monkeypatch.setattr(archive,'MONITOR_SNAPSHOT_DIR',path.parent)
    for source in (path,path.with_suffix('.completed_projection.json')):
        assert archive._gzip_file(source,dry_run=False)[0]
    assert capture_window(tmp_path,[day])==prior
    verify_window(tmp_path,prior)


def test_retained_original_native_hash_reuse_does_not_cache_cost_validity(tmp_path,monkeypatch):
    from src.engine.lifecycle.holding_window_generation import verified_legacy_projection_dependency
    from src.engine.infrastructure.validation_digest_session import postclose_session
    day,path,_=_retained_original_window(tmp_path,monkeypatch)
    with postclose_session(tmp_path,day) as session:
        first=verified_legacy_projection_dependency(tmp_path,day)
        assert verified_legacy_projection_dependency(tmp_path,day)==first
        assert session.stats['full_reads']==1
        assert session.stats['full_bytes']==path.with_suffix('.completed_projection.json').stat().st_size
        assert session.stats['reused_reads']>=1
        revised=receipt_path(tmp_path,day,'49013');revised.parent.mkdir(parents=True);revised.write_text('{}')
        with pytest.raises(ValueError,match='cost_or_census_changed'):
            verified_legacy_projection_dependency(tmp_path,day)


def test_retained_original_metadata_clock_is_read_from_original_not_scalar_factory(tmp_path,monkeypatch):
    from src.tests.test_strategy_position_performance_report import (
        _legacy_unreceipted_original,_write_legacy_status,report_mod,archive_identity)
    day,path=_legacy_unreceipted_original(tmp_path,monkeypatch)
    cutoff=day+'T19:50:00+09:00'
    raw=json.loads(path.read_bytes());raw['meta']['knowledge_cutoff']=cutoff;path.write_text(json.dumps(raw))
    sidecar=path.with_suffix('.completed_projection.json');value=json.loads(sidecar.read_bytes())
    value['meta']['knowledge_cutoff']=cutoff;value['snapshot_identity']=archive_identity(path)
    value['artifact_sha256']=report_mod._canonical_sha256({k:v for k,v in value.items() if k!='artifact_sha256'})
    sidecar.write_text(json.dumps(value))
    scalar=report_mod._load_completion_fact_projection(day,path);_write_legacy_status(day,scalar)
    assert 'knowledge_cutoff' not in scalar['meta']
    dependency=capture_window(tmp_path,[day])['dependencies'][day]
    assert dependency['status']=='observed' and dependency['knowledge_cutoff']==cutoff


def test_retained_original_metadata_open_rejects_fifo_replacement_without_blocking(tmp_path,monkeypatch):
    import os
    day,path,_=_retained_original_window(tmp_path,monkeypatch)
    sidecar=path.with_suffix('.completed_projection.json');real_open=os.open;swapped=[]
    def replace_before_open(p,flags,*a,**k):
        if Path(p)==sidecar and not swapped:
            swapped.append(True);sidecar.rename(sidecar.with_suffix('.saved'));os.mkfifo(sidecar)
        return real_open(p,flags,*a,**k)
    monkeypatch.setattr(os,'open',replace_before_open)
    dependency=capture_window(tmp_path,[day])['dependencies'][day]
    assert swapped and dependency['status']=='source_gap'
    assert 'metadata_changed' in dependency['reason']


def test_retained_raw_original_snapshot_uses_manifest_proof_without_inventing_a_sidecar(tmp_path,monkeypatch):
    import hashlib
    from src.tests.test_strategy_position_performance_report import (
        _legacy_raw_original,_write_legacy_status,report_mod)
    from src.engine.lifecycle.holding_window_generation import verified_legacy_projection_dependency
    day,path=_legacy_raw_original(tmp_path,monkeypatch)
    assert capture_window(tmp_path,[day])['dependencies'][day]['status']=='source_gap'
    old_gzip=Path(str(path)+'.gz');originals={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in (path,old_gzip)}
    value=report_mod._load_completion_fact_projection(day,path);_write_legacy_status(day,value)
    monkeypatch.setattr(report_mod,'_legacy_original_stream',lambda *a,**k:pytest.fail('native stream repeated'))
    metadata,generation=verified_legacy_projection_dependency(tmp_path,day)
    assert generation['path']==path.name and generation['sha256']==originals[path]
    assert metadata['completed_count']==1
    assert metadata['original_snapshot_manifest']['path'].endswith('postclose_exit.json')
    assert 'original_snapshot_manifest' in generation['legacy_validation']
    current=capture_window(tmp_path,[day]);dependency=current['dependencies'][day]
    assert dependency['status']=='observed' and dependency['cost_generation']['count']==0
    assert dependency['projection']['path']==path.name
    verify_window(tmp_path,current)
    assert {p:hashlib.sha256(p.read_bytes()).hexdigest() for p in originals}==originals
    assert not path.with_suffix('.completed_projection.json').exists()
    assert not path.with_suffix('.fact_projection.json').exists()


def _old_empty_projection(tmp_path,day='2026-10-02'):
    from src.engine.sniper_trade_review_report import completed_census_manifest
    from src.engine.lifecycle.snapshot_archive import snapshot_identity
    from src.engine.lifecycle.broker_cost_reconciliation import digest
    directory=tmp_path/'report/monitor_snapshots';directory.mkdir(parents=True,exist_ok=True)
    raw=directory/f'trade_review_{day}.json';raw.write_text('{}')
    value=dict(schema='trade_review_completed_projection_sidecar_v1',date=day,code=None,since=None,
        snapshot_identity=snapshot_identity(raw),meta=dict(snapshot_profile='postclose_exit',sell_completed_event_ids=[],
            completion_event_id_count=0,completed_census_input_sha256='a'*64,
            trailing_event_source_receipts=[dict(path='original-source',logical_sha256='b'*64,size_bytes=123)]),
        metrics=dict(canonical_completed_trades=0,
            open_scalp_position_projection_status='source_gap_historical_open_census_not_reconstructible'),
        sections=dict(completed_trade_projection=[],open_scalp_position_projection=[]))
    census=completed_census_manifest(value);assert census.pop('actual_cost_source_generation') is None
    value['meta']['completed_census_manifest']=census;value['artifact_sha256']=digest(value)
    sidecar=raw.with_suffix('.completed_projection.json');sidecar.write_text(json.dumps(value))
    return raw,sidecar,value


@pytest.mark.parametrize('day',['2026-10-02','2026-10-06'])
def test_original_empty_unknown_cost_census_is_valid_empty_without_resealing(tmp_path,day):
    from src.engine.holding_exit_observation_report import _verified_trade_review_projection
    from src.engine.sniper_trade_review_report import verify_completed_census_manifest
    raw,sidecar,value=_old_empty_projection(tmp_path,day);original=sidecar.read_bytes()
    assert verify_completed_census_manifest(value,day)=='completed_census_generation_mismatch'
    window=capture_window(tmp_path,[day]);dependency=window['dependencies'][day]
    assert dependency['status']=='valid_empty' and dependency['cost_generation']['count']==0
    observed=_verified_trade_review_projection(raw,day,data_root=tmp_path)
    assert observed==value
    assert observed['metrics']['open_scalp_position_projection_status']=='source_gap_historical_open_census_not_reconstructible'
    assert 'actual_cost_source_generation' not in observed['meta']['completed_census_manifest']
    verify_window(tmp_path,window)
    assert sidecar.read_bytes()==original
    assert not Path(str(sidecar)+'.dependencies.json').exists()


@pytest.mark.parametrize('mutation',['wrong_date','nonempty','count_bool','canonical_bool','event_count_bool',
    'unobserved','current_cost','official_cost','meta_present','census_changed','bad_seal','missing_source_receipts'])
def test_original_empty_compatibility_cannot_accept_other_source_gaps(tmp_path,mutation):
    from src.engine.lifecycle.holding_window_generation import completed_projection_census_issue
    from src.engine.lifecycle.broker_cost_reconciliation import source_generation,digest
    day='2026-10-02';_,sidecar,value=_old_empty_projection(tmp_path,day);costs=source_generation(tmp_path,day)
    if mutation=='wrong_date':value['date']='2026-10-06'
    elif mutation=='nonempty':value['sections']['completed_trade_projection']=[dict(id=1)]
    elif mutation=='count_bool':value['meta']['completed_census_manifest']['raw_terminal_count']=False
    elif mutation=='canonical_bool':value['metrics']['canonical_completed_trades']=False
    elif mutation=='event_count_bool':value['meta']['completion_event_id_count']=False
    elif mutation=='unobserved':value['meta']['completed_census_manifest']['unobserved_count']=1
    elif mutation=='current_cost':costs={**costs,'count':1}
    elif mutation=='official_cost':costs={**costs,'official_source_sha256':'a'*64}
    elif mutation=='meta_present':value['meta']['actual_cost_source_generation']=None
    elif mutation=='census_changed':value['meta']['completed_census_manifest']['source_receipts_sha256']='a'*64
    elif mutation=='bad_seal':value['artifact_sha256']='a'*64
    elif mutation=='missing_source_receipts':
        from src.engine.sniper_trade_review_report import completed_census_manifest
        value['meta']['trailing_event_source_receipts']=[]
        census=completed_census_manifest(value);census.pop('actual_cost_source_generation')
        value['meta']['completed_census_manifest']=census
    if mutation!='bad_seal':
        value['artifact_sha256']=digest({k:v for k,v in value.items() if k!='artifact_sha256'})
    sidecar.write_text(json.dumps(value))
    if mutation not in {'current_cost','official_cost','bad_seal'}:
        assert completed_projection_census_issue(value,day,costs=costs) is not None
    elif mutation!='bad_seal':
        assert completed_projection_census_issue(value,day,costs=costs) is not None
    if mutation not in {'current_cost','official_cost'}:
        assert capture_window(tmp_path,[day])['dependencies'][day]['status']=='source_gap'


def _archived_empty_original(tmp_path,*,day='2026-10-08',legacy=False,native_window=False):
    import gzip,hashlib
    from src.engine.lifecycle.broker_cost_source import source_path
    from src.engine.lifecycle.broker_cost_reconciliation import source_generation,digest
    from src.engine.sniper_trade_review_report import completed_census_manifest
    raw,sidecar,value=_old_empty_projection(tmp_path,day)
    value={k:v for k,v in value.items() if k not in {'schema','artifact_sha256','snapshot_identity'}}
    value['scope']='entered';value['sections']['recent_trades']=[]
    if not legacy:
        official=source_path(tmp_path,day);official.parent.mkdir(parents=True,exist_ok=True)
        official.write_text('{"status":"cost_source_unavailable"}')
        value['meta']['actual_cost_source_generation']=source_generation(tmp_path,day)
        value['meta']['completed_census_manifest']=completed_census_manifest(value)
    payload=json.dumps(value,separators=(',',':')).encode()
    physical=Path(str(raw)+'.gz');physical.write_bytes(gzip.compress(payload,mtime=0));raw.unlink()
    kinds=['trade_review','post_sell_feedback','holding_exit_observation','missed_entry_counterfactual']
    manifest=raw.parent/'manifests'/f'monitor_snapshot_manifest_{day}_postclose_exit.json';manifest.parent.mkdir()
    body=dict(target_date=day,profile='postclose_exit',generated_at=day+' 23:00:00',snapshot_kinds=kinds,
        snapshot_paths={k:str(raw.parent/f'{k}_{day}.json') for k in kinds},
        snapshot_sha256={k:(hashlib.sha256(payload).hexdigest() if k=='trade_review' else 'f'*64) for k in kinds})
    if native_window:
        # The retained 08/12/13/14 native manifests have these exact nine
        # fields, including their historical internally sealed input window.
        source=dict(status='valid_empty',projection=dict(path=sidecar.name,size=sidecar.stat().st_size,
                    sha256=hashlib.sha256(sidecar.read_bytes()).hexdigest(),snapshot_identity=dict(device=1,inode=2,
                    size=len(payload),mtime_ns=3,ctime_ns=4)),
                    census_sha256=digest(value['meta']['completed_census_manifest']),
                    cost_generation=value['meta']['actual_cost_source_generation'],profile='postclose_exit',
                    knowledge_cutoff=value['meta'].get('knowledge_cutoff'))
        window=dict(schema='holding_input_window_generation_v1',data_root=str(tmp_path.resolve()),
                    dates=[day],dependencies={day:source})
        window['input_window_generation_sha256']=digest(window)
        body.update(actual_cost_source_generation=value['meta']['actual_cost_source_generation'],
                    input_window_dependencies=window,input_window_generation_sha256=window['input_window_generation_sha256'])
    manifest.write_text(json.dumps(body))
    return raw,physical,sidecar,manifest,value


@pytest.mark.parametrize('legacy',[False,True])
def test_archived_native_empty_uses_actual_gzip_and_preserves_unknown_cost_and_open_gap(tmp_path,legacy):
    import hashlib
    from src.engine.lifecycle.holding_window_generation import verified_archived_empty_projection
    from src.engine.holding_exit_observation_report import _verified_trade_review_projection,_collect_completed_trade_rows
    day='2026-10-07' if legacy else '2026-10-08'
    raw,physical,sidecar,manifest,original=_archived_empty_original(tmp_path,day=day,legacy=legacy)
    originals={p:p.read_bytes() for p in (physical,sidecar,manifest)}
    value,generation=verified_archived_empty_projection(tmp_path,day)
    assert value==original and 'snapshot_identity' not in value
    assert generation['path']==physical.name
    assert generation['sha256']==hashlib.sha256(originals[physical]).hexdigest()
    assert generation['source_basis']=='current_native_gzip_empty_postclose'
    refs={};observed=_verified_trade_review_projection(raw,day,data_root=tmp_path,source_generations=refs)
    assert observed==original and set(refs)=={str(physical),str(manifest)}
    assert _collect_completed_trade_rows([observed],data_root=tmp_path)==([],[])
    window=capture_window(tmp_path,[day]);assert window['dependencies'][day]['status']=='valid_empty'
    assert window['dependencies'][day]['cost_generation']['count']==0
    if not legacy:assert window['dependencies'][day]['cost_generation']['official_source_sha256']
    assert observed['metrics']['open_scalp_position_projection_status']=='source_gap_historical_open_census_not_reconstructible'
    verify_window(tmp_path,window)
    assert not raw.exists() and not Path(str(physical)+'.archive_receipt.json').exists()
    assert {p:p.read_bytes() for p in originals}==originals


@pytest.mark.parametrize('day',['2026-10-08','2026-10-12','2026-10-13','2026-10-14'])
def test_archived_empty_known_nine_field_native_manifest_keeps_original_window_bound(tmp_path,day,monkeypatch):
    from src.engine.lifecycle import holding_window_generation as window
    from src.engine.holding_exit_observation_report import _verified_trade_review_projection
    raw,physical,sidecar,manifest,original=_archived_empty_original(tmp_path,day=day,native_window=True)
    originals={p:p.read_bytes() for p in (physical,sidecar,manifest)}
    # Re-evaluating the original window's generations would incorrectly
    # reject legitimate archives made after that original publication.
    monkeypatch.setattr(window,'verify_window',lambda *_a,**_k:pytest.fail('old window replayed'))
    value,generation=window.verified_archived_empty_projection(tmp_path,day)
    assert value==original
    body=json.loads(manifest.read_bytes())
    assert generation['original_input_window']=={
        'input_window_generation_sha256':body['input_window_generation_sha256'],'dates':[day],
        'validation_basis':'original_manifest_internal_seal_and_source_day_binding'}
    assert _verified_trade_review_projection(raw,day,data_root=tmp_path)==original
    assert window.capture_window(tmp_path,[day])['dependencies'][day]['status']=='valid_empty'
    assert {p:p.read_bytes() for p in originals}==originals


@pytest.mark.parametrize('mutation',['extra_field','missing_window_field','manifest_cost','manifest_cost_bool','window_root','window_schema',
    'window_date','window_gap','window_bool_date','window_hash','manifest_window_hash','window_dependencies',
    'window_source_shape','window_source_cost','window_source_cost_bool','window_source_census','window_source_profile','window_source_cutoff'])
def test_archived_empty_known_native_window_conflicts_fail_closed(tmp_path,mutation):
    from src.engine.lifecycle.broker_cost_reconciliation import digest
    from src.engine.holding_exit_observation_report import _verified_trade_review_projection
    day='2026-10-08';raw,_,_,manifest,_=_archived_empty_original(tmp_path,day=day,native_window=True)
    body=json.loads(manifest.read_bytes());window=body['input_window_dependencies'];source=window['dependencies'][day]
    if mutation=='extra_field':body['unknown']=True
    elif mutation=='missing_window_field':body.pop('actual_cost_source_generation')
    elif mutation=='manifest_cost':body['actual_cost_source_generation']={**body['actual_cost_source_generation'],'count':1}
    elif mutation=='manifest_cost_bool':body['actual_cost_source_generation']={**body['actual_cost_source_generation'],'count':False}
    elif mutation=='window_root':window['data_root']=str(tmp_path/'foreign')
    elif mutation=='window_schema':window['schema']='other'
    elif mutation=='window_date':window['dates']=['2026-10-09']
    elif mutation=='window_gap':window['dates']=['2026-10-06',day];window['dependencies']['2026-10-06']={}
    elif mutation=='window_bool_date':window['dates']=[False]
    elif mutation=='window_hash':window['input_window_generation_sha256']='a'*64
    elif mutation=='manifest_window_hash':body['input_window_generation_sha256']='a'*64
    elif mutation=='window_dependencies':window['dependencies']=['invalid']
    elif mutation=='window_source_shape':source['unknown']=True
    elif mutation=='window_source_cost':source['cost_generation']={**source['cost_generation'],'count':1}
    elif mutation=='window_source_cost_bool':source['cost_generation']={**source['cost_generation'],'count':False}
    elif mutation=='window_source_census':source['census_sha256']='a'*64
    elif mutation=='window_source_profile':source['profile']='intraday_light'
    elif mutation=='window_source_cutoff':source['knowledge_cutoff']='2026-10-09T00:00:00+09:00'
    if mutation not in {'window_hash','manifest_window_hash'}:
        window['input_window_generation_sha256']=digest({k:v for k,v in window.items() if k!='input_window_generation_sha256'})
        body['input_window_generation_sha256']=window['input_window_generation_sha256']
    manifest.write_text(json.dumps(body))
    assert capture_window(tmp_path,[day])['dependencies'][day]['status']=='source_gap'
    assert _verified_trade_review_projection(raw,day,data_root=tmp_path) is None


@pytest.mark.parametrize('mutation',['missing_manifest','missing_scope','missing_source_receipts',
    'manifest_hash','manifest_date','manifest_path','other_path','kinds',
    'crc','isize','truncated','nonempty','metrics_shape','sections_shape','meta_shape','duplicate_key',
    'current_cost','count_bool','event_bool','recorded_cost_bool'])
def test_archived_empty_native_source_failures_are_isolated_in_all_consumers(tmp_path,mutation):
    import gzip,hashlib
    from src.engine.lifecycle.broker_cost_source import source_path
    from src.engine.sniper_trade_review_report import completed_census_manifest
    from src.engine.holding_exit_observation_report import _verified_trade_review_projection
    day='2026-10-08';raw,physical,_,manifest,value=_archived_empty_original(tmp_path)
    body=json.loads(manifest.read_bytes())
    if mutation=='missing_manifest':pass  # Remove only after the common fixture write below.
    elif mutation=='manifest_hash':body['snapshot_sha256']['trade_review']='a'*64
    elif mutation=='manifest_date':body['target_date']='2026-10-09'
    elif mutation=='manifest_path':body['snapshot_paths']['trade_review']=str(raw.with_name('other.json'))
    elif mutation=='other_path':body['snapshot_paths']['post_sell_feedback']=str(raw)
    elif mutation=='kinds':body['snapshot_kinds'][-1]='trade_review'
    elif mutation in {'crc','isize','truncated'}:
        data=bytearray(physical.read_bytes())
        if mutation=='truncated':data=data[:-4]
        else:data[-8 if mutation=='crc' else -4]^=1
        physical.write_bytes(data)
    elif mutation=='current_cost':source_path(tmp_path,day).write_text('{"revision":2}')
    else:
        if mutation=='missing_scope':value.pop('scope')
        elif mutation=='missing_source_receipts':
            value['meta']['trailing_event_source_receipts']=[]
            value['meta']['completed_census_manifest']=completed_census_manifest(value)
        elif mutation=='nonempty':
            value['sections']['completed_trade_projection']=[dict(id=7,completion_observed_date=day,status='COMPLETED')]
            value['meta']['sell_completed_event_ids']=['7'];value['meta']['completion_event_id_count']=1
            value['metrics']['canonical_completed_trades']=1
            value['meta']['completed_census_manifest']=completed_census_manifest(value)
        elif mutation=='metrics_shape':value['metrics']=['invalid']
        elif mutation=='sections_shape':value['sections']=['invalid']
        elif mutation=='meta_shape':value['meta']=['invalid']
        elif mutation=='count_bool':value['meta']['completed_census_manifest']['raw_terminal_count']=False
        elif mutation=='event_bool':value['meta']['completion_event_id_count']=False
        elif mutation=='recorded_cost_bool':
            value['meta']['actual_cost_source_generation']['count']=False
            value['meta']['completed_census_manifest']=completed_census_manifest(value)
        payload=json.dumps(value,separators=(',',':')).encode()
        if mutation=='duplicate_key':payload=payload.replace(b'"scope":"entered"',b'"scope":"entered","scope":"entered"')
        physical.write_bytes(gzip.compress(payload,mtime=0));body['snapshot_sha256']['trade_review']=hashlib.sha256(payload).hexdigest()
    manifest.write_text(json.dumps(body))
    if mutation=='missing_manifest':manifest.unlink()
    window=capture_window(tmp_path,[day])
    assert window['dependencies'][day]['status']=='source_gap'
    assert _verified_trade_review_projection(raw,day,data_root=tmp_path) is None
    assert not Path(str(physical)+'.archive_receipt.json').exists()


def test_archived_empty_resident_decode_claim_lives_until_outer_holding_budget_closes(tmp_path):
    from contextlib import ExitStack
    from src.engine import holding_exit_observation_report as holding
    from src.engine.lifecycle.research_input_budget import health
    raw,_,_,_,value=_archived_empty_original(tmp_path)
    before=health()['used_bytes']
    with ExitStack() as budget:
        token=holding._INPUT_BUDGET.set(budget)
        try:
            assert holding._verified_trade_review_projection(raw,'2026-10-08',data_root=tmp_path)==value
            assert health()['used_bytes']>before
        finally:holding._INPUT_BUDGET.reset(token)
    assert health()['used_bytes']==before


def test_archived_empty_native_reader_binds_requested_logical_source_to_explicit_root(tmp_path):
    from src.engine.holding_exit_observation_report import _verified_trade_review_projection
    raw,physical,_,_,_=_archived_empty_original(tmp_path)
    foreign=tmp_path/'other-root'/raw.name;foreign.parent.mkdir()
    Path(str(foreign)+'.gz').write_bytes(physical.read_bytes())
    assert _verified_trade_review_projection(foreign,'2026-10-08',data_root=tmp_path) is None
