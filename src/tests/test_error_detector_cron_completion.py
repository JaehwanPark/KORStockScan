from __future__ import annotations

import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

import pytest

from src.engine.error_detectors.cron_completion import CronCompletionDetector


@pytest.fixture(autouse=True)
def _force_trading_day(monkeypatch):
    import src.engine.error_detectors.cron_completion as cc

    monkeypatch.setattr(cc, "is_krx_trading_day", lambda target: True)


class TestCronCompletionDetector:
    def test_pass_when_log_not_yet_due(self):
        detector = CronCompletionDetector()
        with _mock_time(5, 0):
            result = detector.check()
        assert result.severity in ("pass", "warning", "fail")

    def test_pass_when_recent_log_has_done(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test_ok.log"
            log_file.write_text(
                "[START] test job\n[DONE] test job completed successfully\n",
                encoding="utf-8",
            )
            detector = CronCompletionDetector()
            result = detector._read_tail(log_file, 100)
            assert "DONE" in result

    def test_warning_when_log_has_errors(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test_error.log"
            log_file.write_text(
                "[START] test job\n[FAIL] error occurred\n[ERROR] something broke\n",
                encoding="utf-8",
            )
            detector = CronCompletionDetector()
            result = detector._read_tail(log_file, 100)
            assert "FAIL" in result
            assert "ERROR" in result

    def test_count_errors(self):
        text = "[START] begin\n[ERROR] first\n[FAIL] second\n[DONE] ok"
        detector = CronCompletionDetector()
        assert detector._count_errors(text) == 2

    def test_count_errors_no_match(self):
        detector = CronCompletionDetector()
        assert detector._count_errors("[DONE] all good") == 0

    def test_read_tail_nonexistent(self):
        detector = CronCompletionDetector()
        result = detector._read_tail(Path("/nonexistent/log.log"), 100)
        assert result == ""

    def test_read_tail_includes_rotated_numeric_logs(self, tmp_path):
        log_file = tmp_path / "threshold_cycle_postclose_cron.log"
        (tmp_path / "threshold_cycle_postclose_cron.log.1").write_text(
            "[START] threshold-cycle postclose target_date=2026-05-22\n"
            "[DONE] threshold-cycle postclose target_date=2026-05-22\n",
            encoding="utf-8",
        )
        log_file.write_text("", encoding="utf-8")

        result = CronCompletionDetector._read_tail(log_file, 100)

        assert "target_date=2026-05-22" in result
        assert "[DONE] threshold-cycle postclose" in result

    def test_last_terminal_marker_fail_after_done(self):
        detector = CronCompletionDetector()
        lines = "[DONE] target_date=2026-05-09\n[FAIL] target_date=2026-05-09\n"
        assert detector._last_terminal_marker(lines) == "error"

    def test_last_terminal_marker_done_after_fail(self):
        detector = CronCompletionDetector()
        lines = "[FAIL] target_date=2026-05-09\n[DONE] target_date=2026-05-09\n"
        assert detector._last_terminal_marker(lines) == "done"

    def test_last_terminal_marker_none(self):
        detector = CronCompletionDetector()
        lines = "just noise\nno markers\n"
        assert detector._last_terminal_marker(lines) == "none"

    def test_filter_today_lines_excludes_other_dates(self):
        detector = CronCompletionDetector()
        lines = "[DONE] target_date=2026-05-08\n[FAIL] target_date=2026-05-09\n[DONE] target_date=2026-05-09\n"
        filtered = detector._filter_today_lines(lines, "2026-05-09")
        assert "2026-05-08" not in filtered
        assert "[FAIL]" in filtered
        assert filtered.count("[DONE]") == 1

    def test_update_kospi_start_only_before_extended_window_end_is_not_fail(self, monkeypatch, tmp_path):
        import src.engine.error_detectors.cron_completion as cc

        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(parents=True)
        (logs_dir / "update_kospi.log").write_text(
            "[START] update_kospi target_date=2026-05-12 started_at=2026-05-12T21:00:03+0900\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(cc, "PROJECT_ROOT", tmp_path)
        monkeypatch.setattr(cc, "_today_kst", lambda: "2026-05-12")

        with _mock_time(21, 16):
            result = CronCompletionDetector().check()

        assert "update_kospi: no completion marker after window end" not in result.summary

    def test_long_verbose_log_keeps_once_job_done_marker_visible(self, monkeypatch, tmp_path):
        import src.engine.error_detectors.cron_completion as cc

        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(parents=True)
        noise = "\n".join(f'{{"row": {idx}, "payload": "verbose report output"}}' for idx in range(300))
        (logs_dir / "threshold_cycle_postclose_cron.log").write_text(
            "\n".join(
                [
                    "[START] threshold-cycle postclose target_date=2026-05-15 started_at=2026-05-15T16:10:01+0900",
                    noise,
                    "[DONE] threshold-cycle postclose target_date=2026-05-15 finished_at=2026-05-15T19:49:19+0900",
                    noise,
                ]
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(cc, "PROJECT_ROOT", tmp_path)
        monkeypatch.setattr(cc, "_today_kst", lambda: "2026-05-15")
        monkeypatch.setattr(
            cc,
            "CRON_JOB_REGISTRY",
            [
                {
                    "id": "threshold_cycle_postclose",
                    "log": "logs/threshold_cycle_postclose_cron.log",
                    "window_start": (16, 10),
                    "window_end": (17, 0),
                    "mode": "once",
                    "critical": True,
                }
            ],
        )

        with _mock_time(19, 55):
            result = CronCompletionDetector().check()

        assert result.severity == "pass"
        assert result.details["threshold_cycle_postclose_status"] == "pass"

    def test_rotated_once_job_done_marker_keeps_cron_status_pass(self, monkeypatch, tmp_path):
        import src.engine.error_detectors.cron_completion as cc

        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(parents=True)
        (logs_dir / "threshold_cycle_postclose_cron.log.1").write_text(
            "[START] threshold-cycle postclose target_date=2026-05-22 started_at=2026-05-22T16:10:01+0900\n"
            "[DONE] threshold-cycle postclose target_date=2026-05-22 finished_at=2026-05-22T17:22:41+0900\n",
            encoding="utf-8",
        )
        (logs_dir / "threshold_cycle_postclose_cron.log").write_text("", encoding="utf-8")
        monkeypatch.setattr(cc, "PROJECT_ROOT", tmp_path)
        monkeypatch.setattr(cc, "_today_kst", lambda: "2026-05-22")
        monkeypatch.setattr(
            cc,
            "CRON_JOB_REGISTRY",
            [
                {
                    "id": "threshold_cycle_postclose",
                    "log": "logs/threshold_cycle_postclose_cron.log",
                    "window_start": (16, 10),
                    "window_end": (17, 0),
                    "mode": "once",
                    "critical": True,
                }
            ],
        )

        with _mock_time(23, 25):
            result = CronCompletionDetector().check()

        assert result.severity == "pass"
        assert result.details["threshold_cycle_postclose_status"] == "pass"

    def test_trading_day_only_jobs_skip_on_non_trading_day(self, monkeypatch, tmp_path):
        import src.engine.error_detectors.cron_completion as cc

        monkeypatch.setattr(cc, "PROJECT_ROOT", tmp_path)
        monkeypatch.setattr(cc, "is_krx_trading_day", lambda target: False)
        monkeypatch.setattr(
            cc,
            "CRON_JOB_REGISTRY",
            [
                {
                    "id": "threshold_cycle_preopen",
                    "log": "logs/threshold_cycle_preopen_cron.log",
                    "window_start": (7, 35),
                    "window_end": (7, 50),
                    "mode": "once",
                    "critical": True,
                    "trading_day_only": True,
                }
            ],
        )

        with _mock_time(10, 45):
            result = CronCompletionDetector().check()

        assert result.severity == "pass"
        assert result.details["threshold_cycle_preopen_status"] == "skip_non_trading_day"


@contextmanager
def _mock_time(hour: int, minute: int):
    import src.engine.error_detectors.cron_completion as cc

    class MockNow:
        def __init__(self):
            self.hour = hour
            self.minute = minute

    class MockDatetime:
        @staticmethod
        def now():
            return MockNow()

    orig = cc.datetime
    cc.datetime = MockDatetime
    try:
        yield
    finally:
        cc.datetime = orig
