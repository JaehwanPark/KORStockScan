import json
from datetime import date

import pytest

from src.engine import compress_db_backfilled_files as archive


@pytest.fixture(autouse=True)
def _isolate_new_archive_roots(tmp_path, monkeypatch):
    canonical_dir = tmp_path / "optional" / "canonical"
    summary_dir = tmp_path / "optional" / "summaries"
    threshold_dir = tmp_path / "optional" / "threshold_cycle"
    snapshot_dir = threshold_dir / "snapshots"
    for path in (canonical_dir, summary_dir, snapshot_dir):
        path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(archive, "POSTCLOSE_STATUS_DIR", tmp_path / "optional" / "postclose_status")
    monkeypatch.setattr(archive, "POSTCLOSE_CONTROLLER_DIR", tmp_path / "optional" / "postclose_controller")
    monkeypatch.setattr(archive, "CANONICAL_CONTEXT_DIR", canonical_dir)
    monkeypatch.setattr(archive, "PIPELINE_SUMMARY_DIR", summary_dir)
    monkeypatch.setattr(archive, "THRESHOLD_CYCLE_DIR", threshold_dir)
    monkeypatch.setattr(archive, "THRESHOLD_SNAPSHOT_DIR", snapshot_dir)


def test_snapshot_manifest_verifies_existing_snapshot(tmp_path, monkeypatch):
    snapshot_dir = tmp_path / "monitor_snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir = snapshot_dir / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    target_date = date(2026, 4, 22)

    snapshot_path = snapshot_dir / "trade_review_2026-04-22.json"
    snapshot_path.write_text("{}", encoding="utf-8")
    manifest_path = manifest_dir / "monitor_snapshot_manifest_2026-04-22_full.json"
    manifest_path.write_text(
        json.dumps(
            {
                "target_date": "2026-04-22",
                "profile": "full",
                "snapshot_paths": {"trade_review": str(snapshot_path)},
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(archive, "MONITOR_SNAPSHOT_DIR", snapshot_dir)
    monkeypatch.setattr(archive, "MONITOR_SNAPSHOT_MANIFEST_DIR", manifest_dir)

    assert archive._snapshot_manifest_verifies("trade_review", target_date) is True


def test_run_uses_snapshot_manifest_without_db_fallback(tmp_path, monkeypatch):
    snapshot_dir = tmp_path / "monitor_snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir = snapshot_dir / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    pipeline_dir = tmp_path / "pipeline_events"
    pipeline_dir.mkdir(parents=True, exist_ok=True)

    snapshot_path = snapshot_dir / "trade_review_2026-04-22.json"
    snapshot_path.write_text("{}", encoding="utf-8")
    (manifest_dir / "monitor_snapshot_manifest_2026-04-22_full.json").write_text(
        json.dumps(
            {
                "target_date": "2026-04-22",
                "profile": "full",
                "snapshot_paths": {"trade_review": str(snapshot_path)},
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(archive, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(archive, "MONITOR_SNAPSHOT_DIR", snapshot_dir)
    monkeypatch.setattr(archive, "MONITOR_SNAPSHOT_MANIFEST_DIR", manifest_dir)

    stats = archive.run(retention_days=1, today=date(2026, 4, 23), dry_run=True)

    assert stats["snapshots"]["scanned"] == 1
    assert stats["snapshots"]["verified"] == 1
    assert stats["snapshots"]["compressed"] == 1
    assert stats["skipped_unverified"] == 0


def test_run_does_not_compress_manifested_corrupt_snapshot(tmp_path, monkeypatch):
    snapshot_dir = tmp_path / "monitor_snapshots"
    snapshot_dir.mkdir(parents=True)
    manifest_dir = snapshot_dir / "manifests"
    manifest_dir.mkdir(parents=True)
    pipeline_dir = tmp_path / "pipeline_events"
    pipeline_dir.mkdir(parents=True)
    snapshot_path = snapshot_dir / "missed_entry_counterfactual_2026-04-22.json"
    snapshot_path.write_text('{"full_rows":[', encoding="utf-8")
    (manifest_dir / "monitor_snapshot_manifest_2026-04-22_full.json").write_text(
        json.dumps(
            {
                "target_date": "2026-04-22",
                "profile": "full",
                "snapshot_paths": {"missed_entry_counterfactual": str(snapshot_path)},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(archive, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(archive, "MONITOR_SNAPSHOT_DIR", snapshot_dir)
    monkeypatch.setattr(archive, "MONITOR_SNAPSHOT_MANIFEST_DIR", manifest_dir)

    stats = archive.run(retention_days=1, today=date(2026, 4, 23), dry_run=False)

    assert stats["snapshots"]["compressed"] == 0
    assert stats["skipped_unverified"] == 1
    assert snapshot_path.exists()
    assert not snapshot_path.with_suffix(".json.gz").exists()
    assert stats["errors"] == [
        "snapshot:missed_entry_counterfactual_2026-04-22.json:"
        "invalid_json_boundary_not_compressed"
    ]


def test_run_compresses_pipeline_events_only_after_parquet_verification(
    tmp_path, monkeypatch
):
    pipeline_dir = tmp_path / "pipeline_events"
    pipeline_dir.mkdir(parents=True, exist_ok=True)
    monitor_snapshot_dir = tmp_path / "monitor_snapshots"
    monitor_snapshot_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir = monitor_snapshot_dir / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    parquet_partition = (
        tmp_path / "analytics" / "parquet" / "pipeline_events" / "date=2026-04-22"
    )
    parquet_partition.mkdir(parents=True, exist_ok=True)
    (parquet_partition / "part-000001.parquet").write_bytes(b"parquet-placeholder")
    raw_path = pipeline_dir / "pipeline_events_2026-04-22.jsonl"
    raw_path.write_text('{"stage":"sample"}\n', encoding="utf-8")

    monkeypatch.setattr(archive, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(archive, "MONITOR_SNAPSHOT_DIR", monitor_snapshot_dir)
    monkeypatch.setattr(archive, "MONITOR_SNAPSHOT_MANIFEST_DIR", manifest_dir)
    monkeypatch.setattr(
        archive, "ANALYTICS_PARQUET_DIR", tmp_path / "analytics" / "parquet"
    )

    stats = archive.run(retention_days=1, today=date(2026, 4, 23), dry_run=True)

    assert stats["pipeline"]["scanned"] == 1
    assert stats["pipeline"]["verified"] == 1
    assert stats["pipeline"]["compressed"] == 1
    assert stats["pipeline"]["saved_bytes"] == raw_path.stat().st_size
    assert raw_path.with_name(f".{raw_path.name}.generation.lock").is_file()


def test_run_skips_pipeline_events_without_parquet_verification(tmp_path, monkeypatch):
    pipeline_dir = tmp_path / "pipeline_events"
    pipeline_dir.mkdir(parents=True, exist_ok=True)
    monitor_snapshot_dir = tmp_path / "monitor_snapshots"
    monitor_snapshot_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir = monitor_snapshot_dir / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    (pipeline_dir / "pipeline_events_2026-04-22.jsonl").write_text(
        '{"stage":"sample"}\n', encoding="utf-8"
    )

    monkeypatch.setattr(archive, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(archive, "MONITOR_SNAPSHOT_DIR", monitor_snapshot_dir)
    monkeypatch.setattr(archive, "MONITOR_SNAPSHOT_MANIFEST_DIR", manifest_dir)
    monkeypatch.setattr(
        archive, "ANALYTICS_PARQUET_DIR", tmp_path / "analytics" / "parquet"
    )

    stats = archive.run(retention_days=1, today=date(2026, 4, 23), dry_run=True)

    assert stats["pipeline"]["scanned"] == 1
    assert stats["pipeline"]["verified"] == 0
    assert stats["pipeline"]["compressed"] == 0
    assert stats["skipped_unverified"] == 1


def test_run_compresses_verified_threshold_snapshots(tmp_path, monkeypatch):
    pipeline_dir = tmp_path / "pipeline_events"
    pipeline_dir.mkdir(parents=True, exist_ok=True)
    monitor_snapshot_dir = tmp_path / "monitor_snapshots"
    monitor_snapshot_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir = monitor_snapshot_dir / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    threshold_dir = tmp_path / "threshold_cycle"
    threshold_snapshot_dir = threshold_dir / "snapshots"
    threshold_snapshot_dir.mkdir(parents=True, exist_ok=True)
    backfill_dir = (
        threshold_dir / "date=2026-04-22" / "family=score65_74_recovery_probe"
    )
    backfill_dir.mkdir(parents=True, exist_ok=True)

    snapshot = (
        threshold_snapshot_dir / "pipeline_events_2026-04-22_20260422_161001.jsonl"
    )
    snapshot.write_text('{"stage":"sample"}\n', encoding="utf-8")
    (backfill_dir / "part-000001.jsonl").write_text(
        '{"stage":"sample"}\n', encoding="utf-8"
    )

    monkeypatch.setattr(archive, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(archive, "MONITOR_SNAPSHOT_DIR", monitor_snapshot_dir)
    monkeypatch.setattr(archive, "MONITOR_SNAPSHOT_MANIFEST_DIR", manifest_dir)
    monkeypatch.setattr(archive, "THRESHOLD_CYCLE_DIR", threshold_dir)
    monkeypatch.setattr(archive, "THRESHOLD_SNAPSHOT_DIR", threshold_snapshot_dir)

    stats = archive.run(retention_days=1, today=date(2026, 4, 23), dry_run=True)

    assert stats["threshold_snapshots"]["scanned"] == 1
    assert stats["threshold_snapshots"]["verified"] == 1
    assert stats["threshold_snapshots"]["compressed"] == 1
    assert stats["threshold_snapshots"]["saved_bytes"] == snapshot.stat().st_size


def test_run_compresses_canonical_context_and_streaming_consumer_reads_gzip(
    tmp_path, monkeypatch
):
    from src.engine.scalping import entry_context_intraday_probe as consumer

    canonical_dir = tmp_path / "canonical"
    canonical_dir.mkdir()
    raw_path = canonical_dir / "ai_canonical_context_candidates_2026-04-22.jsonl"
    row = {
        "schema": "ai_canonical_context_candidate_v1",
        "candidate_id": "candidate-1",
    }
    raw_path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    monkeypatch.setattr(archive, "POSTCLOSE_STATUS_DIR", tmp_path / "optional" / "postclose_status")
    monkeypatch.setattr(archive, "POSTCLOSE_CONTROLLER_DIR", tmp_path / "optional" / "postclose_controller")
    monkeypatch.setattr(archive, "CANONICAL_CONTEXT_DIR", canonical_dir)
    monkeypatch.setattr(consumer, "CONTEXT_CANDIDATE_DIR", canonical_dir)

    stats = archive.run(retention_days=1, today=date(2026, 4, 23), dry_run=False)

    gzip_path = raw_path.with_suffix(".jsonl.gz")
    assert not raw_path.exists()
    assert gzip_path.exists()
    assert stats["canonical_context"]["rows"] == 1
    assert list(consumer._load_context_candidates("2026-04-22")) == [row]


def test_run_compresses_manifested_producer_summary_and_consumer_reads_gzip(
    tmp_path, monkeypatch
):
    from src.engine import pipeline_event_summary as consumer

    summary_dir = tmp_path / "summaries"
    summary_dir.mkdir()
    raw_path = summary_dir / "pipeline_event_producer_summary_2026-04-22.jsonl"
    row = {"producer": "entry", "event_count": 3}
    raw_path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    manifest_path = (
        summary_dir / "pipeline_event_producer_summary_manifest_2026-04-22.json"
    )
    manifest_path.write_text(
        json.dumps(
            {
                "summary_path": str(raw_path),
                "summary_row_count": 1,
                "runtime_effect": False,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(archive, "PIPELINE_SUMMARY_DIR", summary_dir)

    stats = archive.run(retention_days=1, today=date(2026, 4, 23), dry_run=False)

    assert stats["pipeline_summaries"]["rows"] == 1
    assert consumer._load_summary_rows(raw_path) == [row]






def test_run_keeps_incomplete_threshold_partition_plain(tmp_path, monkeypatch):
    threshold_dir = tmp_path / "threshold_cycle"
    family_dir = threshold_dir / "date=2026-04-22" / "family=sample"
    family_dir.mkdir(parents=True)
    raw_path = family_dir / "part-000001.jsonl"
    raw_path.write_text('{"family":"sample"}\n', encoding="utf-8")
    monkeypatch.setattr(archive, "THRESHOLD_CYCLE_DIR", threshold_dir)
    monkeypatch.setattr(archive, "THRESHOLD_SNAPSHOT_DIR", threshold_dir / "snapshots")

    stats = archive.run(retention_days=1, today=date(2026, 5, 23), dry_run=False)

    assert stats["threshold_partitions"]["compressed"] == 0
    assert stats["skipped_unverified"] == 1
    assert raw_path.exists()
    assert not raw_path.with_suffix(".jsonl.gz").exists()


def test_threshold_partition_expected_rows_uses_full_prior_part_and_tail_count():
    checkpoint = {"partitions": {"sample": {"part": 2, "line_count": 17}}}
    family_dir = archive.THRESHOLD_CYCLE_DIR / "family=sample"

    assert (
        archive._threshold_partition_expected_rows(
            checkpoint, family_dir / "part-000001.jsonl"
        )
        == archive.THRESHOLD_PARTITION_MAX_ROWS
    )
    assert (
        archive._threshold_partition_expected_rows(
            checkpoint, family_dir / "part-000002.jsonl"
        )
        == 17
    )


@pytest.mark.parametrize('native_state', ['running', 'failed', 'succeeded'])
def test_archive_preserves_postclose_inputs_through_next_policy_day(tmp_path, monkeypatch, native_state):
    day = date(2026, 10, 2)
    pipeline = tmp_path / 'pipeline'
    snapshots = tmp_path / 'snapshots'
    pipeline.mkdir()
    snapshots.mkdir()
    raw = pipeline / 'pipeline_events_2026-10-02.jsonl'
    snapshot = snapshots / 'holding_exit_observation_2026-10-02.json'
    raw.write_text('{}\n')
    snapshot.write_text('{}')
    archive.POSTCLOSE_STATUS_DIR.mkdir(parents=True)
    (archive.POSTCLOSE_STATUS_DIR / 'threshold_cycle_postclose_2026-10-02.status.json').write_text(
        json.dumps({'target_date': day.isoformat(), 'status': native_state, 'exit_code': 0}))
    monkeypatch.setattr(archive, 'PIPELINE_EVENTS_DIR', pipeline)
    monkeypatch.setattr(archive, 'MONITOR_SNAPSHOT_DIR', snapshots)
    monkeypatch.setattr(archive, '_parquet_partition_exists', lambda *a: pytest.fail('protected source cannot reach ingestion/archive'))
    for when in (day, date(2026, 10, 6)):
        result = archive.run(retention_days=0, today=when, dry_run=False)
        assert result['skipped_postclose_protected'] == 2
        assert result['pipeline']['compressed'] == result['snapshots']['compressed'] == 0
        assert raw.read_text() == '{}\n' and snapshot.read_text() == '{}'


def test_archive_requires_whole_controller_after_policy_day(monkeypatch):
    from src.engine.automation import postclose_done_controller as controller
    monkeypatch.setattr(controller, 'done_terminal_receipt_issues', lambda *a, **kw: [])
    day = date(2026, 10, 2)
    archive.POSTCLOSE_STATUS_DIR.mkdir(parents=True)
    archive.POSTCLOSE_CONTROLLER_DIR.mkdir(parents=True)
    (archive.POSTCLOSE_STATUS_DIR / 'threshold_cycle_postclose_2026-10-02.status.json').write_text(
        json.dumps({'target_date': day.isoformat(), 'status': 'succeeded', 'exit_code': 0}))
    path = archive.POSTCLOSE_CONTROLLER_DIR / 'postclose_done_controller_2026-10-02.json'
    for state, whole in [('summary_verified', False), ('done', False), ('done', True)]:
        path.write_text(json.dumps({'date': day.isoformat(), 'status': state, 'whole_native_chain_done_claimed': whole}))
        reason = archive._postclose_source_protection(day, date(2026, 10, 7))
        assert (reason is None) is (state == 'done' and whole)


@pytest.mark.parametrize('payload', ['{', '[]', '{"target_date": "2026-09-30", "status": "succeeded", "exit_code": 0}'])
def test_archive_invalid_native_custody_receipt_fails_closed(payload):
    archive.POSTCLOSE_STATUS_DIR.mkdir(parents=True)
    (archive.POSTCLOSE_STATUS_DIR / 'threshold_cycle_postclose_2026-10-02.status.json').write_text(payload)
    assert archive._postclose_source_protection(date(2026, 10, 2), date(2026, 10, 7)) is not None


def test_archive_rejects_unverified_controller_done_claim(monkeypatch):
    from src.engine.automation import postclose_done_controller as controller
    monkeypatch.setattr(controller, 'done_terminal_receipt_issues', lambda *a, **kw: ['controller_verification_attempt_missing_or_invalid'])
    archive.POSTCLOSE_STATUS_DIR.mkdir(parents=True)
    archive.POSTCLOSE_CONTROLLER_DIR.mkdir(parents=True)
    (archive.POSTCLOSE_STATUS_DIR / 'threshold_cycle_postclose_2026-10-02.status.json').write_text(
        json.dumps({'target_date': '2026-10-02', 'status': 'succeeded', 'exit_code': 0}))
    (archive.POSTCLOSE_CONTROLLER_DIR / 'postclose_done_controller_2026-10-02.json').write_text(
        json.dumps({'date': '2026-10-02', 'status': 'done', 'whole_native_chain_done_claimed': True}))
    assert archive._postclose_source_protection(date(2026, 10, 2), date(2026, 10, 7)) == 'postclose_controller_receipt_invalid'


def test_archive_broken_native_status_symlink_fails_closed(tmp_path):
    archive.POSTCLOSE_STATUS_DIR.mkdir(parents=True)
    (archive.POSTCLOSE_STATUS_DIR / 'threshold_cycle_postclose_2026-10-02.status.json').symlink_to(tmp_path / 'missing_status')
    assert archive._postclose_source_protection(date(2026, 10, 2), date(2026, 10, 7)) == 'postclose_status_untrusted'
