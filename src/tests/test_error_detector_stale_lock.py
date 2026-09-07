from __future__ import annotations

import fcntl
import os
import time
from unittest.mock import patch

import pytest

from src.engine.error_detectors.stale_lock import StaleLockDetector


def test_missing_lock_directory_is_not_failure(tmp_path):
    with patch("src.engine.error_detectors.stale_lock.LOCK_DIR", tmp_path / "missing"):
        assert StaleLockDetector().check().severity == "pass"


@pytest.mark.parametrize("dry_run", [False, True])
def test_old_unheld_marker_is_preserved(tmp_path, dry_run):
    path = tmp_path / "marker.lock"
    path.write_text("operator provenance")
    os.utime(path, (time.time() - 7200,) * 2)
    before = path.stat().st_ino
    with patch("src.engine.error_detectors.stale_lock.LOCK_DIR", tmp_path):
        result = StaleLockDetector(dry_run=dry_run).check()
    assert result.severity == "pass"
    assert path.stat().st_ino == before
    assert path.read_text() == "operator provenance"
    assert result.details["lock_observations"][0]["state"] == "unheld_marker_preserved"
    assert result.details["cleanup_performed"] is False


@pytest.mark.parametrize("age", [0, 7200])
def test_held_mutex_is_not_called_stale_from_age(tmp_path, age):
    path = tmp_path / "run_tuning_monitoring_postclose.lock"
    path.touch()
    os.utime(path, (time.time() - age,) * 2)
    with path.open("rb") as holder:
        fcntl.flock(holder, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with patch("src.engine.error_detectors.stale_lock.LOCK_DIR", tmp_path):
            result = StaleLockDetector().check()
        assert path.exists()
        assert result.severity == "pass"
        row = result.details["lock_observations"][0]
        assert row["state"] == "held"
        assert row["owner_health"] == "not_assessed"
        assert result.details["held_owner_progress_check_required"] is True
        # Inspection must neither release nor replace another owner's lock.
        with path.open("rb") as contender:
            with pytest.raises(BlockingIOError):
                fcntl.flock(contender, fcntl.LOCK_EX | fcntl.LOCK_NB)


def test_unreadable_occupancy_is_not_normalized_to_unheld(tmp_path):
    (tmp_path / "unknown.lock").touch()
    with (
        patch("src.engine.error_detectors.stale_lock.LOCK_DIR", tmp_path),
        patch.object(
            StaleLockDetector, "_inspect_lock", return_value="inspection_unavailable"
        ),
    ):
        result = StaleLockDetector().check()
    assert result.severity == "warning"
    assert result.details["inspection_unavailable"]
