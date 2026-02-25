import telebot
import sqlite3
import threading
import time
import json
from datetime import datetime
from telebot import types
import os
import signal

# 💡 V2 스캐닝 엔진 임포트
import kiwoom_sniper_v2 

# 🚀 엔진 상태 확인을 위한 전역 변수
engine_thread = None
CONF = None

# --- [1. 환경 설정 및 DB 초기화] ---
def load_config():
    with open('config_prod.json', 'r', encoding='utf-8') as f:
        return json.load(f)

CONF = load_config()
TOKEN = CONF.get('TELEGRAM_TOKEN')

if not TOKEN:
    print("❌ config_prod.json 파일에 TELEGRAM_TOKEN이 없습니다.")
    exit()

bot = telebot.TeleBot(TOKEN)

def init_db():
    conn = sqlite3.connect('users.db', check_same_thread=False)
    cursor = conn.cursor() 
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            chat_id INTEGER PRIMARY KEY,
            user_level INTEGER DEFAULT 0,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    return conn, cursor

conn, cursor = init_db()

# --- [2. 키보드 메뉴 (리모컨) 설정] ---
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton("🏆 오늘의 추천종목")
    btn2 = types.KeyboardButton("🔍 실시간 종목분석")
    btn3 = types.KeyboardButton("☕ 서버 운영 후원하기")
    markup.add(btn1, btn2) 
    markup.add(btn3)       
    return markup

# --- [3. 챗봇 명령어 및 버튼 응대 로직] ---

@bot.message_handler(commands=['start', 'help'])
def handle_start(message):
    chat_id = message.chat.id
    try:
        cursor.execute('INSERT OR IGNORE INTO users (chat_id) VALUES (?)', (chat_id,))
        conn.commit()
    except Exception as e:
        print(f"DB 저장 에러: {e}")

    welcome_caption = (
        "🚀 **국산 기술 KORStockScan v12.1에 오신 것을 환영합니다!**\n\n"
        "백테스트 기준 **승률 63.3%**의 압도적인 정밀도를 자랑합니다.\n\n"
        "📈 **핵심 전략: v12.1 스나이퍼 매매**\n"
        "• 장중 **+2.0% 익절 / -2.5% 손절** 원칙\n"
        "• AI 확신도 75% 이상 정예 종목 선별\n"
        "• 계좌 자산의 10% 비중 분산 투자 전략"
    )
    bot.send_message(chat_id, welcome_caption, parse_mode='Markdown', reply_markup=get_main_keyboard())

# 🚀 [신규 추가] 시스템 상태 확인 핸들러
@bot.message_handler(commands=['상태', 'status'])
def handle_status(message):
    chat_id = message.chat.id
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    msg = f"🟢 *[KORStockScan v12.1 상태 보고]*\n"
    msg += f"⏱ 현재시간: `{now_str}`\n\n"
    
    # 1. 엔진 가동 여부 체크 (전역 변수 engine_thread 활용)
    if engine_thread and engine_thread.is_alive():
        msg += "✅ **스나이퍼 엔진:** `정상 가동 중` 💓\n"
    else:
        msg += "❌ **스나이퍼 엔진:** `중단됨` ⚠️\n"
        
    # 2. DB 기준 현재 실시간 현황 요약
    try:
        db_path = CONF.get('DB_PATH', 'trading_history.db')
        temp_conn = sqlite3.connect(db_path)
        today = datetime.now().strftime('%Y-%m-%d')
        
        watch_cnt = temp_conn.execute("SELECT COUNT(*) FROM recommendation_history WHERE date=? AND status='WATCHING'", (today,)).fetchone()[0]
        hold_cnt = temp_conn.execute("SELECT COUNT(*) FROM recommendation_history WHERE date=? AND status='HOLDING'", (today,)).fetchone()[0]
        temp_conn.close()
        
        msg += f"👀 **감시 대상:** `{watch_cnt} 종목`\n"
        msg += f"💼 **보유 종목:** `{hold_cnt} 종목`"
    except Exception as e:
        msg += f"⚠️ 데이터 조회 오류: {e}"
        
    bot.send_message(chat_id, msg, parse_mode='Markdown')

@bot.message_handler(commands=['분석'])
def handle_analyze(message):
    badge = get_user_badge(message.chat.id)
    chat_id = message.chat.id
    parts = message.text.split()
    
    if len(parts) < 2:
        bot.send_message(chat_id, "⚠️ 종목코드를 함께 입력해주세요. (예: `/분석 005930`)", parse_mode='Markdown')
        return
        
    code = parts[1].strip()
    bot.send_message(chat_id, f"🔄 `{code}` 분석을 시작합니다...", parse_mode='Markdown')
    
    try:
        report = kiwoom_sniper_v2.analyze_stock_now(code)
        final_msg = f"{badge}님을 위한 분석 결과입니다!\n\n{report}"
        bot.send_message(message.chat.id, final_msg, parse_mode='Markdown')
    except Exception as e:
        bot.send_message(chat_id, f"❌ 오류 발생: {e}")

@bot.message_handler(commands=['오늘의추천', '추천'])
def handle_today_picks(message):
    chat_id = message.chat.id
    try:
        db_path = CONF.get('DB_PATH', 'trading_history.db')
        conn_temp = sqlite3.connect(db_path)
        today = datetime.now().strftime('%Y-%m-%d')
        picks = conn_temp.execute("SELECT name, buy_price, type FROM recommendation_history WHERE date=?", (today,)).fetchall()
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

# --- [4. 결제 및 등급 관리 로직] ---

@bot.pre_checkout_query_handler(func=lambda query: True)
def process_pre_checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def handle_payment_success(message):
    chat_id = message.chat.id
    temp_conn = sqlite3.connect('users.db')
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

# --- [5. 텍스트 메시지 및 기타 유틸] ---

@bot.message_handler(func=lambda message: True)
def handle_text_messages(message):
    chat_id = message.chat.id
    text = message.text
    
    if text == "🏆 오늘의 추천종목":
        handle_today_picks(message) 
    elif text == "🔍 실시간 종목분석":
        bot.send_message(chat_id, "분석할 **종목코드 6자리**를 입력해주세요.", parse_mode='Markdown')
        bot.register_next_step_handler(message, process_analyze_step)
    elif text == "☕ 서버 운영 후원하기":
        prices = [types.LabeledPrice(label="서버 후원", amount=50)]
        bot.send_invoice(chat_id, "✨ 서버 후원", "24시간 운영 지원", "donation_50", "", "XTR", prices)
    else:
        bot.send_message(chat_id, "아래 메뉴 버튼을 이용해 주세요.", reply_markup=get_main_keyboard())

def get_user_badge(chat_id):
    try:
        temp_conn = sqlite3.connect('users.db')
        row = temp_conn.execute("SELECT user_level FROM users WHERE chat_id = ?", (chat_id,)).fetchone()
        temp_conn.close()
        return "👑 [VIP 후원자] " if row and row[0] == 1 else "👤 [일반] "
    except: return ""

def process_analyze_step(message):
    chat_id = message.chat.id
    code = message.text.strip()
    
    if len(code) == 6 and code.isdigit():
        bot.send_message(chat_id, f"🔄 `{code}` 분석을 시작합니다...", parse_mode='Markdown')
        try:
            # 엔진의 분석 함수 호출
            report = kiwoom_sniper_v2.analyze_stock_now(code)
            bot.send_message(chat_id, report, parse_mode='Markdown')
        except Exception as e:
            # 🚀 [업데이트] 에러 내용을 사용자에게 직접 전달하여 원인 파악
            bot.send_message(chat_id, f"❌ 시스템 분석 오류 발생:\n`{str(e)}`", parse_mode='Markdown')
    else:
        bot.send_message(chat_id, "⚠️ 올바른 6자리 종목코드를 입력해 주세요.")

def broadcast_alert(message_text):
    temp_conn = sqlite3.connect('users.db')
    rows = temp_conn.execute('SELECT chat_id FROM users').fetchall()
    for row in rows:
        try:
            bot.send_message(row[0], message_text, parse_mode='Markdown')
            time.sleep(0.05)
        except: pass
    temp_conn.close()

def broadcast_today_picks():
    # ... (기존 자동 알림 로직 동일) ... scanner 실행시 1회 알림으로 대체
    pass

# --- [6. 메인 시스템 가동] ---

def start_engine():
    kiwoom_sniper_v2.run_sniper(broadcast_alert)

def monitor_exit_time():
    while True:
        if datetime.now().time() >= datetime.strptime("22:00:00", "%H:%M:%S").time():
            print("🌙 시스템 안전 종료")
            os.kill(os.getpid(), signal.SIGTERM)
        time.sleep(60)

if __name__ == '__main__':
    print("🤖 KORStockScan v12.1 통합 시스템 기동 중...")
    
    # 추천 종목 자동 알림 (선택 사항)
    # broadcast_today_picks()
    
    # 1. 스나이퍼 엔진 백그라운드 가동 (전역 변수에 할당)
    engine_thread = threading.Thread(target=start_engine)
    engine_thread.daemon = True 
    engine_thread.start()

    # 2. 자동 종료 감시 스레드 가동
    exit_thread = threading.Thread(target=monitor_exit_time)
    exit_thread.daemon = True
    exit_thread.start()
    
    print("📱 텔레그램 봇 폴링 시작...")
    bot.infinity_polling()