"""Compression preserves producer identity without replaying large snapshots."""
import gzip
import json
from pathlib import Path

import pytest

from src.engine import compress_db_backfilled_files as archive
from src.engine.lifecycle import snapshot_archive as source
from src.engine.lifecycle.holding_window_generation import byte_generation, capture_window, verify_window


@pytest.fixture
def snapshot(tmp_path, monkeypatch):
    directory = tmp_path/'report/monitor_snapshots'
    directory.mkdir(parents=True)
    monkeypatch.setattr(archive, 'MONITOR_SNAPSHOT_DIR', directory)
    path = directory/'trade_review_2026-10-08.json'
    path.write_text(json.dumps(dict(date='2026-10-08', meta={'knowledge_cutoff':'a'})))
    return path


def test_original_identity_and_generation_survive_compression(snapshot):
    identity = source.snapshot_identity(snapshot)
    before = byte_generation(snapshot)
    root = snapshot.parents[2]
    window = capture_window(root, ['2026-10-08'])
    assert archive._gzip_file(snapshot, dry_run=False)[0]
    assert not snapshot.exists()
    assert source.snapshot_identity(snapshot) == identity
    assert byte_generation(snapshot) == before
    verify_window(root, window)


def test_existing_legacy_gzip_is_verified_without_replacing_it(snapshot):
    archived = Path(str(snapshot)+'.gz')
    with gzip.open(archived,'wb') as handle:
        handle.write(snapshot.read_bytes())
    before = source.file_identity(archived.stat())
    generation = byte_generation(snapshot)
    assert archive._gzip_file(snapshot,dry_run=False)[0]
    assert source.file_identity(archived.stat()) == before
    assert byte_generation(snapshot) == generation


def test_existing_conflicting_gzip_keeps_original_bytes(snapshot):
    original = snapshot.read_bytes()
    archived = Path(str(snapshot)+'.gz')
    with gzip.open(archived,'wb') as handle:
        handle.write(b'conflicting original')
    with pytest.raises((OSError,ValueError)):
        archive._gzip_file(snapshot,dry_run=False)
    assert snapshot.read_bytes() == original
    assert not Path(str(archived)+'.archive_receipt.json').exists()


@pytest.mark.parametrize('mutation',['archive','receipt','replacement','symlink'])
def test_changed_or_untrusted_representation_is_rejected(snapshot, mutation):
    archive._gzip_file(snapshot,dry_run=False)
    archived = Path(str(snapshot)+'.gz')
    if mutation == 'archive':
        raw = archived.read_bytes(); archived.write_bytes(raw[:-4]+b'xxxx')
    elif mutation == 'receipt':
        receipt = Path(str(archived)+'.archive_receipt.json')
        value = json.loads(receipt.read_text());value['logical_size_bytes'] += 1
        receipt.write_text(json.dumps(value))
    elif mutation == 'replacement':
        raw = archived.read_bytes();archived.unlink();archived.write_bytes(raw)
    else:
        target = archived.with_suffix('.other');archived.rename(target);archived.symlink_to(target)
    with pytest.raises(ValueError):
        byte_generation(snapshot)


def test_plain_arrival_cannot_hide_archive_conflict(snapshot):
    archive._gzip_file(snapshot,dry_run=False)
    snapshot.write_text('{"revised":true}')
    with pytest.raises(ValueError,match='plain_gzip_conflict'):
        byte_generation(snapshot)


def test_large_invalid_date_keeps_its_frozen_source_gap(snapshot):
    snapshot.write_bytes(b'{'+b' '*(4*1024*1024)+b'}')
    window = capture_window(snapshot.parents[2],['2026-10-08'])
    assert window['dependencies']['2026-10-08']['status'] == 'source_gap'
    archive._gzip_file(snapshot,dry_run=False)
    verify_window(snapshot.parents[2],window)


def test_bounded_read_rejects_decompression_expansion(snapshot):
    archive._gzip_file(snapshot,dry_run=False)
    with pytest.raises(ValueError,match='size_limit'):
        source.read_bytes(snapshot,maximum=8)


def test_archive_digest_is_reused_only_inside_explicit_native_session(snapshot, monkeypatch):
    from src.engine.infrastructure.validation_digest_session import DigestSession
    # Incompressible bytes keep the physical gzip above the reuse floor.
    import random
    snapshot.write_bytes(random.Random(17).randbytes(2*1024*1024))
    archive._gzip_file(snapshot,dry_run=False)
    session = DigestSession(snapshot.parents[2],'2026-10-08',role='postclose',generation={})
    with session.activate():
        first = byte_generation(snapshot)
        second = byte_generation(snapshot)
    assert first == second
    assert session.stats['full_reads'] == session.stats['reused_reads'] == 1
    assert session.stats['full_bytes'] < 3*1024*1024
    archived = Path(str(snapshot)+'.gz')
    archived.write_bytes(archived.read_bytes()[:-2])
    with pytest.raises(ValueError):
        byte_generation(snapshot)


def test_large_projection_metadata_path_never_decompresses_raw_or_timelines(snapshot, monkeypatch):
    import hashlib
    from src.engine import log_archive_service as snapshots
    from src.engine.sniper_trade_review_report import completed_census_manifest
    from src.engine.lifecycle.holding_window_generation import seal_dependency_receipt
    from src.engine.holding_exit_observation_report import _verified_trade_review_projection
    directory = snapshot.parent
    monkeypatch.setattr(snapshots,'MONITOR_SNAPSHOT_DIR',directory)
    payload = dict(date='2026-10-08',metrics={'canonical_completed_trades':0},
        meta={'snapshot_profile':'postclose_exit','sell_completed_event_ids':[]},
        sections={'completed_trade_projection':[],'open_scalp_position_projection':[]},
        diagnostic_padding='x'*(5*1024*1024))
    payload['meta']['completed_census_manifest'] = completed_census_manifest(payload)
    snapshots.save_monitor_snapshot('trade_review','2026-10-08',payload)
    sidecar = snapshot.with_suffix('.completed_projection.json')
    projection = json.loads(sidecar.read_text())
    projection['test_padding'] = 'x'*(5*1024*1024)
    projection['artifact_sha256'] = hashlib.sha256(json.dumps(
        {k:v for k,v in projection.items() if k!='artifact_sha256'},
        sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
    sidecar.write_text(json.dumps(projection))
    seal_dependency_receipt(sidecar,projection)
    window = capture_window(snapshot.parents[2],['2026-10-08'])
    archive._gzip_file(snapshot,dry_run=False)
    archive._gzip_file(sidecar,dry_run=False)
    def forbidden(*args,**kwargs):
        raise AssertionError('metadata consumer must not decompress large timelines')
    monkeypatch.setattr(gzip,'open',forbidden)
    verify_window(snapshot.parents[2],window)
    assert _verified_trade_review_projection(snapshot,'2026-10-08',
        data_root=snapshot.parents[2],metadata_only=True) is not None


def test_assembly_inventory_keeps_logical_names_and_ignores_storage_receipts(snapshot):
    from src.engine.automation.main_trailing_source_assembler import input_inventory
    master = snapshot.parents[2]/'master.json';master.write_text('{}')
    parent = snapshot.parents[2]/'parent.json';parent.write_text('{}')
    before = input_inventory(snapshot.parents[2],['2026-10-08'],master,parent)
    archive._gzip_file(snapshot,dry_run=False)
    assert input_inventory(snapshot.parents[2],['2026-10-08'],master,parent) == before


def test_stop_dependency_stat_preserves_publisher_identity(snapshot):
    from src.engine.automation.main_stop_postclose import verified_dependency_stats
    generation = byte_generation(snapshot)
    before = verified_dependency_stats({str(snapshot):generation})
    archive._gzip_file(snapshot,dry_run=False)
    assert verified_dependency_stats({str(snapshot):generation}) == before


def test_corrupt_archive_is_an_identifiable_date_gap(snapshot):
    window = capture_window(snapshot.parents[2],['2026-10-08','2026-10-09'])
    archive._gzip_file(snapshot,dry_run=False)
    archived = Path(str(snapshot)+'.gz')
    archived.write_bytes(archived.read_bytes()[:-1])
    observed = capture_window(snapshot.parents[2],window['dates'])
    assert observed['dependencies']['2026-10-08']['status'] == 'source_gap'
    assert observed['dependencies']['2026-10-09'] == window['dependencies']['2026-10-09']
    with pytest.raises(ValueError,match='generation_changed'):
        verify_window(snapshot.parents[2],window)


def test_legacy_archive_does_not_invent_a_previously_missing_inventory(snapshot):
    from src.engine.automation.main_trailing_source_assembler import input_inventory
    master = snapshot.parents[2]/'master.json';master.write_text('{}')
    parent = snapshot.parents[2]/'parent.json';parent.write_text('{}')
    snapshot.unlink()
    before = input_inventory(snapshot.parents[2],['2026-10-08'],master,parent)
    with gzip.open(Path(str(snapshot)+'.gz'),'wb') as handle:
        handle.write(b'{}')
    assert not source.identity_available(snapshot)
    assert input_inventory(snapshot.parents[2],['2026-10-08'],master,parent) == before


def test_stop_cli_reuses_digests_without_persistent_validator_state(tmp_path, monkeypatch):
    from contextlib import nullcontext
    import sys
    from src.engine.automation import main_stop_postclose as stop
    from src.engine.infrastructure.validation_digest_session import ACTIVE
    from src.engine import log_archive_service as snapshots
    from src.utils import constants
    manifest=tmp_path/'manifest.json';manifest.write_text('{}')
    raw=tmp_path/'large.bin';raw.write_bytes(b'x'*(2*1024*1024))
    monkeypatch.setattr(constants,'DATA_DIR',tmp_path)
    monkeypatch.setattr(stop,'direct_job',lambda *a,**k:nullcontext())
    monkeypatch.setattr(snapshots,'verified_postclose_exit_snapshot_manifest',lambda *a,**k:manifest)
    monkeypatch.setattr(stop,'baseline',lambda *a:({},{}))
    monkeypatch.setattr(stop,'sources',lambda *a:[])
    monkeypatch.setattr(stop,'completed_evidence',lambda *a:[])
    observed={}
    def publish(*a,**k):
        session=ACTIVE.get();assert session.binding['role']=='postclose'
        assert byte_generation(raw)==byte_generation(raw)
        observed.update(session.stats)
    monkeypatch.setattr(stop,'publish',publish)
    monkeypatch.setattr(sys,'argv',['main_stop_postclose','--date','2026-10-16','--target','2026-10-19'])
    assert stop.main()==0
    assert observed['full_reads']==observed['reused_reads']==1
    assert ACTIVE.get() is None
    assert not (tmp_path/'runtime/validation_digests').exists()


def test_legacy_gzip_with_sidecar_retains_original_bounded_snapshot_contract(snapshot, monkeypatch):
    import hashlib
    from src.engine import log_archive_service as snapshots
    from src.engine.sniper_trade_review_report import completed_census_manifest
    monkeypatch.setattr(snapshots,'MONITOR_SNAPSHOT_DIR',snapshot.parent)
    payload=dict(date='2026-10-08',metrics={'canonical_completed_trades':0},
        meta={'snapshot_profile':'postclose_exit','sell_completed_event_ids':[]},
        sections={'completed_trade_projection':[],'open_scalp_position_projection':[]})
    payload['meta']['completed_census_manifest']=completed_census_manifest(payload)
    snapshots.save_monitor_snapshot('trade_review','2026-10-08',payload)
    archived=Path(str(snapshot)+'.gz')
    with gzip.open(archived,'wb') as handle:handle.write(snapshot.read_bytes())
    snapshot.unlink()
    window=capture_window(snapshot.parents[2],['2026-10-08'])
    day=window['dependencies']['2026-10-08']
    assert day['status']=='valid_empty'
    assert day['projection']==dict(path=archived.name,size=archived.stat().st_size,
        sha256=hashlib.sha256(archived.read_bytes()).hexdigest())
    assert 'snapshot_identity' not in day['projection']


@pytest.mark.parametrize('profile',['postclose_exit','intraday_light'])
@pytest.mark.parametrize('fails',[False,True])
def test_native_snapshot_cli_scopes_reuse_and_closes_session_on_failure(tmp_path,monkeypatch,capsys,profile,fails):
    import sys
    from src.engine import run_monitor_snapshot as cli
    from src.engine.infrastructure.validation_digest_session import ACTIVE
    from src.utils import constants
    raw=tmp_path/'large.bin';raw.write_bytes(b'x'*(2*1024*1024))
    monkeypatch.setattr(constants,'DATA_DIR',tmp_path)
    monkeypatch.setenv('MONITOR_SNAPSHOT_FROM_WRAPPER','1')
    monkeypatch.setattr(sys,'argv',['run_monitor_snapshot','--date','2026-10-16','--profile',profile,
        '--skip-lock','--lock-file',str(tmp_path/'snapshot.lock')])
    def build(*a,**k):
        assert (ACTIVE.get() is not None)==(profile=='postclose_exit')
        assert byte_generation(raw)==byte_generation(raw)
        if fails:raise ValueError('original_producer_failure')
        return {'snapshot_manifest':'unchanged-native-manifest'}
    monkeypatch.setattr(cli,'save_monitor_snapshots_for_date_with_profile',build)
    assert cli.main()==(1 if fails else 0)
    assert ACTIVE.get() is None
    assert not (tmp_path/'runtime/validation_digests').exists()
    result=json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    if profile=='postclose_exit':
        assert result['validation_io']['full_reads']==result['validation_io']['reused_reads']==1
    else:assert result['validation_io'] is None
    if fails:assert result['error']=='original_producer_failure' and result['snapshots']=={}
    else:assert result['snapshots']=={'snapshot_manifest':'unchanged-native-manifest'}
