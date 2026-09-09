from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
WRAPPER = REPO_ROOT / "deploy/run_postclose_finalization.sh"
TARGET_DATE = "2026-09-02"


def test_storage_lane_recovery_requires_explicit_closed_target_recovery(tmp_path):
    result = subprocess.run(
        ["bash", str(WRAPPER), TARGET_DATE, "", "--recover-storage-only"],
        env={**os.environ, "PROJECT_DIR": str(tmp_path)},
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 2
    assert "unknown_cleanup_recovery_mode" in result.stdout
    script = WRAPPER.read_text()
    assert '"$CLEANUP_RUNNER" 30 "${cleanup_recovery_args[@]}"' in script


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


def _write_ready_predecessors(
    project: Path, *, final_threshold_marker: str = "DONE"
) -> None:
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
    order = (
        order_path.read_text(encoding="utf-8").splitlines()
        if order_path.exists()
        else []
    )
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


@pytest.mark.parametrize("prior_failure", [True, False])
@pytest.mark.parametrize("controller_failed", [True, False])
def test_explicit_recovery_requires_failure_and_retains_source_date(
    tmp_path, prior_failure, controller_failed
):
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo

    day = (datetime.now(ZoneInfo("Asia/Seoul")).date() - timedelta(days=1)).isoformat()
    project = tmp_path / "project"
    (project / "logs").mkdir(parents=True)
    (project / "src").symlink_to(REPO_ROOT / "src", target_is_directory=True)
    (project / "logs/postclose_finalization_cron.log").write_text(
        f"[FAIL] postclose_finalization target_date={day} reason=same_date_hard_deadline\n"
        if prior_failure
        else ""
    )
    controller_dir = project / "data/report/postclose_done_controller"
    controller_dir.mkdir(parents=True)
    (controller_dir / f"postclose_done_controller_{day}.json").write_text(
        json.dumps(
            {"date": day, "status": "failed" if controller_failed else "waiting"}
        ),
        encoding="utf-8",
    )
    detector = project / "detector.sh"
    cleanup = project / "cleanup.sh"
    _write_executable(detector, 'printf "%s\\n" "$@" > "$PROJECT_DIR/detector-args"\n')
    _write_executable(cleanup, 'touch "$PROJECT_DIR/cleanup-called"\n')
    _write_executable(
        project / "bin/systemctl",
        'printf "LoadState=masked\\nUnitFileState=masked\\nActiveState=inactive\\n"\n',
    )
    env = _base_env(project, cleanup, detector)
    env["PATH"] = str(project / "bin") + os.pathsep + env.get("PATH", os.defpath)
    # Fixture-only predecessor status; never inspect the host's actual units.
    result = subprocess.run(
        ["bash", str(WRAPPER), day, "--recover-closed-target"],
        env=env,
        text=True,
        capture_output=True,
    )
    assert result.returncode != 0
    assert not (project / "cleanup-called").exists()
    if prior_failure:
        reason = (
            "predecessor_terminal_failure"
            if controller_failed
            else "predecessor_timeout"
        )
        assert f"reason={reason}" in result.stdout
        assert (project / "detector-args").read_text().splitlines() == ["full", day]
    else:
        assert "recovery_requires_prior_failure" in result.stdout
        assert not (project / "detector-args").exists()


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

    assert "POSTCLOSE_FINALIZATION_WAIT_TIMEOUT_SEC:-5100" in script
    assert "POSTCLOSE_FINALIZATION_HARD_DEADLINE_KST:-23:20" in script
    assert "POSTCLOSE_FINALIZATION_CLEANUP_TIMEOUT_SEC:-600" in script
    assert "POSTCLOSE_FINALIZATION_DETECTOR_TIMEOUT_SEC:-600" in script
    assert "POSTCLOSE_FINALIZATION_SUMMARY_TIMEOUT_SEC:-600" in script
    assert script.count('timeout --foreground "${') == 2
    assert 'timeout --kill-after=10s "${SUMMARY_TIMEOUT_SEC}s"' in script
    assert "reason=same_date_hard_deadline" in script


@pytest.mark.parametrize("refresh_rc", [0, 9])
def test_late_summary_refresh_precedes_cleanup_and_failure_cannot_reuse_done(
    tmp_path, monkeypatch, refresh_rc
):
    monkeypatch.setattr(sys.modules[__name__], "TARGET_DATE", "2026-09-09")
    project = tmp_path / "project"
    project.mkdir()
    (project / "src").symlink_to(REPO_ROOT / "src", target_is_directory=True)
    _write_ready_predecessors(project)
    from src.engine.automation.postclose_recommendation_intake import source_paths

    for path in source_paths(project / "data/report", TARGET_DATE).values():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"target_date": TARGET_DATE}), encoding="utf-8")
    cleanup, detector = project / "bin/cleanup.sh", project / "bin/detector.sh"
    _write_executable(cleanup, 'printf "cleanup\\n" >> "$PROJECT_DIR/order.txt"\n')
    _write_executable(detector, 'printf "detector\\n" >> "$PROJECT_DIR/order.txt"\n')
    systemctl = project / "bin/systemctl"
    _write_executable(
        systemctl,
        "printf '%s\\n' 'LoadState=loaded' 'UnitFileState=static' 'ActiveState=inactive' 'Result=success' 'ExecMainStartTimestamp=2026-09-09 21:15:00 KST'\n",
    )
    python = project / "bin/python"
    _write_executable(
        python,
        'if [[ "${1:-}" == "-m" ]]; then\n'
        '  [[ "$2" == "src.engine.automation.postclose_done_controller" ]]\n'
        '  [[ " $* " == *" --summary-handoff-only "* ]]\n'
        '  printf "summary\\n" >> "$PROJECT_DIR/order.txt"\n'
        f'  exit {refresh_rc}\nfi\nexec "$REAL_PY" "$@"\n',
    )
    env = {
        **_base_env(project, cleanup, detector),
        "VENV_PY": str(python),
        "REAL_PY": sys.executable,
        "PATH": f"{project / 'bin'}:{os.environ['PATH']}",
    }
    result = subprocess.run(
        ["bash", str(WRAPPER), TARGET_DATE], env=env, text=True, capture_output=True
    )
    assert result.returncode == (0 if refresh_rc == 0 else 1), (
        result.stdout + result.stderr
    )
    assert (project / "order.txt").read_text().splitlines() == (
        ["summary", "cleanup", "detector"]
        if refresh_rc == 0
        else ["summary", "detector"]
    )
