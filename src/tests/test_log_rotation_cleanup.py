from __future__ import annotations

import gzip
import hashlib
import os
import json
import shutil
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
            "LOG_ROTATION_ARCHIVE_QUIET_SECONDS": "0",
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

    assert not sentinel.exists()
    assert not snapshot.exists()
    with gzip.open(f"{sentinel}.gz", "rt", encoding="utf-8") as handle:
        assert handle.read() == sentinel_payload
    with gzip.open(f"{snapshot}.gz", "rt", encoding="utf-8") as handle:
        assert handle.read() == snapshot_payload
    assert "sentinel_compressed=1" in result.stdout
    assert "snapshot_compressed=1" in result.stdout
    assert "compression_verify_failures=0" in result.stdout


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


def test_log_rotation_cleanup_reconciles_conflicting_gzip_and_finishes_micro_lane(
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
    original_existing_gzip = gzip.compress(
        b"previous-verified-generation\n", mtime=0
    )
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
    assert not archive.exists()
    assert existing_gzip.read_bytes() == original_existing_gzip
    generation_hash = hashlib.sha256(original_archive.encode()).hexdigest()[:16]
    generation_gzip = Path(f"{archive}.generation_{generation_hash}.gz")
    with gzip.open(generation_gzip, "rt", encoding="utf-8") as handle:
        assert handle.read() == original_archive
    assert not stable_peer.exists()
    with gzip.open(stable_peer.with_suffix(".2.gz"), "rt", encoding="utf-8") as handle:
        assert handle.read() == "stable-peer\n"
    assert not list(log_dir.glob("*.tmp.*"))
    assert not micro_source.exists()
    assert micro_source.with_suffix(".jsonl.gz").exists()
    assert not stale_tmp.exists()
    assert result.stdout.index("[MICRO_REVERSION_STORAGE] status=pass") < result.stdout.index(
        "[ARCHIVE_COLLISION_RECONCILED]"
    )
    assert "[ARCHIVE_COLLISION_RECONCILED] archive=kiwoom_utils_info.log.9" in result.stdout
    assert "micro_reversion_storage_status=pass" in result.stdout
    assert "archive_compressed=2" in result.stdout
    assert "archive_collision_reconciled=1" in result.stdout
    assert "archive_compression_failures=0" in result.stdout
    assert "archive_retention_protected=1" in result.stdout
    assert "reason=reconciled_existing_generation_preserved" in result.stdout
    assert "reason=failed_compression_evidence_preserved" not in result.stdout
    assert "archive_deleted=0" in result.stdout
    assert "[DONE] log_rotation_cleanup" in result.stdout


def test_log_rotation_cleanup_finalizes_matching_existing_gzip(tmp_path):
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

    assert not archive.exists()
    assert existing_gzip.read_bytes() == original_gzip
    assert "archive_compressed=0" in result.stdout
    assert "archive_compression_finalized=1" in result.stdout
    assert "archive_compression_failures=0" in result.stdout
    assert "[DONE] log_rotation_cleanup" in result.stdout


def test_log_rotation_cleanup_finalizes_existing_collision_generation(tmp_path):
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    archive = log_dir / "collision_retry.log.2"
    existing_gzip = archive.with_suffix(".2.gz")
    log_dir.mkdir(parents=True)
    source_payload = b"new-generation-awaiting-unlink\n"
    existing_gzip_bytes = gzip.compress(b"previous-generation\n", mtime=0)
    generation_hash = hashlib.sha256(source_payload).hexdigest()[:16]
    generation_gzip = Path(f"{archive}.generation_{generation_hash}.gz")
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
        check=True,
    )

    assert not archive.exists()
    assert existing_gzip.read_bytes() == existing_gzip_bytes
    assert generation_gzip.read_bytes() == generation_gzip_bytes
    assert "action=finalized_collision_generation" in result.stdout
    assert "archive_compressed=0" in result.stdout
    assert "archive_compression_finalized=1" in result.stdout
    assert "archive_collision_reconciled=1" in result.stdout
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

    assert result.returncode == 1
    assert recent_archive.read_text(encoding="utf-8") == "still-growing\n"
    assert not recent_archive.with_suffix(".2.gz").exists()
    assert not stable_archive.exists()
    with gzip.open(stable_archive.with_suffix(".3.gz"), "rt", encoding="utf-8") as handle:
        assert handle.read() == "stable\n"
    assert "reason=source_not_quiet" in result.stdout
    assert "archive_compressed=1" in result.stdout
    assert "archive_compression_failures=1" in result.stdout
    assert "[LOG_CLEANUP]" in result.stdout
    assert result.stdout.count("[FAIL] log_rotation_cleanup") == 1


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

    assert result.returncode == 1
    assert archive.read_text(encoding="utf-8") == "source-generation\n"
    assert existing_gzip.read_bytes() == invalid_gzip
    assert "reason=existing_gzip_invalid_conflict" in result.stdout
    assert "archive_retention_protected=2" in result.stdout
    assert "reason=failed_compression_evidence_preserved" in result.stdout
    assert "archive_deleted=0" in result.stdout
    assert result.stdout.count("[FAIL] log_rotation_cleanup") == 1


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
    assert not archive.exists()
    with gzip.open(archive.with_suffix(".2.gz"), "rt", encoding="utf-8") as handle:
        assert handle.read() == "stable-after-micro-failure\n"
    assert "archive_compressed=1" in result.stdout
    assert "micro_reversion_storage_status=failed" in result.stdout
    assert "micro_reversion_storage_failures=1" in result.stdout
    assert "[LOG_CLEANUP]" in result.stdout
    assert result.stdout.count("[FAIL] log_rotation_cleanup") == 1


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
        "source_path=\"${@: -1}\"\n"
        "if [[ \"$*\" == *\" -c \"* && \"$source_path\" == *\"growing.log.2\" ]]; then\n"
        "  printf 'growth-during-compression\\n' >> \"$source_path\"\n"
        "  echo \"gzip: $source_path: file size changed while zipping\" >&2\n"
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

    assert result.returncode == 1
    assert archive.read_text(encoding="utf-8") == (
        "before-growth\ngrowth-during-compression\n"
    )
    assert not archive.with_suffix(".2.gz").exists()
    assert "reason=source_changed_during_compression" in result.stdout
    assert "source_preserved=true" in result.stdout
    assert "[FAIL] log_rotation_cleanup" in result.stdout


def test_log_rotation_cleanup_preserves_post_publish_source_change(tmp_path):
    project_root = tmp_path / "project"
    log_dir = project_root / "logs"
    archive = log_dir / "publish_boundary.log.2"
    gzip_path = archive.with_suffix(".2.gz")
    log_dir.mkdir(parents=True)
    original = "before-publish-boundary\n"
    archive.write_text(original, encoding="utf-8")

    real_mv = shutil.which("mv")
    assert real_mv is not None
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_mv = fake_bin / "mv"
    fake_mv.write_text(
        "#!/usr/bin/env bash\n"
        "destination=\"${@: -1}\"\n"
        f'"{real_mv}" "$@"\n'
        "rc=$?\n"
        "if [[ \"$rc\" -eq 0 && \"$destination\" == *\"publish_boundary.log.2.gz\" ]]; then\n"
        "  printf 'growth-after-publish\\n' >> \"${destination%.gz}\"\n"
        "fi\n"
        "exit \"$rc\"\n",
        encoding="utf-8",
    )
    fake_mv.chmod(0o755)

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

    assert result.returncode == 1
    assert archive.read_text(encoding="utf-8") == (
        original + "growth-after-publish\n"
    )
    with gzip.open(gzip_path, "rt", encoding="utf-8") as handle:
        assert handle.read() == original
    assert "reason=source_changed_after_gzip_publish" in result.stdout
    assert "source_preserved=true" in result.stdout
    assert "[FAIL] log_rotation_cleanup" in result.stdout


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
