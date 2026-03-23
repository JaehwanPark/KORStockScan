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
import sys
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
from src.database.db_manager import DBManager
from src.core.event_bus import EventBus
import src.engine.kiwoom_sniper_v2 as kiwoom_sniper_v2
import src.notify.telegram_manager as telegram_manager # 우리가 완성한 텔레그램 수신탑

# ==========================================
# 📝 모든 print()를 가로채서 파일로 저장하는 로거
# ==========================================
class DualLogger:
    def __init__(self):
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        self.logger = logging.getLogger('SniperBot')
        self.logger.setLevel(logging.INFO)
        
        file_handler = TimedRotatingFileHandler(
            filename='logs/bot_history.log',
            when='midnight',
            interval=1,
            backupCount=7,
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

sys.stdout = DualLogger()
sys.stderr = sys.stdout 

# ==========================================
# ⏰ 스케줄러 (배치 작업) 함수
# ==========================================
def broadcast_today_picks_job():
    """아침 08:50 오늘의 추천 종목 브로드캐스트 (안전한 HTML 처리 버전)"""
    try:
        from src.database.models import RecommendationHistory
        db_manager = DBManager()
        event_bus = EventBus()
        today = datetime.now().strftime('%Y-%m-%d')
        
        with db_manager.get_session() as session:
            picks = session.query(RecommendationHistory).filter_by(rec_date=today).all()

        if not picks:
            return

        msg = f"🌅 <b>[{today}] AI KOSPI 종목추천 리포트</b>\n"
        msg += "━━━━━━━━━━━━━━━━━━\n"

        # ... (중략) ...

        if main_picks:
            msg += "🔥 <b>[AI 확신 종목]</b>\n"
            for p in main_picks:
                # 💡 [방어] 종목명에 혹시 모를 특수문자(<, >)가 있을 수 있으므로 escape 처리
                safe_name = html.escape(p.name)
                safe_price = int(p.buy_price) if p.buy_price else 0
                msg += f"• <b>{safe_name}</b> (<code>{safe_price:,}원</code>)\n"
            msg += "\n"

        # (runner_picks, scalp_picks 루프 내 p.name에도 동일하게 html.escape 적용 권장)

        # 발송
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

# 💡 [신규 추가] 30분 단위 글로벌 위기 감지 무한 루프
def crisis_monitor_loop():
    """60분(3600초) 주기로 글로벌 위기를 감시하는 백그라운드 작업"""
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
        
        # 1시간 대기 (3600초)
        time.sleep(3600)

# ==========================================
# 🎯 메인 실행부 (Main Thread)
# ==========================================
if __name__ == '__main__':
    print("🤖 KORStockScan v13.0 통합 관제 시스템 기동 중...")
    
    db_manager = DBManager()
    db_manager.init_db()
    
    # 전역 이벤트 버스 초기화
    event_bus = EventBus()

    # 💡 1. 텔레그램 매니저를 별도의 데몬 쓰레드로 실행 (블로킹 방지)
    tele_thread = threading.Thread(target=telegram_manager.start_telegram_bot, daemon=True)
    tele_thread.start()
    print("✅ [시스템] 텔레그램 수신탑 (백그라운드) 가동 완료.")

    # 💡 2. [신규 추가] 글로벌 위기 감지 모니터는 주말/휴일 상관없이 365일 돌아가야 합니다.
    crisis_thread = threading.Thread(target=crisis_monitor_loop, daemon=True)
    crisis_thread.start()
    print("🌍 [시스템] 글로벌 위기 감지 모니터 (30분 주기) 가동 완료.")

    # 🚀 영업일 체크
    is_open, reason = kiwoom_utils.is_trading_day()

    if is_open:
        # 💡 [아키텍처 포인트 3] 콜백(broadcast_alert) 파라미터 완전 제거!
        engine_thread = threading.Thread(target=kiwoom_sniper_v2.run_sniper, daemon=True)
        engine_thread.start()
        print("✅ [시스템] 정상거래일 - 스나이퍼 매매 엔진 가동 완료. 조건검색식 가동기간으로 코스닥 및 스캘핑 스캐너 가동 임시중단 합니다.")

        # 초단타 스캘핑 스캐너 가동 - 조건검색식 스캐너로 대체
        # try:
        #     import src.scanners.scalping_scanner as scalping_scanner
        #     scalper_thread = threading.Thread(target=scalping_scanner.run_scalper, daemon=True)
        #     scalper_thread.start()
        #     print("⚡ [시스템] 정상거래일 - 초단타 스캘핑 스캐너 가동 완료.")
        # except Exception as e:
        #     print(f"🚨 [시스템] 스캘핑 스캐너 가동 중 오류 발생 (혹은 모듈 없음): {e}")
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

    while True:
        try:
            now = datetime.now()
            
            # [스케줄러 1] 아침 08:50 종목 브로드캐스트 (딱 한 번만 실행되도록 플래그 사용)
            if now.hour == 8 and now.minute == 50 and not morning_report_sent:
                broadcast_today_picks_job()
                morning_report_sent = True
            
            # 자정이 지나면 내일 아침 리포트를 위해 플래그 초기화
            if now.hour == 0 and now.minute == 1:
                morning_report_sent = False

            # [스케줄러 2] 야간(23:50) 시스템 자동 재시작
            if now.hour == 23 and now.minute == 50:
                print("🌙 시스템 일일 초기화 및 메모리 정리를 위해 봇을 재가동합니다.")
                event_bus.publish('TELEGRAM_BROADCAST', {'message': "🌙 자정 메모리 초기화를 위해 시스템을 재가동합니다.", 'audience': 'ADMIN_ONLY'})
                time.sleep(65) # 23:51분으로 넘겨서 무한 재시작 방지
                os.kill(os.getpid(), signal.SIGTERM)

            # [스케줄러 3] 관리자의 우아한 재시작(restart.flag) 감지
            if os.path.exists("restart.flag"):
                print("🔄 [시스템] 수동 재시작 플래그 감지. 관제탑을 종료합니다.")
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