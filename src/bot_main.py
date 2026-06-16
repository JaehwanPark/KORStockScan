# ==============================================================================
# 🚀 KORStockScan V13.0 통합 관제 시스템 (Main Orchestrator)
# ==============================================================================
"""
[KOSDAQ 하이브리드 AI 스캐너 (Kosdaq Scanner)]
"""
import sys
from pathlib import Path

# ==========================================
# 🚀 [핵심 1] 단독 실행을 위한 루트 경로 탐지
# ==========================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))
    
import os
import multiprocessing
import time
import signal
import threading
import logging
import html  # 💡 상단에 임포트 추가
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

# 💡 [아키텍처 포인트 1] 텔레그램 라이브러리(telebot) 임포트 완전 제거 (의존성 분리)
# 모든 텔레그램 로직은 telegram_manager가 전담합니다.

# 💡 내부 모듈 임포트
from src.utils import kiwoom_utils
from src.utils.runtime_flags import is_trading_paused
from src.database.db_manager import DBManager
from src.core.event_bus import EventBus
from src.engine.daily_report_service import save_daily_report, build_daily_report, format_market_status_with_context
from src.engine.log_archive_service import archive_target_date_logs, save_monitor_snapshots_for_date
from src.engine.strategy_position_performance_report import sync_trade_performance_for_date
from src.utils.constants import RESTART_FLAG_PATH, TRADING_RULES
from src.engine.error_detectors.process_health import reset_heartbeat, write_heartbeat
from src.engine.error_detector import ErrorDetectionEngine, REPORT_DIR as ERROR_REPORT_DIR

# ==========================================
# 📅 호출 상단 공용 날짜 helper
# ==========================================
def _today_string() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _resolve_target_date(target_date: str | None = None) -> str:
    return str(target_date or _today_string())


# ==========================================
# 📝 모든 print()를 가로채서 파일로 저장하는 로거
# ==========================================
class DualLogger:
    def __init__(self):
        log_dir = PROJECT_ROOT / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger('SniperBot')
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False
        
        if not any(
            isinstance(handler, TimedRotatingFileHandler)
            and Path(getattr(handler, "baseFilename", "")).name == "bot_history.log"
            for handler in self.logger.handlers
        ):
            file_handler = TimedRotatingFileHandler(
                filename=str(log_dir / 'bot_history.log'),
                when='midnight',
                interval=1,
                backupCount=getattr(TRADING_RULES, 'BOT_HISTORY_BACKUP_COUNT', 7),
                encoding='utf-8'
            )
            formatter = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        self.terminal = sys.stdout

    def write(self, message):
        self.terminal.write(message)
        if message.strip():
            self.logger.info(message.strip())

    def flush(self):
        self.terminal.flush()


def install_dual_logger():
    """Install file-backed stdout/stderr only for the real bot process."""
    if isinstance(sys.stdout, DualLogger):
        return sys.stdout
    logger = DualLogger()
    sys.stdout = logger
    sys.stderr = logger
    return logger

# ==========================================
# ⏰ 스케줄러 (배치 작업) 함수
# ==========================================
def broadcast_today_picks_job():
    """아침 08:50 오늘의 추천 종목 브로드캐스트 (안전한 HTML 처리 버전)"""
    try:
        from src.database.models import RecommendationHistory
        db_manager = DBManager()
        event_bus = EventBus()
        today = _today_string()
        
        with db_manager.get_session() as session:
            picks = session.query(RecommendationHistory).filter_by(rec_date=today).all()

            if not picks:
                print(f"ℹ️ [{today}] 추천 종목 데이터가 없어 브로드캐스트를 건너뜁니다.")
                return

            msg = f"🌅 <b>[{today}] AI KOSPI 종목추천 리포트</b>\n"
            msg += "━━━━━━━━━━━━━━━━━━\n"

            main_picks = [p for p in picks if getattr(p, 'trade_type', '') == 'MAIN']
            runner_picks = [p for p in picks if getattr(p, 'trade_type', '') == 'RUNNER']
            scalp_picks = [p for p in picks if getattr(p, 'trade_type', '') == 'SCALP' or getattr(p, 'strategy', '') == 'SCALPING']

            if main_picks:
                msg += "🔥 <b>[AI 확신 종목]</b>\n"
                for p in main_picks:
                    # 💡 [방어] 종목명에 혹시 모를 특수문자(<, >)가 있을 수 있으므로 escape 처리
                    safe_name = html.escape(p.stock_name)
                    msg += f"• <b>{safe_name}</b> (<code>{p.stock_code}</code>)\n"
                msg += "\n"

            if runner_picks:
                msg += "🥈 <b>[AI 관심 종목 TOP 10]</b>\n"
                for p in runner_picks[:10]:
                    safe_name = html.escape(p.stock_name)
                    msg += f"• <b>{safe_name}</b> (<code>{p.stock_code}</code>)\n"
                msg += "\n"
                
            if scalp_picks:
                msg += "⚡ <b>[초단타(SCALP) 포착 대기열]</b>\n"
                for p in scalp_picks[:10]:
                    safe_name = html.escape(p.stock_name)
                    msg += f"• <b>{safe_name}</b> (<code>{p.stock_code}</code>)\n"

        # 📢 텔레그램 모듈 직접 호출 파괴 -> EventBus 송출
        event_bus.publish('TELEGRAM_BROADCAST', {'message': msg, 'audience': 'VIP_ALL', 'parse_mode': 'HTML'})

    except Exception as e:
        from src.utils.logger import log_error
        # 💡 [핵심] 에러 메시지에 포함된 < > 등 특수문자를 안전하게 변환
        safe_error = html.escape(str(e))
        
        log_error(f"아침 브로드캐스트 실패: {e}")
        
        # 💡 관리자에게 보낼 때 <code> 태그를 입히면 더 보기 좋습니다.
        error_report = f"❌ <b>아침 브로드캐스트 실패</b>\n<code>{safe_error}</code>"
        
        EventBus().publish('TELEGRAM_BROADCAST', {
            'message': error_report, 
            'audience': 'ADMIN_ONLY',
            'parse_mode': 'HTML'
        })

# 💡 글로벌 위기 감지 무한 루프
def crisis_monitor_loop():
    """60분(3600초) 주기로 글로벌 위기를 감시하고 Telegram은 슬롯 단위로 제한한다."""
    # 순환 참조 및 의존성 방지를 위해 쓰레드 내부에서 지역 임포트
    try:
        import src.scanners.crisis_monitor as crisis_monitor
    except ImportError:
        print("⚠️ [시스템] crisis_monitor.py 모듈을 찾을 수 없어 위기 감지 스케줄러를 종료합니다.")
        return

    while True:
        try:
            crisis_monitor.run_crisis_monitor()
        except Exception as e:
            from src.utils.logger import log_error
            log_error(f"위기 감지 스케줄러 에러: {e}")
        write_heartbeat("crisis_monitor")
        time.sleep(3600)


def error_detection_loop(interval: int, event_bus):
    """60초 주기로 시스템 에러 탐지를 실행하는 데몬 루프."""
    from src.utils.logger import log_error as ed_log_error
    from src.utils.logger import log_info as ed_log_info
    alert_state: dict[str, dict] = {}
    ALERT_COOLDOWN_SEC = 600
    while True:
        try:
            write_heartbeat("error_detection")
            engine = ErrorDetectionEngine(dry_run=False, mode="full")
            results = engine.run_all()
            report = engine.build_report(results)
            engine.write_report(report)
            now_ts = time.time()
            for r in results:
                did = r.detector_id
                prev = alert_state.get(did, {})
                prev_severity = prev.get("severity", "pass")
                prev_summary_hash = prev.get("summary_hash", "")
                prev_ts = prev.get("ts", 0)
                curr_summary_hash = str(hash(r.summary))
                is_alert_severity = r.severity == "fail" or (
                    r.detector_id == "kiwoom_auth_8005_restart" and r.severity == "warning"
                )

                if is_alert_severity:
                    ed_log_error(f"[ERROR_DETECTION] {r.detector_id}: {r.summary}")
                    is_transition = prev_severity != r.severity
                    is_new_summary = curr_summary_hash != prev_summary_hash
                    cooldown_ok = (now_ts - prev_ts) >= ALERT_COOLDOWN_SEC
                    if is_transition or (is_new_summary and cooldown_ok):
                        event_bus.publish(
                            "SYSTEM_HEALTH_ALERT",
                            {
                                "message": f"{r.detector_id}: {r.summary}",
                                "audience": "ADMIN_ONLY",
                                "parse_mode": "HTML",
                            },
                        )
                        alert_state[did] = {"severity": r.severity, "summary_hash": curr_summary_hash, "ts": now_ts}
                elif r.severity == "pass" and prev_severity in {"fail", "warning"}:
                    ed_log_info(f"[ERROR_DETECTION] {r.detector_id}: recovered to pass")
                    alert_state[did] = {"severity": "pass", "summary_hash": "", "ts": now_ts}
        except Exception as e:
            ed_log_error(f"[ERROR_DETECTION] Daemon loop error: {e}")
        time.sleep(interval)


def generate_daily_report_job(target_date: str | None = None):
    """웹/API용 일일 리포트 JSON을 생성합니다."""
    try:
        report = build_daily_report(target_date)
        path = save_daily_report(report)
        warnings = report.get("meta", {}).get("warnings", []) or []
        stats = report.get("stats", {}) or {}
        market_status = format_market_status_with_context(stats)
        risk_text = stats.get("risk_status_text")
        risk_part = f", 리스크={risk_text}" if risk_text else ""
        print(
            f"📘 [시스템] 일일 리포트 생성 완료: {path} "
            f"(시장상태={market_status}{risk_part}, 경고={len(warnings)}건)"
        )
        return report
    except Exception as e:
        from src.utils.logger import log_error

        log_error(f"일일 리포트 생성 실패: {e}")
        print(f"⚠️ [시스템] 일일 리포트 생성 실패: {e}")
        return None


def generate_monitor_archive_job(target_date: str | None = None):
    """장마감 핵심 모니터 요약과 날짜별 gzip 로그 아카이브를 생성합니다."""
    resolved_date = _resolve_target_date(target_date)
    try:
        perf_sync = sync_trade_performance_for_date(resolved_date)
        snapshot_paths = save_monitor_snapshots_for_date(resolved_date)
        archived_logs = archive_target_date_logs(
            resolved_date,
            [
                PROJECT_ROOT / "logs" / "sniper_state_handlers_info.log",
                PROJECT_ROOT / "logs" / "sniper_execution_receipts_info.log",
            ],
        )
        print(
            f"🗂️ [시스템] 모니터 스냅샷/로그 아카이브 완료: "
            f"date={resolved_date} snapshots={len(snapshot_paths)} archived_logs={len(archived_logs)}"
        )
        return {
            "target_date": resolved_date,
            "performance_sync": perf_sync,
            "snapshots": snapshot_paths,
            "archived_logs": archived_logs,
        }
    except Exception as e:
        from src.utils.logger import log_error

        log_error(f"모니터 스냅샷/로그 아카이브 실패: {e}")
        print(f"⚠️ [시스템] 모니터 스냅샷/로그 아카이브 실패: {e}")
        return None


def run_scheduler_job_async(job_name: str, func, *args, **kwargs):
    """Run slow scheduled jobs away from the main heartbeat loop."""
    def _runner():
        try:
            func(*args, **kwargs)
        except Exception as e:
            from src.utils.logger import log_error

            log_error(f"스케줄러 비동기 작업 실패: {job_name}: {e}")

    thread = threading.Thread(target=_runner, name=f"scheduler:{job_name}", daemon=True)
    thread.start()
    return thread


# ==========================================
# 🎯 메인 실행부 (Main Thread)
# ==========================================
if __name__ == '__main__':
    install_dual_logger()
    print("🤖 KORStockScan v13.0 통합 관제 시스템 기동 중...")
    
    db_manager = DBManager()
    db_manager.init_db()

    # 웹/API에서 바로 읽을 수 있도록 부팅 시점에 최신 리포트 1회 생성
    generate_daily_report_job()
    
    # 전역 이벤트 버스 초기화
    event_bus = EventBus()

    # 💡 1. 텔레그램 매니저를 별도의 데몬 쓰레드로 실행 (블로킹 방지)
    import src.notify.telegram_manager as telegram_manager # 우리가 완성한 텔레그램 수신탑
    tele_thread = threading.Thread(target=telegram_manager.start_telegram_bot, daemon=True)
    tele_thread.start()
    print("✅ [시스템] 텔레그램 수신탑 (백그라운드) 가동 완료.")

    if is_trading_paused():
        pause_boot_msg = "⏸ 부팅 시 pause.flag 감지: 신규 매수 및 추가매수 중단 상태로 시작합니다."
        print(pause_boot_msg)
        event_bus.publish(
            'TELEGRAM_BROADCAST',
            {'message': pause_boot_msg, 'audience': 'ADMIN_ONLY', 'parse_mode': 'HTML'},
        )

    # 💡 [신규] 에러 탐지 heartbeat initial write
    reset_heartbeat()
    write_heartbeat("main_loop")
    write_heartbeat("telegram")
    write_heartbeat("crisis_monitor")

    # 🚀 영업일 체크
    is_open, reason = kiwoom_utils.is_trading_day()
    if is_open:
        write_heartbeat("sniper_engine")
        write_heartbeat("scalping_scanner")

    # 💡 [신규] 에러 탐지 데몬 스레드
    ed_enabled = bool(getattr(TRADING_RULES, "ERROR_DETECTOR_ENABLED", True))
    ed_interval = int(getattr(TRADING_RULES, "ERROR_DETECTOR_DAEMON_INTERVAL_SEC", 60))
    if ed_enabled:
        write_heartbeat("error_detection")
        error_detect_thread = threading.Thread(
            target=error_detection_loop, args=(ed_interval, event_bus), daemon=True
        )
        error_detect_thread.start()
        print(f"[시스템] 에러 탐지 데몬 ({ed_interval}초 주기) 가동 완료.")
    else:
        print("[시스템] 에러 탐지 데몬 DISABLED (TRADING_RULES.ERROR_DETECTOR_ENABLED=False)")

    # 💡 2. [신규 추가] 글로벌 위기 감지 모니터는 주말/휴일 상관없이 365일 돌아가야 합니다.
    crisis_thread = threading.Thread(target=crisis_monitor_loop, daemon=True)
    crisis_thread.start()
    print("🌍 [시스템] 글로벌 위기 감지 모니터 (60분 수집, 장전/정오/장후 알림 제한) 가동 완료.")

    if is_open:
        import src.engine.kiwoom_sniper_v2 as kiwoom_sniper_v2

        # 💡 [아키텍처 포인트 3] 콜백(broadcast_alert) 파라미터 완전 제거!
        engine_thread = threading.Thread(target=kiwoom_sniper_v2.run_sniper, daemon=True)
        engine_thread.start()
        write_heartbeat("sniper_engine")
        print("✅ [시스템] 정상거래일 - 스나이퍼 매매 엔진 가동 완료. 조건검색식 가동기간으로 코스닥 스캐너 가동 임시중단 합니다.")

        # 초단타 스캘핑 스캐너 가동 - 장초반/후반 90초, 그 외 120초 주기로
        # stale open-top 대신 회전형 신선도 우선 로직으로 감시 대상을 발굴
        try:
            import src.scanners.scalping_scanner as scalping_scanner
            scalper_thread = threading.Thread(target=scalping_scanner.run_scalper, daemon=True)
            scalper_thread.start()
            write_heartbeat("scalping_scanner")
            print("⚡ [시스템] 정상거래일 - 초단타 스캘핑 스캐너 가동 완료.")
        except Exception as e:
            print(f"🚨 [시스템] 스캘핑 스캐너 가동 중 오류 발생 (혹은 모듈 없음): {e}")
# 
        # 코스닥 AI 하이브리드 스캐너 가동
        # try:
        #     import src.scanners.kosdaq_scanner as kosdaq_scanner
        #     kosdaq_thread = threading.Thread(target=kosdaq_scanner.run_kosdaq_scanner, daemon=True)
        #     kosdaq_thread.start()
        #     print("🚀 [시스템] 정상거래일 - 코스닥 하이브리드 스캐너 가동 완료.")
        # except Exception as e:
        #     print(f"🚨 [시스템] 코스닥 스캐너 가동 중 오류 발생 (혹은 모듈 없음): {e}")

    else:
        # 휴장일 처리
        print(f"🛑 [시스템] 오늘은 {reason} 휴장일입니다. 매매 엔진과 스캐너 가동을 생략합니다.")
        event_bus.publish('TELEGRAM_BROADCAST', {'message': f"🛑 오늘은 {reason} 휴장일입니다. 텔레그램 관제 모드만 가동합니다.", 'audience': 'VIP_ALL'})

    print("🛡️ 메인 관제탑 루프 진입 (스케줄링 및 무중단 감시 시작)...")
    
    # 💡 [아키텍처 포인트 4] 메인 쓰레드는 오직 시스템 스케줄링과 예외 종료 감시만 수행합니다.
    morning_report_sent = False
    daily_report_sent = False
    monitor_archive_sent = False

    heartbeat_counter = 0
    while True:
        try:
            now = datetime.now()
            heartbeat_counter += 1
            if heartbeat_counter % 5 == 0:
                write_heartbeat("main_loop")
            
            # [스케줄러 1] 아침 08:50 종목 브로드캐스트 (딱 한 번만 실행되도록 플래그 사용)
            if now.hour == 8 and now.minute == 50 and not morning_report_sent:
                broadcast_today_picks_job()
                morning_report_sent = True
            
            # 자정이 지나면 내일 아침 리포트를 위해 플래그 초기화
            if now.hour == 0 and now.minute == 1:
                morning_report_sent = False
                daily_report_sent = False
                monitor_archive_sent = False

            # [스케줄러 1-0] 아침 리포트 JSON 생성
            if now.hour == 8 and now.minute == 45 and not daily_report_sent:
                generate_daily_report_job()
                daily_report_sent = True

            # [스케줄러 1-1] 장 마감 후 모니터 요약/로그 아카이브 저장
            if now.hour == 15 and now.minute == 45 and not monitor_archive_sent:
                monitor_archive_sent = True
                run_scheduler_job_async("monitor_archive", generate_monitor_archive_job)

            # [스케줄러 2] 야간(23:50) 시스템 자동 재시작
            if now.hour == 23 and now.minute == 50:
                print("🌙 시스템 일일 초기화 및 메모리 정리를 위해 봇을 재가동합니다.")
                event_bus.publish('TELEGRAM_BROADCAST', {'message': "🌙 자정 메모리 초기화를 위해 시스템을 재가동합니다.", 'audience': 'ADMIN_ONLY'})
                time.sleep(65) # 23:51분으로 넘겨서 무한 재시작 방지
                os.kill(os.getpid(), signal.SIGTERM)

            # [스케줄러 3] 관리자의 우아한 재시작(restart.flag) 감지
            if RESTART_FLAG_PATH.exists():
                print("🔄 [시스템] 수동 재시작 플래그 감지. 관제탑을 종료합니다.")
                RESTART_FLAG_PATH.unlink()
                time.sleep(3) # 다른 쓰레드들이 종료될 시간을 잠시 부여
                os.kill(os.getpid(), signal.SIGTERM)

            # 메인 루프 부하 방지
            time.sleep(1)

        except KeyboardInterrupt:
            print("\n🛑 관리자에 의해 통합 관제 시스템이 종료되었습니다.")
            sys.exit(0)

        except Exception as e:
            from src.utils.logger import log_error
            log_error(f"메인 관제탑 루프 에러: {e}")
            time.sleep(5)
