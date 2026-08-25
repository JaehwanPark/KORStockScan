from __future__ import annotations

import fcntl
import gzip
import hashlib
import os
import json
import shutil
import subprocess
import time
from pathlib import Path

import pytest


def _generation_gzip(source: Path) -> Path:
    base_name, numeric_slot = source.name.rsplit(".", 1)
    assert numeric_slot.isdigit()
    matches = sorted(source.parent.glob(f"{base_name}.generation_*.gz"))
    assert len(matches) == 1
    return matches[0]


def test_log_rotation_cleanup_defers_active_rotation_preserves_open_backups_and_runs_peers(
    tmp_path,
):
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    micro_source = (
        project_root
        / "data"
        / "observations"
        / "scalp_micro_reversion_forward"
        / "trade_date=2026-05-21"
        / "venue=KRX"
        / "session=KRX_REGULAR"
        / "market_stream.jsonl"
    )
    log_dir.mkdir(parents=True)
    micro_source.parent.mkdir(parents=True)
    active_log = log_dir / "threshold_cycle_postclose_cron.log"
    source_backup = log_dir / "threshold_cycle_postclose_cron.log.1"
    open_backup = log_dir / "threshold_cycle_postclose_cron.log.2"
    peer_archive = log_dir / "closed_peer.log.3"
    active_payload = "active" * 32
    active_log.write_text(active_payload, encoding="utf-8")
    source_backup.write_text("source-backup", encoding="utf-8")
    open_backup.write_text("open-backup", encoding="utf-8")
    peer_archive.write_text("closed-peer", encoding="utf-8")
    micro_source.write_text('{"schema":"stream","series_sequence":1}\n')
    original_inodes = {
        path: path.stat().st_ino for path in (active_log, source_backup, open_backup)
    }

    env = os.environ.copy()
    env.update(
        {
            "PROJECT_DIR": str(project_root),
            "LOG_ROTATION_ACTIVE_MAX_BYTES": "8",
            "LOG_ROTATION_BACKUP_COUNT": "4",
            "LOG_ROTATION_COMPRESS_MIN_INDEX": "3",
            "LOG_ROTATION_ARCHIVE_QUIET_SECONDS": "0",
            "TARGET_DATE": "2026-05-22",
        }
    )
    open_handle = open_backup.open("rb")
    try:
        result = subprocess.run(
            ["bash", "deploy/run_logs_rotation_cleanup_cron.sh", "7"],
            cwd=Path(__file__).resolve().parents[2],
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

        assert result.returncode == 0
        assert active_log.read_text(encoding="utf-8") == active_payload
        assert source_backup.read_text(encoding="utf-8") == "source-backup"
        assert open_backup.read_text(encoding="utf-8") == "open-backup"
        for path, inode in original_inodes.items():
            assert path.stat().st_ino == inode
        assert os.fstat(open_handle.fileno()).st_nlink == 1
        assert peer_archive.exists()
        with gzip.open(
            _generation_gzip(peer_archive), "rt", encoding="utf-8"
        ) as handle:
            assert handle.read() == "closed-peer"
        assert not micro_source.exists()
        assert micro_source.with_suffix(".jsonl.gz").exists()
        assert "status=disabled_pending_writer_owner" in result.stdout
        assert "numeric_rename_shift_prune_disabled=true" in result.stdout
        assert "archive_source_unlink_deferred=1" in result.stdout
        assert "active_rotation_deferred=1" in result.stdout
        assert "active_rotated=0" in result.stdout
        assert "archive_compressed=1" in result.stdout
        assert "micro_reversion_storage_status=pass" in result.stdout
        assert "writer_defer_escalated=0" in result.stdout
        assert "[DONE] log_rotation_cleanup" in result.stdout
    finally:
        open_handle.close()


def test_log_rotation_cleanup_ignores_unsafe_active_rotation_opt_in(tmp_path):
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    log_dir.mkdir(parents=True)
    active_log = log_dir / "run_error_detection_cron.log"
    backup = log_dir / "run_error_detection_cron.log.1"
    active_payload = "new" * 64
    active_log.write_text(active_payload, encoding="utf-8")
    backup.write_text("old1", encoding="utf-8")
    original_inodes = (active_log.stat().st_ino, backup.stat().st_ino)

    env = os.environ.copy()
    env.update(
        {
            "PROJECT_DIR": str(project_root),
            "LOG_ROTATION_ACTIVE_MAX_BYTES": "64",
            "LOG_ROTATION_BACKUP_COUNT": "2",
            "LOG_ROTATION_COMPRESS_MIN_INDEX": "99",
            "LOG_ROTATION_ARCHIVE_QUIET_SECONDS": "0",
            "LOG_ROTATION_ACTIVE_ROTATION_ENABLED": "true",
            "DATA_MAINTENANCE_ENABLED": "false",
            "TARGET_DATE": "2026-05-22",
        }
    )

    result = subprocess.run(
        ["bash", "deploy/run_logs_rotation_cleanup_cron.sh", "7"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert active_log.read_text(encoding="utf-8") == active_payload
    assert backup.read_text(encoding="utf-8") == "old1"
    assert (active_log.stat().st_ino, backup.stat().st_ino) == original_inodes
    assert not (log_dir / "run_error_detection_cron.log.2").exists()
    assert "active_rotation_status=disabled_pending_writer_owner" in result.stdout
    assert "status=deferred_writer_active" in result.stdout
    assert "active_rotation_deferred=1" in result.stdout
    assert "writer_defer_escalated=0" in result.stdout
    assert "[DONE] log_rotation_cleanup" in result.stdout
    assert "[LOG_ROTATE]" not in result.stdout


def test_log_rotation_cleanup_compresses_closed_archive_without_shifting_slots(
    tmp_path,
):
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    log_dir.mkdir(parents=True)
    active_log = log_dir / "threshold_cycle_postclose_cron.log"
    active_log.write_text("small", encoding="utf-8")
    (log_dir / "threshold_cycle_postclose_cron.log.1").write_text(
        "old1", encoding="utf-8"
    )
    slot_two = log_dir / "threshold_cycle_postclose_cron.log.2"
    slot_two.write_text("old2", encoding="utf-8")

    env = os.environ.copy()
    env.update(
        {
            "PROJECT_DIR": str(project_root),
            "LOG_ROTATION_ACTIVE_MAX_BYTES": "4096",
            "LOG_ROTATION_BACKUP_COUNT": "3",
            "LOG_ROTATION_COMPRESS_MIN_INDEX": "2",
            "LOG_ROTATION_ARCHIVE_QUIET_SECONDS": "0",
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

    assert active_log.read_text(encoding="utf-8") == "small"
    assert (log_dir / "threshold_cycle_postclose_cron.log.1").read_text(
        encoding="utf-8"
    ) == "old1"
    assert slot_two.exists()
    with gzip.open(_generation_gzip(slot_two), "rt", encoding="utf-8") as handle:
        assert handle.read() == "old2"
    assert not (log_dir / "threshold_cycle_postclose_cron.log.3.gz").exists()
    assert "active_rotation_deferred=0" in result.stdout
    assert "active_rotated=0" in result.stdout
    assert "archive_compressed=1" in result.stdout
    assert "archive_source_unlink_deferred=1" in result.stdout


def test_log_rotation_cleanup_uses_proc_when_fuser_cannot_verify_open_archive(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    log_dir.mkdir(parents=True)
    archive = log_dir / "open_with_fuser_error.log.2"
    archive.write_text("held-open", encoding="utf-8")
    original_inode = archive.stat().st_ino
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_fuser = fake_bin / "fuser"
    fake_fuser.write_text("#!/usr/bin/env bash\nexit 1\n", encoding="utf-8")
    fake_fuser.chmod(0o755)
    env = os.environ.copy()
    env.update(
        {
            "PROJECT_DIR": str(project_root),
            "TARGET_DATE": "2026-05-22",
            "DATA_MAINTENANCE_ENABLED": "false",
            "MICRO_REVERSION_STORAGE_MAINTENANCE_ENABLED": "false",
            "LOG_ROTATION_BACKUP_COUNT": "4",
            "LOG_ROTATION_COMPRESS_MIN_INDEX": "2",
            "LOG_ROTATION_ARCHIVE_QUIET_SECONDS": "0",
            "PATH": f"{fake_bin}:{env['PATH']}",
        }
    )
    handle = archive.open("rb")
    try:
        result = subprocess.run(
            ["bash", "deploy/run_logs_rotation_cleanup_cron.sh", "30"],
            cwd=Path(__file__).resolve().parents[2],
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

        assert result.returncode == 0
        assert archive.stat().st_ino == original_inode
        assert archive.read_text(encoding="utf-8") == "held-open"
        assert os.fstat(handle.fileno()).st_nlink == 1
        assert not archive.with_suffix(".2.gz").exists()
        assert "status=deferred_writer_active reason=source_in_use" in result.stdout
        assert "archive_writer_active_deferred=1" in result.stdout
        assert "writer_defer_escalated=0" in result.stdout
        assert "[DONE] log_rotation_cleanup" in result.stdout
    finally:
        handle.close()


def test_log_rotation_cleanup_find_failure_is_visible_and_peer_lane_continues(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    archive = log_dir / "enumeration_blocked.log.2"
    micro_source = (
        project_root
        / "data"
        / "observations"
        / "scalp_micro_reversion_forward"
        / "trade_date=2026-05-21"
        / "venue=KRX"
        / "session=KRX_REGULAR"
        / "market_stream.jsonl"
    )
    log_dir.mkdir(parents=True)
    micro_source.parent.mkdir(parents=True)
    archive.write_text("enumeration-blocked", encoding="utf-8")
    micro_source.write_text('{"series_sequence":1}\n', encoding="utf-8")
    real_find = shutil.which("find")
    assert real_find is not None
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_find = fake_bin / "find"
    fake_find.write_text(
        "#!/usr/bin/env bash\n"
        'for arg in "$@"; do\n'
        '  if [[ "$arg" == "*.log.[0-9]*" ]]; then\n'
        "    exit 7\n"
        "  fi\n"
        "done\n"
        f'exec "{real_find}" "$@"\n',
        encoding="utf-8",
    )
    fake_find.chmod(0o755)
    env = os.environ.copy()
    env.update(
        {
            "PROJECT_DIR": str(project_root),
            "TARGET_DATE": "2026-05-22",
            "LOG_ROTATION_BACKUP_COUNT": "4",
            "LOG_ROTATION_COMPRESS_MIN_INDEX": "2",
            "LOG_ROTATION_ARCHIVE_QUIET_SECONDS": "0",
            "PATH": f"{fake_bin}:{env['PATH']}",
        }
    )

    result = subprocess.run(
        ["bash", "deploy/run_logs_rotation_cleanup_cron.sh", "30"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert archive.read_text(encoding="utf-8") == "enumeration-blocked"
    assert not archive.with_suffix(".2.gz").exists()
    assert not micro_source.exists()
    assert micro_source.with_suffix(".jsonl.gz").exists()
    assert "[CLEANUP_ENUMERATION_FAIL] lane=archive_compression_census" in (
        result.stdout
    )
    enumeration_counts = [
        int(token.removeprefix("find_enumeration_failures="))
        for token in result.stdout.split()
        if token.startswith("find_enumeration_failures=")
    ]
    assert enumeration_counts and min(enumeration_counts) > 0
    assert result.stdout.count("[FAIL] log_rotation_cleanup") == 1
    assert "[DONE] log_rotation_cleanup" not in result.stdout


def test_log_rotation_cleanup_does_not_prune_numeric_slots_beyond_backup_limit(
    tmp_path,
):
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    log_dir.mkdir(parents=True)
    active_log = log_dir / "run_error_detection_cron.log"
    active_log.write_text("small", encoding="utf-8")
    (log_dir / "run_error_detection_cron.log.1").write_text("old1", encoding="utf-8")
    slot_two = log_dir / "run_error_detection_cron.log.2.gz"
    slot_three = log_dir / "run_error_detection_cron.log.3.gz"
    slot_two.write_bytes(gzip.compress(b"old2", mtime=0))
    slot_three.write_bytes(gzip.compress(b"old3", mtime=0))

    env = os.environ.copy()
    env.update(
        {
            "PROJECT_DIR": str(project_root),
            "LOG_ROTATION_ACTIVE_MAX_BYTES": "4096",
            "LOG_ROTATION_BACKUP_COUNT": "2",
            "LOG_ROTATION_COMPRESS_MIN_INDEX": "99",
            "LOG_ROTATION_ARCHIVE_QUIET_SECONDS": "0",
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

    assert active_log.read_text(encoding="utf-8") == "small"
    assert (log_dir / "run_error_detection_cron.log.1").read_text(
        encoding="utf-8"
    ) == "old1"
    assert slot_two.exists()
    assert slot_three.exists()
    assert "archive_pruned_to_backup_limit=0" in result.stdout


def test_log_rotation_cleanup_defers_all_unknown_writer_retention_candidates(
    tmp_path,
):
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    log_dir.mkdir(parents=True)
    open_active = log_dir / "run_open_retention.log"
    open_archive = log_dir / "orphan_open.log.2.gz"
    peer_archive = log_dir / "closed_peer.log.4.gz"
    open_active.write_text("open-active", encoding="utf-8")
    open_archive.write_bytes(gzip.compress(b"open-archive", mtime=0))
    peer_archive.write_bytes(gzip.compress(b"closed-peer", mtime=0))
    old_ts = time.time() - 40 * 86400
    for path in (open_active, open_archive, peer_archive):
        os.utime(path, (old_ts, old_ts))

    env = os.environ.copy()
    env.update(
        {
            "PROJECT_DIR": str(project_root),
            "TARGET_DATE": "2026-05-22",
            "DATA_MAINTENANCE_ENABLED": "false",
            "LOG_ROTATION_ACTIVE_MAX_BYTES": "4096",
            "LOG_ROTATION_COMPRESS_MIN_INDEX": "99",
            "LOG_ROTATION_ARCHIVE_QUIET_SECONDS": "0",
        }
    )
    active_handle = open_active.open("rb")
    archive_handle = open_archive.open("rb")
    original_inodes = (
        os.fstat(active_handle.fileno()).st_ino,
        os.fstat(archive_handle.fileno()).st_ino,
    )
    try:
        result = subprocess.run(
            ["bash", "deploy/run_logs_rotation_cleanup_cron.sh", "30"],
            cwd=Path(__file__).resolve().parents[2],
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

        assert result.returncode == 0
        assert open_active.stat().st_ino == original_inodes[0]
        assert open_archive.stat().st_ino == original_inodes[1]
        assert os.fstat(active_handle.fileno()).st_nlink == 1
        assert os.fstat(archive_handle.fileno()).st_nlink == 1
        assert peer_archive.exists()
        assert "active_retention_deferred=1" in result.stdout
        assert "archive_retention_deferred=2" in result.stdout
        assert "active_deleted=0" in result.stdout
        assert "archive_deleted=0" in result.stdout
        assert "[DONE] log_rotation_cleanup" in result.stdout
    finally:
        active_handle.close()
        archive_handle.close()


def test_log_rotation_cleanup_never_calls_rm_for_deferred_archive_retention(
    tmp_path,
):
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    log_dir.mkdir(parents=True)
    failed_archive = log_dir / "a_rm_failure.log.4.gz"
    peer_archive = log_dir / "z_rm_peer.log.5.gz"
    failed_payload = gzip.compress(b"rm-failure", mtime=0)
    failed_archive.write_bytes(failed_payload)
    peer_archive.write_bytes(gzip.compress(b"rm-peer", mtime=0))
    old_ts = time.time() - 40 * 86400
    os.utime(failed_archive, (old_ts, old_ts))
    os.utime(peer_archive, (old_ts, old_ts))

    real_rm = shutil.which("rm")
    assert real_rm is not None
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_rm = fake_bin / "rm"
    fake_rm.write_text(
        "#!/usr/bin/env bash\n"
        'for path in "$@"; do\n'
        '  if [[ "$path" == *"a_rm_failure.log.4.gz" ]]; then\n'
        "    exit 1\n"
        "  fi\n"
        "done\n"
        f'exec "{real_rm}" "$@"\n',
        encoding="utf-8",
    )
    fake_rm.chmod(0o755)
    env = os.environ.copy()
    env.update(
        {
            "PROJECT_DIR": str(project_root),
            "TARGET_DATE": "2026-05-22",
            "DATA_MAINTENANCE_ENABLED": "false",
            "LOG_ROTATION_ACTIVE_MAX_BYTES": "4096",
            "LOG_ROTATION_COMPRESS_MIN_INDEX": "99",
            "LOG_ROTATION_ARCHIVE_QUIET_SECONDS": "0",
            "PATH": f"{fake_bin}:{env['PATH']}",
        }
    )
    result = subprocess.run(
        ["bash", "deploy/run_logs_rotation_cleanup_cron.sh", "30"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert failed_archive.read_bytes() == failed_payload
    assert peer_archive.exists()
    assert "archive_retention_deferred=2" in result.stdout
    assert "archive_retention_failures=0" in result.stdout
    assert "archive_deleted=0" in result.stdout
    assert "[DONE] log_rotation_cleanup" in result.stdout


def test_log_rotation_cleanup_preserves_open_micro_source_and_compresses_peer(
    tmp_path,
):
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    micro_source = (
        project_root
        / "data"
        / "observations"
        / "scalp_micro_reversion_forward"
        / "trade_date=2026-05-21"
        / "venue=KRX"
        / "session=KRX_REGULAR"
        / "market_stream.jsonl"
    )
    peer_archive = log_dir / "micro_failure_peer.log.3"
    log_dir.mkdir(parents=True)
    micro_source.parent.mkdir(parents=True)
    micro_source.write_text('{"value":1}\n', encoding="utf-8")
    peer_archive.write_text("peer", encoding="utf-8")
    env = os.environ.copy()
    env.update(
        {
            "PROJECT_DIR": str(project_root),
            "TARGET_DATE": "2026-05-22",
            "LOG_ROTATION_ACTIVE_MAX_BYTES": "4096",
            "LOG_ROTATION_BACKUP_COUNT": "4",
            "LOG_ROTATION_COMPRESS_MIN_INDEX": "3",
            "LOG_ROTATION_ARCHIVE_QUIET_SECONDS": "0",
        }
    )
    source_handle = micro_source.open("a+", encoding="utf-8")
    source_inode = os.fstat(source_handle.fileno()).st_ino
    try:
        result = subprocess.run(
            ["bash", "deploy/run_logs_rotation_cleanup_cron.sh", "30"],
            cwd=Path(__file__).resolve().parents[2],
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

        assert result.returncode == 1
        assert micro_source.stat().st_ino == source_inode
        assert os.fstat(source_handle.fileno()).st_nlink == 1
        assert not micro_source.with_suffix(".jsonl.gz").exists()
        source_handle.write('{"value":2}\n')
        source_handle.flush()
        os.fsync(source_handle.fileno())
        assert peer_archive.exists()
        with gzip.open(
            _generation_gzip(peer_archive), "rt", encoding="utf-8"
        ) as handle:
            assert handle.read() == "peer"
        assert "[MICRO_REVERSION_STORAGE_FAIL]" in result.stdout
        assert "micro_reversion_storage_status=partial_failure" in result.stdout
        assert "micro_reversion_storage_partition_failures=1" in result.stdout
        assert "micro_reversion_storage_failures=1" in result.stdout
        assert "archive_compressed=1" in result.stdout
        assert "archive_source_unlink_deferred=1" in result.stdout
        assert result.stdout.count("[FAIL] log_rotation_cleanup") == 1
        assert "[DONE] log_rotation_cleanup" not in result.stdout
    finally:
        source_handle.close()
    assert micro_source.read_text(encoding="utf-8") == '{"value":1}\n{"value":2}\n'


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


def test_log_rotation_cleanup_quarantines_malformed_system_metric_line(tmp_path):
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    log_dir.mkdir(parents=True)
    sample_path = log_dir / "system_metric_samples.jsonl"
    valid = {"ts": "2999-01-01T00:00:00+09:00", "epoch": 2}
    sample_path.write_text(
        '{"ts":"broken"\n' + json.dumps(valid) + "\n", encoding="utf-8"
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

    assert [json.loads(line) for line in sample_path.read_text().splitlines()] == [
        valid
    ]
    quarantine_path = log_dir / "system_metric_samples.invalid.jsonl"
    quarantine = json.loads(quarantine_path.read_text().splitlines()[0])
    assert quarantine["raw_sha256"]
    assert quarantine["raw_line"] == '{"ts":"broken"'
    assert "system_metric_invalid=1" in result.stdout


def test_log_rotation_cleanup_verifies_sentinel_and_snapshot_gzip(tmp_path):
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    sentinel_dir = project_root / "data" / "runtime" / "sentinel_event_cache"
    snapshot_dir = project_root / "data" / "threshold_cycle" / "snapshots"
    log_dir.mkdir(parents=True)
    sentinel_dir.mkdir(parents=True)
    snapshot_dir.mkdir(parents=True)
    sentinel = sentinel_dir / "buy_funnel_events_2026-05-21.jsonl"
    snapshot = snapshot_dir / "pipeline_events_2026-05-21_20260521_200000.jsonl"
    sentinel_payload = '{"event":"sentinel"}\n'
    snapshot_payload = '{"event":"snapshot"}\n'
    sentinel.write_text(sentinel_payload, encoding="utf-8")
    snapshot.write_text(snapshot_payload, encoding="utf-8")
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

    assert sentinel.exists()
    assert snapshot.exists()
    with gzip.open(f"{sentinel}.gz", "rt", encoding="utf-8") as handle:
        assert handle.read() == sentinel_payload
    with gzip.open(f"{snapshot}.gz", "rt", encoding="utf-8") as handle:
        assert handle.read() == snapshot_payload
    assert "sentinel_compressed=1" in result.stdout
    assert "snapshot_compressed=1" in result.stdout
    assert "sentinel_verified_existing_source_preserved=0" in result.stdout
    assert "snapshot_verified_existing_source_preserved=0" in result.stdout
    assert "data_source_unlink_deferred=2" in result.stdout
    assert "compression_verify_failures=0" in result.stdout

    sentinel_gzip = Path(f"{sentinel}.gz")
    snapshot_gzip = Path(f"{snapshot}.gz")
    sentinel_gzip_before = sentinel_gzip.read_bytes()
    snapshot_gzip_before = snapshot_gzip.read_bytes()
    repeated = subprocess.run(
        ["bash", "deploy/run_logs_rotation_cleanup_cron.sh", "7"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )

    assert sentinel_gzip.read_bytes() == sentinel_gzip_before
    assert snapshot_gzip.read_bytes() == snapshot_gzip_before
    assert "sentinel_compressed=0" in repeated.stdout
    assert "snapshot_compressed=0" in repeated.stdout
    assert "sentinel_verified_existing_source_preserved=1" in repeated.stdout
    assert "snapshot_verified_existing_source_preserved=1" in repeated.stdout


def test_log_rotation_cleanup_maintains_bounded_micro_reversion_storage(tmp_path):
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    source = (
        project_root
        / "data"
        / "observations"
        / "scalp_micro_reversion_forward"
        / "trade_date=2026-05-21"
        / "venue=KRX"
        / "session=KRX_REGULAR"
        / "market_stream.jsonl"
    )
    log_dir.mkdir(parents=True)
    source.parent.mkdir(parents=True)
    original = '{"schema":"stream","series_sequence":1}\n'
    source.write_text(original, encoding="utf-8")
    env = os.environ.copy()
    env.update(
        {
            "PROJECT_DIR": str(project_root),
            "PYTHON_BIN": str(Path(__file__).resolve().parents[2] / ".venv/bin/python"),
            "TARGET_DATE": "2026-05-22",
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

    compressed = source.with_suffix(".jsonl.gz")
    assert not source.exists()
    with gzip.open(compressed, "rt", encoding="utf-8") as handle:
        assert handle.read() == original
    assert "micro_reversion_storage_status=pass" in result.stdout
    assert "micro_reversion_storage_actions=1" in result.stdout
    assert "micro_reversion_storage_compressed=1" in result.stdout
    assert "micro_reversion_storage_purged=0" in result.stdout
    assert "micro_reversion_storage_purge_enabled=false" in result.stdout
    assert (
        "micro_reversion_storage_purge_status=disabled_no_deletion_authority"
        in result.stdout
    )


def test_log_rotation_cleanup_defers_conflicting_gzip_and_finishes_micro_lane(
    tmp_path,
):
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    archive = log_dir / "kiwoom_utils_info.log.9"
    existing_gzip = archive.with_suffix(".9.gz")
    stable_peer = log_dir / "stable_peer.log.2"
    micro_source = (
        project_root
        / "data"
        / "observations"
        / "scalp_micro_reversion_forward"
        / "trade_date=2026-05-21"
        / "venue=KRX"
        / "session=KRX_REGULAR"
        / "market_stream.jsonl"
    )
    stale_tmp = project_root / "tmp" / "workorder-stale"
    log_dir.mkdir(parents=True)
    micro_source.parent.mkdir(parents=True)
    stale_tmp.mkdir(parents=True)
    original_archive = "new-archive-generation\n"
    original_existing_gzip = gzip.compress(b"previous-verified-generation\n", mtime=0)
    archive.write_text(original_archive, encoding="utf-8")
    existing_gzip.write_bytes(original_existing_gzip)
    stable_peer.write_text("stable-peer\n", encoding="utf-8")
    old_ts = time.time() - 40 * 86400
    os.utime(archive, (old_ts, old_ts))
    os.utime(existing_gzip, (old_ts, old_ts))
    os.utime(stable_peer, (old_ts, old_ts))
    os.utime(stale_tmp, (old_ts, old_ts))
    micro_source.write_text('{"schema":"stream","series_sequence":1}\n')

    env = os.environ.copy()
    env.update(
        {
            "PROJECT_DIR": str(project_root),
            "PYTHON_BIN": str(Path(__file__).resolve().parents[2] / ".venv/bin/python"),
            "TARGET_DATE": "2026-05-22",
        }
    )
    result = subprocess.run(
        ["bash", "deploy/run_logs_rotation_cleanup_cron.sh", "30"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert archive.read_text(encoding="utf-8") == original_archive
    assert existing_gzip.read_bytes() == original_existing_gzip
    generation_gzip = _generation_gzip(archive)
    with gzip.open(generation_gzip, "rt", encoding="utf-8") as handle:
        assert handle.read() == original_archive
    assert stable_peer.exists()
    with gzip.open(_generation_gzip(stable_peer), "rt", encoding="utf-8") as handle:
        assert handle.read() == "stable-peer\n"
    assert not list(log_dir.glob("*.tmp.*"))
    assert not micro_source.exists()
    assert micro_source.with_suffix(".jsonl.gz").exists()
    assert not stale_tmp.exists()
    assert "micro_reversion_storage_status=pass" in result.stdout
    assert "archive_compressed=2" in result.stdout
    assert "archive_generation_compressed=2" in result.stdout
    assert "archive_compression_failures=0" in result.stdout
    assert "archive_deleted=0" in result.stdout
    assert "[DONE] log_rotation_cleanup" in result.stdout


def test_log_rotation_cleanup_verifies_matching_gzip_and_preserves_source(tmp_path):
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    archive = log_dir / "stable.log.2"
    existing_gzip = archive.with_suffix(".2.gz")
    log_dir.mkdir(parents=True)
    payload = b"same-verified-generation\n"
    original_gzip = gzip.compress(payload, mtime=0)
    archive.write_bytes(payload)
    existing_gzip.write_bytes(original_gzip)

    env = os.environ.copy()
    env.update(
        {
            "PROJECT_DIR": str(project_root),
            "TARGET_DATE": "2026-05-22",
            "LOG_ROTATION_ARCHIVE_QUIET_SECONDS": "0",
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

    assert archive.read_bytes() == payload
    assert existing_gzip.read_bytes() == original_gzip
    generation_gzip = _generation_gzip(archive)
    with gzip.open(generation_gzip, "rb") as handle:
        assert handle.read() == payload
    assert "archive_compressed=1" in result.stdout
    assert "archive_compression_finalized=0" in result.stdout
    assert "archive_generation_compressed=1" in result.stdout
    assert "archive_compression_failures=0" in result.stdout
    assert "archive_source_unlink_deferred=1" in result.stdout
    assert "[DONE] log_rotation_cleanup" in result.stdout


def test_log_rotation_cleanup_reuses_generation_across_numeric_slots(tmp_path):
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    slot_two = log_dir / "shared_identity.log.2"
    slot_three = log_dir / "shared_identity.log.3"
    log_dir.mkdir(parents=True)
    slot_two.write_text("same-generation\n", encoding="utf-8")
    slot_three.write_text("same-generation\n", encoding="utf-8")
    env = os.environ.copy()
    env.update(
        {
            "PROJECT_DIR": str(project_root),
            "TARGET_DATE": "2026-05-22",
            "DATA_MAINTENANCE_ENABLED": "false",
            "LOG_ROTATION_ARCHIVE_QUIET_SECONDS": "0",
        }
    )

    result = subprocess.run(
        ["bash", "deploy/run_logs_rotation_cleanup_cron.sh", "30"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert _generation_gzip(slot_two) == _generation_gzip(slot_three)
    assert "archive_generation_compressed=1" in result.stdout
    assert "archive_generation_verified=1" in result.stdout


def test_log_rotation_cleanup_reuses_verified_collision_generation(tmp_path):
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    archive = log_dir / "collision_retry.log.2"
    existing_gzip = archive.with_suffix(".2.gz")
    log_dir.mkdir(parents=True)
    source_payload = b"new-generation-awaiting-unlink\n"
    existing_gzip_bytes = gzip.compress(b"previous-generation\n", mtime=0)
    generation_hash = hashlib.sha256(source_payload).hexdigest()[:16]
    generation_gzip = archive.with_name(
        f"collision_retry.log.generation_{generation_hash}.gz"
    )
    generation_gzip_bytes = gzip.compress(source_payload, mtime=0)
    archive.write_bytes(source_payload)
    existing_gzip.write_bytes(existing_gzip_bytes)
    generation_gzip.write_bytes(generation_gzip_bytes)

    env = os.environ.copy()
    env.update(
        {
            "PROJECT_DIR": str(project_root),
            "TARGET_DATE": "2026-05-22",
            "LOG_ROTATION_ARCHIVE_QUIET_SECONDS": "0",
        }
    )
    result = subprocess.run(
        ["bash", "deploy/run_logs_rotation_cleanup_cron.sh", "30"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert archive.read_bytes() == source_payload
    assert existing_gzip.read_bytes() == existing_gzip_bytes
    assert generation_gzip.read_bytes() == generation_gzip_bytes
    assert "archive_compressed=0" in result.stdout
    assert "archive_compression_finalized=0" in result.stdout
    assert "archive_generation_verified=1" in result.stdout
    assert "archive_compression_failures=0" in result.stdout
    assert "[DONE] log_rotation_cleanup" in result.stdout


def test_log_rotation_cleanup_defers_recent_archive_then_compresses_next_archive(
    tmp_path,
):
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    recent_archive = log_dir / "a_recent.log.2"
    stable_archive = log_dir / "z_stable.log.3"
    log_dir.mkdir(parents=True)
    recent_archive.write_text("still-growing\n", encoding="utf-8")
    stable_archive.write_text("stable\n", encoding="utf-8")
    old_ts = time.time() - 3600
    os.utime(stable_archive, (old_ts, old_ts))

    env = os.environ.copy()
    env.update({"PROJECT_DIR": str(project_root), "TARGET_DATE": "2026-05-22"})
    result = subprocess.run(
        ["bash", "deploy/run_logs_rotation_cleanup_cron.sh", "30"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert recent_archive.read_text(encoding="utf-8") == "still-growing\n"
    assert not recent_archive.with_suffix(".2.gz").exists()
    assert stable_archive.exists()
    with gzip.open(_generation_gzip(stable_archive), "rt", encoding="utf-8") as handle:
        assert handle.read() == "stable\n"
    assert "status=deferred_writer_active reason=source_not_quiet" in result.stdout
    assert "archive_compressed=1" in result.stdout
    assert "archive_compression_failures=0" in result.stdout
    assert "archive_writer_active_deferred=1" in result.stdout
    assert "[LOG_CLEANUP]" in result.stdout
    assert "[DONE] log_rotation_cleanup" in result.stdout


def test_log_rotation_cleanup_escalates_only_after_repeated_writer_defer(tmp_path):
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    archive = log_dir / "writer_active.log.2"
    log_dir.mkdir(parents=True)
    archive.write_text("writer-active\n", encoding="utf-8")
    env = os.environ.copy()
    env.update(
        {
            "PROJECT_DIR": str(project_root),
            "TARGET_DATE": "2026-05-22",
            "DATA_MAINTENANCE_ENABLED": "false",
            "LOG_ROTATION_ARCHIVE_QUIET_SECONDS": "0",
            "LOG_ROTATION_WRITER_DEFER_FAILURE_THRESHOLD": "3",
        }
    )

    handle = archive.open("rb")
    try:
        results = [
            subprocess.run(
                ["bash", "deploy/run_logs_rotation_cleanup_cron.sh", "30"],
                cwd=Path(__file__).resolve().parents[2],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            for _ in range(3)
        ]
    finally:
        handle.close()

    assert [result.returncode for result in results] == [0, 0, 1]
    assert all("status=deferred_writer_active" in result.stdout for result in results)
    assert "writer_defer_max_consecutive=1" in results[0].stdout
    assert "writer_defer_max_consecutive=2" in results[1].stdout
    assert "[WRITER_DEFER_ESCALATED]" in results[2].stdout
    assert "writer_defer_escalated=1" in results[2].stdout
    assert results[2].stdout.count("[FAIL] log_rotation_cleanup") == 1
    state_payload = json.loads(
        (project_root / "tmp/log_rotation_cleanup_writer_defer_state.json").read_text(
            encoding="utf-8"
        )
    )
    assert list(state_payload["entries"]) == ["numeric_archive:writer_active.log"]
    assert next(iter(state_payload["entries"].values()))["observed_slot"] == (
        "writer_active.log.2"
    )


def test_log_rotation_cleanup_resets_writer_defer_after_stable_pass(tmp_path):
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    archive = log_dir / "writer_reset.log.2"
    log_dir.mkdir(parents=True)
    archive.write_text("writer-reset\n", encoding="utf-8")
    env = os.environ.copy()
    env.update(
        {
            "PROJECT_DIR": str(project_root),
            "TARGET_DATE": "2026-05-22",
            "DATA_MAINTENANCE_ENABLED": "false",
            "LOG_ROTATION_ARCHIVE_QUIET_SECONDS": "0",
            "LOG_ROTATION_WRITER_DEFER_FAILURE_THRESHOLD": "3",
        }
    )

    handle = archive.open("rb")
    try:
        first = subprocess.run(
            ["bash", "deploy/run_logs_rotation_cleanup_cron.sh", "30"],
            cwd=Path(__file__).resolve().parents[2],
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
    finally:
        handle.close()
    stable = subprocess.run(
        ["bash", "deploy/run_logs_rotation_cleanup_cron.sh", "30"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    handle = archive.open("rb")
    try:
        recurrence = subprocess.run(
            ["bash", "deploy/run_logs_rotation_cleanup_cron.sh", "30"],
            cwd=Path(__file__).resolve().parents[2],
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
    finally:
        handle.close()

    assert [first.returncode, stable.returncode, recurrence.returncode] == [0, 0, 0]
    assert "writer_defer_max_consecutive=1" in first.stdout
    assert "writer_defer_tracked=0" in stable.stdout
    assert "writer_defer_max_consecutive=1" in recurrence.stdout


def test_log_rotation_cleanup_preserves_invalid_existing_gzip(tmp_path):
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    archive = log_dir / "invalid_existing.log.2"
    existing_gzip = archive.with_suffix(".2.gz")
    log_dir.mkdir(parents=True)
    archive.write_text("source-generation\n", encoding="utf-8")
    invalid_gzip = b"not-a-valid-gzip"
    existing_gzip.write_bytes(invalid_gzip)
    old_ts = time.time() - 40 * 86400
    os.utime(archive, (old_ts, old_ts))
    os.utime(existing_gzip, (old_ts, old_ts))

    env = os.environ.copy()
    env.update({"PROJECT_DIR": str(project_root), "TARGET_DATE": "2026-05-22"})
    result = subprocess.run(
        ["bash", "deploy/run_logs_rotation_cleanup_cron.sh", "30"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert archive.read_text(encoding="utf-8") == "source-generation\n"
    assert existing_gzip.read_bytes() == invalid_gzip
    with gzip.open(_generation_gzip(archive), "rt", encoding="utf-8") as handle:
        assert handle.read() == "source-generation\n"
    assert "archive_generation_compressed=1" in result.stdout
    assert "archive_compression_failures=0" in result.stdout
    assert "archive_deleted=0" in result.stdout
    assert "[DONE] log_rotation_cleanup" in result.stdout


def test_log_rotation_cleanup_aggregates_micro_failure_after_generic_cleanup(
    tmp_path,
):
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    archive = log_dir / "stable_after_micro_failure.log.2"
    fake_python = tmp_path / "python-fail"
    log_dir.mkdir(parents=True)
    archive.write_text("stable-after-micro-failure\n", encoding="utf-8")
    fake_python.write_text("#!/usr/bin/env bash\nexit 1\n", encoding="utf-8")
    fake_python.chmod(0o755)

    env = os.environ.copy()
    env.update(
        {
            "PROJECT_DIR": str(project_root),
            "PYTHON_BIN": str(fake_python),
            "TARGET_DATE": "2026-05-22",
            "LOG_ROTATION_ARCHIVE_QUIET_SECONDS": "0",
        }
    )
    result = subprocess.run(
        ["bash", "deploy/run_logs_rotation_cleanup_cron.sh", "30"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "[MICRO_REVERSION_STORAGE_FAIL]" in result.stdout
    assert archive.exists()
    with gzip.open(_generation_gzip(archive), "rt", encoding="utf-8") as handle:
        assert handle.read() == "stable-after-micro-failure\n"
    assert "archive_compressed=1" in result.stdout
    assert "micro_reversion_storage_status=failed" in result.stdout
    assert "micro_reversion_storage_failures=1" in result.stdout
    assert "[LOG_CLEANUP]" in result.stdout
    assert result.stdout.count("[FAIL] log_rotation_cleanup") == 1


def test_log_rotation_cleanup_reports_micro_global_lock_busy_and_runs_peer(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    tmp_dir = project_root / "tmp"
    archive = log_dir / "lock_busy_peer.log.2"
    log_dir.mkdir(parents=True)
    tmp_dir.mkdir(parents=True)
    archive.write_text("peer", encoding="utf-8")
    lock_path = tmp_dir / "micro_reversion_storage_maintenance.lock"
    lock_handle = lock_path.open("a+", encoding="utf-8")
    fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    env = os.environ.copy()
    env.update(
        {
            "PROJECT_DIR": str(project_root),
            "TARGET_DATE": "2026-05-22",
            "LOG_ROTATION_ARCHIVE_QUIET_SECONDS": "0",
        }
    )
    try:
        result = subprocess.run(
            ["bash", "deploy/run_logs_rotation_cleanup_cron.sh", "30"],
            cwd=Path(__file__).resolve().parents[2],
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
    finally:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
        lock_handle.close()

    assert result.returncode == 1
    assert archive.exists()
    assert _generation_gzip(archive).exists()
    assert "micro_reversion_storage_status=lock_busy" in result.stdout
    assert "micro_reversion_storage_failures=1" in result.stdout
    assert result.stdout.count("[FAIL] log_rotation_cleanup") == 1
    assert "[DONE] log_rotation_cleanup" not in result.stdout


def test_log_rotation_cleanup_rejects_micro_lock_symlink_without_truncating_target(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    tmp_dir = project_root / "tmp"
    archive = log_dir / "unsafe_lock_peer.log.2"
    external = tmp_path / "external-lock-target"
    log_dir.mkdir(parents=True)
    tmp_dir.mkdir(parents=True)
    archive.write_text("peer", encoding="utf-8")
    external.write_text("DO-NOT-TRUNCATE", encoding="utf-8")
    (tmp_dir / "micro_reversion_storage_maintenance.lock").symlink_to(external)
    env = os.environ.copy()
    env.update(
        {
            "PROJECT_DIR": str(project_root),
            "TARGET_DATE": "2026-05-22",
            "LOG_ROTATION_ARCHIVE_QUIET_SECONDS": "0",
        }
    )

    result = subprocess.run(
        ["bash", "deploy/run_logs_rotation_cleanup_cron.sh", "30"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert external.read_text(encoding="utf-8") == "DO-NOT-TRUNCATE"
    assert archive.exists()
    assert _generation_gzip(archive).exists()
    assert "micro_reversion_storage_status=unsafe_lock" in result.stdout
    assert result.stdout.count("[FAIL] log_rotation_cleanup") == 1
    assert "[DONE] log_rotation_cleanup" not in result.stdout


def test_log_rotation_cleanup_rejects_system_metric_lock_symlink(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    tmp_dir = project_root / "tmp"
    sample = log_dir / "system_metric_samples.jsonl"
    external = tmp_path / "external-system-lock-target"
    log_dir.mkdir(parents=True)
    tmp_dir.mkdir(parents=True)
    sample.write_text(
        json.dumps({"ts": "2099-01-01T00:00:00+09:00"}) + "\n",
        encoding="utf-8",
    )
    original_sample = sample.read_bytes()
    external.write_text("DO-NOT-TRUNCATE", encoding="utf-8")
    (tmp_dir / "system_metric_samples.lock").symlink_to(external)
    env = os.environ.copy()
    env.update(
        {
            "PROJECT_DIR": str(project_root),
            "TARGET_DATE": "2026-05-22",
            "DATA_MAINTENANCE_ENABLED": "false",
            "MICRO_REVERSION_STORAGE_MAINTENANCE_ENABLED": "false",
        }
    )

    result = subprocess.run(
        ["bash", "deploy/run_logs_rotation_cleanup_cron.sh", "30"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert external.read_text(encoding="utf-8") == "DO-NOT-TRUNCATE"
    assert sample.read_bytes() == original_sample
    assert "[SYSTEM_METRIC_PRUNE_FAIL]" in result.stdout
    assert "data_maintenance_failures=1" in result.stdout
    assert result.stdout.count("[FAIL] log_rotation_cleanup") == 1
    assert "[DONE] log_rotation_cleanup" not in result.stdout


def test_log_rotation_cleanup_preserves_partial_micro_purge_census(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    fake_bin = tmp_path / "bin"
    log_dir.mkdir(parents=True)
    fake_bin.mkdir()
    fake_ionice = fake_bin / "ionice"
    capacity_status_path = project_root / "data" / "report" / "capacity.json"
    capacity_status_path.parent.mkdir(parents=True)
    capacity_status_content = {
        "schema": "scalp_micro_reversion_storage_capacity_status_v1",
        "target_date": "2026-05-22",
        "capacity_state": "healthy",
        "disk_free_bytes_after": 3,
        "retained_physical_bytes_after": 3,
        "compressed_target_bytes": 0,
        "bytes_reclaimed": 7,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "trading_runtime_effect": False,
        "provider_runtime_effect": False,
        "provider_route_change_allowed": False,
        "network_call_performed_by_module": False,
        "automatic_deletion_authorized": False,
    }
    capacity_status_path.write_text(
        json.dumps(
            {
                **capacity_status_content,
                "artifact_content_sha256": hashlib.sha256(
                    json.dumps(
                        capacity_status_content,
                        ensure_ascii=True,
                        sort_keys=True,
                        separators=(",", ":"),
                        default=str,
                    ).encode("utf-8")
                ).hexdigest(),
            }
        )
        + "\n",
        encoding="utf-8",
    )
    payload = {
        "schema": "scalp_micro_reversion_storage_maintenance_v1",
        "as_of_date": "2026-05-22",
        "mode": "apply",
        "status": "partial_failure",
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "trading_runtime_effect": False,
        "actions": [
            {
                "action": "purge_trade_date_partial",
                "path": "/safe/test-partition",
                "trade_date": "2026-05-01",
                "source_bytes": 7,
                "applied": True,
            }
        ],
        "action_count": 1,
        "source_bytes": 7,
        "partition_failure_count": 1,
        "partition_failures": [
            {
                "candidate_count": "1",
                "candidate_bytes": "3",
                "recovery_required": "true",
            }
        ],
        "failed_candidate_count": 1,
        "failed_candidate_bytes": 3,
        "recovery_required_count": 1,
        "purge_enabled": True,
        "purge_status": "explicit_opt_in_apply",
        "purge_candidate_count": 1,
        "purge_candidate_bytes": 10,
        "purge_applied_count": 0,
        "purge_partial_applied_count": 1,
        "deletion_performed": True,
        "disk_total_bytes": 1_000,
        "disk_used_bytes_after": 997,
        "disk_free_bytes_before": 10,
        "disk_free_bytes_after": 3,
        "disk_free_bytes_delta": -7,
        "retained_physical_bytes_before": 10,
        "retained_physical_bytes_after": 3,
        "retained_physical_bytes_delta": -7,
        "compressed_target_bytes": 0,
        "bytes_reclaimed": 7,
        "low_disk_watermark_bytes": 1,
        "critical_disk_watermark_bytes": 0,
        "capacity_state": "healthy",
        "capacity_warning": False,
        "capacity_failure": False,
        "capacity_workorder_required": False,
        "capacity_reason_codes": [],
        "capacity_status_artifact_path": str(capacity_status_path),
        "capacity_status_written": True,
        "capacity_status_write_failure_count": 0,
        "capacity_status_write_failure_reason": None,
    }
    fake_ionice.write_text(
        "#!/usr/bin/env bash\nprintf '%s\\n' "
        + repr(json.dumps(payload, separators=(",", ":")))
        + "\n",
        encoding="utf-8",
    )
    fake_ionice.chmod(0o755)
    env = os.environ.copy()
    env.update(
        {
            "PROJECT_DIR": str(project_root),
            "TARGET_DATE": "2026-05-22",
            "MICRO_REVERSION_STORAGE_PURGE_ENABLED": "true",
            "PATH": f"{fake_bin}:{env['PATH']}",
        }
    )

    result = subprocess.run(
        ["bash", "deploy/run_logs_rotation_cleanup_cron.sh", "30"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "micro_reversion_storage_status=partial_failure" in result.stdout
    assert "micro_reversion_storage_purge_partial=1" in result.stdout
    assert "micro_reversion_storage_failed_candidates=1" in result.stdout
    assert "micro_reversion_storage_recovery_required=1" in result.stdout
    assert "invalid_result" not in result.stdout
    assert result.stdout.count("[FAIL] log_rotation_cleanup") == 1
    assert "[DONE] log_rotation_cleanup" not in result.stdout


@pytest.mark.parametrize(
    ("tamper_field", "tamper_value"),
    [
        ("action_count", 2),
        ("source_bytes", 8),
        ("failed_candidate_count", 2),
        ("failed_candidate_bytes", 4),
        ("recovery_required_count", 0),
        ("action", "unknown_storage_action"),
    ],
)
def test_log_rotation_cleanup_rejects_tampered_micro_result_census(
    tmp_path: Path,
    tamper_field: str,
    tamper_value: object,
) -> None:
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    fake_bin = tmp_path / "bin"
    log_dir.mkdir(parents=True)
    fake_bin.mkdir()
    fake_ionice = fake_bin / "ionice"
    payload = {
        "schema": "scalp_micro_reversion_storage_maintenance_v1",
        "mode": "apply",
        "status": "partial_failure",
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "trading_runtime_effect": False,
        "actions": [
            {
                "action": "purge_trade_date_partial",
                "path": "/safe/test-partition",
                "trade_date": "2026-05-01",
                "source_bytes": 7,
                "applied": True,
            }
        ],
        "action_count": 1,
        "source_bytes": 7,
        "partition_failure_count": 1,
        "partition_failures": [
            {
                "candidate_count": "1",
                "candidate_bytes": "3",
                "recovery_required": "true",
            }
        ],
        "failed_candidate_count": 1,
        "failed_candidate_bytes": 3,
        "recovery_required_count": 1,
        "purge_enabled": True,
        "purge_status": "explicit_opt_in_apply",
        "purge_candidate_count": 1,
        "purge_candidate_bytes": 10,
        "purge_applied_count": 0,
        "purge_partial_applied_count": 1,
        "deletion_performed": True,
    }
    if tamper_field == "action":
        payload["actions"][0]["action"] = tamper_value
    else:
        payload[tamper_field] = tamper_value
    fake_ionice.write_text(
        "#!/usr/bin/env bash\nprintf '%s\\n' "
        + repr(json.dumps(payload, separators=(",", ":")))
        + "\n",
        encoding="utf-8",
    )
    fake_ionice.chmod(0o755)
    env = os.environ.copy()
    env.update(
        {
            "PROJECT_DIR": str(project_root),
            "TARGET_DATE": "2026-05-22",
            "MICRO_REVERSION_STORAGE_PURGE_ENABLED": "true",
            "PATH": f"{fake_bin}:{env['PATH']}",
        }
    )

    result = subprocess.run(
        ["bash", "deploy/run_logs_rotation_cleanup_cron.sh", "30"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "micro_reversion_storage_status=invalid_result" in result.stdout
    assert result.stdout.count("[FAIL] log_rotation_cleanup") == 1
    assert "[DONE] log_rotation_cleanup" not in result.stdout


def test_log_rotation_cleanup_preserves_source_changed_during_gzip(tmp_path):
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    archive = log_dir / "growing.log.2"
    log_dir.mkdir(parents=True)
    archive.write_text("before-growth\n", encoding="utf-8")

    real_gzip = shutil.which("gzip")
    assert real_gzip is not None
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_gzip = fake_bin / "gzip"
    fake_gzip.write_text(
        "#!/usr/bin/env bash\n"
        'source_path="${@: -1}"\n'
        'if [[ "$*" == *" -c "* && "$source_path" == *"growing.log.2" ]]; then\n'
        "  printf 'growth-during-compression\\n' >> \"$source_path\"\n"
        '  echo "gzip: $source_path: file size changed while zipping" >&2\n'
        "  exit 1\n"
        "fi\n"
        f'exec "{real_gzip}" "$@"\n',
        encoding="utf-8",
    )
    fake_gzip.chmod(0o755)

    env = os.environ.copy()
    env.update(
        {
            "PROJECT_DIR": str(project_root),
            "TARGET_DATE": "2026-05-22",
            "LOG_ROTATION_ARCHIVE_QUIET_SECONDS": "0",
            "PATH": f"{fake_bin}:{env['PATH']}",
        }
    )
    result = subprocess.run(
        ["bash", "deploy/run_logs_rotation_cleanup_cron.sh", "30"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert archive.read_text(encoding="utf-8") == (
        "before-growth\ngrowth-during-compression\n"
    )
    assert not archive.with_suffix(".2.gz").exists()
    assert (
        "status=deferred_writer_active reason=source_changed_during_compression"
        in result.stdout
    )
    assert "source_preserved=true" in result.stdout
    assert "archive_writer_active_deferred=1" in result.stdout
    assert "archive_compression_failures=0" in result.stdout
    assert "[DONE] log_rotation_cleanup" in result.stdout


def test_log_rotation_cleanup_preserves_post_publish_source_change(tmp_path):
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    archive = log_dir / "publish_boundary.log.2"
    log_dir.mkdir(parents=True)
    original = "before-publish-boundary\n"
    archive.write_text(original, encoding="utf-8")

    real_ln = shutil.which("ln")
    assert real_ln is not None
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_ln = fake_bin / "ln"
    fake_ln.write_text(
        "#!/usr/bin/env bash\n"
        'destination="${@: -1}"\n'
        f'"{real_ln}" "$@"\n'
        "rc=$?\n"
        'if [[ "$rc" -eq 0 && "$destination" == *"publish_boundary.log.generation_"*".gz" ]]; then\n'
        f"  printf 'growth-after-publish\\n' >> '{archive}'\n"
        "fi\n"
        'exit "$rc"\n',
        encoding="utf-8",
    )
    fake_ln.chmod(0o755)

    env = os.environ.copy()
    env.update(
        {
            "PROJECT_DIR": str(project_root),
            "TARGET_DATE": "2026-05-22",
            "LOG_ROTATION_ARCHIVE_QUIET_SECONDS": "0",
            "PATH": f"{fake_bin}:{env['PATH']}",
        }
    )
    result = subprocess.run(
        ["bash", "deploy/run_logs_rotation_cleanup_cron.sh", "30"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert archive.read_text(encoding="utf-8") == (original + "growth-after-publish\n")
    with gzip.open(_generation_gzip(archive), "rt", encoding="utf-8") as handle:
        assert handle.read() == original
    assert (
        "status=deferred_writer_active reason=source_changed_after_gzip_publish"
        in result.stdout
    )
    assert "source_preserved=true" in result.stdout
    assert "archive_writer_active_deferred=1" in result.stdout
    assert "archive_compression_failures=0" in result.stdout
    assert "[DONE] log_rotation_cleanup" in result.stdout


def test_log_rotation_cleanup_does_not_purge_expired_micro_storage_by_default(
    tmp_path,
):
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    trade_dir = (
        project_root
        / "data"
        / "observations"
        / "scalp_micro_reversion_forward"
        / "trade_date=2026-04-01"
    )
    source = trade_dir / "venue=KRX" / "session=KRX_REGULAR" / "market_stream.jsonl"
    log_dir.mkdir(parents=True)
    source.parent.mkdir(parents=True)
    source.write_text("{}\n", encoding="utf-8")
    env = os.environ.copy()
    env.update(
        {
            "PROJECT_DIR": str(project_root),
            "PYTHON_BIN": str(Path(__file__).resolve().parents[2] / ".venv/bin/python"),
            "TARGET_DATE": "2026-05-22",
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

    assert trade_dir.exists()
    assert not source.exists()
    assert source.with_suffix(".jsonl.gz").exists()
    assert "micro_reversion_storage_purged=0" in result.stdout
    assert "micro_reversion_storage_purge_candidates=1" in result.stdout
    assert "micro_reversion_storage_purge_enabled=false" in result.stdout


def test_log_rotation_cleanup_purges_micro_storage_only_with_explicit_opt_in(
    tmp_path,
):
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    trade_dir = (
        project_root
        / "data"
        / "observations"
        / "scalp_micro_reversion_forward"
        / "trade_date=2026-04-01"
    )
    source = trade_dir / "venue=KRX" / "session=KRX_REGULAR" / "market_stream.jsonl"
    log_dir.mkdir(parents=True)
    source.parent.mkdir(parents=True)
    source.write_text("{}\n", encoding="utf-8")
    env = os.environ.copy()
    env.update(
        {
            "PROJECT_DIR": str(project_root),
            "PYTHON_BIN": str(Path(__file__).resolve().parents[2] / ".venv/bin/python"),
            "TARGET_DATE": "2026-05-22",
            "MICRO_REVERSION_STORAGE_PURGE_ENABLED": "true",
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

    assert not trade_dir.exists()
    assert "micro_reversion_storage_purged=1" in result.stdout
    assert "micro_reversion_storage_purge_enabled=true" in result.stdout
    assert "micro_reversion_storage_purge_status=explicit_opt_in_apply" in result.stdout


def test_log_rotation_cleanup_can_disable_micro_reversion_storage_maintenance(
    tmp_path,
):
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    source = (
        project_root
        / "data"
        / "observations"
        / "scalp_micro_reversion_forward"
        / "trade_date=2026-05-21"
        / "venue=KRX"
        / "session=KRX_REGULAR"
        / "market_stream.jsonl"
    )
    log_dir.mkdir(parents=True)
    source.parent.mkdir(parents=True)
    source.write_text("{}\n", encoding="utf-8")
    env = os.environ.copy()
    env.update(
        {
            "PROJECT_DIR": str(project_root),
            "TARGET_DATE": "2026-05-22",
            "MICRO_REVERSION_STORAGE_MAINTENANCE_ENABLED": "false",
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

    assert source.exists()
    assert not source.with_suffix(".jsonl.gz").exists()
    assert "micro_reversion_storage_status=disabled" in result.stdout
    assert "micro_reversion_storage_purge_status=maintenance_disabled" in result.stdout


def test_log_rotation_cleanup_low_capacity_warns_and_keeps_peer_lanes_running(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    log_dir.mkdir(parents=True)
    peer_archive = log_dir / "capacity_warning_peer.log.3"
    peer_archive.write_text("peer", encoding="utf-8")
    status_path = project_root / "data" / "report" / "capacity" / "status.json"
    env = os.environ.copy()
    env.update(
        {
            "PROJECT_DIR": str(project_root),
            "PYTHON_BIN": str(Path(__file__).resolve().parents[2] / ".venv/bin/python"),
            "TARGET_DATE": "2026-05-22",
            "LOG_ROTATION_ARCHIVE_QUIET_SECONDS": "0",
            "MICRO_REVERSION_STORAGE_LOW_DISK_WATERMARK_BYTES": "1000000000000000",
            "MICRO_REVERSION_STORAGE_CRITICAL_DISK_WATERMARK_BYTES": "0",
            "MICRO_REVERSION_STORAGE_CAPACITY_STATUS_PATH": str(status_path),
        }
    )

    result = subprocess.run(
        ["bash", "deploy/run_logs_rotation_cleanup_cron.sh", "30"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    artifact = json.loads(status_path.read_text(encoding="utf-8"))
    assert result.returncode == 0
    assert artifact["status"] == "low_warning_workorder_open"
    assert artifact["automatic_deletion_authorized"] is False
    assert "[MICRO_REVERSION_STORAGE_CAPACITY_WARNING]" in result.stdout
    assert "capacity_state=low_warning" in result.stdout
    assert "cleanup_will_continue=true" in result.stdout
    assert _generation_gzip(peer_archive).exists()
    assert "[DONE] log_rotation_cleanup" in result.stdout


def test_log_rotation_cleanup_critical_capacity_fails_after_peer_lanes_continue(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    log_dir.mkdir(parents=True)
    peer_archive = log_dir / "critical_capacity_peer.log.3"
    peer_archive.write_text("peer", encoding="utf-8")
    status_path = project_root / "data" / "report" / "capacity" / "status.json"
    env = os.environ.copy()
    env.update(
        {
            "PROJECT_DIR": str(project_root),
            "PYTHON_BIN": str(Path(__file__).resolve().parents[2] / ".venv/bin/python"),
            "TARGET_DATE": "2026-05-22",
            "LOG_ROTATION_ARCHIVE_QUIET_SECONDS": "0",
            "MICRO_REVERSION_STORAGE_LOW_DISK_WATERMARK_BYTES": "1000000000000000",
            "MICRO_REVERSION_STORAGE_CRITICAL_DISK_WATERMARK_BYTES": "999999999999999",
            "MICRO_REVERSION_STORAGE_CAPACITY_STATUS_PATH": str(status_path),
        }
    )

    result = subprocess.run(
        ["bash", "deploy/run_logs_rotation_cleanup_cron.sh", "30"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    artifact = json.loads(status_path.read_text(encoding="utf-8"))
    assert result.returncode == 1
    assert artifact["status"] == "critical_blocked"
    assert artifact["capacity_workorder"]["state"] == "open"
    assert "[MICRO_REVERSION_STORAGE_FAIL] status=critical_capacity" in result.stdout
    assert "capacity_state=critical" in result.stdout
    assert "generic_cleanup_will_continue=true" in result.stdout
    assert _generation_gzip(peer_archive).exists()
    assert "[FAIL] log_rotation_cleanup" in result.stdout


def test_log_rotation_cleanup_compresses_closed_micro_reversion_report_artifact(
    tmp_path,
):
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    report_root = (
        project_root
        / "data"
        / "report"
        / "ai_micro_reversion_materialized_replay_requests"
    )
    paired_root = project_root / "data" / "report" / "ai_prompt_paired_replay"
    quality_root = project_root / "data" / "report" / "main_ai_quality_r0_r3"
    artifact = report_root / ("ai_micro_reversion_replay_source_bundle_2026-05-21.json")
    log_dir.mkdir(parents=True)
    report_root.mkdir(parents=True)
    paired_root.mkdir(parents=True)
    quality_root.mkdir(parents=True)
    authority = {
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }

    def canonical_hash(payload: dict) -> str:
        return hashlib.sha256(
            json.dumps(
                payload,
                ensure_ascii=True,
                sort_keys=True,
                separators=(",", ":"),
                default=str,
            ).encode("utf-8")
        ).hexdigest()

    source_bundle_content = {
        "schema": "ai_micro_reversion_replay_source_bundle_v1",
        "target_date": "2026-05-21",
        "rows": [],
        **authority,
    }
    source_bundle = {
        **source_bundle_content,
        "source_bundle_content_sha256": canonical_hash(source_bundle_content),
    }
    artifact.write_text(json.dumps(source_bundle) + "\n", encoding="utf-8")
    materialized_content = {
        "schema": "ai_micro_reversion_materialized_replay_requests_v1",
        "target_date": "2026-05-21",
        "source_bundle_content_sha256": source_bundle["source_bundle_content_sha256"],
        "source_bundle_artifact_sha256": canonical_hash(source_bundle),
        **authority,
    }
    materialized = {
        **materialized_content,
        "report_content_sha256": canonical_hash(materialized_content),
    }
    materialized_path = report_root / (
        "ai_micro_reversion_materialized_replay_requests_2026-05-21.json"
    )
    materialized_path.write_text(
        json.dumps(materialized) + "\n",
        encoding="utf-8",
    )
    terminal_content = {
        "schema": "ai_micro_reversion_three_arm_offline_results_v1",
        "target_date": "2026-05-21",
        "status": "offline_three_arm_execution_complete",
        "materialized_report_content_sha256": materialized["report_content_sha256"],
        "materialized_request_census_sha256": "a" * 64,
        "request_count": 1,
        "result_count": 1,
        "deferred_request_count": 0,
        **authority,
    }
    terminal_hash = hashlib.sha256(
        json.dumps(
            terminal_content,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()
    (
        report_root / "ai_micro_reversion_three_arm_offline_results_2026-05-21.json"
    ).write_text(
        json.dumps({**terminal_content, "report_content_sha256": terminal_hash}) + "\n",
        encoding="utf-8",
    )
    paired = paired_root / "ai_prompt_paired_replay_2026-05-21.json"
    paired.write_text(
        json.dumps(
            {
                "schema": "ai_prompt_paired_replay_v1",
                "target_date": "2026-05-21",
                **authority,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    floor_content = {
        "schema": "micro_reversion_provider_ablation_sample_floor_v1",
        "target_date": "2026-05-21",
        **authority,
    }
    floor = quality_root / (
        "micro_reversion_provider_ablation_sample_floor_2026-05-21.json"
    )
    floor.write_text(
        json.dumps(
            {
                **floor_content,
                "floor_content_sha256": canonical_hash(floor_content),
            }
        )
        + "\n",
        encoding="utf-8",
    )
    suffixed_paired = paired_root / "ai_prompt_paired_replay_2026-05-21_entry_KRX.json"
    suffixed_paired.write_text('{"target_date":"2026-05-21"}\n', encoding="utf-8")
    env = os.environ.copy()
    env.update(
        {
            "PROJECT_DIR": str(project_root),
            "PYTHON_BIN": str(Path(__file__).resolve().parents[2] / ".venv/bin/python"),
            "TARGET_DATE": "2026-05-22",
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

    compressed = artifact.with_suffix(".json.gz")
    assert not artifact.exists()
    with gzip.open(compressed, "rt", encoding="utf-8") as handle:
        assert json.load(handle)["target_date"] == "2026-05-21"
    assert not paired.exists()
    assert paired.with_suffix(".json.gz").exists()
    assert suffixed_paired.exists()
    assert not suffixed_paired.with_suffix(".json.gz").exists()
    assert not materialized_path.exists()
    assert materialized_path.with_suffix(".json.gz").exists()
    assert not floor.exists()
    with gzip.open(floor.with_suffix(".json.gz"), "rt", encoding="utf-8") as handle:
        floor_after = json.load(handle)
    assert floor_after["floor_content_sha256"] == canonical_hash(floor_content)
    assert "report_artifact_compressed=5" in result.stdout
    assert "artifact_set_terminal=1" in result.stdout
    assert "report_artifact_failures=0" in result.stdout


def test_log_rotation_cleanup_compresses_closed_provider_budget_ledger(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    budget_root = project_root / "data" / "offline_provider_budget"
    log_dir.mkdir(parents=True)
    budget_root.mkdir(parents=True)
    execution_date = "2026-05-21"
    ledger = budget_root / f"ai_micro_reversion_provider_budget_{execution_date}.jsonl"
    authority = {
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "provider_route_change_allowed": False,
        "network_call_performed_by_module": False,
    }

    def with_hash(payload: dict, field: str) -> dict:
        encoded = json.dumps(
            payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
        return {**payload, field: hashlib.sha256(encoded).hexdigest()}

    record = with_hash(
        {
            "schema": "ai_provider_budget_ledger_record_v1",
            "sequence": 1,
            "previous_record_sha256": None,
            "execution_date": execution_date,
            **authority,
        },
        "record_content_sha256",
    )
    ledger_bytes = (json.dumps(record, separators=(",", ":")) + "\n").encode()
    ledger.write_bytes(ledger_bytes)
    ledger_hash = hashlib.sha256(ledger_bytes).hexdigest()
    manifest = with_hash(
        {
            "schema": "ai_provider_budget_ledger_manifest_v1",
            "execution_date": execution_date,
            "ledger_file": ledger.name,
            "ledger_size_bytes": len(ledger_bytes),
            "ledger_bytes_sha256": ledger_hash,
            "record_count": 1,
            "head_record_sha256": record["record_content_sha256"],
            **authority,
        },
        "manifest_content_sha256",
    )
    ledger.with_suffix(".manifest.json").write_text(
        json.dumps(manifest) + "\n", encoding="utf-8"
    )
    summary = with_hash(
        {
            "schema": "ai_provider_budget_summary_v1",
            "execution_date": execution_date,
            "ledger_record_count": 1,
            "ledger_head_sha256": record["record_content_sha256"],
            "ledger_bytes_sha256": ledger_hash,
            **authority,
        },
        "summary_content_sha256",
    )
    ledger.with_suffix(".json").write_text(json.dumps(summary) + "\n", encoding="utf-8")
    ledger.with_suffix(".lock").touch()
    env = os.environ.copy()
    env.update(
        {
            "PROJECT_DIR": str(project_root),
            "PYTHON_BIN": str(Path(__file__).resolve().parents[2] / ".venv/bin/python"),
            "TARGET_DATE": "2026-05-22",
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

    assert not ledger.exists()
    with gzip.open(ledger.with_suffix(".jsonl.gz"), "rb") as handle:
        assert handle.read() == ledger_bytes
    assert "provider_budget_ledgers=1" in result.stdout
    assert "provider_authority=false" in result.stdout


def test_log_rotation_cleanup_defers_archived_and_stale_active_logs(tmp_path):
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

    assert stale_active.exists()
    assert fresh_active.exists()
    assert old_archive.exists()
    assert old_archive_gz.exists()
    assert fresh_archive.exists()
    assert "active_deleted=0" in result.stdout
    assert "active_retention_deferred=1" in result.stdout
    assert "archive_deleted=0" in result.stdout
    assert "archive_retention_deferred=2" in result.stdout


def test_log_rotation_cleanup_defers_old_raw_row_exclusion_backups_after_seven_days(
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

    assert backup_path.exists()
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest == {"backup_path": str(backup_path)}
    assert "raw_row_exclusion_backup_retention_days=7" in result.stdout
    assert "raw_row_exclusion_backup_deleted=0" in result.stdout
    assert "raw_row_exclusion_backup_delete_deferred=1" in result.stdout


def test_log_rotation_cleanup_preserves_raw_row_backup_and_manifest_on_rm_failure(
    tmp_path,
):
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    exclusion_dir = (
        project_root
        / "data"
        / "source_quality"
        / "raw_row_exclusion"
        / "2026-05-22_20260522T101010000000+0900"
    )
    log_dir.mkdir(parents=True)
    exclusion_dir.mkdir(parents=True)
    backup_path = exclusion_dir / "pipeline_events_2026-05-22.jsonl.gz"
    backup_payload = b"gzip-placeholder"
    backup_path.write_bytes(backup_payload)
    manifest_path = exclusion_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps({"backup_path": str(backup_path)}, ensure_ascii=False),
        encoding="utf-8",
    )
    peer_archive = log_dir / "raw_row_rm_peer.log.4.gz"
    peer_archive.write_bytes(gzip.compress(b"peer", mtime=0))
    old_ts = time.time() - 40 * 86400
    os.utime(backup_path, (old_ts, old_ts))
    os.utime(peer_archive, (old_ts, old_ts))

    real_rm = shutil.which("rm")
    assert real_rm is not None
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_rm = fake_bin / "rm"
    fake_rm.write_text(
        "#!/usr/bin/env bash\n"
        'for path in "$@"; do\n'
        '  if [[ "$path" == *"pipeline_events_2026-05-22.jsonl.gz" ]]; then\n'
        "    exit 1\n"
        "  fi\n"
        "done\n"
        f'exec "{real_rm}" "$@"\n',
        encoding="utf-8",
    )
    fake_rm.chmod(0o755)
    env = os.environ.copy()
    env.update(
        {
            "PROJECT_DIR": str(project_root),
            "TARGET_DATE": "2026-05-31",
            "MICRO_REVERSION_STORAGE_MAINTENANCE_ENABLED": "false",
            "LOG_ROTATION_ACTIVE_MAX_BYTES": "4096",
            "LOG_ROTATION_COMPRESS_MIN_INDEX": "99",
            "LOG_ROTATION_ARCHIVE_QUIET_SECONDS": "0",
            "PATH": f"{fake_bin}:{env['PATH']}",
        }
    )
    result = subprocess.run(
        ["bash", "deploy/run_logs_rotation_cleanup_cron.sh", "30"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert backup_path.read_bytes() == backup_payload
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest == {"backup_path": str(backup_path)}
    assert peer_archive.exists()
    assert "lane=backup" in result.stdout
    assert "status=disabled_pending_storage_owner" in result.stdout
    assert "raw_row_exclusion_backup_deleted=0" in result.stdout
    assert "raw_row_exclusion_backup_delete_deferred=1" in result.stdout
    assert "data_maintenance_failures=0" in result.stdout
    assert "archive_deleted=0" in result.stdout
    assert "[DONE] log_rotation_cleanup" in result.stdout


def test_log_rotation_cleanup_blocks_backup_delete_for_malformed_manifest(tmp_path):
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
    manifest_path.write_text("{malformed", encoding="utf-8")
    old_ts = time.time() - 40 * 86400
    os.utime(backup_path, (old_ts, old_ts))
    env = os.environ.copy()
    env.update(
        {
            "PROJECT_DIR": str(project_root),
            "TARGET_DATE": "2026-05-31",
            "MICRO_REVERSION_STORAGE_MAINTENANCE_ENABLED": "false",
            "LOG_ROTATION_ACTIVE_MAX_BYTES": "4096",
            "LOG_ROTATION_COMPRESS_MIN_INDEX": "99",
        }
    )
    result = subprocess.run(
        ["bash", "deploy/run_logs_rotation_cleanup_cron.sh", "30"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert backup_path.exists()
    assert manifest_path.read_text(encoding="utf-8") == "{malformed"
    assert "[RAW_ROW_EXCLUSION_DELETE_DEFERRED] lane=backup" in result.stdout
    assert "raw_row_exclusion_backup_deleted=0" in result.stdout
    assert "raw_row_exclusion_backup_delete_deferred=1" in result.stdout
    assert "[DONE] log_rotation_cleanup" in result.stdout


def test_log_rotation_cleanup_preserves_duplicate_raw_row_run_on_rm_failure(tmp_path):
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    exclusion_root = project_root / "data" / "source_quality" / "raw_row_exclusion"
    old_run = exclusion_root / "2026-05-22_20260522T101010000000+0900"
    latest_run = exclusion_root / "2026-05-22_20260522T202020000000+0900"
    log_dir.mkdir(parents=True)
    old_run.mkdir(parents=True)
    latest_run.mkdir(parents=True)
    (old_run / "evidence.json").write_text("old", encoding="utf-8")

    real_rm = shutil.which("rm")
    assert real_rm is not None
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_rm = fake_bin / "rm"
    fake_rm.write_text(
        "#!/usr/bin/env bash\n"
        'for path in "$@"; do\n'
        '  if [[ "$path" == *"2026-05-22_20260522T101010000000+0900" ]]; then\n'
        "    exit 1\n"
        "  fi\n"
        "done\n"
        f'exec "{real_rm}" "$@"\n',
        encoding="utf-8",
    )
    fake_rm.chmod(0o755)
    env = os.environ.copy()
    env.update(
        {
            "PROJECT_DIR": str(project_root),
            "TARGET_DATE": "2026-05-31",
            "MICRO_REVERSION_STORAGE_MAINTENANCE_ENABLED": "false",
            "PATH": f"{fake_bin}:{env['PATH']}",
        }
    )
    result = subprocess.run(
        ["bash", "deploy/run_logs_rotation_cleanup_cron.sh", "30"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert old_run.exists()
    assert latest_run.exists()
    assert "lane=duplicate" in result.stdout
    assert "raw_row_exclusion_deleted=0" in result.stdout
    assert "raw_row_exclusion_delete_deferred=1" in result.stdout
    assert "data_maintenance_failures=0" in result.stdout
    assert "[DONE] log_rotation_cleanup" in result.stdout
