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

# 전역 변수로 스레드 관리
sniper_thread = None

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
    # 1. DB 연결 (check_same_thread=False는 텔레그램 스레드 충돌 방지용)
    conn = sqlite3.connect('users.db', check_same_thread=False)
    cursor = conn.cursor() 
    
    # 2. 테이블 생성 (user_level 컬럼 포함)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            chat_id INTEGER PRIMARY KEY,
            user_level INTEGER DEFAULT 0,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    
    # 3. ⚠️ 반드시 두 개를 리턴해야 합니다!
    return conn, cursor

conn, cursor = init_db()

# --- [2. 키보드 메뉴 (리모컨) 설정] ---
def get_main_keyboard():
    """채팅창 하단에 고정될 버튼 메뉴를 생성합니다."""
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
    
    # [DB 등록 로직 동일]
    try:
        cursor.execute('INSERT OR IGNORE INTO users (chat_id) VALUES (?)', (chat_id,))
        conn.commit()
    except Exception as e:
        print(f"DB 저장 에러: {e}")

    image_path = 'Gemini_Generated_Image_wlfi3awlfi3awlfi.jpg'
    
    # 🚀 [v12.1 업데이트] 웰컴 문구 고도화 (승률 63.3% 및 분산투자 전략 반영)
    welcome_caption = (
        "🚀 **국산 기술 KORStockScan v12.1에 오신 것을 환영합니다!**\n\n"
        "본 시스템은 4개의 전문 AI 모델의 의견을 종합하는 **'스태킹 앙상블(Stacking Ensemble)'** "
        "기술을 도입하여, 백테스트 기준 **승률 63.3%**의 압도적인 정밀도를 자랑합니다.\n\n"
        "📈 **핵심 전략: v12.1 스나이퍼 매매**\n"
        "• 장중 **+2.0% 익절 / -2.5% 손절** 원칙으로 시장의 노이즈를 극복합니다.\n"
        "• AI가 엄선한(확신도 75% 이상) 종목만 골라내는 '철저한 타점 매매'를 지향합니다.\n"
        "• 계좌 자산의 10% 비중 분산 투자로 리스크(MDD)를 최소화합니다.\n\n"
        "🔍 **주요 기능**\n"
        "• `오늘의 추천`: 스태킹 엔진이 선별한 고확신 종목 리스트\n"
        "• `실시간 분석`: 종목코드 입력 시 즉시 AI 판독 결과 생성\n\n"
        "⚠️ **주의**: 본 서비스는 정보 제공용이며 투자 책임은 본인에게 있습니다."
    )

    try:
        with open(image_path, 'rb') as photo:
            bot.send_photo(
                chat_id, 
                photo, 
                caption=welcome_caption, 
                parse_mode='Markdown',
                reply_markup=get_main_keyboard()
            )
    except FileNotFoundError:
        bot.send_message(chat_id, welcome_caption, parse_mode='Markdown', reply_markup=get_main_keyboard())

@bot.message_handler(commands=['분석'])
def handle_analyze(message):
    badge = get_user_badge(message.chat.id)
    chat_id = message.chat.id
    parts = message.text.split()
    
    if len(parts) < 2:
        bot.send_message(chat_id, "⚠️ 종목코드를 함께 입력해주세요. (예: `/분석 005930`)", parse_mode='Markdown')
        return
        
    code = parts[1].strip()
    bot.send_message(chat_id, f"🔄 `{code}` 종목의 AI 스태킹 분석을 시작합니다...", parse_mode='Markdown')
    
    try:
        # 🚀 [오타 수정] rreport -> report 로 통일
        report = kiwoom_sniper_v2.analyze_stock_now(code)
        final_msg = f"{badge}님을 위한 분석 결과입니다!\n\n{report}"
        bot.send_message(message.chat.id, final_msg, parse_mode='Markdown')
    except Exception as e:
        bot.send_message(chat_id, f"❌ 분석 중 오류 발생: {e}")

@bot.message_handler(commands=['오늘의추천', '추천'])
def handle_today_picks(message):
    chat_id = message.chat.id
    try:
        db_path = CONF.get('DB_PATH', 'trading_history.db')
        conn_temp = sqlite3.connect(db_path)
        today = datetime.now().strftime('%Y-%m-%d')
        cursor_temp = conn_temp.execute("SELECT name, buy_price, type FROM recommendation_history WHERE date=?", (today,))
        picks = cursor_temp.fetchall()
        conn_temp.close()
        
        if not picks:
            bot.send_message(chat_id, "🧐 오늘은 AI 앙상블 엔진이 추천한 종목이 아직 없습니다.")
            return
            
        msg = "🏆 **[오늘의 AI 앙상블 추천 종목]**\n\n"
        # [수정] runner_picks를 전체 다 가져오더라도 출력은 10개로 제한
        main_picks = [p for p in picks if p[2] == 'MAIN']
        runner_picks = [p for p in picks if p[2] == 'RUNNER']
        
        if main_picks:
            msg += "🔥 **[강력 추천]**\n"
            for name, price, _ in main_picks:
                msg += f"• **{name}** (기준가: `{price:,}원`)\n"
            msg += "\n"
            
        if runner_picks:
            msg += "🥈 **[관심 종목 상위 10개]**\n"
            # 🚀 여기서 [:10]으로 슬라이싱을 해주어야 300개가 한꺼번에 출력되는 대참사를 막습니다.
            for name, price, _ in runner_picks[:10]: 
                msg += f"• **{name}** (기준가: `{price:,}원`)\n"
                
        bot.send_message(chat_id, msg, parse_mode='Markdown')
        
    except Exception as e:
        bot.send_message(chat_id, "❌ 추천 종목을 불러오는 데 실패했습니다.")

@bot.message_handler(commands=['상태', 'status'])
def handle_status(message):
    """현재 봇의 가동 상태를 보고합니다."""
    chat_id = message.chat.id
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    status_msg = f"🟢 *[KORStockScan v12.1 상태 보고]*\n"
    status_msg += f"⏱ 현재시간: `{now_str}`\n\n"
    
    # 1. 엔진 가동 여부
    if sniper_thread and sniper_thread.is_alive():
        status_msg += "✅ **스나이퍼 엔진:** `가동 중` 💓\n"
    else:
        status_msg += "❌ **스나이퍼 엔진:** `중단됨` ⚠️\n"
        
    # 2. 오늘 성과 요약 (DB 조회)
    try:
        conn = sqlite3.connect(CONF['DB_PATH'])
        today = datetime.now().strftime('%Y-%m-%d')
        # 감시/보유 현황 파악
        watch_cnt = conn.execute("SELECT COUNT(*) FROM recommendation_history WHERE date=? AND status='WATCHING'", (today,)).fetchone()[0]
        hold_cnt = conn.execute("SELECT COUNT(*) FROM recommendation_history WHERE date=? AND status='HOLDING'", (today,)).fetchone()[0]
        conn.close()
        
        status_msg += f"👀 **감시 대기:** `{watch_cnt}종목`\n"
        status_msg += f"💼 **현재 보유:** `{hold_cnt}종목`\n"
    except:
        status_msg += "⚠️ DB 조회 오류\n"
        
    bot.send_message(chat_id, status_msg, parse_mode='Markdown')

# --- [메인 실행 로직] ---
if __name__ == "__main__":
    # 스나이퍼 엔진을 별도 스레드로 실행
    sniper_thread = threading.Thread(target=kiwoom_sniper_v2.run_sniper, args=(None,), daemon=True)
    sniper_thread.start()
    
    print("🚀 KORStockScan v12.1 텔레그램 컨트롤러 가동 시작...")
    bot.infinity_polling()

@bot.message_handler(func=lambda message: True)
def handle_text_messages(message):
    chat_id = message.chat.id
    text = message.text
    
    if text == "🏆 오늘의 추천종목":
        handle_today_picks(message) 
        
    elif text == "🔍 실시간 종목분석":
        bot.send_message(chat_id, "분석할 종목의 **'종목코드 6자리'**를 입력해주세요.\n(예: `005930`)", parse_mode='Markdown')
        bot.register_next_step_handler(message, process_analyze_step)
        
    # handle_text_messages 함수 내의 후원하기 분기
    elif text == "☕ 서버 운영 후원하기":
        # 텔레그램 별(Stars) 결제 생성
        # amount는 별의 개수입니다. (예: 50개)
        prices = [types.LabeledPrice(label="서버 후원 (커피 한 잔)", amount=50)]
        
        bot.send_invoice(
            chat_id=chat_id,
            title="✨ KORStockScan 서버 후원",
            description="한국주식스캐너의 24시간 안정적인 운영을 위해 커피 한 잔을 후원해 주세요! 후원해주신 별은 서버 유지비로 소중히 사용됩니다.",
            invoice_payload="support_donation_50", # 나중에 결제 성공 시 확인할 ID
            provider_token="",                    # Stars 결제는 빈 값
            currency="XTR",                       # 🌟 핵심: 별 통화 코드
            prices=prices,
            start_parameter="donation-stars-50"   # 통계용 파라미터
        )
        
    else:
        bot.send_message(chat_id, "아래의 메뉴 버튼을 이용해 주세요. 👇", reply_markup=get_main_keyboard())

# 파일 하단에 추가

# 1. 사용자가 결제 버튼을 누른 직후 "최종 승인" 단계
@bot.pre_checkout_query_handler(func=lambda query: True)
def process_pre_checkout(pre_checkout_query):
    # 특별한 결격 사유가 없다면 ok=True를 보냅니다.
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

# 2. 결제가 실제로 완료되었을 때 실행
@bot.message_handler(content_types=['successful_payment'])
def handle_payment_success(message):
    chat_id = message.chat.id
    # DB 업데이트: 일반 사용자(0) -> 후원자(1)
    temp_conn = sqlite3.connect('users.db')
    temp_conn.execute("UPDATE users SET user_level = 1 WHERE chat_id = ?", (chat_id,))
    temp_conn.commit()
    temp_conn.close()

    bot.send_message(chat_id, "🎊 **축하합니다! VIP 등급으로 승격되었습니다.**\n이제 모든 알림에 👑 뱃지가 붙으며, 전용 혜택을 누리실 수 있습니다!")

# 👇 bot_main.py 파일의 명령어 핸들러 부분에 추가 👇

@bot.message_handler(commands=['reload'])
def handle_reload(message):
    # [수정] global 선언을 함수 최상단으로 옮겼습니다.
    global CONF 
    
    chat_id = message.chat.id
    admin_id = CONF.get('ADMIN_ID')
    
    # 1. 보안 체크: 명령어 입력자가 관리자인지 확인
    if str(chat_id) != str(admin_id):
        bot.send_message(chat_id, "⛔ 관리자만 사용할 수 있는 명령어입니다.")
        return

    bot.send_message(chat_id, "🔄 설정 파일을 다시 불러오는 중...", parse_mode='Markdown')

    try:
        # 2. bot_main.py의 전역 설정 새로고침
        CONF = load_config()
        
        # 3. kiwoom_sniper_v2 엔진의 설정 새로고침 함수 호출
        # (sniper 내부에서도 global CONF가 선언된 reload_config 함수가 있어야 합니다)
        if kiwoom_sniper_v2.reload_config():
            bot.send_message(chat_id, "✅ **[시스템]** `config_prod.json` 파일이 성공적으로 새로고침 되었습니다!", parse_mode='Markdown')
        else:
            bot.send_message(chat_id, "❌ **[시스템]** 엔진 설정 새로고침 실패. JSON 파일의 문법을 확인하세요.")
            
    except Exception as e:
        bot.send_message(chat_id, f"❌ 메인 시스템 새로고침 중 오류 발생: {e}")

def get_user_badge(chat_id):
    """사용자의 등급을 확인하여 뱃지 문자열을 반환합니다."""
    try:
        temp_conn = sqlite3.connect('users.db')
        cursor = temp_conn.execute("SELECT user_level FROM users WHERE chat_id = ?", (chat_id,))
        row = cursor.fetchone()
        temp_conn.close()
        
        if row and row[0] == 1:
            return "👑 [VIP 후원자] "
        return "👤 [일반] "
    except:
        return ""

def process_analyze_step(message):
    chat_id = message.chat.id
    code = message.text.strip()
    
    if len(code) == 6 and code.isdigit():
        bot.send_message(chat_id, f"🔄 `{code}` 분석을 시작합니다...", parse_mode='Markdown')
        try:
            report = kiwoom_sniper_v2.analyze_stock_now(code)
            bot.send_message(chat_id, report, parse_mode='Markdown')
        except Exception as e:
            bot.send_message(chat_id, "❌ 분석 중 오류가 발생했습니다.")
    else:
        bot.send_message(chat_id, "⚠️ 올바른 6자리 종목코드를 입력해 주세요. (예: 005930)")

# --- [4. 전체 브로드캐스트 로직] ---
def broadcast_alert(message_text):
    """kiwoom_sniper_v2 엔진이 신호를 포착하면 호출되는 알림 전송 함수"""
    temp_conn = sqlite3.connect('users.db')
    temp_cursor = temp_conn.cursor()
    temp_cursor.execute('SELECT chat_id FROM users')
    rows = temp_cursor.fetchall()
    
    success_count = 0
    for row in rows:
        target_id = row[0]
        try:
            bot.send_message(target_id, message_text, parse_mode='Markdown')
            success_count += 1
            time.sleep(0.05) 
        except Exception as e:
            print(f"⚠️ {target_id} 전송 실패 (차단 의심) - {e}")
            
    temp_conn.close()
    if success_count > 0:
        print(f"📢 총 {success_count}명에게 알림 전송 완료!")

def broadcast_today_picks():
    """봇 시작 시, 오늘 날짜의 추천 종목을 전체 가입자에게 전송"""
    try:
        db_path = CONF.get('DB_PATH', 'trading_history.db')
        conn = sqlite3.connect(db_path)
        today = datetime.now().strftime('%Y-%m-%d')
        
        cursor = conn.execute("SELECT name, buy_price, type FROM recommendation_history WHERE date=?", (today,))
        picks = cursor.fetchall()
        conn.close()
        
        if not picks: 
            print("🧐 오늘 추천 종목이 없어 자동 브로드캐스트를 생략합니다.")
            return
        
        msg = f"🌅 **[{today}] AI 스태킹 앙상블 추천 리포트 (v12.1)**\n\n"
        msg += "🎯 **전략: 당일 장중 +2.0% 익절 (손절 방어선 -2.5%)**\n"
        msg += "------------------------------------------\n"
        
        main_picks = [p for p in picks if p[2] == 'MAIN']
        runner_picks = [p for p in picks if p[2] == 'RUNNER']
        
        if main_picks:
            msg += "🔥 **[고확신 종목]**\n"
            for name, price, _ in main_picks:
                msg += f"• **{name}** (기준가: `{price:,}원`)\n"
            msg += "\n"
            
        if runner_picks:
            # 🚀 [수정] DB에 300개가 있어도 메시지 가독성을 위해 상위 10개만 출력
            msg += "🥈 **[관심 종목 상위 10개]**\n"
            for name, price, _ in runner_picks[:10]: 
                msg += f"• **{name}** (기준가: `{price:,}원`)\n"
            
            # 💡 사용자에게 봇이 열심히 일하고 있음을 알리는 멘트 추가
            if len(runner_picks) > 10:
                msg += f"\n*(그 외 {len(runner_picks)-10}개의 종목을 AI가 실시간 추적 중입니다)*"
                
        broadcast_alert(msg)
        print("📢 오늘의 추천 종목 자동 브로드캐스트 완료!")
        
    except Exception as e:
        print(f"자동 브로드캐스트 에러: {e}")

# --- [5. 시스템 구동 스레드 설정] ---
def start_engine():
    kiwoom_sniper_v2.run_sniper(broadcast_alert)

def monitor_exit_time():
    """매일 밤 22:00분에 프로세스를 안전하게 종료"""
    while True:
        now = datetime.now().time()
        # 장 마감 후 데이터 정리까지 끝날 넉넉한 시간(22:00)에 종료
        if now >= datetime.strptime("22:00:00", "%H:%M:%S").time():
            print("🌙 시스템을 안전하게 종료하고 퇴근합니다.")
            # 전체 프로세스 종료 (자폭)
            os.kill(os.getpid(), signal.SIGTERM)
        time.sleep(60) # 1분마다 체크

if __name__ == '__main__':
    print("========================================")
    print("🤖 텔레그램 주식 스캐너 봇 메인 시스템 가동")
    print("========================================")
    
    # 봇 가동 시 모닝 브로드캐스트 실행!
    broadcast_today_picks()
    
    # 스캐닝 엔진 백그라운드 실행
    engine_thread = threading.Thread(target=start_engine)
    engine_thread.daemon = True 
    engine_thread.start()

    # 2. [신규] 자동 종료 감시 스레드 실행
    exit_thread = threading.Thread(target=monitor_exit_time)
    exit_thread.daemon = True
    exit_thread.start()
    
    print("📱 텔레그램 봇이 사용자의 메시지를 기다리고 있습니다...")
    bot.polling(none_stop=True)