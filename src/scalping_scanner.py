import os
import time
import json
import requests
from datetime import datetime

import kiwoom_utils
from signal_radar import SniperRadar  # 🚀 신규 추가: 정보국 레이더
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
# 2. 실시간 급등주 포착 API (Signal_radar 로 교체함)
# ==========================================
#def get_realtime_soaring_stocks(token):
#    """
#    kiwoom_utils의 ka10027 API를 호출하여
#    수급이 몰리는 급등 종목을 스캘핑 조건으로 필터링합니다.
#    """
#    soaring_list = []
#
#    # 🚀 1. 유틸리티 함수 호출 (전체 시장 000, 10만주 이상 0100, 넉넉하게 50개 가져오기)
#    raw_items = kiwoom_utils.get_top_fluctuation_ka10027(token, mrkt_tp="000", trde_qty_cnd="0100", limit=50)
#
#    # 🚀 2. 스캘핑 전략 전용 정밀 필터링
#    for item in raw_items:
#        price = item['Price']
#        volume = item['Volume']
#        change_rate = item['ChangeRate']
#        cntr_str = item['CntrStr']
#
#        # 거래대금 계산 (억원 단위)
#        transaction_amount = (price * volume) / 100_000_000
#
#        # [초단타 정밀 필터링 - 유동성 강화 버전]
#        if (3.0 <= change_rate <= 15.0) and \
#                (cntr_str >= 120.0) and \
#                (transaction_amount >= 70.0) and \
#                (volume >= 300000) and \
#                (price >= 1500):
#
#            # 💡 [핵심 방어] ETF, ETN, 우선주, 스팩 등 파생/불순물 종목 완벽 차단!
#            if kiwoom_utils.is_valid_stock(item['Code'], item['Name']):
#                soaring_list.append(item)
#
#    return soaring_list

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
            
        # 🚀 1. 레이더 가동! (토큰 장착)
        radar = SniperRadar(token)

        print(f"🔍 [{now.strftime('%H:%M:%S')}] 실시간 수급 쏠림 & 폭발 전조 종목 스캔 중...")
        
        # 🚀 2. 트랙 A: 기존의 '이미 급등을 시작한' 대장주 포착 (ka10027)
        # (기존 유틸에서 이사 온 함수 사용)
        soaring_targets = radar.get_top_fluctuation_ka10027(mrkt_tp="101", limit=30)
        
        # 🚀 3. 트랙 B: [핵심] 오르기 직전, 거래량/수급 폭발 전조 포착 (7개 API 콤보)
        supernova_targets = radar.find_supernova_targets()

        # 🚀 4. 두 타겟 리스트를 하나로 합치기 (중복 제거)
        all_targets = {}
        for t in soaring_targets:
            all_targets[t['Code']] = t
            
        for t in supernova_targets:
            # 트랙 B에서 잡힌 종목은 'ChangeRate'나 'CntrStr' 키가 다를 수 있으므로 맞춰줍니다.
            if t['code'] not in all_targets:
                all_targets[t['code']] = {
                    'Code': t['code'],
                    'Name': t['name'],
                    'ChangeRate': t.get('spike_rate', 0), # 급증률을 일단 등락률 칸에 표기
                    'CntrStr': 150.0  # 초신성은 수급이 폭발 중이므로 임의의 높은 강도 부여
                }

        # 🚀 5. DB 저장 및 스나이퍼 대기열 전송 로직
        for code, t in all_targets.items():
            if code not in already_picked:
                print(f"🎯 [타겟 포착] {t['Name']} (등락/급증률: +{t['ChangeRate']}%, 체결강도: {t['CntrStr']})")
                already_picked.add(code)

                # DB 저장 (스나이퍼가 웹소켓으로 가져가기 위함)
                try:
                    with db._get_connection() as conn:
                        conn.execute('''
                                     INSERT INTO recommendation_history (date, code, name, buy_price, type, strategy)
                                     VALUES (?, ?, ?, ?, ?, ?)
                                     ''', (today, code, t['Name'], 0, 'SCALP', 'SCALPING'))
                        conn.commit()
                except Exception as e:
                    print(f"⚠️ DB 저장 실패: {e}")

                broadcast_scalping_target(conf, t)

        time.sleep(60)


if __name__ == "__main__":
    run_scalper()