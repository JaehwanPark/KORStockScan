# ==========================================
# # 🚀 코스닥 하이브리드 AI 스캐너
# ==========================================

import os
import time
import json
import threading
from datetime import datetime

import pandas as pd
import numpy as np
import requests

import kiwoom_utils
from db_manager import DBManager
import final_ensemble_scanner  # 💡 기존 KOSPI의 AI 예측 로직과 모델을 재활용하기 위해 임포트

# ==========================================
# 1. 경로 및 환경 설정
# ==========================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..', 'data'))
CONFIG_PATH = os.path.join(DATA_DIR, 'config_prod.json')


def load_config():
    # 암호화된 설정 파일(config_prod.enc)을 사용하는 로직이 있다면 그에 맞게 수정해주세요.
    # 여기서는 범용적인 JSON 로드 방식을 사용합니다.
    try:
        from cryptography.fernet import Fernet
        enc_path = os.path.join(DATA_DIR, 'config_prod.enc')
        master_key = os.environ.get('KORSTOCK_KEY')
        if master_key and os.path.exists(enc_path):
            cipher_suite = Fernet(master_key.encode('utf-8'))
            with open(enc_path, 'rb') as f:
                decrypted_data = cipher_suite.decrypt(f.read())
            return json.loads(decrypted_data.decode('utf-8'))
    except:
        pass

    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


# ==========================================
# 2. 텔레그램 브로드캐스트 (코스닥 전용)
# ==========================================
def broadcast_kosdaq_picks(conf, picks):
    if not picks: return

    token = conf.get('TELEGRAM_TOKEN')
    db = DBManager()
    chat_ids = db.get_telegram_chat_ids()
    today = datetime.now().strftime('%Y-%m-%d')

    msg = f"🚀 <b>[KOSDAQ AI 스태킹 리포트]</b> {today}\n"
    msg += f"당일 수급 폭발 코스닥 종목 중 AI가 엄선한 타겟입니다.\n\n"

    for r in picks:
        msg += f"🥇 <b>{r['Name']}</b> ({r['Code']})\n"
        msg += f"   • 현재가: {r['Price']:,}원\n"
        msg += f"   • AI 확신지수: <b>{r['Prob']:.1%}</b>\n"
        msg += f"   • 체결강도: {r['CntrStr']}%\n"
        msg += f"   • 전략 태그: <code>KOSDAQ_ML</code>\n\n"

    for cid in chat_ids:
        try:
            requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                data={"chat_id": cid, "text": msg, "parse_mode": "HTML"},
                timeout=5
            )
        except Exception as e:
            print(f"텔레그램 전송 에러: {e}")


# ==========================================
# 3. 메인 스캐너 엔진 (하이브리드 온디맨드 방식)
# ==========================================
def run_kosdaq_scanner():
    print("🚀 [KOSDAQ 스캐너] 코스닥 하이브리드 AI 감시 가동...")
    conf = load_config()
    db = DBManager()
    today = datetime.now().strftime('%Y-%m-%d')

    # AI 모델 로드 (기존 final_ensemble_scanner 의 모델 재활용)
    models = final_ensemble_scanner.load_models()
    if not models:
        print("❌ AI 모델을 불러오지 못했습니다. 스캐너를 종료합니다.")
        return

    while True:
        now = datetime.now()
        now_time = now.time()

        # 장중(09:05 ~ 15:20)에만 동작 (장 초반 5분은 데이터 안정화를 위해 대기)
        if not (datetime.strptime("09:05:00", "%H:%M:%S").time() <= now_time <= datetime.strptime("15:20:00",
                                                                                                  "%H:%M:%S").time()):
            print("🌙 [KOSDAQ] 장 마감 혹은 개장 전입니다. 대기 중...")
            time.sleep(60)
            continue

        token = kiwoom_utils.get_kiwoom_token(conf)
        if not token:
            time.sleep(10)
            continue

        print(f"\n🔍 [{now.strftime('%H:%M:%S')}] KOSDAQ 수급 주도주 1차 필터링 중...")

        # 🚀 1단계: 코스닥(101) 거래대금/상승률 상위 종목 추출 (기존 유틸리티 활용)
        raw_targets = kiwoom_utils.get_top_fluctuation_ka10027(token, mrkt_tp="101", trde_qty_cnd="0100", limit=50)

        kosdaq_picks = []

        # 🚀 2단계: 하드 필터링 및 실시간 일봉 차트(ka10081) 수집
        for item in raw_targets:
            code = item['Code']
            name = item['Name']
            price = item['Price']
            volume = item['Volume']
            cntr_str = item['CntrStr']

            transaction_amount = (price * volume) / 100_000_000

            # [안전장치] 동전주(1500원 미만), 거래대금 30억 미만, 체결강도 100 미만 컷트
            if price < 1500 or transaction_amount < 30.0 or cntr_str < 100.0:
                continue

            print(f"   📥 [{name}] 실시간 일봉 데이터(ka10081) 수집 및 AI 분석 중...")

            # 🚀 3단계: 준비된 유틸리티로 해당 종목의 일봉 DF 실시간 생성
            df = kiwoom_utils.get_daily_ohlcv_ka10081_df(token, code)
            time.sleep(0.3)  # API 초당 호출 제한 방어 (매우 중요)

            if df is None or len(df) < 60:
                continue  # 상장한지 얼마 안 된 신규 상장주 등은 AI 분석 불가로 패스

            # 🚀 4단계: 기존 AI 앙상블 로직에 실시간 DF를 통과시켜 확신지수(Prob) 추출
            try:
                # final_ensemble_scanner 내부의 피처 엔지니어링 및 예측 함수 재활용
                prob = final_ensemble_scanner.predict_prob_for_df(df, models)

                # 코스닥은 리스크가 크므로 확신도 80% 이상일 때만 타겟팅
                if prob >= 0.80:
                    print(f"   🎯 [KOSDAQ AI 포착!] {name} (확신도: {prob:.1%})")
                    kosdaq_picks.append({
                        'Code': code, 'Name': name, 'Price': price,
                        'Prob': prob, 'CntrStr': cntr_str, 'Position': 'MIDDLE'
                    })
            except Exception as e:
                print(f"⚠️ {name} AI 분석 중 에러: {e}")
                continue

        # 🚀 5단계: DB 저장 및 스나이퍼 엔진 호출
        if kosdaq_picks:
            for r in kosdaq_picks:
                try:
                    with db._get_connection() as conn:
                        # 이미 오늘 추천된 종목인지 확인 (중복 알림 방지)
                        cur = conn.execute("SELECT COUNT(*) FROM recommendation_history WHERE date=? AND code=?",
                                           (today, r['Code']))
                        if cur.fetchone()[0] == 0:
                            # 💡 핵심: strategy='KOSDAQ_ML' 태그를 달아 스나이퍼가 인식하게 함
                            conn.execute('''
                                         INSERT INTO recommendation_history (date, code, name, buy_price, type, position_tag, prob, strategy)
                                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                         ''',
                                         (today, r['Code'], r['Name'], r['Price'], 'MAIN', r['Position'], r['Prob'],
                                          'KOSDAQ_ML'))

                            broadcast_kosdaq_picks(conf, [r])  # 새 종목만 텔레그램 발송
                except Exception as e:
                    print(f"DB 저장 에러: {e}")

        # 코스닥 스캐너는 15분마다 한 번씩 묵직하게 돕니다.
        time.sleep(900)


if __name__ == "__main__":
    run_kosdaq_scanner()