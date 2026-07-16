from __future__ import annotations

import gzip
import os
import json
import subprocess
import time
from pathlib import Path


def test_log_rotation_cleanup_rotates_active_cron_log(tmp_path):
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    log_dir.mkdir(parents=True)
    active_log = log_dir / "threshold_cycle_postclose_cron.log"
    active_log.write_text("x" * 128, encoding="utf-8")

    env = os.environ.copy()
    env.update(
        {
            "PROJECT_DIR": str(project_root),
            "LOG_ROTATION_ACTIVE_MAX_BYTES": "64",
            "LOG_ROTATION_BACKUP_COUNT": "2",
            "TARGET_DATE": "2026-05-22",
        }
    )

    result = subprocess.run(
        ["bash", "deploy/run_logs_rotation_cleanup_cron.sh", "7"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )

    assert "active_rotated=1" in result.stdout
    assert active_log.read_text(encoding="utf-8") == ""
    assert (log_dir / "threshold_cycle_postclose_cron.log.1").read_text(
        encoding="utf-8"
    ) == "x" * 128


def test_log_rotation_cleanup_shifts_numeric_backups(tmp_path):
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    log_dir.mkdir(parents=True)
    active_log = log_dir / "run_error_detection_cron.log"
    active_log.write_text("new" * 64, encoding="utf-8")
    (log_dir / "run_error_detection_cron.log.1").write_text("old1", encoding="utf-8")

    env = os.environ.copy()
    env.update(
        {
            "PROJECT_DIR": str(project_root),
            "LOG_ROTATION_ACTIVE_MAX_BYTES": "64",
            "LOG_ROTATION_BACKUP_COUNT": "2",
            "TARGET_DATE": "2026-05-22",
        }
    )

    subprocess.run(
        ["bash", "deploy/run_logs_rotation_cleanup_cron.sh", "7"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )

    assert active_log.read_text(encoding="utf-8") == ""
    assert (log_dir / "run_error_detection_cron.log.1").read_text(
        encoding="utf-8"
    ) == "new" * 64
    assert not (log_dir / "run_error_detection_cron.log.2").exists()
    with gzip.open(
        log_dir / "run_error_detection_cron.log.2.gz", "rt", encoding="utf-8"
    ) as handle:
        assert handle.read() == "old1"


def test_log_rotation_cleanup_compresses_older_rotated_logs_and_shifts_gzip_slots(
    tmp_path,
):
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    log_dir.mkdir(parents=True)
    active_log = log_dir / "threshold_cycle_postclose_cron.log"
    active_log.write_text("new" * 64, encoding="utf-8")
    (log_dir / "threshold_cycle_postclose_cron.log.1").write_text(
        "old1", encoding="utf-8"
    )
    (log_dir / "threshold_cycle_postclose_cron.log.2.gz").write_bytes(b"old2-gz")

    env = os.environ.copy()
    env.update(
        {
            "PROJECT_DIR": str(project_root),
            "LOG_ROTATION_ACTIVE_MAX_BYTES": "64",
            "LOG_ROTATION_BACKUP_COUNT": "3",
            "LOG_ROTATION_COMPRESS_MIN_INDEX": "2",
            "TARGET_DATE": "2026-05-22",
        }
    )

    result = subprocess.run(
        ["bash", "deploy/run_logs_rotation_cleanup_cron.sh", "7"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )

    assert active_log.read_text(encoding="utf-8") == ""
    assert (log_dir / "threshold_cycle_postclose_cron.log.1").read_text(
        encoding="utf-8"
    ) == "new" * 64
    assert not (log_dir / "threshold_cycle_postclose_cron.log.2").exists()
    assert (log_dir / "threshold_cycle_postclose_cron.log.2.gz").exists()
    assert (
        log_dir / "threshold_cycle_postclose_cron.log.3.gz"
    ).read_bytes() == b"old2-gz"
    assert "archive_compressed=1" in result.stdout


def test_log_rotation_cleanup_prunes_rotated_logs_beyond_backup_limit(tmp_path):
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    log_dir.mkdir(parents=True)
    active_log = log_dir / "run_error_detection_cron.log"
    active_log.write_text("new" * 64, encoding="utf-8")
    (log_dir / "run_error_detection_cron.log.1").write_text("old1", encoding="utf-8")
    (log_dir / "run_error_detection_cron.log.2.gz").write_bytes(b"old2")
    (log_dir / "run_error_detection_cron.log.3.gz").write_bytes(b"old3")

    env = os.environ.copy()
    env.update(
        {
            "PROJECT_DIR": str(project_root),
            "LOG_ROTATION_ACTIVE_MAX_BYTES": "64",
            "LOG_ROTATION_BACKUP_COUNT": "2",
            "TARGET_DATE": "2026-05-22",
        }
    )

    result = subprocess.run(
        ["bash", "deploy/run_logs_rotation_cleanup_cron.sh", "7"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )

    assert (log_dir / "run_error_detection_cron.log.1").read_text(
        encoding="utf-8"
    ) == "new" * 64
    assert (log_dir / "run_error_detection_cron.log.2.gz").exists()
    assert not (log_dir / "run_error_detection_cron.log.3.gz").exists()
    assert "archive_pruned_to_backup_limit=1" in result.stdout


def test_log_rotation_cleanup_prunes_old_system_metric_samples(tmp_path):
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    log_dir.mkdir(parents=True)
    sample_path = log_dir / "system_metric_samples.jsonl"
    old_sample = {"ts": "2000-01-01T00:00:00+09:00", "epoch": 1}
    new_sample = {"ts": "2999-01-01T00:00:00+09:00", "epoch": 2}
    sample_path.write_text(
        json.dumps(old_sample) + "\n" + json.dumps(new_sample) + "\n",
        encoding="utf-8",
    )

    env = os.environ.copy()
    env.update({"PROJECT_DIR": str(project_root), "TARGET_DATE": "2026-05-22"})

    result = subprocess.run(
        ["bash", "deploy/run_logs_rotation_cleanup_cron.sh", "7"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )

    lines = sample_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["epoch"] == 2
    assert "system_metric_pruned=1" in result.stdout


def test_log_rotation_cleanup_prunes_archived_and_stale_active_logs(tmp_path):
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    log_dir.mkdir(parents=True)
    stale_active = log_dir / "run_panic_buying.log"
    fresh_active = log_dir / "run_error_detection.log"
    old_archive = log_dir / "bot_history.log.2026-05-01"
    old_archive_gz = log_dir / "threshold_cycle_postclose_cron.log.1.gz"
    fresh_archive = log_dir / "bot_history.log.2026-05-31"
    for path in (
        stale_active,
        fresh_active,
        old_archive,
        old_archive_gz,
        fresh_archive,
    ):
        path.write_text("log", encoding="utf-8")

    now = time.time()
    old_active_ts = now - 15 * 86400
    old_archive_ts = now - 31 * 86400
    os.utime(stale_active, (old_active_ts, old_active_ts))
    os.utime(old_archive, (old_archive_ts, old_archive_ts))
    os.utime(old_archive_gz, (old_archive_ts, old_archive_ts))

    env = os.environ.copy()
    env.update(
        {
            "PROJECT_DIR": str(project_root),
            "LOG_ROTATION_ACTIVE_RETENTION_DAYS": "14",
            "TARGET_DATE": "2026-05-31",
        }
    )

    result = subprocess.run(
        ["bash", "deploy/run_logs_rotation_cleanup_cron.sh", "30"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )

    assert not stale_active.exists()
    assert fresh_active.exists()
    assert not old_archive.exists()
    assert not old_archive_gz.exists()
    assert fresh_archive.exists()
    assert "active_deleted=1" in result.stdout
    assert "archive_deleted=2" in result.stdout


def test_log_rotation_cleanup_prunes_old_raw_row_exclusion_backups_after_seven_days(
    tmp_path,
):
    project_root = tmp_path / "project"
    exclusion_dir = (
        project_root
        / "data"
        / "source_quality"
        / "raw_row_exclusion"
        / "2026-05-22_20260522T101010000000+0900"
    )
    exclusion_dir.mkdir(parents=True)
    backup_path = exclusion_dir / "pipeline_events_2026-05-22.jsonl.gz"
    backup_path.write_bytes(b"gzip-placeholder")
    manifest_path = exclusion_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps({"backup_path": str(backup_path)}, ensure_ascii=False),
        encoding="utf-8",
    )

    now = time.time()
    old_ts = now - 8 * 86400
    os.utime(backup_path, (old_ts, old_ts))

    env = os.environ.copy()
    env.update(
        {
            "PROJECT_DIR": str(project_root),
            "TARGET_DATE": "2026-05-31",
        }
    )

    result = subprocess.run(
        ["bash", "deploy/run_logs_rotation_cleanup_cron.sh", "30"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )

    assert not backup_path.exists()
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["backup_path"] is None
    assert manifest["backup_retention_expired"] is True
    assert manifest["backup_deleted_at"]
    assert "raw_row_exclusion_backup_retention_days=7" in result.stdout
    assert "raw_row_exclusion_backup_deleted=1" in result.stdout
