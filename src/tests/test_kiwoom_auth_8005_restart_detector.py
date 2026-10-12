from __future__ import annotations

import json
import fcntl
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
import pytest

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

    def test_unread_preboot_error_without_main_does_not_request_restart(self, monkeypatch):
        import src.engine.error_detectors.kiwoom_auth_8005_restart as module

        invalidations = []
        cutoff = datetime.fromisoformat("2026-10-12T05:30:52+09:00").timestamp()
        monkeypatch.setattr(module, "_historical_auth_cutoff", lambda: cutoff)
        monkeypatch.setattr(module, "_current_runtime_identity", lambda: None)
        monkeypatch.setattr(module.kiwoom_utils, "invalidate_kiwoom_token_cache",
                            lambda reason="": invalidations.append(reason) or True)
        with tempfile.TemporaryDirectory() as tmpdir:
            log = Path(tmpdir) / "kiwoom_utils_info.log"
            log.write_text("old ok\n")
            self._write_state(log, restart_count=0, last_restart_ts=0)
            _append(log, "[2026-10-09 22:36:36] [ka10080] API auth failure 8005 Token invalid\n")
            with _mock_logs_dir(Path(tmpdir)):
                result = KiwoomAuth8005RestartDetector().check()
        assert result.severity == "pass"
        assert result.details["historical_auth_8005_count"] == 1
        assert result.details["restart_requested"] is False
        assert result.details["token_cache_invalidated"] is False
        assert invalidations == [] and not self._restart_flag_path.exists()
        state = json.loads(self._scan_state_path.read_text())
        assert state["restart_count"] == 0

    def test_mixed_history_and_current_error_preserves_current_recovery(self, monkeypatch):
        import src.engine.error_detectors.kiwoom_auth_8005_restart as module

        cutoff = datetime.fromisoformat("2026-10-12T05:30:52+09:00").timestamp()
        monkeypatch.setattr(module, "_historical_auth_cutoff", lambda: cutoff)
        monkeypatch.setattr(module.kiwoom_utils, "invalidate_kiwoom_token_cache", lambda reason="": True)
        with tempfile.TemporaryDirectory() as tmpdir:
            log = Path(tmpdir) / "kiwoom_utils_info.log"
            log.write_text("old ok\n")
            self._write_state(log, restart_count=0, last_restart_ts=0)
            _append(log, "[2026-10-09 22:36:36] [ka10080] auth 8005 Token invalid\n")
            _append(log, "[2026-10-12 07:00:00] [ka10080] auth 8005 Token invalid\n")
            with _mock_logs_dir(Path(tmpdir)):
                result = KiwoomAuth8005RestartDetector().check()
        assert result.details["historical_auth_8005_count"] == 1
        assert result.details["fresh_auth_8005_count"] == 1
        assert result.details["restart_requested"] is True

    def test_history_cutoff_uses_kst_day_and_preserves_boot_second(self, monkeypatch, tmp_path):
        import src.engine.error_detectors.kiwoom_auth_8005_restart as module

        now = datetime.fromisoformat("2026-10-12T07:00:00+09:00").timestamp()
        boot = int(datetime.fromisoformat("2026-10-12T05:30:53+09:00").timestamp())
        (tmp_path / "stat").write_text(f"btime {boot}\n")
        monkeypatch.setattr(module, "PROC_ROOT", tmp_path)
        monkeypatch.setattr(module, "_now_ts", lambda: now)
        assert module._historical_auth_cutoff() == boot - 1
        (tmp_path / "stat").write_text("btime invalid\n")
        assert module._historical_auth_cutoff() == datetime.fromisoformat("2026-10-12T00:00:00+09:00").timestamp()

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


def test_atomic_state_replace_keeps_prior_generation_on_failure(monkeypatch, tmp_path):
    from src.engine.error_detectors import kiwoom_auth_8005_restart as module
    state_path = tmp_path/'state.json'
    monkeypatch.setattr(module, 'SCAN_STATE_PATH', state_path)
    old = dict(files={'bot_history.log': dict(position=17)}, restart_count=2)
    module.KiwoomAuth8005RestartDetector._save_state(old)
    def fail_replace(source, target):
        assert module.KiwoomAuth8005RestartDetector._load_state() == old
        assert json.loads(Path(source).read_text())['restart_count'] == 3
        raise OSError('injected publication failure')
    monkeypatch.setattr(module.os, 'replace', fail_replace)
    with pytest.raises(OSError, match='publication failure'):
        module.KiwoomAuth8005RestartDetector._save_state(dict(old, restart_count=3))
    assert json.loads(state_path.read_text()) == old
    assert list(tmp_path.glob('.*.tmp')) == []


def test_atomic_state_preserves_existing_access_mode(monkeypatch, tmp_path):
    from src.engine.error_detectors import kiwoom_auth_8005_restart as module
    state = tmp_path/'state.json'; state.write_text('{}'); state.chmod(0o664)
    monkeypatch.setattr(module, 'SCAN_STATE_PATH', state)
    value = dict(files={'bot_history.log': dict(position=39)}, restart_count=2, last_restart_ts=123)
    module.KiwoomAuth8005RestartDetector._save_state(value)
    assert state.stat().st_mode & 0o777 == 0o664
    assert module.KiwoomAuth8005RestartDetector._load_state() == value
    assert list(tmp_path.glob('.*.tmp')) == []


@pytest.mark.parametrize('payload', [b'[]', b'{"files": []}', b'{"files":{"x":{"position":null}}}',
    b'{"files":{},"restart_count":true}', b'{"files":{},"last_restart_ts":NaN}', b'\xff'])
def test_invalid_state_shape_and_encoding_never_scan_history(monkeypatch, tmp_path, payload):
    from src.engine.error_detectors import kiwoom_auth_8005_restart as module
    state = tmp_path/'state.json'; state.write_bytes(payload)
    log = tmp_path/'bot_history.log'; log.write_text('8005 Token invalid\n')
    monkeypatch.setattr(module, 'SCAN_STATE_PATH', state)
    monkeypatch.setattr(module, 'RESTART_FLAG_PATH', tmp_path/'restart.flag')
    monkeypatch.setattr(module, '_get_target_log_files', lambda: [log])
    monkeypatch.setattr(module.kiwoom_utils, 'invalidate_kiwoom_token_cache', lambda **k: pytest.fail('historical restart'))
    first = module.KiwoomAuth8005RestartDetector().check()
    assert first.severity == 'warning' and first.details['state_load_error_kind']['error_type']
    assert first.details['restart_requested'] is False
    assert module.KiwoomAuth8005RestartDetector().check().severity == 'pass'
    assert not module.RESTART_FLAG_PATH.exists()


def test_daemon_and_cron_share_one_recovery_transaction(monkeypatch, tmp_path):
    from src.engine.error_detectors import kiwoom_auth_8005_restart as module
    state = tmp_path/'state.json'
    log = tmp_path/'bot_history.log'; log.write_text('old ok\n')
    monkeypatch.setattr(module, 'SCAN_STATE_PATH', state)
    monkeypatch.setattr(module, 'RESTART_FLAG_PATH', tmp_path/'restart.flag')
    monkeypatch.setattr(module, '_get_target_log_files', lambda: [log])
    monkeypatch.setattr(module, '_current_runtime_identity', lambda: None)
    detector = module.KiwoomAuth8005RestartDetector
    detector().check()
    _append(log, '8005 Token invalid\n')
    calls=[]; entered=threading.Event(); release=threading.Event()
    def invalidate(reason):
        calls.append(reason); entered.set()
        assert release.wait(timeout=3)
        return True
    monkeypatch.setattr(module.kiwoom_utils, 'invalidate_kiwoom_token_cache', invalidate)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first=pool.submit(detector().check)
        assert entered.wait(timeout=3)
        second=pool.submit(detector().check)
        release.set()
        answers=[first.result(timeout=4), second.result(timeout=4)]
    assert len(calls)==1
    assert sum(r.details.get('restart_requested') is True for r in answers)==1
    assert json.loads(state.read_text())['restart_count']==1
    assert answers[1].severity=='pass'


def test_busy_state_lock_defers_without_mutation_and_dry_run_does_not_create_lock(monkeypatch, tmp_path):
    from src.engine.error_detectors import kiwoom_auth_8005_restart as module
    state = tmp_path/'state.json'
    monkeypatch.setattr(module, 'SCAN_STATE_PATH', state)
    monkeypatch.setattr(module, '_get_target_log_files', lambda: [])
    module.KiwoomAuth8005RestartDetector(dry_run=True).check()
    assert list(tmp_path.iterdir()) == []
    monkeypatch.setattr(module, '_STATE_LOCK_WAIT_SEC', 0)
    with state.with_name(state.name+'.lock').open('a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        result=module.KiwoomAuth8005RestartDetector().check()
    assert result.severity=='warning' and result.details['state_lock_busy'] is True
    assert result.details['restart_requested'] is result.details['token_cache_invalidated'] is False
    assert not state.exists()
