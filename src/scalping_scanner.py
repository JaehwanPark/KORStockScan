import os
import time
import json
import requests
from datetime import datetime

import kiwoom_utils
from db_manager import DBManager

# ==========================================
# 1. 경로 및 환경 설정
# ==========================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..', 'data'))
CONFIG_PATH = os.path.join(DATA_DIR, 'config_prod.json')


def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


# ==========================================
# 2. 실시간 급등주 포착 API (ka10027 적용)
# ==========================================
def get_realtime_soaring_stocks(token):
    """
    kiwoom_utils의 ka10027 API를 호출하여
    수급이 몰리는 급등 종목을 스캘핑 조건으로 필터링합니다.
    """
    soaring_list = []

    # 🚀 1. 유틸리티 함수 호출 (전체 시장 000, 10만주 이상 0100, 넉넉하게 50개 가져오기)
    raw_items = kiwoom_utils.get_top_fluctuation_ka10027(token, mrkt_tp="000", trde_qty_cnd="0100", limit=50)

    # 🚀 2. 스캘핑 전략 전용 정밀 필터링
    for item in raw_items:
        price = item['Price']
        volume = item['Volume']
        change_rate = item['ChangeRate']
        cntr_str = item['CntrStr']

        # 거래대금 계산 (억원 단위)
        transaction_amount = (price * volume) / 100_000_000

        # [초단타 정밀 필터링 - 유동성 강화 버전]
        if (3.0 <= change_rate <= 15.0) and \
                (cntr_str >= 120.0) and \
                (transaction_amount >= 70.0) and \
                (volume >= 300000) and \
                (price >= 1500):
            # 조건을 통과한 종목만 리스트에 추가 (이미 딕셔너리 형태이므로 그대로 추가)
            soaring_list.append(item)

    return soaring_list

# ==========================================
# 3. 텔레그램 브로드캐스트
# ==========================================
def broadcast_scalping_target(conf, target):
    token = conf.get('TELEGRAM_TOKEN')
    db = DBManager()
    chat_ids = db.get_telegram_chat_ids()

    msg = f"⚡ <b>[초단타(SCALP) 레이더 포착]</b>\n"
    msg += f"• <b>{target['Name']}</b> ({target['Code']})\n"
    msg += f"• 현재가: <code>{target['Price']:,}원</code> (<b>+{target['ChangeRate']}%</b>)\n"
    msg += f"• 체결강도: <b>{target['CntrStr']}%</b> (수급 폭발🔥)\n"
    msg += "🎯 <b>전략: +2.0% 익절 / -2.5% 칼손절</b>"

    for cid in chat_ids:
        try:
            requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                data={"chat_id": cid, "text": msg, "parse_mode": "HTML"},
                timeout=5
            )
        except:
            pass


# ==========================================
# 4. 메인 감시 루프
# ==========================================
def run_scalper():
    print("⚡ [SCALPING 스캐너] 초단타 감시 엔진 가동 (1분 주기)...")
    conf = load_config()
    db = DBManager()
    today = datetime.now().strftime('%Y-%m-%d')

    # 당일 이미 추천한 종목 중복 방지 세트
    already_picked = set()

    while True:
        now = datetime.now()
        now_time = now.time()

        # 장중(09:00 ~ 15:20)에만 동작
        if not (datetime.strptime("09:00:00", "%H:%M:%S").time() <= now_time <= datetime.strptime("15:20:00",
                                                                                                  "%H:%M:%S").time()):
            print("🌙 장 마감 혹은 개장 전입니다. 대기 중...")
            time.sleep(60)
            continue

        token = kiwoom_utils.get_kiwoom_token(conf)
        if not token:
            time.sleep(10)
            continue

        print(f"🔍 [{now.strftime('%H:%M:%S')}] 실시간 수급 쏠림 종목 스캔 중...")
        targets = get_realtime_soaring_stocks(token)

        for t in targets:
            if t['Code'] not in already_picked:
                print(f"🎯 [타겟 포착] {t['Name']} (+{t['ChangeRate']}%, 체결강도: {t['CntrStr']})")
                already_picked.add(t['Code'])

                # DB 저장 (스나이퍼가 웹소켓으로 가져가기 위함)
                try:
                    with db._get_connection() as conn:
                        conn.execute('''
                                     INSERT INTO recommendation_history (date, code, name, buy_price, type, strategy)
                                     VALUES (?, ?, ?, ?, ?, ?)
                                     ''', (today, t['Code'], t['Name'], t['Price'], 'SCALP', 'SCALPING'))
                except Exception as e:
                    print(f"DB 저장 에러: {e}")

                broadcast_scalping_target(conf, t)

        time.sleep(60)


if __name__ == "__main__":
    run_scalper()