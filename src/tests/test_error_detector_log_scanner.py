from __future__ import annotations

import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

import pytest

from src.engine.error_detectors.log_scanner import LogScanner


class TestLogScanner:
    def setup_method(self, method):
        import src.engine.error_detectors.log_scanner as ls

        self._tmp_state_dir = tempfile.TemporaryDirectory()
        self._orig_scan_state_path = ls.SCAN_STATE_PATH
        self._scan_state_path = Path(self._tmp_state_dir.name) / "scan_state.json"
        ls.SCAN_STATE_PATH = self._scan_state_path

    def teardown_method(self, method):
        import src.engine.error_detectors.log_scanner as ls

        ls.SCAN_STATE_PATH = self._orig_scan_state_path
        self._tmp_state_dir.cleanup()

    def test_pass_when_no_log_files(self):
        scanner = LogScanner()
        with _mock_logs_dir(tempfile.mkdtemp()):
            result = scanner.check()
        assert result.severity == "pass"

    def test_pass_when_no_new_errors(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            log_file = log_dir / "test_error.log"
            log_file.write_text("normal line\n[DONE] ok\n", encoding="utf-8")
            with _mock_logs_dir(log_dir):
                scanner = LogScanner()
                result = scanner.check()
        assert result.severity == "pass"

    def test_excludes_error_detection_wrapper_logs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            (log_dir / "run_error_detection.log").write_text("[ERROR] detector json\n", encoding="utf-8")
            (log_dir / "run_error_detection_cron.log").write_text("Permission denied\n", encoding="utf-8")
            with _mock_logs_dir(log_dir):
                scanner = LogScanner()
                result = scanner.check()
        assert result.severity == "pass"

    def test_warning_on_few_new_errors(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            log_file = log_dir / "test_error.log"
            log_file.write_text(
                "[ERROR] something failed\n[WARN] connection timeout\n", encoding="utf-8"
            )
            with _mock_logs_dir(log_dir):
                scanner = LogScanner()
                result = scanner.check()
        assert result.severity in ("warning", "fail")

    def test_fail_on_error_burst(self):
        scanner = LogScanner()
        with _mock_logs_dir(None):
            pass
        result = scanner._classify(
            10,
            __import__("collections").Counter({"API_ERROR": 6, "DB_ERROR": 4}),
        )
        severity, _ = result
        assert severity == "fail"

    def test_state_file_tracking(self):
        scanner = LogScanner()
        state = scanner._load_state()
        assert state == {}

        scanner._save_state({"test_file.log": {"position": 100, "scanned_at": 12345.0}})
        assert self._scan_state_path.exists()

        loaded = scanner._load_state()
        assert loaded["test_file.log"]["position"] == 100

    def test_scan_file_only_new_lines(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test_error.log"
            log_file.write_text("old ok line\n", encoding="utf-8")
            initial_size = log_file.stat().st_size
            log_file.write_text(
                log_file.read_text(encoding="utf-8") + "[ERROR] new failure\n",
                encoding="utf-8",
            )

            scanner = LogScanner()
            errors, new_pos, details = scanner._scan_file(
                log_file, initial_size, __import__("collections").Counter()
            )
            assert errors == 1
            assert new_pos > initial_size

    def test_scan_file_ignores_error_detection_meta_alerts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "bot_main_error.log"
            log_file.write_text(
                "[2026-05-11 09:40:47] 🚨 ERROR in bot_main: "
                "[ERROR_DETECTION] log_scanner: Error burst detected\n",
                encoding="utf-8",
            )

            scanner = LogScanner()
            counter = __import__("collections").Counter()
            errors, new_pos, _ = scanner._scan_file(log_file, 0, counter)

            assert errors == 0
            assert new_pos == 0
            assert counter == {}

    def test_scan_file_ignores_test_fixture_noise(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "sniper_state_handlers_error.log"
            log_file.write_text(
                "\n".join([
                    "[2026-05-11 18:22:21] 🚨 ERROR in sniper_state_handlers: "
                    "🚨 [DB 조회 에러] ID 1 수량 조회 실패: 'NoneType' object has no attribute 'get_session'",
                    "[2026-05-11 18:22:21] 🚨 ERROR in sniper_state_handlers: "
                    "[ADD_CANCELLED] TEST(123456) pending add missing order number.",
                    "[2026-05-11 18:22:22] 🚨 ERROR in sniper_scale_in_utils: "
                    "[ADD_HISTORY] event persist failed: '_DummySession' object has no attribute 'add'",
                    "[2026-05-11 18:22:22] 🚨 ERROR in telegram_manager: "
                    "[TRADING_PAUSED] EventBus publish failed after pause: bus fail",
                    "[2026-05-11 18:22:22] 🚨 ERROR in kiwoom_orders: "
                    "❌ [취소거절] 123456: 인증에 실패했습니다[8005:Token이 유효하지 않습니다]",
                    "[2026-05-11 18:22:23] 🚨 ERROR in live_component: real API error",
                ]),
                encoding="utf-8",
            )

            scanner = LogScanner()
            counter = __import__("collections").Counter()
            errors, _, _ = scanner._scan_file(log_file, 0, counter)

            assert errors == 2
            assert counter == {"DB_ERROR": 1, "API_ERROR": 1}
            severity, _ = scanner._classify(errors, counter)
            assert severity == "warning"

    def test_scan_file_ignores_korean_openai_transport_fixture_noise(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "ai_engine_openai_error.log"
            log_file.write_text(
                "\n".join([
                    "[2026-05-15 07:54:35] 🚨 ERROR in ai_engine_openai: "
                    "🚨 [테스트][SCALPING] OpenAI 실시간 분석 에러 (연속 실패 1회, API키 인덱스 0): ws timeout",
                    "[2026-05-15 07:54:35] 🚨 ERROR in ai_engine_openai: "
                    "⚠️ [OpenAI WS fallback] test: ws timeout",
                    "[2026-05-15 07:54:35] 🚨 ERROR in ai_engine_openai: "
                    "🚨 [OpenAI WS fail-closed] 테스트(SCALPING:scalping_entry): request_id mismatch",
                    "[2026-05-15 07:54:36] 🚨 ERROR in ai_engine_openai: "
                    "🚨 [삼성전자][SCALPING] OpenAI 실시간 분석 에러: request timeout",
                ]),
                encoding="utf-8",
            )

            scanner = LogScanner()
            counter = __import__("collections").Counter()
            errors, _, _ = scanner._scan_file(log_file, 0, counter)

            assert errors == 1
            assert counter == {"TIMEOUT_ERROR": 1}

    def test_scan_file_ignores_openai_latency_acceptance_fixture_noise(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "ai_engine_openai_error.log"
            log_file.write_text(
                "\n".join([
                    "[2026-07-03 23:06:13] 🚨 ERROR in ai_engine_openai: "
                    "🚨 [HOLDING_SCORE] OpenAI score error (LIVE_SMOKE_TEST, failures 1): "
                    "OpenAI Responses HTTP 응답/파싱 실패: Request timed out.",
                    "[2026-07-03 23:26:49] 🚨 ERROR in ai_engine_openai: "
                    "🚨 [HOLDING_SCORE] OpenAI score error (LatencyTest, failures 1): "
                    "OpenAI Responses HTTP 응답/파싱 실패: Request timed out.",
                    "[2026-07-03 23:29:01] 🚨 ERROR in ai_engine_openai: "
                    "🚨 [LatencyLegacyHolding][SCALPING] OpenAI 실시간 분석 에러 "
                    "(연속 실패 1회, API키 인덱스 0): OpenAI Responses HTTP 응답/파싱 실패: "
                    "Request timed out.",
                    "[2026-07-04 13:46:19] 🚨 ERROR in ai_engine_openai: "
                    "🚨 [LatencyEntry][SCALPING] OpenAI 실시간 분석 에러 "
                    "(연속 실패 1회, API키 인덱스 0): OpenAI Responses HTTP 응답/파싱 실패: "
                    "Request timed out.",
                    "[2026-07-04 13:46:24] 🚨 ERROR in ai_engine_openai: "
                    "🚨 [ENTRY_PRICE] OpenAI 가격결정 에러 (LatencyEntryPrice, 연속 실패 1회): "
                    "OpenAI Responses HTTP 응답/파싱 실패: Request timed out.",
                    "[2026-07-04 14:25:25] 🚨 ERROR in ai_engine_openai: "
                    "🚨 [LIVE_ENTRY_TIMEOUT_700_TEST][SCALPING] OpenAI 실시간 분석 에러 "
                    "(연속 실패 1회, API키 인덱스 0): OpenAI Responses HTTP 응답/파싱 실패: "
                    "Request timed out.",
                    "[2026-07-04 14:27:05] 🚨 ERROR in ai_engine_openai: "
                    "🚨 [LIVE_ENTRY_TIMEOUT_700_REVIEW_FIX][SCALPING] OpenAI 실시간 분석 에러 "
                    "(연속 실패 1회, API키 인덱스 0): OpenAI Responses HTTP 응답/파싱 실패: "
                    "Request timed out.",
                    "[2026-07-04 14:36:29] 🚨 ERROR in ai_engine_openai: "
                    "🚨 [ENTRY_LIVE_REVIEW_TEST][SCALPING] OpenAI 실시간 분석 에러 "
                    "(연속 실패 1회, API키 인덱스 0): OpenAI Responses HTTP 응답/파싱 실패: "
                    "Error code: 400 - {'error': {'message': 'Invalid schema for response_format'}}",
                    "[2026-07-06 09:31:00] 🚨 ERROR in ai_engine_openai: "
                    "🚨 [삼성전자][SCALPING] OpenAI 실시간 분석 에러: Request timed out.",
                ]),
                encoding="utf-8",
            )

            scanner = LogScanner()
            counter = __import__("collections").Counter()
            errors, _, _ = scanner._scan_file(log_file, 0, counter)

            assert errors == 1
            assert counter == {"TIMEOUT_ERROR": 1}

    def test_scan_file_ignores_pytest_tmp_fixture_leakage(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "kiwoom_utils_error.log"
            log_file.write_text(
                "\n".join([
                    "[2026-05-27 10:49:41] 🚨 ERROR in kiwoom_utils: "
                    "❌ [TOKEN CACHE] 캐시 로드 실패: "
                    "/tmp/pytest-of-ubuntu/pytest-34/test_token/kiwoom_token_cache.json",
                    "[2026-05-27 10:49:41] 🚨 ERROR in kiwoom_utils: "
                    "🚨 [kt00008] 8005 token refresh retry 후에도 인증 실패. 조회를 중단합니다.",
                ]),
                encoding="utf-8",
            )

            scanner = LogScanner()
            counter = __import__("collections").Counter()
            errors, _, _ = scanner._scan_file(log_file, 0, counter)

            assert errors == 1
            assert counter == {"UNKNOWN": 1}

    def test_scan_file_ignores_info_db_success_lines_in_error_log(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "update_kospi_error.log"
            log_file.write_text(
                "\n".join([
                    "2026-05-12 21:27:31,342 - INFO - DB 일괄 삽입 성공! (총 42359행 적재 완료)",
                    "2026-05-12 21:27:32,461 - INFO - swing daily reports 시작...",
                    "2026-05-12 21:27:53,598 - INFO - swing daily reports 완료",
                    "2026-05-12 21:28:06,978 - ERROR - 추천 모델 실행 중 에러 발생: "
                    "Command returned non-zero exit status 1.",
                ]),
                encoding="utf-8",
            )

            scanner = LogScanner()
            counter = __import__("collections").Counter()
            errors, _, _ = scanner._scan_file(log_file, 0, counter)

            assert errors == 1
            assert counter == {"UNKNOWN": 1}

    def test_scan_file_does_not_classify_kiwoom_as_oom(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "kiwoom_orders_error.log"
            log_file.write_text(
                "\n".join([
                    "[2026-05-14 11:05:37] 🚨 ERROR in kiwoom_orders: "
                    "❌ [예수금조회 실패] attempt=1/2 사유: "
                    "인증에 실패했습니다[8005:Token이 유효하지 않습니다]",
                    "[2026-05-14 11:05:37] 🚨 ERROR in runtime: "
                    "MemoryError: failed to allocate buffer",
                    "[2026-05-14 11:05:38] 🚨 ERROR in runtime: "
                    "out of memory while building report",
                ]),
                encoding="utf-8",
            )

            scanner = LogScanner()
            counter = __import__("collections").Counter()
            errors, _, _ = scanner._scan_file(log_file, 0, counter)

            assert errors == 3
            assert counter == {"UNKNOWN": 1, "MEMORY_ERROR": 2}

    def test_scan_file_classifies_korean_broker_order_rejections(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "kiwoom_orders_error.log"
            log_file.write_text(
                "\n".join([
                    "[2026-06-30 15:50:14] 🚨 ERROR in kiwoom_orders: "
                    "❌ [매수거절] 종목:000500, 사유:[2000](521790:주문 불가능합니다.) (코드:20)",
                    "[2026-06-30 16:02:05] 🚨 ERROR in kiwoom_orders: "
                    "❌ [취소거절] 281820: [2000](571412:SOR정정 및 취소주문은 원주문이 SOR주문인 경우 가능합니다.)",
                    "[2026-06-30 08:42:37] 🚨 ERROR in sniper_state_handlers: "
                    "❌ [매도거절] 제룡전기: [2000](800033:매도가능수량이 부족합니다. 0주 매도가능)",
                    "[2026-06-30 16:56:56] 🚨 ERROR in sniper_state_handlers: "
                    "❌ [에코프로비엠] 추가매수 주문 거절: [2000](521790:주문 불가능합니다.)",
                ]),
                encoding="utf-8",
            )

            scanner = LogScanner()
            counter = __import__("collections").Counter()
            errors, _, _ = scanner._scan_file(log_file, 0, counter)

            assert errors == 4
            assert counter == {"ORDER_REJECT": 4}

    def test_scan_file_classifies_scanner_source_identity_guard(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "scalping_scanner_error.log"
            log_file.write_text(
                "[2026-07-15 18:50:42] ERROR "
                "[SCANNER_SOURCE_IDENTITY_GUARD] candidate rejected "
                "code=001200 payload_name=삼양바이오팜 authoritative_name=유진투자증권\n",
                encoding="utf-8",
            )

            scanner = LogScanner()
            counter = __import__("collections").Counter()
            errors, _, _ = scanner._scan_file(log_file, 0, counter)

            assert errors == 1
            assert counter == {"SOURCE_IDENTITY_ERROR": 1}

    def test_scan_file_no_change(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test_error.log"
            log_file.write_text("no error here\n", encoding="utf-8")
            scanner = LogScanner()
            errors, new_pos, details = scanner._scan_file(
                log_file, log_file.stat().st_size, __import__("collections").Counter()
            )
            assert errors == 0

    def test_dry_run_does_not_save_state(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            log_file = log_dir / "test_error.log"
            log_file.write_text("[ERROR] new error\n", encoding="utf-8")
            with _mock_logs_dir(log_dir):
                scanner = LogScanner(dry_run=True)
                result = scanner.check()
                assert result.severity in ("warning", "fail")
                assert not self._scan_state_path.exists()

    def test_scan_file_rotation_reset(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test_error.log"
            log_file.write_text("[ERROR] old log contents\n", encoding="utf-8")
            scanner = LogScanner()
            counter = __import__("collections").Counter()
            errors1, pos1, _ = scanner._scan_file(log_file, 0, counter)
            assert errors1 == 1
            log_file.write_text("[ERROR] new after rotation\n", encoding="utf-8")
            stale_pos = pos1 + 9999
            errors2, pos2, _ = scanner._scan_file(log_file, stale_pos, counter)
            assert errors2 == 1
            assert pos2 > 0


@contextmanager
def _mock_logs_dir(tmpdir_path):
    import src.engine.error_detectors.log_scanner as ls
    orig = ls.LOGS_DIR

    if tmpdir_path is not None:
        ls.LOGS_DIR = Path(tmpdir_path)
    else:
        ls.LOGS_DIR = Path("/nonexistent_logs_xxx")
    try:
        yield
    finally:
        ls.LOGS_DIR = orig
