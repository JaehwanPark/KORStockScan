import json
from datetime import date

from src.engine import compress_db_backfilled_files as archive


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
