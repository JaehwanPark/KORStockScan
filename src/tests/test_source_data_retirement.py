"""Destructive boundary and stale-file regressions for file-source retirement."""
import json
import os
from pathlib import Path

import pytest

from src.engine.automation import source_data_retirement as retirement


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    workspace = tmp_path / "KORStockScan"
    monkeypatch.setattr(retirement, "WORKSPACE", workspace)
    monkeypatch.setattr(retirement, "open_inodes", lambda: (set(), []))
    raw = workspace / "data/analytics/parquet/pipeline_events/date=2026-08-31/events.parquet"
    raw.parent.mkdir(parents=True)
    raw.write_bytes(b"reviewed raw")
    protected = workspace / "data/runtime/initial_quantity/current.json"
    protected.parent.mkdir(parents=True)
    protected.write_text('{"policy":"keep"}')
    entry = dict(path=str(raw), sha256=retirement.file_hash(raw),
                 identity=retirement.identity(raw.stat()), kind="analytics_parquet",
                 classification="delete_unused_raw", consumer_evidence="offline_only",
                 period_evidence=dict(mode="parquet_clock", rows=1, unresolved_rows=0,
                                      max_date="2026-08-31"))
    value = dict(schema=retirement.SCHEMA, cutoff_exclusive=retirement.CUTOFF,
                 protected_files={str(protected): retirement.file_hash(protected)},
                 candidates=[entry])
    manifest = workspace / "manifest.json"

    def save():
        value.pop("content_sha256", None)
        value["content_sha256"] = retirement.digest(value)
        manifest.write_text(json.dumps(value))

    save()
    return raw, protected, value, manifest, workspace / "journal.jsonl", save


def test_dry_run_then_apply_preserves_policy(prepared):
    raw, protected, _, manifest, journal, _ = prepared
    dry = retirement.run(manifest, journal)
    assert dry["deleted_files"] == 0 and raw.is_file()
    result = retirement.run(manifest, journal.with_name("apply.jsonl"), apply=True)
    assert result["deleted_files"] == 1 and not raw.exists()
    assert protected.read_text() == '{"policy":"keep"}'
    assert [json.loads(line)["status"] for line in journal.with_name("apply.jsonl").read_text().splitlines()] == ["delete_intent", "deleted"]


@pytest.mark.parametrize("field,value", [("max_date", "2026-09-01"), ("unresolved_rows", 1), ("rows", 0)])
def test_current_or_unresolved_clock_is_rejected(prepared, field, value):
    raw, _, data, manifest, journal, save = prepared
    data["candidates"][0]["period_evidence"][field] = value
    save()
    with pytest.raises(ValueError):
        retirement.run(manifest, journal, apply=True)
    assert raw.exists()


def test_manifest_tamper_is_rejected(prepared):
    raw, _, _, manifest, journal, _ = prepared
    manifest.write_text(manifest.read_text().replace("2026-08-31", "2026-08-30"))
    with pytest.raises(ValueError, match="manifest_contract"):
        retirement.run(manifest, journal, apply=True)
    assert raw.exists()


def test_changed_source_is_skipped(prepared):
    raw, _, _, manifest, journal, _ = prepared
    raw.write_bytes(b"new current source")
    result = retirement.run(manifest, journal, apply=True)
    assert result["deleted_files"] == 0 and result["skipped"]
    assert raw.exists()


def test_symlink_and_hardlink_are_not_deleted(prepared):
    raw, _, _, manifest, journal, _ = prepared
    link = raw.with_name("link.parquet")
    os.link(raw, link)
    result = retirement.run(manifest, journal, apply=True)
    assert result["deleted_files"] == 0 and raw.exists() and link.exists()


def test_intermediate_symlink_is_rejected(prepared):
    raw, _, data, manifest, journal, save = prepared
    linked = raw.parents[4] / "alias"
    linked.symlink_to(raw.parent, target_is_directory=True)
    data["candidates"][0]["path"] = str(linked / raw.name)
    save()
    with pytest.raises(ValueError, match="symlink"):
        retirement.run(manifest, journal, apply=True)
    assert raw.exists()


def test_policy_and_database_paths_are_not_raw(prepared):
    raw, protected, data, manifest, journal, save = prepared
    data["candidates"][0]["path"] = str(protected)
    save()
    with pytest.raises(ValueError, match="protected"):
        retirement.run(manifest, journal, apply=True)
    data["candidates"][0]["path"] = str(raw.parents[3] / "duckdb/live.duckdb")
    save()
    with pytest.raises(ValueError, match="allowlisted"):
        retirement.run(manifest, journal, apply=True)


def test_observed_open_fd_is_skipped(prepared, monkeypatch):
    raw, _, _, manifest, journal, _ = prepared
    st = raw.stat()
    monkeypatch.setattr(retirement, "open_inodes", lambda: ({(st.st_dev, st.st_ino)}, [123]))
    result = retirement.run(manifest, journal, apply=True)
    assert result["deleted_files"] == 0 and raw.exists()
    assert result["fd_census_complete"] is False


def test_protected_hash_failure_stops_before_any_delete(prepared):
    raw, protected, _, manifest, journal, _ = prepared
    protected.write_text("changed policy")
    with pytest.raises(ValueError, match="protected_file_changed"):
        retirement.run(manifest, journal, apply=True)
    assert raw.exists() and not journal.exists()


def test_reader_fix_is_rejected(prepared):
    raw, _, data, manifest, journal, save = prepared
    data["candidates"][0]["classification"] = "delete_after_reader_fix"
    save()
    with pytest.raises(ValueError, match="unreleased_reader"):
        retirement.run(manifest, journal, apply=True)
    assert raw.exists()


def test_archive_without_preservation_is_rejected(prepared):
    raw, _, data, manifest, journal, save = prepared
    archive = retirement.WORKSPACE.parent / "KORStockScan-storage-archives/old.tar.zst"
    archive.parent.mkdir()
    archive.write_bytes(b"mixed archive")
    item = data["candidates"][0]
    item.update(path=str(archive), kind="retired_archive", sha256=retirement.file_hash(archive),
                identity=retirement.identity(archive.stat()), period_evidence=dict(mode="archive_member_census"))
    save()
    with pytest.raises(ValueError, match="preservation_missing"):
        retirement.run(manifest, journal, apply=True)
    assert raw.exists() and archive.exists()


def test_archive_preserved_config_hash_must_match(prepared):
    raw, protected, data, manifest, journal, save = prepared
    archive = retirement.WORKSPACE.parent / "KORStockScan-storage-archives/old.tar.zst"
    archive.parent.mkdir()
    archive.write_bytes(b"mixed archive")
    receipt = manifest.with_name("preservation.json")
    receipt.write_text(json.dumps(dict(schema="file_source_archive_nonraw_preservation_v1",
        source_archive_sha256=retirement.file_hash(archive),complete=True,unclassified_members=[],
        raw_backup_created=False,member_byte_identity_verified=1,retired_raw_members=[],
        preserved_files=[dict(path=str(protected),sha256="0"*64)])))
    item=data["candidates"][0]
    item.update(path=str(archive),kind="retired_archive",sha256=retirement.file_hash(archive),
        identity=retirement.identity(archive.stat()),period_evidence=dict(mode="archive_member_census",
        preserved_nonraw_receipt=str(receipt),preserved_nonraw_receipt_sha256=retirement.file_hash(receipt)))
    save()
    with pytest.raises(ValueError,match="preserved_file_changed"):
        retirement.run(manifest,journal,apply=True)
    assert raw.exists() and archive.exists()


def test_consumer_change_is_rejected(prepared):
    raw, _, data, manifest, journal, save = prepared
    consumer=manifest.with_name("consumer.py")
    consumer.write_text("date selection")
    data["candidates"][0]["consumer_evidence"] = dict(readers=[dict(path=str(consumer),sha256=retirement.file_hash(consumer))])
    save()
    consumer.write_text("changed date selection")
    with pytest.raises(ValueError,match="protected_file_changed"):
        retirement.run(manifest,journal,apply=True)
    assert raw.exists()


def test_database_even_inside_raw_family_is_rejected(prepared):
    raw, _, data, manifest, journal, save=prepared
    database=raw.with_suffix(".duckdb")
    database.write_bytes(b"database excluded")
    data["candidates"][0]["path"]=str(database)
    save()
    with pytest.raises(ValueError,match="database_file"):
        retirement.run(manifest,journal,apply=True)
    assert raw.exists() and database.exists()


def test_journal_cannot_be_reused(prepared):
    raw, _, _, manifest, journal, _ = prepared
    retirement.run(manifest, journal)
    with pytest.raises(FileExistsError):
        retirement.run(manifest, journal, apply=True)
    assert raw.exists()


@pytest.mark.parametrize('apply', [False, True])
def test_incomplete_fd_census_never_certifies_or_deletes(prepared, monkeypatch, apply):
    raw, _, _, manifest, journal, _ = prepared
    monkeypatch.setattr(retirement, 'open_inodes', lambda: (set(), [123]))
    result = retirement.run(manifest, journal, apply=apply)
    assert result['deleted_files'] == 0 and raw.exists()
    assert result['skipped'][0]['reason'] == 'fd_census_incomplete'


def test_unlink_success_is_not_reported_as_skipped_when_directory_fsync_fails(prepared, monkeypatch, capsys):
    import stat
    raw, _, data, manifest, journal, save = prepared
    another = raw.with_name('later.parquet')
    another.write_bytes(b'later reviewed raw')
    data['candidates'].append(dict(data['candidates'][0], path=str(another),
        sha256=retirement.file_hash(another), identity=retirement.identity(another.stat())))
    save()
    fsync = os.fsync
    def fail_directory(fd):
        if stat.S_ISDIR(os.fstat(fd).st_mode):
            raise OSError('directory durability unavailable')
        return fsync(fd)
    monkeypatch.setattr(retirement.os, 'fsync', fail_directory)
    exit_code = retirement.main(['--manifest', str(manifest), '--journal', str(journal), '--apply'])
    result = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert not raw.exists() and result['deleted_files'] == 1
    assert result['skipped'] == []
    assert another.exists() and result['remaining_unprocessed'] == 1
    assert result['post_delete_errors'][0]['status'] == 'deleted_durability_unconfirmed'
    assert json.loads(journal.read_text().splitlines()[-1])['status'] == 'deleted_durability_unconfirmed'


def test_summary_hash_identifies_the_manifest_bytes_actually_consumed(prepared, monkeypatch):
    raw, _, _, manifest, journal, _ = prepared
    consumed_hash = retirement.file_hash(manifest)
    original = retirement._validate_entry
    def replace_after_parse(entry, protected):
        path = original(entry, protected)
        manifest.write_text('{"unrelated":"new generation"}')
        return path
    monkeypatch.setattr(retirement, '_validate_entry', replace_after_parse)
    result = retirement.run(manifest, journal)
    assert result['manifest_sha256'] == consumed_hash
    assert raw.exists()


def test_additional_manifest_is_typed_and_reader_sealed(prepared):
 raw,protected,value,manifest,journal,save=prepared
 new=raw.parent.with_name('date=2026-09-28');new.mkdir();target=new/raw.name;raw.rename(target)
 reader=target.parents[3]/'reader.py';reader.write_text('bounded reader')
 entry=value['candidates'][0]
 entry.update(path=str(target),identity=retirement.identity(target.stat()),kind='out_of_window_parquet',
              consumer_evidence=dict(readers=[dict(path=str(reader),sha256=retirement.file_hash(reader))],receipts=[dict(path=str(reader),sha256=retirement.file_hash(reader))]),
              period_evidence=dict(mode='unused_file_consumer_census',reader_scope_verified=True,earliest_required_date='2026-10-04',selected_consumer_readers=[dict(path=str(reader),sha256=retirement.file_hash(reader))]))
 value.pop('cutoff_exclusive');value.update(schema=retirement.ADDITIONAL_SCHEMA,selection='explicit_unused_file_inventory_no_global_cutoff');save()
 assert retirement.run(manifest,journal)['skipped']==[]
 reader.write_text('unbounded new reader')
 with pytest.raises(ValueError,match='reader_changed'):retirement.run(manifest,journal.with_name('apply.jsonl'),apply=True)
 assert target.exists() and protected.exists()


def test_additional_snapshot_cannot_disguise_current_filename_as_old_date(prepared):
 raw,_,value,manifest,journal,save=prepared
 target=raw.parents[4]/'threshold_cycle/snapshots/pipeline_events_2026-10-07_20261007_201000.jsonl.gz'
 target.parent.mkdir(parents=True);raw.rename(target)
 proof=target.parent/'proof.json';proof.write_text('{}')
 entry=value['candidates'][0];entry.update(path=str(target),identity=retirement.identity(target.stat()),kind='retired_threshold_snapshot',
  consumer_evidence=dict(readers=[dict(path=str(proof),sha256=retirement.file_hash(proof))],receipts=[dict(path=str(proof),sha256=retirement.file_hash(proof))]),
  period_evidence=dict(mode='unused_file_consumer_census',reader_scope_verified=True,source_date='2026-09-15',required_dates=['2026-10-06']))
 value.pop('cutoff_exclusive');value.update(schema=retirement.ADDITIONAL_SCHEMA,selection='explicit_unused_file_inventory_no_global_cutoff');save()
 with pytest.raises(ValueError,match='filename_date_conflict'):retirement.run(manifest,journal,apply=True)
 assert target.exists()
