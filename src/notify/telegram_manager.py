import sys
import os
import json
import re
import telebot
from telebot import types
import time
from datetime import datetime
from pathlib import Path
import logging

# ==========================================
# 🚀 1. 경로 자동 탐지 (어느 위치에서 실행해도 OK)
# ==========================================
# 현재 파일: src/managers/telegram_manager.py
# .parent(managers) -> .parent(src) -> .parent(KORStockScan)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from src.utils.constants import CONFIG_PATH, DEV_PATH  # 💡 중앙 관리 경로 활용
from src.utils.logger import log_error, log_info
from src.database.db_manager import DBManager
from src.core.event_bus import EventBus
from src.utils import kiwoom_utils


# ==========================================
# ⚙️ 2. 설정 로드 및 봇 초기화 (함수화로 깔끔하게)
# ==========================================
def _load_config():
    target = CONFIG_PATH if CONFIG_PATH.exists() else DEV_PATH
    try:
        with open(target, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"🚨 설정 로드 실패: {e}")
        exit(1)

CONF = _load_config()
TOKEN = CONF.get('TELEGRAM_TOKEN')
ADMIN_ID = str(CONF.get('ADMIN_ID', ''))

def _configure_telebot_http():
    """telebot 내부 요청 세션을 재시도 가능하도록 설정"""
    try:
        import requests
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        import telebot.apihelper as apihelper

        retry = Retry(
            total=5,
            connect=5,
            read=5,
            status=5,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(["GET", "POST"]),
        )
        session = requests.Session()
        adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        apihelper.SESSION = session
        apihelper.RETRY_ON_ERROR = True
        apihelper.CONNECT_TIMEOUT = 10
        apihelper.READ_TIMEOUT = 60

        # telebot 내부 로그 과다 출력 방지
        try:
            telebot.logger.setLevel(logging.CRITICAL)
        except Exception:
            pass
    except Exception as e:
        log_info(f"⚠️ telebot HTTP 설정 스킵: {e}")

def _create_bot_instance():
    if not TOKEN:
        raise ValueError("TELEGRAM_TOKEN 이 비어 있습니다.")
    # TeleBot 인스턴스 생성 자체는 네트워크를 사용하지 않으므로,
    # import 시점에는 연결 검증(get_me 등)을 하지 않습니다.
    bot_instance = telebot.TeleBot(TOKEN)
    _configure_telebot_http()
    return bot_instance

# ==========================================
# 3. 핵심 객체 단일 초기화
# ==========================================
try:
    bot = _create_bot_instance()
    db_manager = DBManager()
    event_bus = EventBus()

    print(f"🤖 Telegram Bot 초기화 완료 - 관리자 ID: {ADMIN_ID or '미설정'}")
except Exception as e:
    log_error(f"🚨 텔레그램 매니저 초기화 실패: {e}")
    exit(1)

# ==========================================
# 📢 4. 핵심 발송 로직 (내부 함수화)
# ==========================================
def _send_to_admin(message_text, parse_mode='HTML'):
    """시스템 에러나 관리자 전용 정보를 ADMIN_ID에게 발송"""
    if not ADMIN_ID: return
    try:
        bot.send_message(chat_id=ADMIN_ID, text=message_text, parse_mode=parse_mode)
    except telebot.apihelper.ApiTelegramException as e:
        if "can't parse entities" in str(e):
            # 🛡️ 최후의 방어: 파싱 에러 시 평문으로 재전송
            try:
                bot.send_message(chat_id=ADMIN_ID, text=f"⚠️ [형식오류 발생] {message_text}", parse_mode=None)
            except Exception:
                pass  # 이미 에러 로깅됨
        print(f"⚠️ 관리자 다이렉트 발송 실패: {e}")
        log_info(f"⚠️ 관리자 다이렉트 발송 실패: {e}")
    except Exception as e:
        print(f"⚠️ 관리자 다이렉트 발송 실패: {e}")
        log_info(f"⚠️ 관리자 다이렉트 발송 실패: {e}")

def _broadcast_alert(message_text, audience='VIP_ALL', parse_mode='HTML'): 
    """권한(Audience)에 따라 가입자에게 브로드캐스트 (중복 함수 병합 완료)"""
    chat_ids = db_manager.get_telegram_chat_ids()
    
    for chat_id in chat_ids:
        user_level = db_manager.get_user_level(chat_id)
        
        should_send = False
        if user_level == 'A':
            should_send = True  # Admin은 무조건 수신
        elif user_level == 'V' and audience == 'VIP_ALL':
            should_send = True  # VIP는 일반 알림 수신

        if should_send:
            try:
                # 💡 [핵심] 만약 parse_mode가 HTML인데 message_text에 생으로 <, >가 들어있으면 에러남
                # 호출하는 쪽에서 이미 html.escape를 썼는지 확인이 필요합니다.
                bot.send_message(chat_id, message_text, parse_mode=parse_mode)
            except telebot.apihelper.ApiTelegramException as e:
                if "can't parse entities" in str(e):
                    # 🛡️ 최후의 방어: 파싱 에러 시 평문으로 재전송
                    # HTML 태그 제거
                    clean_text = re.sub(r'<[^>]+>', '', message_text)
                    try:
                        bot.send_message(chat_id, f"⚠️ [형식오류 발생] {clean_text}", parse_mode=None)
                    except Exception:
                        pass  # 이미 에러 로깅됨
                log_info(f"⚠️ 메시지 전송 중 API 에러: {e}")
            except Exception as e:
                print(f"⚠️ chat_id {chat_id} 메시지 전송 실패: {e}")
                log_info(f"⚠️ chat_id {chat_id} 메시지 전송 실패: {e}")

def _is_transient_connection_issue(exc):
    """흔한 네트워크 순단(Reset/Timeout/Remote close)만 조용히 재시도 대상으로 분류"""
    error_text = str(exc).lower()
    transient_signatures = (
        "connection reset by peer",
        "errno 104",
        "[errno 104]",
        "remote end closed connection without response",
        "connection aborted",
        "broken pipe",
        "read timed out",
        "connect timeout",
        "timed out",
        "temporarily unavailable",
    )
    return any(signature in error_text for signature in transient_signatures)
# ==========================================
# 🎧 5. EventBus 구독 (Subscriber) 핸들러
# ==========================================
def handle_telegram_event(event_data):
    """
    💡 [핵심 아키텍처] 스나이퍼나 스캐너가 발행한 이벤트를 수신하여 텔레그램으로 쏘는 역할
    """
    # 1. 단순 메시지 형태 (update_kospi.py 등에서 보냄)
    if 'message' in event_data:
        msg = event_data.get('message', '')
        audience = event_data.get('audience', 'VIP_ALL')
        parse_mode = event_data.get('parse_mode', 'HTML')
        
        if not msg: return

        if audience == 'ADMIN_ONLY':
            _send_to_admin(msg, parse_mode)
        else:
            _broadcast_alert(msg, audience, parse_mode)
            
    # 2. 💡 [신규] 장전 리포트 형태 (final_ensemble_scanner.py 에서 보냄)
    elif event_data.get('type') == 'START_OF_DAY_REPORT':
        perf = event_data.get('performance_report', '')
        ai_brief = event_data.get('ai_briefing', '')
        main_picks = event_data.get('main_picks', [])
        
        # 메시지를 예쁘게 조립합니다.
        msg = f"🏆 <b>[오늘의 AI 리포트]</b>\n\n{perf}"
        if main_picks:
            msg += "🔥 <b>[오늘의 강력 추천]</b>\n"
            for p in main_picks:
                # msg += f"• {p['Name']} ({p['Code']}) - AI확신: {p['Prob']*100:.1f}%\n"
                msg += f"• {p['Name']} ({p['Code']}) \n"
        
        msg += f"\n🤖 <b>[AI 수석 브리핑]</b>\n{ai_brief}"
        _broadcast_alert(msg, audience='VIP_ALL', parse_mode='HTML')
        
    # 3. 💡 [핵심 추가] 코스닥 장중 스캐너 리포트 수신 처리
    elif event_data.get('type') == 'KOSDAQ_REPORT':
        picks = event_data.get('picks', [])
        if not picks: return
        
        msg = "⚡ <b>[KOSDAQ AI 수급 폭발 포착]</b>\n\n"
        for p in picks:
            msg += f"🎯 <b>{p['Name']}</b> (<code>{p['Code']}</code>)\n"
            msg += f" ├ 현재가: {p['Price']:,}원\n"
            msg += f" ├ AI확신: {p['Prob']*100:.1f}%\n"
            msg += f" └ 수급상태: {p['ProgramStatus']}\n\n"
            
        msg += "<i>※ 해당 종목은 즉시 실시간 스나이퍼 감시망에 투입되었습니다.</i>"
        
        # 장중 속보이므로 VIP에게 즉시 쏩니다.
        _broadcast_alert(msg, audience='VIP_ALL', parse_mode='HTML')

def handle_admin_notify(event_data):
    """💡 [신규] TELEGRAM_ADMIN_NOTIFY 전용 수신기"""
    msg = event_data.get('text', '')
    if msg:
        _send_to_admin(msg, parse_mode='Markdown')

# 🚀 모듈이 로드될 때 EventBus에 텔레그램 수신기를 등록합니다!
event_bus.subscribe('TELEGRAM_BROADCAST', handle_telegram_event)
event_bus.subscribe('TELEGRAM_ADMIN_NOTIFY', handle_admin_notify)
# ==========================================
# 6. 텔레그램 UI 및 헬퍼 함수
# ==========================================
def has_special_auth(chat_id):
    chat_id_str = str(chat_id)
    try:
        if chat_id_str == ADMIN_ID: return True
        return db_manager.check_special_auth(chat_id_str)
    except Exception as e:
        print(f"⚠️ 권한 체크 중 DB 에러: {e}")
        log_info(f"⚠️ 권한 체크 중 DB 에러: {e}")
    return False

def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🏆 오늘의 추천종목", "🔍 실시간 종목분석")
    markup.add("📜 감시/보유 리스트", "➕ 수동 종목 추가")
    markup.add("☕ 서버 운영 후원하기", "🤖 AI 확신지수란?")
    return markup

def get_user_badge(chat_id):
    level = db_manager.get_user_level(chat_id)
    return "👑 [VIP 후원자] " if level == 'V' else ("🛡️ [관리자] " if level == 'A' else "👤 [일반] ")

def format_price(p):
    safe_price = int(p.buy_price) if getattr(p, 'buy_price', None) else 0
    status = getattr(p, 'status', 'WATCHING')
    
    if status == 'COMPLETED':
        return "<code>✅ 매매 완료</code>"
    elif status == 'HOLDING':
        return f"<code>📈 보유중 ({safe_price:,}원)</code>"
    elif status == 'BUY_ORDERED':
        return f"<code>🛒 매수 예약 ({safe_price:,}원)</code>"
    elif status == 'SELL_ORDERED':
        return f"<code>💸 매도 주문중</code>"
    else: 
        if safe_price > 0:
            return f"<code>👀 감시중 (포착가: {safe_price:,}원)</code>"
        else:
            return "<code>⏳ 실시간 타점 추적중</code>"

def process_analyze_step(message):
    """
    사용자가 입력한 종목코드를 받아 AI 및 레이더 기반의 실시간 분석 리포트를 회신합니다.
    (DB에 감시 종목으로 추가하지 않습니다)
    """
    code = message.text.strip()
    chat_id = message.chat.id
    
    if not code.isdigit() or len(code) != 6:
        bot.send_message(chat_id, "❌ 잘못된 입력입니다. 6자리 숫자로 된 종목코드를 다시 입력해 주세요.")
        return
    
    # 💡 [신규] 정상적인 종목코드일 때만 횟수를 1회 차감합니다.
    is_allowed, remaining, msg_text = db_manager.check_analyze_quota(chat_id, consume=True)
    if not is_allowed:
        bot.send_message(chat_id, f"🚫 {msg_text}")
        return

    # 대기 메시지 전송
    bot.send_message(chat_id, f"🔄 `{code}` 종목의 실시간 호가창과 차트를 분석 중입니다. 잠시만 기다려주세요...", parse_mode='Markdown')
    
    try:
        import src.engine.kiwoom_sniper_v2 as kiwoom_sniper_v2
        
        # 💡 [핵심 교정 2] 스나이퍼 엔진의 실시간 분석 전용 함수 호출
        report = kiwoom_sniper_v2.analyze_stock_now(code)
        
        bot.send_message(chat_id, report, parse_mode='Markdown')
        
    except Exception as e:
        from src.utils.logger import log_error, log_info
        log_error(f"실시간 종목분석 에러 ({code}): {e}")
        bot.send_message(chat_id, f"❌ 종목 분석 중 시스템 에러 발생: {e}")
        
# ==========================================
# 7. 텔레그램 메시지/명령어 핸들러 (@bot.message_handler)
# ==========================================
# 💡 [기술 부채 노트] 
# 향후 Level 3 아키텍처에서는 사용자의 명령어 입력도 이벤트(예: USER_COMMAND_RECEIVED)로 
# 변환하여 EventBus에 태우는 것이 이상적입니다. 현재는 임포트 지옥을 막기 위해 함수 내 지역 임포트를 유지합니다.

@bot.message_handler(commands=['start', 'help'])
def handle_start(message):
    db_manager.add_new_user(message.chat.id)
    # 관리자는 VIP 승격 패스 (관리자 권한 유지)
    if str(message.chat.id) != str(ADMIN_ID):
        db_manager.upgrade_user_level(message.chat.id, level='V')  # 가입 즉시 VIP로 승격 (테스트용)
    # 💡 [교정 1] 마크다운 문법 오류 수정 (닫히지 않은 백틱 제거 및 이탤릭/볼드체로 깔끔하게 정돈)
    welcome_msg = (
    "🎯 *[KORStockScan V13.0] 스나이퍼 엔진 온라인*\n\n"
    "감정을 배제한 기계의 심장. 백테스트 승률 *63.3%*의 AI 앙상블 타격망이 전개되었습니다.\n\n"
    "⚡ *Sniper Protocol Activating...*\n"
    "✓ `[Targeting]` 다중 AI 합의체 교차 검증 기반 정예 타점 스캐닝\n"
    "✓ `[Radar]` FDR ✖️ Kiwoom 2중 지수 판독 및 실시간 수급 추적\n"
    "✓ `[Action]` 찰나를 파고드는 가변 익절/손절 스마트 트레일링 스탑\n\n"
    "💡 _시장의 노이즈를 뚫고, 가장 완벽한 타점만 저격합니다._" 
    )
    bot.send_message(message.chat.id, welcome_msg, reply_markup=get_main_keyboard(), parse_mode='Markdown')

@bot.message_handler(commands=['상태', 'status'])
def handle_status(message):
    from src.engine.signal_radar import SniperRadar

    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 💡 [교정 2] 더 이상 쓰지 않는 CONF 파라미터 삭제 (의존성 분리 완료)
    token = kiwoom_utils.get_kiwoom_token() 
    regime = SniperRadar.get_market_regime(token)
    regime_icon = "🐂 (상승장)" if regime == 'BULL' else "🐻 (조정장)"

    msg = f"🟢 *[상태 보고]*\n⏱ `{now_str}`\n📊 시장판독: *{regime_icon}*\n"
    bot.send_message(message.chat.id, msg, parse_mode='Markdown')

@bot.message_handler(commands=['restart'])
def cmd_restart(message):
    # 관리자 여부 확인 (ADMIN_ID가 문자열인지 확실히 하기 위해 형변환)
    if str(message.chat.id) == str(ADMIN_ID):
        bot.reply_to(message, "🔄 수동 재시작 플래그를 작동합니다. 관제탑이 안전하게 재가동됩니다.")
        # bot_main.py의 메인 루프가 이 파일을 감지하고 우아하게 종료합니다.
        with open("restart.flag", "w") as f: 
            f.write("restart")
    else:
        bot.reply_to(message, "⛔ 권한이 없습니다.")

@bot.message_handler(func=lambda message: message.text == "🔍 실시간 종목분석")
def handle_analyze_btn(message):
    chat_id = message.chat.id
    
    # 💡 [신규] 권한 및 횟수 단순 검사 (소진 안 함)
    is_allowed, remaining, msg_text = db_manager.check_analyze_quota(chat_id, consume=False)
    if not is_allowed:
        bot.send_message(chat_id, f"🚫 {msg_text}")
        return
        
    remain_text = f"*(남은 횟수: {remaining}회)*" if remaining != -1 else "*(무제한)*"
    msg = bot.reply_to(message, f"🔍 분석할 *종목코드 6자리* 입력 {remain_text}", parse_mode='Markdown')
    bot.register_next_step_handler(msg, process_analyze_step)
    
@bot.message_handler(func=lambda message: message.text == "📜 감시/보유 리스트")
def handle_watch_list(message):
    import pandas as pd
    from src.utils.constants import TRADING_RULES # 상수 안전 임포트
    from src.utils.logger import log_error, log_info
    import telebot.apihelper

    def escape_markdown(text):
        if not isinstance(text, str):
            text = str(text)
        # Escape Markdown special characters (excluding parentheses/brackets/dot/exclamation)
        for ch in '*_``~>#+-=|{}':
            text = text.replace(ch, '\\' + ch)
        return text

    # 💡 [신규] 실시간 분석이 진행되는 동안 대기 메시지 표시
    wait_msg = bot.reply_to(message, "🔄 감시 종목들의 실시간 틱/호가창을 분석하여 **AI 확신점수**를 가져옵니다. 잠시만 기다려주세요...", parse_mode='Markdown')

    try:
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 💡 [아키텍처 포인트 1] 원시 Connection 대신 안전한 ORM Session Bind 활용
        with db_manager.get_session() as session:
            query = f"SELECT * FROM recommendation_history WHERE rec_date='{today}' OR status='HOLDING'"
            df = pd.read_sql(query, session.bind)

        if df.empty:
            bot.edit_message_text(chat_id=message.chat.id, message_id=wait_msg.message_id, text="📭 현재 감시 중이거나 보유 중인 종목이 없습니다.")
            return

        # 💡 [핵심 교정 1] 중복 제거 기준: 'code' -> 'stock_code'
        df = df.sort_values(by='status').drop_duplicates(subset=['stock_code'], keep='first')

        # 구버전 DB라서 prob 컬럼이 아예 없다면, V3 기본값(70%)을 채워줍니다.
        if 'prob' not in df.columns:
            df['prob'] = getattr(TRADING_RULES, 'SNIPER_AGGRESSIVE_PROB', 0.70)

        # 💡 [아키텍처 포인트 2] 스나이퍼 V13.0 상태 머신과 완벽 동기화
        watching = df[df['status'] == 'WATCHING']
        buy_ordered = df[df['status'] == 'BUY_ORDERED']
        sell_ordered = df[df['status'] == 'SELL_ORDERED']
        holding = df[df['status'] == 'HOLDING']
        completed = df[df['status'] == 'COMPLETED']

        # 💡 [핵심] 스나이퍼 엔진을 호출하여 WATCHING 종목들의 실시간 AI 점수를 평가합니다.
        import src.engine.kiwoom_sniper_v2 as kiwoom_sniper_v2
        watching_codes = watching['stock_code'].tolist()
        rt_scores = kiwoom_sniper_v2.get_realtime_ai_scores(watching_codes)

        msg = "📜 *[KORStockScan 감시/보유 현황]*\n"
        msg += "━━━━━━━━━━━━━━\n"

        # 1. 감시 중 (WATCHING)
        watching_display = watching.head(10)
        msg += f"👀 *감시 대기 (WATCHING)* : {len(watching)}종목 (상위 10개 표시)\n"
        for _, row in watching_display.iterrows():
            code = row['stock_code']
            rt_score = rt_scores.get(code)
            
            # 실시간 점수가 정상적으로 수신되었으면 표기하고, 통신 실패 등의 이유로 없으면 DB에 저장된 과거 기본값을 표기합니다.
            if rt_score is not None and rt_score != 50:
                prob_str = f"`{rt_score}점` *(실시간)*"
            else:
                prob_val = row['prob'] if pd.notna(row['prob']) else getattr(TRADING_RULES, 'SNIPER_AGGRESSIVE_PROB', 0.70)
                prob_str = f"{prob_val * 100:.0f}%"
                
            msg += f" • {escape_markdown(row['stock_name'])} ({code}) | AI확신: {prob_str}\n"

        # 2. 주문/체결 대기 (BUY_ORDERED / SELL_ORDERED)
        if not buy_ordered.empty or not sell_ordered.empty:
            total_ordered = len(buy_ordered) + len(sell_ordered)
            msg += f"\n⏳ *주문 전송/대기* : {total_ordered}종목\n"
            for _, row in buy_ordered.iterrows():
                buy_price = row.get('buy_price', 0)
                msg += f" • [매수대기] {escape_markdown(row['stock_name'])} | {int(buy_price) if pd.notna(buy_price) else 0:,}원\n"
            for _, row in sell_ordered.iterrows():
                msg += f" • [매도대기] {escape_markdown(row['stock_name'])} | 체결 확인 중...\n"

        # 3. 보유 중 (HOLDING) - 전략별 구분
        if not holding.empty:
            msg += f"\n💰 *보유 중 (HOLDING)* : {len(holding)}종목\n"
            
            # 전략별 그룹화
            strategy_groups = {
                'SCALPING': '⚡ 단타매매 (SCALPING)',
                'KOSPI_ML': '🛡️ 우량주 스윙 (KOSPI_ML)',
                'KOSDAQ_ML': '🚀 코스닥 스윙 (KOSDAQ_ML)'
            }
            
            # strategy 컬럼이 없을 경우 기본값 KOSPI_ML로 처리
            if 'strategy' not in holding.columns:
                holding = holding.copy()
                holding['strategy'] = 'KOSPI_ML'
            
            for strategy, label in strategy_groups.items():
                subset = holding[holding['strategy'].fillna('KOSPI_ML').str.upper() == strategy.upper()]
                if not subset.empty:
                    msg += f"  {label} : {len(subset)}종목\n"
                    for _, row in subset.iterrows():
                        buy_price = row.get('buy_price', 0)
                        buy_qty = row.get('buy_qty', 0)
                        msg += f"    • {escape_markdown(row['stock_name'])} ({row['stock_code']}) | {int(buy_price) if pd.notna(buy_price) else 0:,}원 ({int(buy_qty) if pd.notna(buy_qty) else 0}주)\n"


        msg += "━━━━━━━━━━━━━━"
        try:
            bot.edit_message_text(chat_id=message.chat.id, message_id=wait_msg.message_id, text=msg, parse_mode='Markdown')
        except telebot.apihelper.ApiTelegramException as e:
            if "can't parse entities" in str(e):
                # Strip markdown formatting and resend as plain text (no extra escaping)
                bot.edit_message_text(chat_id=message.chat.id, message_id=wait_msg.message_id, text=msg, parse_mode=None)
            else:
                raise

    except Exception as e:
        from src.utils.logger import log_error, log_info
        log_error(f"감시 리스트 조회 에러: {e}")
        bot.edit_message_text(chat_id=message.chat.id, message_id=wait_msg.message_id, text=f"❌ 리스트 조회 중 시스템 에러 발생: {e}")

@bot.message_handler(func=lambda message: message.text == "🤖 AI 확신지수란?")
def handle_ai_confidence_info(message):
    info_msg = (
        "🤖 *[KORStockScan AI 확신지수 안내]*\n\n"
        "**AI 확신지수(Probability)**는 4개의 머신러닝 앙상블 모델(XGBoost, LightGBM 등)이 "
        "과거 3년 치의 차트 패턴, 외국인/기관 수급, 호가창 체결 데이터를 입체적으로 학습하여 도출한 **'이 종목이 당일 단기 상승할 확률'**을 의미합니다.\n\n"
        "📊 *확신지수 구간별 의미*\n"
        "• `90% 이상` : 🌟 **[초고확신]** 알고리즘이 찾아낸 완벽한 조건의 S급 타점\n"
        "• `80% ~ 89%` : 🔥 **[고확신]** 강력한 매집 수급이 포착된 주도주 (기본 스나이핑 대상)\n"
        "• `70% ~ 79%` : 🎯 **[유망]** 폭락장/조정장에서 기술적 반등이 예상되는 낙폭과대주\n"
        "• `70% 미만` : 🛑 **[관망]** 하락 리스크가 높아 시스템이 매수를 보류하는 구간\n\n"
        "💡 *스나이퍼 매매 작동 원리*\n"
        "현재 봇은 **AI 확신지수 80% 이상**(폭락장 세팅 시 70% 이상)인 종목 중에서도, "
        "단순히 차트만 보지 않고 **실시간 체결강도가 100을 돌파**하며 세력의 진짜 돈이 들어오는 순간에만 정밀하게 방아쇠를 당깁니다 🔫"
    )
    bot.reply_to(message, info_msg, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == "🏆 오늘의 추천종목")
def handle_today_picks(message):
    chat_id = message.chat.id
    try:
        from src.database.models import RecommendationHistory
        today = datetime.now().date()
        
        with db_manager.get_session() as session:
            picks = session.query(RecommendationHistory).filter_by(rec_date=today).all()

            if not picks:
                bot.send_message(chat_id, "🧐 오늘은 아직 추천 종목이 없습니다.")
                return

            msg = "🏆 <b>[오늘의 AI 추천 종목]</b>\n\n"

            main_picks = [p for p in picks if getattr(p, 'trade_type', '') == 'MAIN']
            runner_picks = [p for p in picks if getattr(p, 'trade_type', '') == 'RUNNER']
            scalp_picks = [p for p in picks if getattr(p, 'trade_type', '') == 'SCALP' or getattr(p, 'strategy', '') == 'SCALPING'] 

            # 💡 [호출부] 안쪽이 훨씬 가벼워졌습니다!
            if main_picks:
                msg += "🔥 <b>[고확신 스윙]</b>\n"
                for p in main_picks:
                    msg += f"• <b>{p.stock_name}</b> ({format_price(p)})\n"
                msg += "\n"

            if runner_picks:
                msg += "🥈 <b>[관심 종목 TOP 10]</b>\n"
                for p in runner_picks[:10]:
                    msg += f"• <b>{p.stock_name}</b> ({format_price(p)})\n"
                msg += "\n"

            if scalp_picks:
                msg += "⚡ <b>[초단타(SCALP) 포착 리스트]</b>\n"
                for p in scalp_picks[:10]:
                    msg += f"• <b>{p.stock_name}</b> ({format_price(p)})\n"

        bot.send_message(chat_id, msg, parse_mode='HTML')

    except Exception as e:
        from src.utils.logger import log_error, log_info
        log_error(f"오늘의 추천종목 에러: {e}")
        bot.send_message(chat_id, f"❌ 추천 종목 로드 실패: {e}")

@bot.message_handler(func=lambda message: message.text == "➕ 수동 종목 추가")
def handle_manual_add_btn(message):
    # 🛡️ 권한 체크: 어드민(A) 또는 VIP(V)
    if not has_special_auth(message.chat.id):
        bot.reply_to(message, "🚫 권한이 없습니다. 관리자(A)만 사용할 수 있는 기능입니다.")
        return

    msg = bot.reply_to(message, "📝 실시간 감시망에 추가할 *종목코드 6자리*를 입력해 주세요.\n*(예: 005930)*", parse_mode='Markdown')
    bot.register_next_step_handler(msg, process_manual_add_step)

def process_manual_add_step(message):
    """
    사용자가 입력한 종목코드를 검증하고 DB에 WATCHING 상태로 추가합니다.
    """
    code = message.text.strip()
    chat_id = message.chat.id
    
    # 💡 [핵심 교정] 람다에서 하던 숫자 검증을 내부로 옮기고, 실패 시 사용자에게 알림을 줍니다.
    if not code.isdigit():
        bot.send_message(message.chat.id, "❌ 잘못된 입력입니다. 숫자로 된 종목코드를 다시 입력해 주세요.")
        return

    bot.send_message(chat_id, f"🔄 `{code}` 종목을 분석하여 스나이퍼 감시망에 투입합니다...", parse_mode='Markdown')

    try:
        from src.utils import kiwoom_utils
        from src.database.models import RecommendationHistory
        from src.utils.constants import TRADING_RULES
        from datetime import datetime

        # 💡 [교정 1] CONF 파라미터 삭제 (독립 호출)
        token = kiwoom_utils.get_kiwoom_token()
        try:
            info = kiwoom_utils.get_basic_info_ka10001(token, code)
            stock_name = info.get('Name', code)
        except Exception as e:
            stock_name = code
            print(f"⚠️ API 종목명 조회 실패, 코드로 대체: {e}")

        # 💡 [교정 2] ORM 호환을 위해 날짜를 date() 객체로 변환
        today = datetime.now().date()
        high_prob = getattr(TRADING_RULES, 'SNIPER_AGGRESSIVE_PROB', 0.8)
        
        with db_manager.get_session() as session:
            # 💡 [교정 3] 구버전 date, code -> 최신 rec_date, stock_code 매핑
            record = session.query(RecommendationHistory).filter_by(rec_date=today, stock_code=code).first()
            
            if record:
                # 이미 오늘 등록된 이력이 있다면 상태를 강제로 감시(WATCHING)로 멱등성 업데이트
                record.status = 'WATCHING'
                record.trade_type = 'SCALP' # 확실한 수동 타입 지정
                record.strategy = 'SCALPING'
                record.prob = high_prob
            else:
                # 없다면 신규 생성 (최신 컬럼명 적용)
                new_record = RecommendationHistory(
                    rec_date=today,          # 💡 교정
                    stock_code=code,         # 💡 교정
                    stock_name=stock_name,   # 💡 교정
                    prob=high_prob,
                    status='WATCHING',
                    trade_type='SCALP',     # 💡 type -> trade_type
                    strategy='SCALPING'
                )
                session.add(new_record)
        
        # 💡 [교정 4] 텔레그램 마크다운 링크 에러 유발 코드 제거
        # (기존의 `[이름](코드)`를 안전한 `*이름 (코드)*` 형태로 변경)
        msg_text = f"✅ *{stock_name} ({code})* 수동 감시 투입 완료!\n\n"
        msg_text += "📡 스나이퍼 엔진이 최대 5초 이내에 해당 종목의 호가창 감시를 시작합니다."
        bot.send_message(chat_id, msg_text, parse_mode='Markdown')

    except Exception as e:
        from src.utils.logger import log_error, log_info
        log_error(f"수동 종목 추가 에러: {e}")
        bot.send_message(chat_id, f"❌ 종목 추가 중 시스템 에러 발생: {e}")

@bot.my_chat_member_handler()
def handle_my_chat_member_update(message: types.ChatMemberUpdated):
    """
    봇의 상태 변화(차단, 해제, 나가기 등)를 실시간으로 감지합니다.
    """
    new_status = message.new_chat_member.status
    chat_id = message.chat.id
    
    if new_status in ['kicked', 'left']:
        # 사용자가 봇을 차단(kicked)하거나 그룹에서 봇을 내보냄(left)
        print(f"👋 [상태변경] 유저 {chat_id}가 봇을 떠났습니다. (상태: {new_status}) DB에서 삭제합니다.")
        db_manager.delete_user(chat_id)
        
    elif new_status == 'member':
        # 차단했던 유저가 다시 대화방에 들어오거나 차단을 해제함
        print(f"✅ [상태변경] 유저 {chat_id}가 다시 복귀했습니다!")
        db_manager.add_new_user(chat_id)

@bot.message_handler(commands=['사유', 'why'])
def handle_why_not(message):
    chat_id = message.chat.id
    parts = message.text.split()
    
    if len(parts) < 2: 
        bot.send_message(chat_id, "⚠️ 종목코드를 함께 입력해 주세요. (예: `/why 005930`)", parse_mode='Markdown')
        return
        
    code = parts[1].strip()
    
    if not code.isdigit() or len(code) != 6:
        bot.send_message(chat_id, "❌ 잘못된 입력입니다. 6자리 숫자 종목코드를 입력해 주세요.")
        return

    # 대기 메시지 (백틱 유지)
    bot.send_message(chat_id, f"🔄 `{code}` 종목의 AI 타점 미달 사유를 분석 중입니다...", parse_mode='Markdown')
    
    try:
        import src.engine.kiwoom_sniper_v2 as kiwoom_sniper_v2
        
        report = kiwoom_sniper_v2.get_detailed_reason(code)
        
        # 💡 [핵심 교정 1] 사유 리포트에는 닫히지 않은 마크다운/특수문자가 섞일 수 있으므로
        # 파싱 없이 평문으로 전송해 리포트 자체 때문에 전송 실패가 나지 않도록 합니다.
        bot.send_message(chat_id, report, parse_mode=None)
        
    except Exception as e:
        from src.utils.logger import log_error, log_info
        log_error(f"미진입 사유 분석 에러 ({code}): {e}")
        bot.send_message(chat_id, f"❌ 사유 분석 중 오류 발생: {e}")

@bot.pre_checkout_query_handler(func=lambda query: True)
def process_pre_checkout(pre_checkout_query):
    """결제 직전 유효성 검사 (Telegram 결제 필수 콜백)"""
    try:
        bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
    except Exception as e:
        from src.utils.logger import log_error, log_info
        log_error(f"결제 사전 승인 에러: {e}")

@bot.message_handler(content_types=['successful_payment'])
def handle_payment_success(message):
    """결제 완료 및 V 등급 승격 처리"""
    chat_id = message.chat.id
    
    try:
        db_manager.upgrade_user_level(chat_id, level='V')
        
        # 💡 [핵심 교정 2] 텔레그램 마크다운 볼드는 ** 가 아니라 * 하나입니다.
        msg = (
            "🎊 *VIP 등급으로 승격되었습니다!*\n\n"
            "이제부터 KORStockScan의 *모든 VIP 전용 알림(초단타 타점, AI 교차 검증 리포트 등)*을 "
            "실시간으로 받아보실 수 있습니다. 후원해 주셔서 진심으로 감사합니다! 👑"
        )
        bot.send_message(chat_id, msg, parse_mode='Markdown')
        
        # EventBus를 통한 관리자 다이렉트 보고
        from src.core.event_bus import EventBus
        event_bus = EventBus()
        admin_msg = f"💸 *[결제 발생]* Chat ID `{chat_id}` 님이 V 등급으로 승격되었습니다."
        event_bus.publish('TELEGRAM_BROADCAST', {'message': admin_msg, 'audience': 'ADMIN_ONLY', 'parse_mode': 'Markdown'})
        
    except Exception as e:
        from src.utils.logger import log_error, log_info
        log_error(f"결제 완료 처리 중 시스템 에러: {e}")
        bot.send_message(chat_id, "✅ 결제는 확인되었으나 시스템 지연으로 등급 반영이 지연되고 있습니다. 관리자가 곧 수동으로 처리해 드릴 예정입니다.")

@bot.message_handler(func=lambda message: True)
def handle_text_messages(message):
    bot.send_message(message.chat.id, "메뉴 버튼을 이용해 주세요.", reply_markup=get_main_keyboard())

# ==========================================
# 🚀 8. 봇 구동 진입점 (bot_main.py에서 호출됨)
# ==========================================
def start_telegram_bot():
    print("🤖 텔레그램 봇 수신 대기 시작...")
    import requests.exceptions
    import random
    import traceback
    global bot
    
    retry_delay = 5  # seconds
    max_retry_delay = 60
    consecutive_failures = 0
    max_consecutive_failures = 10  # 재생성 임계값

    while True:
        try:
            # 💡 [핵심 최적화 1] 타임아웃을 넉넉하게 늘리고, 내부 에러 로그(CRITICAL)를 꺼서 화면을 깔끔하게 유지합니다.
            bot.infinity_polling(
                timeout=30, 
                long_polling_timeout=20, 
                logger_level=logging.CRITICAL
            )
            
            # 폴링이 예외 없이 반환되면 안정화된 것으로 간주
            retry_delay = 5
            consecutive_failures = 0
            print("✅ 텔레그램 연결 안정화, 재시도 대기 시간 초기화.")
            continue
            
        except requests.exceptions.ConnectionError as ce:
            if _is_transient_connection_issue(ce):
                print(f"⚠️ [WS] 일시적 텔레그램 연결 순단 감지: {ce}. {retry_delay}초 후 재접속합니다...")
            else:
                log_error(f"텔레그램 ConnectionError 발생: {type(ce).__name__}: {ce}")
                print(f"⚠️ 텔레그램 ConnectionError ({ce}). {retry_delay}초 후 재시도...")
            
        except Exception as e:
            # 기타 심각한 에러에 대해서만 전체 에러 트레이스백을 로깅합니다.
            error_trace = traceback.format_exc()
            log_error(f"텔레그램 봇 예외 발생: {e}\n{error_trace}")
            print(f"⚠️ 텔레그램 예외 ({e}). {retry_delay}초 후 재시도...")

        # 지수 백오프(Exponential backoff) 및 지터(Jitter) 대기
        consecutive_failures += 1
        retry_delay = min(retry_delay * 2, max_retry_delay)
        jitter = random.uniform(0, 2)
        sleep_time = retry_delay + jitter
        print(f"⚠️ 텔레그램 재시도 {consecutive_failures}회 실패, {sleep_time:.1f}초 후 재접속...")

        # 연속 실패 횟수가 임계값을 넘으면 봇 인스턴스 완전 재생성
        if consecutive_failures >= max_consecutive_failures:
            print(f"🔄 연속 {consecutive_failures}회 실패로 봇 인스턴스를 재생성합니다.")
            try:
                bot = _create_bot_instance()
                print("🤖 새로운 봇 인스턴스 생성 완료.")
            except Exception as e:
                log_error(f"봇 인스턴스 재생성 실패: {e}")
            consecutive_failures = 0  # 재생성 후 카운터 리셋

        time.sleep(sleep_time)
