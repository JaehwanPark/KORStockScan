import os
import inspect
import logging
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler

from src.utils.constants import LEGACY_LOGS_DIR, LOGS_DIR, TRADING_RULES

_MODULE_LOGGERS = {}
_MAINTENANCE_RAN_AT = 0.0


def _resolve_caller_filename(explicit: str | None = None) -> str:
    if explicit:
        return explicit

    frame = inspect.currentframe()
    if frame is None or frame.f_back is None:
        return "unknown"

    caller_frame = frame.f_back.f_back
    if caller_frame is None:
        return "unknown"
    return os.path.basename(caller_frame.f_code.co_filename).replace(".py", "")


def _run_log_maintenance_if_needed():
    global _MAINTENANCE_RAN_AT

    now_ts = time.time()
    if now_ts - _MAINTENANCE_RAN_AT < 3600:
        return

    retention_days = max(1, int(getattr(TRADING_RULES, "LOG_RETENTION_DAYS", 14) or 14))
    cutoff_ts = now_ts - (retention_days * 86400)
    candidate_dirs = [LOGS_DIR, LEGACY_LOGS_DIR]

    for log_dir in candidate_dirs:
        try:
            if not os.path.isdir(log_dir):
                continue

            for entry in os.scandir(log_dir):
                if not entry.is_file():
                    continue
                if ".log" not in entry.name:
                    continue
                if entry.stat().st_mtime >= cutoff_ts:
                    continue
                try:
                    os.remove(entry.path)
                except FileNotFoundError:
                    pass
        except Exception as exc:
            print(f"[WARN] 로그 정리 중 오류 발생 ({log_dir}): {exc}")

    _MAINTENANCE_RAN_AT = now_ts


def _get_module_logger(caller_filename: str, level: str):
    logger_key = f"{caller_filename}:{level}"
    logger = _MODULE_LOGGERS.get(logger_key)
    if logger is not None:
        return logger

    os.makedirs(LOGS_DIR, exist_ok=True)
    log_filepath = LOGS_DIR / f"{caller_filename}_{level}.log"

    logger = logging.getLogger(f"module_logger.{logger_key}")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        handler = RotatingFileHandler(
            log_filepath,
            maxBytes=int(
                getattr(TRADING_RULES, "MODULE_LOG_MAX_BYTES", 20 * 1024 * 1024)
                or 20 * 1024 * 1024
            ),
            backupCount=int(
                getattr(TRADING_RULES, "MODULE_LOG_BACKUP_COUNT", 10) or 10
            ),
            encoding="utf-8",
        )
        formatter = logging.Formatter(
            "[%(asctime)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    _MODULE_LOGGERS[logger_key] = logger
    return logger


def log_error(
    msg: str, send_telegram: bool = False, caller_filename: str | None = None
):
    """
    중앙 집중형 에러 관리 함수 (호출한 파일명으로 분리 & 상세 원인 자동 기록)
    """
    try:
        _run_log_maintenance_if_needed()

        caller_filename = _resolve_caller_filename(caller_filename)

        # 2. 에러 메시지 포맷팅
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_payload = f"🚨 ERROR in {caller_filename}: {msg}"
        _get_module_logger(caller_filename, "error").error(log_payload)

        print(f"[{timestamp}] {log_payload}")  # 콘솔에도 출력

        # 💡 주의: 텔레그램 발송 기능은 순환 참조 방지를 위해 여기서 직접 import하지 않고,
        # bot_main.py나 최상단 계층에서 비동기로 처리하는 것이 안전해!
        if send_telegram:
            pass  # (임시 보류) 알림 시스템 리팩토링 시 콜백 구조로 연결할 예정

    except Exception as e:
        print(f"[FATAL] 로깅 시스템 자체 에러 발생: {e}")


def log_info(msg: str, send_telegram: bool = False, caller_filename: str | None = None):
    """
    중앙 집중형 정보 로깅 함수 (호출한 파일명으로 분리 & 자동 기록)
    """
    try:
        _run_log_maintenance_if_needed()

        caller_filename = _resolve_caller_filename(caller_filename)

        # 2. 정보 메시지 포맷팅
        log_payload = f"📢 INFO in {caller_filename}: {msg}"
        _get_module_logger(caller_filename, "info").info(log_payload)

        # 💡 주의: 텔레그램 발송 기능은 순환 참조 방지를 위해 여기서 직접 import하지 않고,
        # bot_main.py나 최상단 계층에서 비동기로 처리하는 것이 안전해!
        if send_telegram:
            pass  # (임시 보류) 알림 시스템 리팩토링 시 콜백 구조로 연결할 예정

    except Exception as e:
        print(f"[FATAL] 로깅 시스템 자체 에러 발생: {e}")
