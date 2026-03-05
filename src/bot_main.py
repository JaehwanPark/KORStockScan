# ==========================================
# 1. 임포트 및 전역 변수 설정 (TOKEN, CONF, DBManager 등)
# ==========================================
import json
import os
import signal
import sqlite3
import threading
import time
from datetime import datetime

import telebot
from telebot import types

# 💡 엔진 및 유틸리티 모듈 임포트
import kiwoom_sniper_v2
import kiwoom_utils
from db_manager import DBManager
from constants import TRADING_RULES

# ==========================================
# 2. 경로 및 환경 설정 (상대 참조 고정)
# ==========================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..', 'data'))
os.makedirs(DATA_DIR, exist_ok=True)

CONFIG_PATH = os.path.join(DATA_DIR, 'config_prod.json')
USERS_DB_PATH = os.path.join(DATA_DIR, 'users.db')
STOCK_DB_PATH = os.path.join(DATA_DIR, 'kospi_stock_data.db')

# 전역 DB 매니저 인스턴스 생성
db_manager = DBManager()

def load_config():
    """안전한 설정 파일 로드"""
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ 설정 파일을 찾을 수 없습니다: {CONFIG_PATH}")
        return {}

CONF = load_config()
TOKEN = CONF.get('TELEGRAM_TOKEN')

if not TOKEN:
    print("🚨 TELEGRAM_TOKEN이 없어 봇을 기동할 수 없습니다.")
    exit()

bot = telebot.TeleBot(TOKEN)
engine_thread = None


def has_special_auth(chat_id):
    """
    요청한 사용자가 최고관리자(ADMIN_ID)이거나,
    users.db 상에서 auth_group이 'A'(어드민) 또는 'V'(VIP)인 사용자인지 판별합니다.
    """
    chat_id_str = str(chat_id)

    # 1. 최고 관리자(config.json의 ADMIN_ID)는 무조건 프리패스 (안전장치)
    admin_id = str(CONF.get('ADMIN_ID', ''))
    if chat_id_str == admin_id:
        return True

    # 2. DB에서 권한 그룹 조회 (A: 어드민, V: VIP)
    try:
        # USER_DB_PATH 변수가 봇 파일 상단에 정의되어 있어야 합니다.
        with sqlite3.connect(USERS_DB_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT auth_group FROM users WHERE chat_id = ?", (chat_id_str,))
            result = cursor.fetchone()

            # 💡 [핵심] 결과가 'A' 이거나 'V' 이면 통과!
            if result and result[0] in ['A', 'V']:
                return True
    except Exception as e:
        print(f"⚠️ 권한 체크 중 DB 에러 발생: {e}")

    # 권한이 없거나 에러가 나면 False 반환
    return False

# ==========================================
# 3. 데이터베이스 유틸리티 (Thread-safe)
# ==========================================
def init_db():
    """사용자 관리 DB 초기화"""
    with sqlite3.connect(USERS_DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                chat_id INTEGER PRIMARY KEY,
                user_level INTEGER DEFAULT 0,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

def get_db_connection(db_path):
    """함수 내에서 개별적으로 연결하여 스레드 충돌 방지"""
    return sqlite3.connect(db_path, timeout=10)

# ==========================================
# 4. 유틸리티 및 UI 함수 (핸들러보다 무조건 위에 위치!)
# ==========================================
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🏆 오늘의 추천종목", "🔍 실시간 종목분석")
    markup.add("📜 감시/보유 리스트", "➕ 수동 종목 추가")
    # 💡 [수정] 후원하기 버튼 옆에 나란히 배치되도록 버튼 추가!
    markup.add("☕ 서버 운영 후원하기", "🤖 AI 확신지수란?")
    return markup

def get_user_badge(chat_id):
    try:
        temp_conn = sqlite3.connect(USERS_DB_PATH)
        row = temp_conn.execute("SELECT user_level FROM users WHERE chat_id = ?", (chat_id,)).fetchone()
        temp_conn.close()
        return "👑 [VIP 후원자] " if row and row[0] == 1 else "👤 [일반] "
    except:
        return ""

def process_manual_add_logic(message, code):
    stock_name = code

    # 🛡️ 오직 키움 API(ka10001) 다이렉트 호출 (FDR 완전 제거)
    try:
        token = kiwoom_utils.get_kiwoom_token(CONF)
        info = kiwoom_utils.get_basic_info_ka10001(token, code)
        stock_name = info['Name']

        # 엉뚱한 코드 입력 시 방어
        if stock_name == code:
            raise ValueError("존재하지 않는 종목코드이거나 상장폐지된 종목입니다.")

    except Exception as api_e:
        bot.reply_to(message, f"❌ 종목명 조회 실패: 올바른 종목코드인지 확인해 주세요. ({api_e})")
        return

        # 🎯 DB 저장 및 V3 룰 적용
    try:
        db = DBManager()
        today = datetime.now().strftime('%Y-%m-%d')

        with db._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO recommendation_history 
                (date, code, name, prob, status) 
                VALUES (?, ?, ?, ?, 'WATCHING')
            """, (today, code, stock_name, TRADING_RULES['SNIPER_AGGRESSIVE_PROB']))
            conn.commit()

        # ==========================================
        # 💡 [신규] 수동 추가 시 차트 기반 목표가 즉시 계산
        # ==========================================

        df = db.get_stock_data(code, limit=20)

        target_price_str = "데이터 부족 (기본값 적용)"
        target_reason = f"기본 시스템 익절선 (+{TRADING_RULES.get('TRAILING_START_PCT', 3.0)}%)"

        # DB에 데이터가 충분히 있는 경우 차트 저항대 계산
        if df is not None and len(df) >= 10:
            # 어제 종가 기준(또는 DB상 가장 최근 종가)
            curr_price = int(df.iloc[-1]['Close'])
            high_20d = df['High'].max()

            # 볼린저 밴드 상단 계산
            ma20 = df['Close'].mean()
            std20 = df['Close'].std()
            upper_bb = ma20 + (2 * std20)

            chart_resistance = max(high_20d, upper_bb)
            rally_pct = TRADING_RULES.get('RALLY_TARGET_PCT', 5.0)

            if chart_resistance > curr_price:
                target_price = int(chart_resistance)
                expected_rtn = ((target_price / curr_price) - 1) * 100
                target_price_str = f"{target_price:,}원 (+{expected_rtn:.1f}%)"
                target_reason = "차트 저항대 (20일 고점/볼린저 상단)"
            else:
                # 저항선을 뚫은 신고가 영역
                target_price = int(curr_price * (1 + (rally_pct / 100)))
                target_price_str = f"{target_price:,}원 (+{rally_pct}%)"
                target_reason = "신고가 돌파 랠리 (단기 추세)"

        # ==========================================
        # 💡 업그레이드된 알림 메시지 구성
        # ==========================================
        msg = (
            f"✅ *[{stock_name}]({code}) 수동 감시 추가 완료!*\n\n"
            f"📊 *차트 기반 1차 목표가*\n"
            f"• 목표 단가: `{target_price_str}`\n"
            f"• 산출 사유: *{target_reason}*\n\n"
            f"⚙️ *현재 적용 기준 (V3 황금 비율)*\n"
            f"• 매수 조건: 수급 포착 시 (AI 확신도 {TRADING_RULES.get('SNIPER_AGGRESSIVE_PROB', 0.8) * 100:.0f}% 간주)\n"
            f"• 기계 익절선: `+{TRADING_RULES.get('TRAILING_START_PCT', 3.0)}%` (도달 시 트레일링 스탑)\n"
            f"• 기본 손절선: `{TRADING_RULES.get('STOP_LOSS_BULL', -2.5)}%`\n\n"
            f"🔫 지금부터 스나이퍼가 실시간 타점을 감시합니다."
        )
        bot.reply_to(message, msg, parse_mode='Markdown')

    except Exception as e:
        bot.reply_to(message, f"❌ DB 저장 중 시스템 에러 발생: {e}")

def broadcast_alert(message_text):
    temp_conn = sqlite3.connect(USERS_DB_PATH)
    rows = temp_conn.execute('SELECT chat_id FROM users').fetchall()
    for row in rows:
        try:
            bot.send_message(row[0], message_text, parse_mode='Markdown')
            time.sleep(0.05)
        except:
            pass
    temp_conn.close()

def broadcast_today_picks():
    """
    [v12.1 복구] 봇 시작 시, 오늘 날짜의 추천 종목을 모든 가입자에게 브로드캐스트합니다.
    """
    try:
        # 1. DB 연결 및 오늘자 추천 종목 조회
        conn = sqlite3.connect(STOCK_DB_PATH)
        today = datetime.now().strftime('%Y-%m-%d')

        # 종목코드 6자리를 보장하며 데이터 추출
        query = "SELECT name, buy_price, type, code FROM recommendation_history WHERE date=?"
        picks = conn.execute(query, (today,)).fetchall()
        conn.close()

        if not picks:
            print(f"🧐 [{today}] 추천 종목이 아직 생성되지 않아 알림을 대기합니다.")
            return

        # 💡 constants.py에 세팅된 익절/손절 기준값을 가져옵니다.
        # (키 이름이 다르다면 constants.py에 적힌 이름으로 맞춰주세요!)
        take_profit = TRADING_RULES.get('TRAILING_START_PCT', 3.0)
        stop_loss = TRADING_RULES.get('STOP_LOSS_PCT', 2.5)

        # 2. 메시지 헤더 구성
        msg = f"🌅 **[{today}] AI 스태킹 앙상블 리포트**\n"
        msg += f"🎯 **전략: 장중 +{take_profit}% 익절(가변익절) / -{stop_loss}% 손절**\n"
        msg += "--------------------------------------\n"

        # 3. 등급별 종목 분류 (code[:6] 원칙 적용)
        main_picks = [p for p in picks if p[2] == 'MAIN']
        runner_picks = [p for p in picks if p[2] == 'RUNNER']

        # 강력 추천 종목 출력
        if main_picks:
            msg += "🔥 **[고확신 종목]**\n"
            for name, price, _, code in main_picks:
                clean_code = str(code)[:6]  # 🚀 무조건 6자리만 사용
                msg += f"• **{name}** ({clean_code}) : `{price:,}원`\n"
            msg += "\n"

        # 관심 종목 출력 (상위 10개로 제한하여 도배 방지)
        if runner_picks:
            msg += "🥈 **[관심 종목 TOP 10]**\n"
            for name, price, _, code in runner_picks[:10]:
                clean_code = str(code)[:6]
                msg += f"• **{name}** ({clean_code}) : `{price:,}원`\n"

            # 전체 개수 안내로 신뢰도 상승
            if len(runner_picks) > 10:
                msg += f"\n*(그 외 {len(runner_picks) - 10}개의 유망 종목 실시간 추적 중)*"

        msg += "\n--------------------------------------\n"
        msg += "💡 `/상태` 입력 시 엔진 가동 현황을 확인하실 수 있습니다."

        # 4. 전체 사용자에게 전송
        broadcast_alert(msg)
        print(f"📢 [{today}] 추천 종목 브로드캐스트 완료 (총 {len(picks)}종목)")

    except Exception as e:
        # 통합 에러 로깅 활용
        import kiwoom_utils
        kiwoom_utils.log_error(f"❌ 아침 브로드캐스트 실패: {e}", config=CONF)

def process_manual_add_step(message):
    code = message.text.strip()

    # 사용자가 코드를 안 치고 다른 메뉴 버튼을 눌러버렸을 경우 (취소 처리)
    if not code.isdigit() or len(code) != 6:
        bot.reply_to(message, "🚫 종목 추가가 취소되었거나 올바른 6자리 숫자가 아닙니다.")
        return

    process_manual_add_logic(message, code)

def process_analyze_logic(message, code):
    """실제 분석을 수행하는 핵심 로직"""
    badge = get_user_badge(message.chat.id)
    chat_id = message.chat.id

    bot.send_message(chat_id, f"🔄 `{code}` 종목의 실시간 데이터를 수집하고 분석을 시작합니다...\n*(데이터 수신에 몇 초 정도 소요될 수 있습니다)*", parse_mode='Markdown')

    try:
        # 스나이퍼 V2의 분석 함수 호출
        report = kiwoom_sniper_v2.analyze_stock_now(code)
        final_msg = f"{badge}님을 위한 분석 결과입니다!\n\n{report}"
        bot.send_message(chat_id, final_msg, parse_mode='Markdown')
    except Exception as e:
        bot.send_message(chat_id, f"❌ 분석 중 오류 발생: {e}")

def process_analyze_step(message):
    """버튼 클릭 후 사용자가 입력한 코드를 검증하는 단계"""
    code = message.text.strip()

    # 올바른 6자리 숫자인지 검증 (다른 메뉴 버튼을 눌렀을 때 방어)
    if not code.isdigit() or len(code) != 6:
        bot.reply_to(message, "🚫 분석이 취소되었거나 올바른 6자리 숫자가 아닙니다.")
        return

    process_analyze_logic(message, code)

def start_engine():
    kiwoom_sniper_v2.run_sniper(broadcast_alert)

def monitor_exit_time():
    while True:
        if datetime.now().time() >= datetime.strptime("23:50:00", "%H:%M:%S").time():
            print("🌙 시스템 안전 종료")
            os.kill(os.getpid(), signal.SIGTERM)
        time.sleep(60)

# ==========================================
# 🎯 5. 메인 키보드 버튼 전용 핸들러들 (우선순위 높음)
# ==========================================

@bot.message_handler(func=lambda message: message.text == "📜 감시/보유 리스트")
def handle_watch_list(message):
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        with db_manager._get_connection() as conn:
            # 💡 [수정] prob 컬럼을 콕 집어 부르지 않고 전체(*)를 안전하게 가져옵니다.
            query = "SELECT * FROM recommendation_history WHERE date=? OR status='HOLDING'"
            import pandas as pd
            df = pd.read_sql(query, conn, params=(today,))

        if df.empty:
            bot.reply_to(message, "📭 현재 감시 중이거나 보유 중인 종목이 없습니다.")
            return

        # 스나이퍼 엔진과 동일하게 중복 제거 (HOLDING 우선)
        df = df.sort_values(by='status').drop_duplicates(subset=['code'], keep='first')

        # 💡 [핵심 방어] 구버전 DB라서 prob 컬럼이 아예 없다면, V3 기본값(70%)을 채워줍니다.
        if 'prob' not in df.columns:
            df['prob'] = TRADING_RULES['SNIPER_AGGRESSIVE_PROB']

        # 상태별로 분류
        watching = df[df['status'] == 'WATCHING']
        pending = df[df['status'] == 'PENDING']
        holding = df[df['status'] == 'HOLDING']
        completed = df[df['status'] == 'COMPLETED']

        msg = "📜 *[KORStockScan V3 감시/보유 현황]*\n"
        msg += "━━━━━━━━━━━━━━\n"

        # 1. 감시 중 (WATCHING)
        msg += f"👀 *감시 대기 (WATCHING)* : {len(watching)}종목\n"
        for _, row in watching.iterrows():
            # 안전하게 prob 값 추출 (결측치면 70%)
            prob_val = row['prob'] if pd.notna(row['prob']) else TRADING_RULES['SNIPER_AGGRESSIVE_PROB']
            msg += f" • {row['name']} ({row['code']}) | AI확신: {prob_val * 100:.0f}%\n"

        # 2. 주문/체결 대기 (PENDING)
        if not pending.empty:
            msg += f"\n⏳ *주문 대기 (PENDING)* : {len(pending)}종목\n"
            for _, row in pending.iterrows():
                buy_price = row.get('buy_price', 0)
                msg += f" • {row['name']} | {int(buy_price) if pd.notna(buy_price) else 0:,}원 주문 중\n"

        # 3. 보유 중 (HOLDING)
        if not holding.empty:
            msg += f"\n💰 *보유 중 (HOLDING)* : {len(holding)}종목\n"
            for _, row in holding.iterrows():
                buy_price = row.get('buy_price', 0)
                buy_qty = row.get('buy_qty', 0)
                msg += f" • {row['name']} ({row['code']}) | {int(buy_price) if pd.notna(buy_price) else 0:,}원 ({int(buy_qty) if pd.notna(buy_qty) else 0}주)\n"

        # 4. 오늘 매매 완료 (COMPLETED)
        if not completed.empty:
            msg += f"\n🏁 *금일 매매 완료* : {len(completed)}종목\n"
            for _, row in completed.iterrows():
                msg += f" • {row['name']}\n"

        msg += "━━━━━━━━━━━━━━"
        bot.reply_to(message, msg, parse_mode='Markdown')

    except Exception as e:
        bot.reply_to(message, f"❌ 리스트 조회 중 시스템 에러 발생: {e}")

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

@bot.message_handler(func=lambda message: message.text == "🔍 실시간 종목분석")
def handle_analyze_btn(message):
    """버튼을 눌렀을 때 안내 메시지를 띄우고 다음 입력을 기다림"""
    msg = bot.reply_to(message, "🔍 실시간으로 분석할 **종목코드 6자리**를 입력해 주세요.\n*(예: 005930)*", parse_mode='Markdown')
    bot.register_next_step_handler(msg, process_analyze_step)


# --- [명령어로 직접 입력 시 (/분석 005930)] ---
@bot.message_handler(commands=['분석', 'analyze'])
def handle_analyze_cmd(message):
    """/분석 명령어로 직접 입력했을 때 처리"""
    parts = message.text.split()

    if len(parts) < 2:
        bot.reply_to(message, "⚠️ 종목코드를 함께 입력해 주세요. (예: `/분석 005930`)", parse_mode='Markdown')
        return

    process_analyze_logic(message, parts[1].strip())

@bot.message_handler(func=lambda message: message.text == "🏆 오늘의 추천종목")
def handle_today_picks(message):
    chat_id = message.chat.id
    try:
        conn_temp = sqlite3.connect(STOCK_DB_PATH)
        today = datetime.now().strftime('%Y-%m-%d')
        picks = conn_temp.execute("SELECT name, buy_price, type FROM recommendation_history WHERE date=?",
                                  (today,)).fetchall()
        conn_temp.close()

        if not picks:
            bot.send_message(chat_id, "🧐 오늘은 아직 추천 종목이 없습니다.")
            return

        msg = "🏆 **[오늘의 AI 추천 종목]**\n\n"
        main_picks = [p for p in picks if p[2] == 'MAIN']
        runner_picks = [p for p in picks if p[2] == 'RUNNER']

        if main_picks:
            msg += "🔥 **[강력 추천]**\n"
            for name, price, _ in main_picks:
                msg += f"• **{name}** (`{price:,}원`)\n"
            msg += "\n"

        if runner_picks:
            msg += "🥈 **[관심 종목 상위 10개]**\n"
            for name, price, _ in runner_picks[:10]:
                msg += f"• **{name}** (`{price:,}원`)\n"

        bot.send_message(chat_id, msg, parse_mode='Markdown')
    except:
        bot.send_message(chat_id, "❌ 추천 종목 로드 실패")

@bot.message_handler(func=lambda message: message.text == "➕ 수동 종목 추가")
def handle_manual_add_btn(message):
    # 🛡️ 권한 체크: 어드민(A) 또는 VIP(V)
    if not has_special_auth(message.chat.id):
        bot.reply_to(message, "🚫 권한이 없습니다. 봇 관리자(A) 또는 VIP(V) 등급만 사용할 수 있는 기능입니다.")
        return

    msg = bot.reply_to(message, "📝 실시간 감시망에 추가할 **종목코드 6자리**를 입력해 주세요.\n*(예: 005930)*", parse_mode='Markdown')
    bot.register_next_step_handler(msg, process_manual_add_step)


# --- [명령어로 직접 입력 시 (/add 005930)] ---
@bot.message_handler(commands=['add'])
def handle_manual_add_cmd(message):
    # 🛡️ 권한 체크: 어드민(A) 또는 VIP(V)
    if not has_special_auth(message.chat.id):
        bot.reply_to(message, "🚫 권한이 없습니다. 봇 관리자(A) 또는 VIP(V) 등급만 사용할 수 있는 기능입니다.")
        return

    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "⚠️ 종목코드를 함께 입력해 주세요. (예: `/add 005930`)", parse_mode='Markdown')
        return

    process_manual_add_logic(message, args[1])

# ==========================================
# 🎯 6. 명령어 핸들러들 (/상태, /분석, /add 등)
# ==========================================

@bot.message_handler(commands=['start', 'help'])
def handle_start(message):
    chat_id = message.chat.id
    with sqlite3.connect(USERS_DB_PATH) as conn:
        conn.execute('INSERT OR IGNORE INTO users (chat_id) VALUES (?)', (chat_id,))

    welcome_msg = (
        "🚀 **KORStockScan v12.1 관제 시스템 기동**\n\n"
        "백테스트 **승률 63.3%**의 AI 앙상블이 실시간 감시 중입니다.\n\n"
        "📈 **스나이퍼 매매 원칙**\n"
        "• 장중 가변 익절 / 손절 시스템 적용\n"
        "• FDR-Kiwoom API 2중 지수 판독 적용\n"
        "• AI 확신도 기반 정예 종목 선별"
    )
    bot.send_message(chat_id, welcome_msg, parse_mode='Markdown', reply_markup=get_main_keyboard())

@bot.message_handler(commands=['상태', 'status'])
def handle_status(message):
    chat_id = message.chat.id
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    token = kiwoom_utils.get_kiwoom_token(CONF)
    regime = kiwoom_utils.get_market_regime(token)
    regime_icon = "🐂 (상승장)" if regime == 'BULL' else "🐻 (조정장)"

    msg = f"🟢 *[KORStockScan 시스템 보고]*\n"
    msg += f"⏱ 현재시간: `{now_str}`\n"
    msg += f"📊 시장판독: **{regime_icon}**\n\n"

    msg += "✅ **매매 엔진:** `정상 가동 중` 💓\n" if engine_thread and engine_thread.is_alive() else "❌ **매매 엔진:** `중단됨` ⚠️\n"

    # 💡 [최적화] DBManager 활용 (락 방지)
    try:
        with db_manager._get_connection() as conn:
            today = datetime.now().strftime('%Y-%m-%d')
            watch_cnt = conn.execute("SELECT COUNT(*) FROM recommendation_history WHERE date=? AND status='WATCHING'",
                                     (today,)).fetchone()[0]
            hold_cnt = conn.execute("SELECT COUNT(*) FROM recommendation_history WHERE date=? AND status='HOLDING'",
                                    (today,)).fetchone()[0]
            msg += f"👀 **감시 대상:** `{watch_cnt} 종목`\n"
            msg += f"💼 **보유 종목:** `{hold_cnt} 종목`"
    except Exception as e:
        msg += f"⚠️ DB 조회 불가: {e}"

    bot.send_message(chat_id, msg, parse_mode='Markdown')

@bot.message_handler(commands=['사유', 'why'])
def handle_why_not(message):
    chat_id = message.chat.id
    parts = message.text.split()

    if len(parts) < 2:
        bot.send_message(chat_id, "⚠️ 종목코드를 입력해주세요. (예: `/사유 005930`)")
        return

    code = parts[1].strip()
    bot.send_message(chat_id, f"🔍 `{code}` 종목의 실시간 진입 요건을 정밀 분석합니다...")

    try:
        # 스나이퍼 엔진의 상세 사유 함수 호출
        reason_report = kiwoom_sniper_v2.get_detailed_reason(code)
        bot.send_message(chat_id, reason_report, parse_mode='Markdown')
    except Exception as e:
        bot.send_message(chat_id, f"❌ 분석 중 오류 발생: {e}")

@bot.pre_checkout_query_handler(func=lambda query: True)
def process_pre_checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def handle_payment_success(message):
    chat_id = message.chat.id
    temp_conn = sqlite3.connect(USERS_DB_PATH)
    temp_conn.execute("UPDATE users SET user_level = 1 WHERE chat_id = ?", (chat_id,))
    temp_conn.commit()
    temp_conn.close()
    bot.send_message(chat_id, "🎊 **VIP 등급으로 승격되었습니다!**")

@bot.message_handler(commands=['reload'])
def handle_reload(message):
    global CONF
    chat_id = message.chat.id
    if str(chat_id) != str(CONF.get('ADMIN_ID')):
        bot.send_message(chat_id, "⛔ 관리 권한이 없습니다.")
        return

    try:
        CONF = load_config()
        if kiwoom_sniper_v2.reload_config():
            bot.send_message(chat_id, "✅ 설정이 성공적으로 새로고침 되었습니다!")
    except Exception as e:
        bot.send_message(chat_id, f"❌ 새로고침 오류: {e}")

# ==========================================
# 🎯 블랙홀(Catch-all) 핸들러 (반드시 맨 마지막에 위치!)
# ==========================================

@bot.message_handler(func=lambda message: True)
def handle_text_messages(message):
    # 위에서 정의된 버튼 텍스트나 명령어에 해당하지 않는 '모든 잡다한 텍스트'는 여기서 걸러집니다.
    bot.send_message(message.chat.id, "아래 메뉴 버튼을 이용해 주세요.", reply_markup=get_main_keyboard())

if __name__ == '__main__':
    print("🤖 KORStockScan v12.1 관제 시스템 기동 중...")
    init_db()

    # 🚀 영업일 체크
    is_open, reason = kiwoom_utils.is_trading_day()

    if is_open:
        # 정상 영업일에만 리포트 발송 및 매매 엔진 스레드 시작
        broadcast_today_picks()

        engine_thread = threading.Thread(target=start_engine, daemon=True)
        engine_thread.start()
        print("✅ [시스템] 정상거래일 - 스나이퍼 엔진 스레드가 가동되었습니다.")
    else:
        # 휴장일 처리
        print(f"🛑 [시스템] 오늘은 {reason} 휴장일입니다. 매매 엔진과 리포트 발송을 생략합니다.")
        # engine_thread는 None 상태로 유지되어 /상태 명령어 시 '중단됨'으로 정상 표시됨

    # 야간 자동 종료 감시 시작 (휴장일이어도 봇 프로세스 자체는 꺼야 하므로 실행)
    threading.Thread(target=monitor_exit_time, daemon=True).start()

    print("📱 텔레그램 봇 폴링 시작 (명령어 대기 중)...")
    # 🚀 [수정] 강력한 네트워크 끊김(10054) 발생 시 5초 후 무한 자동 재시작
    while True:
        try:
            # timeout 설정을 주어 연결이 좀비 상태가 되는 것을 방지
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(f"⚠️ 텔레그램 서버 연결 순단 발생 ({e}). 5초 후 재접속을 시도합니다...")
            time.sleep(5)