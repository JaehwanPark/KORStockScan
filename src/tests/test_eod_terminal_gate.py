from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

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


@pytest.mark.parametrize('day', ['2026-10-09', '2026-10-10'])
def test_dashboard_archive_holiday_skips_before_eod_or_compression(tmp_path, day):
    (tmp_path / '.venv').symlink_to(ROOT / '.venv', target_is_directory=True)
    (tmp_path / 'src').symlink_to(ROOT / 'src', target_is_directory=True)
    result = subprocess.run(
        ['bash', str(ROOT / 'deploy/run_dashboard_db_archive_cron.sh'), '0'],
        env={**os.environ, 'PROJECT_DIR': str(tmp_path), 'TARGET_DATE': day,
             'DASHBOARD_ARCHIVE_EOD_WAIT_SEC': '0'},
        capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert f'[SKIP] dashboard_db_archive target_date={day}' in result.stdout
    assert 'no_archive_mutation=true' in result.stdout
    assert '[DONE]' not in result.stdout and 'EOD' not in result.stdout
    assert not (tmp_path / 'logs/dashboard_db_archive.log').exists()


def test_dashboard_archive_trading_day_missing_eod_still_fails(tmp_path):
    (tmp_path / '.venv').symlink_to(ROOT / '.venv', target_is_directory=True)
    (tmp_path / 'src').symlink_to(ROOT / 'src', target_is_directory=True)
    result = subprocess.run(
        ['bash', str(ROOT / 'deploy/run_dashboard_db_archive_cron.sh'), '0'],
        env={**os.environ, 'PROJECT_DIR': str(tmp_path), 'TARGET_DATE': '2026-10-08',
             'DASHBOARD_ARCHIVE_EOD_WAIT_SEC': '0'},
        capture_output=True, text=True, timeout=15,
    )
    assert result.returncode != 0
    assert '[FAIL] dashboard_db_archive target_date=2026-10-08' in result.stdout
    assert 'EOD wait timeout' in result.stderr
    assert '[DONE]' not in result.stdout
    assert not (tmp_path / 'logs/dashboard_db_archive.log').exists()
