"""Unit tests for fetch_remote_scalping_logs module."""

from unittest.mock import patch, MagicMock
import pytest
from pathlib import Path

from src.engine.fetch_remote_scalping_logs import (
    _build_remote_paths,
    _build_optional_snapshot_paths,
    _build_remote_tar_command,
    _build_remote_tar_command_with_optional_snapshots,
    fetch_remote_scalping_logs,
)


def test_build_remote_paths():
    remote_root = "/home/windy80xyt/KORStockScan"
    target_date = "2026-04-10"
    paths = _build_remote_paths(remote_root, target_date)
    expected = [
        f"{remote_root}/logs/sniper_state_handlers_info.log",
        f"{remote_root}/logs/sniper_execution_receipts_info.log",
        f"{remote_root}/data/pipeline_events/pipeline_events_{target_date}.jsonl",
        f"{remote_root}/data/post_sell/post_sell_candidates_{target_date}.jsonl",
        f"{remote_root}/data/post_sell/post_sell_evaluations_{target_date}.jsonl",
    ]
    assert paths == expected


def test_build_optional_snapshot_paths():
    remote_root = "/home/windy80xyt/KORStockScan"
    target_date = "2026-04-10"
    paths = _build_optional_snapshot_paths(remote_root, target_date)
    expected = [
        f"{remote_root}/data/report/monitor_snapshots/trade_review_{target_date}.json",
        f"{remote_root}/data/report/monitor_snapshots/post_sell_feedback_{target_date}.json",
        f"{remote_root}/data/report/monitor_snapshots/performance_tuning_{target_date}.json",
    ]
    assert paths == expected


def test_build_remote_tar_command():
    paths = ["/home/user/file1.log", "/home/user/file2.jsonl"]
    cmd = _build_remote_tar_command(paths)
    # Check that the command contains essential components
    assert "set -euo pipefail" in cmd
    assert "tmpdir=$(mktemp -d)" in cmd
    assert "cp -p" in cmd
    assert 'tar -czf - .' in cmd
    # Ensure each path is quoted and appears in the array
    for path in paths:
        assert path in cmd


def test_build_remote_tar_command_with_optional_snapshots():
    required = ["/home/user/req1.log"]
    optional = ["/home/user/opt1.json"]
    cmd = _build_remote_tar_command_with_optional_snapshots(required, optional)
    assert "set -euo pipefail" in cmd
    assert "tmpdir=$(mktemp -d)" in cmd
    assert "cp -p" in cmd
    assert 'tar -czf - .' in cmd


@patch("src.engine.fetch_remote_scalping_logs.subprocess.run")
def test_fetch_remote_scalping_logs_success(mock_run):
    mock_run.side_effect = [
        MagicMock(),  # ssh tar command
        MagicMock(),  # local tar extract
    ]
    result = fetch_remote_scalping_logs(
        target_date="2026-04-10",
        host="example.com",
        user="user",
        remote_root="/remote",
        local_root=Path("/tmp/test_fetch_success"),
        include_snapshots_if_exist=False,
        snapshot_only_on_live_failure=False,
    )
    
    @patch("src.engine.fetch_remote_scalping_logs.subprocess.run")
    def test_fetch_remote_scalping_logs_live_failure_no_fallback_exit1_no_message(mock_run):
        from subprocess import CalledProcessError
        mock_run.side_effect = CalledProcessError(1, "ssh", stderr=b"some other error")
        with pytest.raises(CalledProcessError):
            fetch_remote_scalping_logs(
                target_date="2026-04-10",
                host="example.com",
                user="user",
                remote_root="/remote",
                local_root=Path("/tmp/test_fetch_no_fallback"),
                include_snapshots_if_exist=False,
                snapshot_only_on_live_failure=True,
            )
    
    @patch("src.engine.fetch_remote_scalping_logs.subprocess.run")
    def test_fetch_remote_scalping_logs_live_failure_no_fallback_exit2(mock_run):
        from subprocess import CalledProcessError
        mock_run.side_effect = CalledProcessError(2, "ssh")
        with pytest.raises(CalledProcessError):
            fetch_remote_scalping_logs(
                target_date="2026-04-10",
                host="example.com",
                user="user",
                remote_root="/remote",
                local_root=Path("/tmp/test_fetch_no_fallback"),
                include_snapshots_if_exist=False,
                snapshot_only_on_live_failure=True,
            )
    assert result["date"] == "2026-04-10"
    assert "archive_path" in result
    assert "output_dir" in result
    assert mock_run.call_count == 2


@patch("src.engine.fetch_remote_scalping_logs.subprocess.run")
def test_fetch_remote_scalping_logs_live_failure_fallback(mock_run):
    # First ssh call raises CalledProcessError with exit 1 and race message, second succeeds
    from subprocess import CalledProcessError
    mock_run.side_effect = [
        CalledProcessError(1, "ssh", stderr=b"tar: file changed as we read it"),
        MagicMock(),  # fallback snapshot-only ssh
        MagicMock(),  # local tar extract
    ]
    result = fetch_remote_scalping_logs(
        target_date="2026-04-10",
        host="example.com",
        user="user",
        remote_root="/remote",
        local_root=Path("/tmp/test_fetch_fallback"),
        include_snapshots_if_exist=False,
        snapshot_only_on_live_failure=True,
    )
    assert result["date"] == "2026-04-10"
    # Should have called subprocess.run 3 times (1 fail + 1 success + extract)
    assert mock_run.call_count == 3


@patch("src.engine.fetch_remote_scalping_logs.subprocess.run")
def test_fetch_remote_scalping_logs_live_failure_no_fallback(mock_run):
    from subprocess import CalledProcessError
    mock_run.side_effect = CalledProcessError(1, "ssh")
    with pytest.raises(CalledProcessError):
        fetch_remote_scalping_logs(
            target_date="2026-04-10",
            host="example.com",
            user="user",
            remote_root="/remote",
            local_root=Path("/tmp/test_fetch_no_fallback"),
            include_snapshots_if_exist=False,
            snapshot_only_on_live_failure=False,
        )