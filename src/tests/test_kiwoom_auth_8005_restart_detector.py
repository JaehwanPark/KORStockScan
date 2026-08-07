from __future__ import annotations

import json
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from src.engine.error_detectors.kiwoom_auth_8005_restart import (
    KiwoomAuth8005RestartDetector,
)


class TestKiwoomAuth8005RestartDetector:
    def setup_method(self, method):
        import src.engine.error_detectors.kiwoom_auth_8005_restart as detector_module

        self._tmp_state_dir = tempfile.TemporaryDirectory()
        self._orig_scan_state_path = detector_module.SCAN_STATE_PATH
        self._orig_restart_flag_path = detector_module.RESTART_FLAG_PATH
        self._scan_state_path = Path(self._tmp_state_dir.name) / "scan_state.json"
        self._restart_flag_path = Path(self._tmp_state_dir.name) / "restart.flag"
        detector_module.SCAN_STATE_PATH = self._scan_state_path
        detector_module.RESTART_FLAG_PATH = self._restart_flag_path

    def teardown_method(self, method):
        import src.engine.error_detectors.kiwoom_auth_8005_restart as detector_module

        detector_module.SCAN_STATE_PATH = self._orig_scan_state_path
        detector_module.RESTART_FLAG_PATH = self._orig_restart_flag_path
        self._tmp_state_dir.cleanup()

    def test_bootstrap_ignores_existing_8005(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            log_file = log_dir / "bot_history.log"
            log_file.write_text(
                "old 인증에 실패했습니다[8005:Token이 유효하지 않습니다]\n",
                encoding="utf-8",
            )
            initial_size = log_file.stat().st_size

            with _mock_logs_dir(log_dir):
                result = KiwoomAuth8005RestartDetector().check()

        assert result.severity == "pass"
        assert result.details["baseline_initialized"] is True
        assert not self._restart_flag_path.exists()
        state = json.loads(self._scan_state_path.read_text(encoding="utf-8"))
        assert state["files"]["bot_history.log"]["position"] == initial_size

    def test_fresh_8005_touches_restart_flag(self, monkeypatch):
        import src.engine.error_detectors.kiwoom_auth_8005_restart as detector_module

        invalidations = []
        monkeypatch.setattr(
            detector_module.kiwoom_utils,
            "invalidate_kiwoom_token_cache",
            lambda reason="": invalidations.append(reason) or True,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            log_file = log_dir / "kiwoom_utils_info.log"
            log_file.write_text("old ok\n", encoding="utf-8")
            self._write_state(log_file, restart_count=0, last_restart_ts=0)
            _append(log_file, "인증에 실패했습니다[8005:Token이 유효하지 않습니다]\n")

            with _mock_logs_dir(log_dir):
                result = KiwoomAuth8005RestartDetector().check()

        assert result.severity == "warning"
        assert self._restart_flag_path.exists()
        assert result.details["restart_requested"] is True
        assert result.details["would_restart"] is True
        assert result.details["fresh_auth_8005_count"] == 1
        assert result.details["token_cache_invalidated"] is True
        assert invalidations == ["error_detector_auth_8005"]

    def test_recovered_8005_does_not_invalidate_cache_or_restart(self, monkeypatch):
        import src.engine.error_detectors.kiwoom_auth_8005_restart as detector_module

        invalidations = []
        monkeypatch.setattr(
            detector_module.kiwoom_utils,
            "invalidate_kiwoom_token_cache",
            lambda reason="": invalidations.append(reason) or True,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            log_file = log_dir / "kiwoom_utils_info.log"
            log_file.write_text("old ok\n", encoding="utf-8")
            self._write_state(log_file, restart_count=0, last_restart_ts=0)
            observed = datetime.now().astimezone()
            stamp = f"[{observed:%Y-%m-%d %H:%M:%S}]"
            _append(
                log_file,
                f"{stamp} [ka10004] API 거절: 인증 실패[8005:Token invalid]\n",
            )
            _append(
                log_file,
                f"{stamp} [TOKEN HANDOFF] source=api_8005_retry:ka10004:retry_success\n",
            )
            _append(
                log_file,
                f"{stamp} [TOKEN HANDOFF] source=websocket_login_ack_success\n",
            )

            with _mock_logs_dir(log_dir):
                result = KiwoomAuth8005RestartDetector().check()

        assert result.severity == "pass"
        assert result.details["recovered_auth_8005_count"] == 1
        assert result.details["recovery_state"] == "recovered_without_restart"
        assert result.details["recovery_reason"] == (
            "same_runtime_retry_and_handoff_succeeded"
        )
        assert result.details["restart_requested"] is False
        assert result.details["token_cache_invalidated"] is False
        assert invalidations == []
        assert not self._restart_flag_path.exists()

    def test_8005_after_retry_success_remains_actionable(self, monkeypatch):
        import src.engine.error_detectors.kiwoom_auth_8005_restart as detector_module

        invalidations = []
        monkeypatch.setattr(
            detector_module.kiwoom_utils,
            "invalidate_kiwoom_token_cache",
            lambda reason="": invalidations.append(reason) or True,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            log_file = log_dir / "kiwoom_utils_info.log"
            log_file.write_text("old ok\n", encoding="utf-8")
            self._write_state(log_file, restart_count=0, last_restart_ts=0)
            observed = datetime.now().astimezone()
            recovered_stamp = f"[{observed:%Y-%m-%d %H:%M:%S}]"
            _append(
                log_file,
                f"{recovered_stamp} [ka10004] 인증 실패[8005:Token invalid]\n",
            )
            _append(
                log_file,
                f"{recovered_stamp} [TOKEN HANDOFF] source=api_8005_retry:ka10004:retry_success\n",
            )
            _append(
                log_file,
                f"{recovered_stamp} [ka10004] 인증 실패[8005:Token invalid]\n",
            )

            with _mock_logs_dir(log_dir):
                result = KiwoomAuth8005RestartDetector().check()

        assert result.severity == "warning"
        assert result.details["recovered_auth_8005_count"] == 1
        assert result.details["fresh_auth_8005_count"] == 1
        assert result.details["restart_requested"] is True
        assert invalidations == ["error_detector_auth_8005"]
        assert self._restart_flag_path.exists()

    def test_unrelated_api_retry_success_does_not_suppress_8005(self, monkeypatch):
        import src.engine.error_detectors.kiwoom_auth_8005_restart as detector_module

        invalidations = []
        monkeypatch.setattr(
            detector_module.kiwoom_utils,
            "invalidate_kiwoom_token_cache",
            lambda reason="": invalidations.append(reason) or True,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            log_file = log_dir / "kiwoom_utils_info.log"
            log_file.write_text("old ok\n", encoding="utf-8")
            self._write_state(log_file, restart_count=0, last_restart_ts=0)
            observed = datetime.now().astimezone()
            stamp = f"[{observed:%Y-%m-%d %H:%M:%S}]"
            _append(
                log_file,
                f"{stamp} [ka10004] 인증 실패[8005:Token invalid]\n",
            )
            _append(
                log_file,
                f"{stamp} [TOKEN HANDOFF] source=api_8005_retry:ka10001:retry_success\n",
            )

            with _mock_logs_dir(log_dir):
                result = KiwoomAuth8005RestartDetector().check()

        assert result.severity == "warning"
        assert result.details["fresh_auth_8005_count"] == 1
        assert result.details["restart_requested"] is True
        assert invalidations == ["error_detector_auth_8005"]
        assert self._restart_flag_path.exists()

    def test_dry_run_would_restart_without_touching_flag(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            log_file = log_dir / "kiwoom_orders_error.log"
            log_file.write_text("old ok\n", encoding="utf-8")
            self._write_state(log_file, restart_count=0, last_restart_ts=0)
            _append(
                log_file,
                "[매수거절] 인증에 실패했습니다[8005:Token이 유효하지 않습니다]\n",
            )

            with _mock_logs_dir(log_dir):
                result = KiwoomAuth8005RestartDetector(dry_run=True).check()

        assert result.severity == "warning"
        assert not self._restart_flag_path.exists()
        assert result.details["would_restart"] is True
        assert result.details["restart_requested"] is False

    def test_ignores_fixture_and_error_detection_meta_lines(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            log_file = log_dir / "sniper_state_handlers_error.log"
            log_file.write_text("old ok\n", encoding="utf-8")
            self._write_state(log_file, restart_count=0, last_restart_ts=0)
            _append(
                log_file,
                "[ERROR_DETECTION] TEST(123456) 인증에 실패했습니다[8005:Token이 유효하지 않습니다]\n",
            )

            with _mock_logs_dir(log_dir):
                result = KiwoomAuth8005RestartDetector().check()

        assert result.severity == "pass"
        assert not self._restart_flag_path.exists()

    def test_cooldown_suppresses_duplicate_restart_but_invalidates_token_cache(
        self, monkeypatch
    ):
        import src.engine.error_detectors.kiwoom_auth_8005_restart as detector_module

        invalidations = []
        monkeypatch.setattr(
            detector_module.kiwoom_utils,
            "invalidate_kiwoom_token_cache",
            lambda reason="": invalidations.append(reason) or True,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            log_file = log_dir / "bot_history.log"
            log_file.write_text("old ok\n", encoding="utf-8")
            self._write_state(log_file, restart_count=1, last_restart_ts=time.time())
            _append(log_file, "8005 Token이 유효하지 않습니다\n")

            with _mock_logs_dir(log_dir):
                result = KiwoomAuth8005RestartDetector().check()

        assert result.severity == "warning"
        assert not self._restart_flag_path.exists()
        assert result.details["restart_suppressed_by_cooldown"] is True
        assert result.details["would_restart"] is False
        assert result.details["token_cache_invalidated"] is True
        assert invalidations == ["error_detector_auth_8005"]

    def test_pid_handoff_consumes_prior_runtime_8005_without_alert_or_invalidation(
        self, monkeypatch
    ):
        import src.engine.error_detectors.kiwoom_auth_8005_restart as detector_module

        now = time.time()
        invalidations = []
        monkeypatch.setattr(
            detector_module,
            "_current_runtime_identity",
            lambda: {"pid": 222, "start_ts": now - 5},
        )
        monkeypatch.setattr(
            detector_module.kiwoom_utils,
            "invalidate_kiwoom_token_cache",
            lambda reason="": invalidations.append(reason) or True,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            log_file = log_dir / "kiwoom_utils_info.log"
            log_file.write_text("old ok\n", encoding="utf-8")
            self._write_state(log_file, restart_count=1, last_restart_ts=now - 10)
            prior_at = datetime.fromtimestamp(now - 7).astimezone()
            _append(
                log_file,
                f"[{prior_at:%Y-%m-%d %H:%M:%S}] 인증에 실패했습니다[8005:Token이 유효하지 않습니다]\n",
            )

            with _mock_logs_dir(log_dir):
                result = KiwoomAuth8005RestartDetector().check()

        assert result.severity == "pass"
        assert result.details["current_runtime_pid"] == 222
        assert result.details["prior_runtime_auth_8005_count"] == 1
        assert "Prior-runtime" in result.summary
        assert invalidations == []
        assert not self._restart_flag_path.exists()

    def test_pid_handoff_keeps_current_runtime_8005_actionable(self, monkeypatch):
        import src.engine.error_detectors.kiwoom_auth_8005_restart as detector_module

        now = time.time()
        invalidations = []
        monkeypatch.setattr(
            detector_module,
            "_current_runtime_identity",
            lambda: {"pid": 333, "start_ts": now - 5},
        )
        monkeypatch.setattr(
            detector_module.kiwoom_utils,
            "invalidate_kiwoom_token_cache",
            lambda reason="": invalidations.append(reason) or True,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            log_file = log_dir / "kiwoom_utils_info.log"
            log_file.write_text("old ok\n", encoding="utf-8")
            self._write_state(log_file, restart_count=1, last_restart_ts=now - 10)
            prior_at = datetime.fromtimestamp(now - 7).astimezone()
            current_at = datetime.fromtimestamp(now - 3).astimezone()
            _append(
                log_file,
                f"[{prior_at:%Y-%m-%d %H:%M:%S}] 인증에 실패했습니다[8005:Token이 유효하지 않습니다]\n",
            )
            _append(
                log_file,
                f"[{current_at:%Y-%m-%d %H:%M:%S}] 인증에 실패했습니다[8005:Token이 유효하지 않습니다]\n",
            )

            with _mock_logs_dir(log_dir):
                result = KiwoomAuth8005RestartDetector().check()

        assert result.severity == "warning"
        assert result.details["prior_runtime_auth_8005_count"] == 1
        assert result.details["fresh_auth_8005_count"] == 1
        assert result.details["restart_suppressed_by_cooldown"] is True
        assert invalidations == ["error_detector_auth_8005"]

    def test_runtime_identity_rejects_reused_non_bot_pid(self, monkeypatch, tmp_path):
        import src.engine.error_detectors.kiwoom_auth_8005_restart as detector_module

        heartbeat_path = tmp_path / "heartbeat.json"
        proc_root = tmp_path / "proc"
        proc_dir = proc_root / "222"
        proc_dir.mkdir(parents=True)
        heartbeat_path.write_text(
            json.dumps({"main_loop": {"pid": 222}}), encoding="utf-8"
        )
        (proc_dir / "cmdline").write_bytes(b"/usr/bin/python\x00other_job.py\x00")
        monkeypatch.setattr(detector_module, "HEARTBEAT_PATH", heartbeat_path)
        monkeypatch.setattr(detector_module, "PROC_ROOT", proc_root)

        assert detector_module._current_runtime_identity() is None

    def test_runtime_identity_accepts_live_bot_process(self, monkeypatch, tmp_path):
        import src.engine.error_detectors.kiwoom_auth_8005_restart as detector_module

        heartbeat_path = tmp_path / "heartbeat.json"
        proc_root = tmp_path / "proc"
        proc_dir = proc_root / "333"
        proc_dir.mkdir(parents=True)
        heartbeat_path.write_text(
            json.dumps({"main_loop": {"pid": 333}}), encoding="utf-8"
        )
        (proc_dir / "cmdline").write_bytes(
            b"/home/ubuntu/KORStockScan/.venv/bin/python\x00bot_main.py\x00"
        )
        stat_fields = ["S", *("0" for _ in range(18)), "500"]
        (proc_dir / "stat").write_text(
            f"333 (bot_main.py) {' '.join(stat_fields)}\n", encoding="utf-8"
        )
        (proc_root / "stat").write_text("btime 1000\n", encoding="utf-8")
        monkeypatch.setattr(detector_module, "HEARTBEAT_PATH", heartbeat_path)
        monkeypatch.setattr(detector_module, "PROC_ROOT", proc_root)
        monkeypatch.setattr(detector_module.os, "sysconf", lambda _key: 100)

        assert detector_module._current_runtime_identity() == {
            "pid": 333,
            "start_ts": 1005.0,
        }

    def test_daily_restart_count_threshold_is_fail(self, monkeypatch):
        import src.engine.error_detectors.kiwoom_auth_8005_restart as detector_module

        monkeypatch.setattr(
            detector_module.kiwoom_utils,
            "invalidate_kiwoom_token_cache",
            lambda reason="": True,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            log_file = log_dir / "bot_history.log"
            log_file.write_text("old ok\n", encoding="utf-8")
            self._write_state(log_file, restart_count=2, last_restart_ts=0)
            _append(log_file, "8005 Token이 유효하지 않습니다\n")

            with _mock_logs_dir(log_dir):
                result = KiwoomAuth8005RestartDetector().check()

        assert result.severity == "fail"
        assert self._restart_flag_path.exists()
        assert result.details["restart_count"] == 3
        assert result.details["restart_suppressed_by_daily_cap"] is False

    def test_daily_restart_cap_suppresses_additional_restart_but_invalidates_cache(
        self, monkeypatch
    ):
        import src.engine.error_detectors.kiwoom_auth_8005_restart as detector_module

        invalidations = []
        monkeypatch.setattr(
            detector_module.kiwoom_utils,
            "invalidate_kiwoom_token_cache",
            lambda reason="": invalidations.append(reason) or True,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            log_file = log_dir / "bot_history.log"
            log_file.write_text("old ok\n", encoding="utf-8")
            self._write_state(log_file, restart_count=3, last_restart_ts=0)
            _append(log_file, "8005 Token이 유효하지 않습니다\n")

            with _mock_logs_dir(log_dir):
                result = KiwoomAuth8005RestartDetector().check()

        assert result.severity == "fail"
        assert not self._restart_flag_path.exists()
        assert result.details["restart_requested"] is False
        assert result.details["would_restart"] is False
        assert result.details["restart_suppressed_by_daily_cap"] is True
        assert result.details["restart_count"] == 3
        assert result.details["token_cache_invalidated"] is True
        assert invalidations == ["error_detector_auth_8005"]

    def test_cache_invalidation_exception_does_not_silence_restart(self, monkeypatch):
        import src.engine.error_detectors.kiwoom_auth_8005_restart as detector_module

        def _raise(reason=""):
            raise RuntimeError("cache failure")

        monkeypatch.setattr(
            detector_module.kiwoom_utils, "invalidate_kiwoom_token_cache", _raise
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            log_file = log_dir / "bot_history.log"
            log_file.write_text("old ok\n", encoding="utf-8")
            self._write_state(log_file, restart_count=0, last_restart_ts=0)
            _append(log_file, "8005 Token이 유효하지 않습니다\n")

            with _mock_logs_dir(log_dir):
                result = KiwoomAuth8005RestartDetector().check()

        assert result.severity == "warning"
        assert self._restart_flag_path.exists()
        assert result.details["restart_requested"] is True
        assert result.details["token_cache_invalidated"] is False
        assert result.details["token_cache_invalidation_error"] == "cache failure"

    def test_corrupt_state_warns_instead_of_quiet_pass(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            log_file = log_dir / "bot_history.log"
            log_file.write_text("old ok\n", encoding="utf-8")
            self._scan_state_path.write_text("{", encoding="utf-8")

            with _mock_logs_dir(log_dir):
                result = KiwoomAuth8005RestartDetector().check()

        assert result.severity == "warning"
        assert result.details["baseline_initialized"] is True
        assert result.details["state_load_error"] is True
        assert "state could not be loaded" in result.summary

    def _write_state(self, log_file: Path, restart_count: int, last_restart_ts: float):
        today = __import__("datetime").datetime.now().astimezone().strftime("%Y-%m-%d")
        state = {
            "files": {
                log_file.name: {
                    "position": log_file.stat().st_size,
                    "scanned_at": time.time(),
                }
            },
            "restart_count_date": today,
            "restart_count": restart_count,
            "last_restart_ts": last_restart_ts,
        }
        self._scan_state_path.write_text(json.dumps(state), encoding="utf-8")


def _append(path: Path, text: str):
    path.write_text(path.read_text(encoding="utf-8") + text, encoding="utf-8")


@contextmanager
def _mock_logs_dir(tmpdir_path: Path):
    import src.engine.error_detectors.kiwoom_auth_8005_restart as detector_module

    orig = detector_module.LOGS_DIR
    detector_module.LOGS_DIR = tmpdir_path
    try:
        yield
    finally:
        detector_module.LOGS_DIR = orig
