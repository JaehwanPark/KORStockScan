"""Host-wide heavy admission and inherited reservation proof."""

import fcntl
import os
import subprocess
import sys

import pytest

from src.engine.lifecycle.research_admission import acquire, direct_job, inherited


def test_weighted_admission_releases_first_slot_if_second_is_busy(tmp_path):
    first = acquire(tmp_path, "ordinary", "2026-10-08")
    second = acquire(tmp_path, "ordinary", "2026-10-08")
    first.close()
    assert acquire(tmp_path, "pre_submit_delay", "2026-10-08") is None
    # A failed heavy reservation cannot strand the first slot.
    ordinary = acquire(tmp_path, "ordinary", "2026-10-08")
    assert ordinary is not None
    ordinary.close()
    second.close()
    heavy = acquire(tmp_path, "pre_submit_delay", "2026-10-08")
    assert len(heavy.pass_fds) == 2
    assert acquire(tmp_path, "ordinary", "2026-10-08") is None
    heavy.close()


def test_env_flag_or_forged_receipt_does_not_waive_admission(tmp_path):
    assert not inherited(
        tmp_path, "pre_submit_delay", "2026-10-08", env={"POSTCLOSE_STAGE_WORKER": "1"}
    )
    with pytest.raises(ValueError, match="unverified"):
        inherited(
            tmp_path,
            "pre_submit_delay",
            "2026-10-08",
            env={"POSTCLOSE_RESEARCH_RESERVATION": "{}"},
        )


def test_child_verifies_inherited_descriptors_and_parent_start(tmp_path):
    reservation = acquire(tmp_path, "pre_submit_delay", "2026-10-08")
    command = [
        sys.executable,
        "-c",
        "from src.engine.lifecycle.research_admission import inherited; import sys; "
        'assert inherited(sys.argv[1], "pre_submit_delay", "2026-10-08")',
        str(tmp_path),
    ]
    try:
        passed = subprocess.run(
            command,
            env={**os.environ, **reservation.environment()},
            pass_fds=reservation.pass_fds,
            capture_output=True,
            text=True,
        )
        assert passed.returncode == 0, passed.stderr
        missing = subprocess.run(
            command,
            env={**os.environ, **reservation.environment()},
            capture_output=True,
            text=True,
        )
        assert missing.returncode != 0
        wrong = subprocess.run(
            command[:-1] + [str(tmp_path / "other")],
            env={**os.environ, **reservation.environment()},
            pass_fds=reservation.pass_fds,
            capture_output=True,
            text=True,
        )
        assert wrong.returncode != 0
    finally:
        reservation.close()


def test_direct_cli_writer_precedes_slots_and_releases_on_failure(tmp_path):
    with pytest.raises(RuntimeError):
        with direct_job(tmp_path, "pre_submit_delay", "2026-10-08", timeout=0):
            with pytest.raises(ValueError, match="existing_stage_writer"):
                with direct_job(tmp_path, "pre_submit_delay", "2026-10-08", timeout=0):
                    pass
            raise RuntimeError("interrupted")
    with direct_job(tmp_path, "main_trailing_all_scope", "2026-10-08", timeout=0):
        assert acquire(tmp_path, "ordinary", "2026-10-08") is None


def test_slot_symlink_is_rejected_without_locking_target(tmp_path):
    directory = tmp_path / "runtime/postclose_stage_slots"
    directory.mkdir(parents=True)
    target = tmp_path / "unrelated"
    target.touch()
    (directory / "0.lock").symlink_to(target)
    with pytest.raises(ValueError, match="path_invalid"):
        acquire(tmp_path, "pre_submit_delay", "2026-10-08")
    with target.open("a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)


def test_synchronous_worker_requires_actual_locks_and_exact_identity(tmp_path):
    from src.engine.lifecycle.research_admission import acquire, direct_job

    slot = acquire(tmp_path, "pre_submit_delay", "2026-10-08")
    try:
        with slot.worker():
            with direct_job(tmp_path, "pre_submit_delay", "2026-10-08"):
                pass
            with pytest.raises(ValueError, match="identity_invalid"):
                with direct_job(tmp_path, "main_trailing_all_scope", "2026-10-08"):
                    pass
    finally:
        slot.close()
    with slot.worker(), pytest.raises(ValueError, match="identity_invalid"):
        with direct_job(tmp_path, "pre_submit_delay", "2026-10-08"):
            pass


def test_synchronous_heavy_worker_cannot_duplicate_one_reserved_slot(tmp_path):
    from src.engine.lifecycle.research_admission import acquire, Reservation, direct_job

    one = acquire(tmp_path, "summary_handoff", "2026-10-08")
    forged = Reservation(
        [one.handles[0], one.handles[0]],
        data_root=tmp_path,
        stage="pre_submit_delay",
        day="2026-10-08",
    )
    try:
        with forged.worker(), pytest.raises(ValueError, match="descriptor_invalid"):
            with direct_job(tmp_path, "pre_submit_delay", "2026-10-08"):
                pass
    finally:
        one.close()


def test_quantity_cli_waits_for_heavy_predecessor_beyond_sixty_seconds(
    tmp_path, monkeypatch
):
    from contextlib import nullcontext
    from src.engine.lifecycle import research_admission as admission
    from src.engine.lifecycle import research_disk_budget
    from src.engine.scalping import initial_quantity_policy as policy

    clock = [0.0]
    predecessor = acquire(tmp_path, "pre_submit_delay", "2026-10-13")
    monkeypatch.setattr(admission.time, "monotonic", lambda: clock[0])

    def advance(_):
        clock[0] += 31
        if clock[0] >= 90 and predecessor.handles:
            predecessor.close()

    monkeypatch.setattr(admission.time, "sleep", advance)
    monkeypatch.setattr(research_disk_budget, "use", lambda *a: nullcontext())
    monkeypatch.setattr(policy, "_main_impl", lambda argv: 17)
    try:
        assert policy.main(["--as-of", "2026-10-13", "--data-dir", str(tmp_path)]) == 17
        assert clock[0] >= 90
        free = acquire(tmp_path, "main_stop_confirmation", "2026-10-13")
        assert free is not None
        free.close()
    finally:
        predecessor.close()
