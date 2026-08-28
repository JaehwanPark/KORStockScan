from __future__ import annotations

import gzip
import json
import os
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]


def _base_env(project_root: Path) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "PROJECT_DIR": str(project_root),
            "LOG_ROTATION_ACTIVE_MAX_BYTES": "8",
            "OWNED_LOG_ROTATION_LOCK_WAIT_SEC": "1",
            "TARGET_DATE": "2026-08-28",
        }
    )
    return env


def test_owned_log_writer_rotates_quiescent_active_with_verified_receipt(tmp_path):
    project_root = tmp_path / "project"
    log_path = project_root / "logs" / "writer.log"
    log_path.parent.mkdir(parents=True)
    original = "closed-generation\n" * 4
    log_path.write_text(original, encoding="utf-8")

    result = subprocess.run(
        [
            "bash",
            "deploy/run_with_owned_log.sh",
            "--owner",
            "test_writer",
            "--log",
            str(log_path),
            "bash",
            "-c",
            "printf 'new-generation\\n'",
        ],
        cwd=REPO_ROOT,
        env=_base_env(project_root),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "new-generation" in log_path.read_text(encoding="utf-8")
    archives = list(log_path.parent.glob("writer.log.generation_*.gz"))
    assert len(archives) == 1
    with gzip.open(archives[0], "rt", encoding="utf-8") as handle:
        assert handle.read() == original
    receipts = (
        project_root
        / "data"
        / "report"
        / "log_writer_rollover_receipts"
        / "log_writer_rollover_2026-08-28.jsonl"
    )
    rows = [json.loads(line) for line in receipts.read_text().splitlines()]
    assert rows[-1]["status"] == "rotated_verified"
    assert rows[-1]["writer_owner"] == "test_writer"
    assert rows[-1]["runtime_effect"] is False
    assert rows[-1]["source_size_bytes"] == len(original.encode())


def test_owned_log_rotation_defers_open_inode_without_mutation(tmp_path):
    project_root = tmp_path / "project"
    log_path = project_root / "logs" / "writer.log"
    log_path.parent.mkdir(parents=True)
    original = "open-generation\n" * 4
    log_path.write_text(original, encoding="utf-8")
    original_inode = log_path.stat().st_ino

    with log_path.open("rb"):
        result = subprocess.run(
            [
                "bash",
                "deploy/run_owned_log_rotation.sh",
                "test_writer",
                str(log_path),
            ],
            cwd=REPO_ROOT,
            env=_base_env(project_root),
            text=True,
            capture_output=True,
            check=False,
        )

    assert result.returncode == 0
    assert log_path.stat().st_ino == original_inode
    assert log_path.read_text(encoding="utf-8") == original
    assert not list(log_path.parent.glob("writer.log.generation_*.gz"))
    assert "reason=active_inode_open" in result.stderr
    receipt_path = (
        project_root
        / "data"
        / "report"
        / "log_writer_rollover_receipts"
        / "log_writer_rollover_2026-08-28.jsonl"
    )
    row = json.loads(receipt_path.read_text().splitlines()[-1])
    assert row["status"] == "deferred_writer_active"
    assert row["archive_path"] == "not_available"


def test_owned_log_writer_deduplicates_same_content_generation(tmp_path):
    project_root = tmp_path / "project"
    log_path = project_root / "logs" / "writer.log"
    log_path.parent.mkdir(parents=True)
    original = "same-generation\n" * 4

    for _ in range(2):
        log_path.write_text(original, encoding="utf-8")
        result = subprocess.run(
            [
                "bash",
                "deploy/run_owned_log_rotation.sh",
                "test_writer",
                str(log_path),
            ],
            cwd=REPO_ROOT,
            env=_base_env(project_root),
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0

    assert len(list(log_path.parent.glob("writer.log.generation_*.gz"))) == 1
    assert log_path.read_text(encoding="utf-8") == ""


@pytest.mark.parametrize(
    ("installer", "owner"),
    [
        ("deploy/install_error_detection_cron.sh", "error_detection_cron"),
        (
            "deploy/install_stage2_ops_cron.sh",
            "rising_missed_intraday_feedback_cron",
        ),
        ("deploy/install_panic_sell_defense_cron.sh", "panic_sell_defense_cron"),
        ("deploy/install_threshold_cycle_cron.sh", "threshold_cycle_preopen_cron"),
        ("deploy/install_threshold_cycle_cron.sh", "threshold_cycle_postclose_cron"),
        ("deploy/install_eod_data_chain_cron.sh", "log_rotation_cleanup_cron"),
    ],
)
def test_installed_log_writers_use_owner_wrapper(installer: str, owner: str):
    script = (REPO_ROOT / installer).read_text(encoding="utf-8")

    assert "run_with_owned_log.sh" in script
    assert f"--owner {owner}" in script
