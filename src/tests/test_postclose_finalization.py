from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WRAPPER = REPO_ROOT / "deploy/run_postclose_finalization.sh"
TARGET_DATE = "2026-09-02"


def _write_executable(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/usr/bin/env bash\nset -euo pipefail\n" + body, encoding="utf-8")
    path.chmod(0o755)


def _base_env(project: Path, cleanup: Path, detector: Path) -> dict[str, str]:
    return {
        **os.environ,
        "PROJECT_DIR": str(project),
        "VENV_PY": sys.executable,
        "POSTCLOSE_FINALIZATION_ALLOW_NONCURRENT_TARGET": "true",
        "POSTCLOSE_FINALIZATION_WAIT_TIMEOUT_SEC": "0",
        "POSTCLOSE_FINALIZATION_POLL_SEC": "1",
        "POSTCLOSE_FINALIZATION_CLEANUP_RUNNER": str(cleanup),
        "POSTCLOSE_FINALIZATION_ERROR_DETECTION_RUNNER": str(detector),
    }


def _write_ready_predecessors(project: Path, *, final_threshold_marker: str = "DONE") -> None:
    threshold_dir = project / "data/report/threshold_cycle_postclose_status"
    controller_dir = project / "data/report/postclose_done_controller"
    tuning_dir = project / "data/report/tuning_monitoring/status"
    log_dir = project / "logs"
    for path in (threshold_dir, controller_dir, tuning_dir, log_dir):
        path.mkdir(parents=True, exist_ok=True)
    (threshold_dir / f"threshold_cycle_postclose_{TARGET_DATE}.status.json").write_text(
        json.dumps({"target_date": TARGET_DATE, "status": "succeeded", "exit_code": 0}),
        encoding="utf-8",
    )
    (controller_dir / f"postclose_done_controller_{TARGET_DATE}.json").write_text(
        json.dumps({"date": TARGET_DATE, "status": "done"}),
        encoding="utf-8",
    )
    (tuning_dir / f"tuning_monitoring_postclose_{TARGET_DATE}.json").write_text(
        json.dumps({"target_date": TARGET_DATE, "status": "success", "exit_code": 0}),
        encoding="utf-8",
    )
    (log_dir / "threshold_cycle_postclose_cron.log").write_text(
        f"[DONE] threshold-cycle postclose target_date={TARGET_DATE}\n"
        + (
            f"[START] threshold-cycle postclose target_date={TARGET_DATE}\n"
            if final_threshold_marker == "START"
            else ""
        ),
        encoding="utf-8",
    )
    (log_dir / "postclose_done_controller_cron.log").write_text(
        f"[DONE] postclose_done_controller target_date={TARGET_DATE}\n",
        encoding="utf-8",
    )
    (log_dir / "tuning_monitoring_postclose_cron.log").write_text(
        f"[DONE] tuning_monitoring_postclose target_date={TARGET_DATE}\n",
        encoding="utf-8",
    )
    (log_dir / "dashboard_db_archive_cron.log").write_text(
        f"[DONE] dashboard_db_archive target_date={TARGET_DATE}\n",
        encoding="utf-8",
    )


def _run(
    tmp_path: Path,
    *,
    ready: bool,
    final_threshold_marker: str = "DONE",
    controller_status: str = "done",
    cleanup_exit_code: int = 0,
    detector_exit_code: int = 0,
):
    project = tmp_path / "project"
    project.mkdir()
    order_path = project / "order.txt"
    cleanup = project / "bin/cleanup.sh"
    detector = project / "bin/detector.sh"
    _write_executable(
        cleanup,
        'printf "cleanup\\n" >> "$PROJECT_DIR/order.txt"\n'
        f"exit {cleanup_exit_code}\n",
    )
    _write_executable(
        detector,
        'printf "detector\\n" >> "$PROJECT_DIR/order.txt"\n'
        f"exit {detector_exit_code}\n",
    )
    if ready:
        _write_ready_predecessors(
            project, final_threshold_marker=final_threshold_marker
        )
        controller_path = (
            project
            / "data/report/postclose_done_controller"
            / f"postclose_done_controller_{TARGET_DATE}.json"
        )
        controller_path.write_text(
            json.dumps({"date": TARGET_DATE, "status": controller_status}),
            encoding="utf-8",
        )
    result = subprocess.run(
        ["bash", str(WRAPPER), TARGET_DATE],
        cwd=REPO_ROOT,
        env=_base_env(project, cleanup, detector),
        text=True,
        capture_output=True,
        check=False,
    )
    order = order_path.read_text(encoding="utf-8").splitlines() if order_path.exists() else []
    return result, order


def test_finalization_waits_for_exact_terminal_chain_then_cleans_and_detects(tmp_path):
    result, order = _run(tmp_path, ready=True)

    assert result.returncode == 0, result.stdout + result.stderr
    assert order == ["cleanup", "detector"]
    assert "predecessors_ready" in result.stdout
    finalization_done = result.stdout.index("[DONE] postclose_finalization")
    detector_done = result.stdout.index("[DONE] postclose_final_detector")
    assert finalization_done < detector_done
    assert "detector_handoff=started" in result.stdout


def test_finalization_timeout_preserves_cleanup_and_still_runs_detector(tmp_path):
    result, order = _run(tmp_path, ready=False)

    assert result.returncode == 1
    assert order == ["detector"]
    assert "reason=predecessor_timeout" in result.stdout


def test_finalization_rejects_start_after_done_as_nonterminal(tmp_path):
    result, order = _run(tmp_path, ready=True, final_threshold_marker="START")

    assert result.returncode == 1
    assert order == ["detector"]
    assert "threshold_log" in result.stdout


def test_finalization_treats_prefixed_controller_block_as_terminal_failure(tmp_path):
    result, order = _run(
        tmp_path,
        ready=True,
        controller_status="blocked_structural_contract_gap",
    )

    assert result.returncode == 1
    assert order == ["detector"]
    assert "reason=predecessor_terminal_failure" in result.stdout
    assert "controller_artifact" in result.stdout
    assert "reason=predecessor_timeout" not in result.stdout


def test_final_detector_failure_overrides_pre_detector_done_marker(tmp_path):
    result, order = _run(tmp_path, ready=True, detector_exit_code=7)

    assert result.returncode == 1
    assert order == ["cleanup", "detector"]
    assert "[DONE] postclose_finalization" in result.stdout
    assert "[FAIL] postclose_finalization" in result.stdout
    assert "[DONE] postclose_final_detector" not in result.stdout
    assert result.stdout.rindex("[FAIL] postclose_finalization") > result.stdout.index(
        "[DONE] postclose_finalization"
    )


def test_cleanup_failure_preserves_detector_handoff_but_not_success_marker(tmp_path):
    result, order = _run(tmp_path, ready=True, cleanup_exit_code=9)

    assert result.returncode == 1
    assert order == ["cleanup", "detector"]
    assert "reason=cleanup_failed" in result.stdout
    assert "[DONE] postclose_finalization" not in result.stdout


def test_finalization_reserves_same_date_margin_before_midnight():
    script = WRAPPER.read_text(encoding="utf-8")

    assert 'POSTCLOSE_FINALIZATION_WAIT_TIMEOUT_SEC:-5100' in script
    assert 'POSTCLOSE_FINALIZATION_HARD_DEADLINE_KST:-23:20' in script
    assert 'POSTCLOSE_FINALIZATION_CLEANUP_TIMEOUT_SEC:-600' in script
    assert 'POSTCLOSE_FINALIZATION_DETECTOR_TIMEOUT_SEC:-600' in script
    assert script.count('timeout --foreground "${') == 2
    assert "reason=same_date_hard_deadline" in script
