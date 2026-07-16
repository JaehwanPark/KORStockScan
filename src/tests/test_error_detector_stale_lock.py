from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.engine.error_detectors.stale_lock import (
    StaleLockDetector,
    LOCK_DIR,
    MAX_LOCK_AGE_SEC,
)


class TestStaleLockDetector:
    def test_pass_when_no_lock_dir(self):
        with patch(
            "src.engine.error_detectors.stale_lock.LOCK_DIR",
            Path("/nonexistent_lock_dir_xyz"),
        ):
            detector = StaleLockDetector()
            result = detector.check()
            assert result.severity == "pass"

    def test_pass_when_no_lock_files(self, tmp_path):
        lock_dir = tmp_path / "empty_lock_dir"
        lock_dir.mkdir()
        with patch("src.engine.error_detectors.stale_lock.LOCK_DIR", lock_dir):
            detector = StaleLockDetector()
            result = detector.check()
            assert result.severity == "pass"

    def test_clean_stale_lock(self, tmp_path):
        lock_dir = tmp_path / "lock_dir"
        lock_dir.mkdir()
        stale_lock = lock_dir / "test_stale.lock"
        stale_lock.write_text("stale", encoding="utf-8")
        import os as _os

        stale_ts = __import__("time").time() - 7200
        _os.utime(str(stale_lock), (stale_ts, stale_ts))

        with patch("src.engine.error_detectors.stale_lock.LOCK_DIR", lock_dir):
            detector = StaleLockDetector()
            result = detector.check()
            assert result.severity == "warning"
            assert "stale_locks_cleaned" in result.details
            assert not stale_lock.exists()

    def test_active_lock_not_removed(self, tmp_path):
        lock_dir = tmp_path / "lock_dir"
        lock_dir.mkdir()
        fresh_lock = lock_dir / "test_fresh.lock"
        fresh_lock.write_text("fresh", encoding="utf-8")

        with patch("src.engine.error_detectors.stale_lock.LOCK_DIR", lock_dir):
            with open(fresh_lock, "w") as fp:
                import fcntl

                fcntl.flock(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
                detector = StaleLockDetector()
                result = detector.check()
                assert result.severity == "pass"
                assert fresh_lock.exists()
            fresh_lock.unlink()

    def test_dry_run_preserves_stale_lock(self, tmp_path):
        lock_dir = tmp_path / "lock_dir"
        lock_dir.mkdir()
        stale_lock = lock_dir / "stale_dry.lock"
        stale_lock.write_text("stale", encoding="utf-8")
        import os as _os

        stale_ts = __import__("time").time() - 7200
        _os.utime(str(stale_lock), (stale_ts, stale_ts))

        with patch("src.engine.error_detectors.stale_lock.LOCK_DIR", lock_dir):
            detector = StaleLockDetector(dry_run=True)
            result = detector.check()
            assert stale_lock.exists(), "dry-run should not delete lock file"
            assert "stale_locks_would_clean_dry_run" in result.details
            assert result.severity == "pass"
