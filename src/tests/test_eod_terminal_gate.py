from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GATE = ROOT / "deploy/eod_terminal_gate.sh"




def _run_gate(tmp_path: Path, payload: dict) -> subprocess.CompletedProcess[str]:
    target = "2026-09-28"
    status = tmp_path / "data/runtime/update_kospi_status" / f"update_kospi_{target}.json"
    status.parent.mkdir(parents=True)
    status.write_text(json.dumps(payload), encoding="utf-8")
    return subprocess.run(
        [
            "bash",
            "-c",
            'source "$1"; wait_for_eod_terminal "$2" "$3" test 0 1',
            "eod-gate-test",
            str(GATE),
            str(tmp_path),
            target,
        ],
        env=os.environ.copy(),
        capture_output=True,
        text=True,
        check=False,
    )


def test_eod_gate_accepts_exact_date_warning_terminal_with_rows(tmp_path):
    result = _run_gate(
        tmp_path,
        {
            "status": "completed_with_warnings",
            "target_date": "2026-09-28",
            "db_state": {"latest_quote_date": "2026-09-28", "rows_on_latest_date": 13},
        },
    )

    assert result.returncode == 0, result.stderr
    assert "EOD ready target_date=2026-09-28" in result.stdout


def test_eod_gate_rejects_terminal_with_wrong_latest_date(tmp_path):
    result = _run_gate(
        tmp_path,
        {
            "status": "completed",
            "target_date": "2026-09-28",
            "db_state": {"latest_quote_date": "2026-09-25", "rows_on_latest_date": 13},
        },
    )

    assert result.returncode == 1
    assert "terminal contract mismatch" in result.stderr


def test_eod_gate_rejects_failed_terminal_without_waiting(tmp_path):
    result = _run_gate(
        tmp_path,
        {
            "status": "failed",
            "target_date": "2026-09-28",
            "db_state": {"latest_quote_date": "2026-09-28", "rows_on_latest_date": 13},
        },
    )

    assert result.returncode == 1
    assert "EOD failed target_date=2026-09-28" in result.stderr


def test_eod_gates_precede_surviving_machine_dispatch():
    assert not (ROOT / "deploy/run_widget_evaluation.sh").exists()
    assert not (ROOT / "deploy/run_machine_microstructure_final_refresh.sh").exists()
    assert not (ROOT / "deploy/install_postclose_eod_gate_systemd.sh").exists()
    threshold = (ROOT / "deploy/run_threshold_cycle_postclose.sh").read_text(encoding="utf-8")

    start_marker = threshold.index('emit_postclose_marker "[START] threshold-cycle')
    gate = threshold.index('wait_for_eod_terminal "$PROJECT_DIR"', start_marker)
    assert gate < threshold.index("stop_postclose_bot_if_requested", start_marker)
    assert gate < threshold.index('--stage main_machine_policy --date "$TARGET_DATE"', start_marker)
