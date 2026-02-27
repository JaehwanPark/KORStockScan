import sqlite3
import pandas as pd
from datetime import datetime
import json
import os

# --- [1. 임시 설정 로드] ---
# 실제 환경의 config 파일을 읽어옵니다. (파일명이 다르다면 맞춰서 수정해주세요)
config_path = 'config_prod.json'
if not os.path.exists(config_path):
    config_path = 'config.json' # config_prod가 없으면 기본 config 시도

try:
    with open(config_path, 'r', encoding='utf-8') as f:
        CONF = json.load(f)
except Exception as e:
    print(f"⚠️ 설정 파일 로드 실패. 기본 DB 경로를 임의로 지정합니다: {e}")
    CONF = {'DB_PATH': 'trading_history.db'} # 기본 DB 파일명

# --- [2. 테스트할 함수 (대표님이 작성하신 코드)] ---
def get_active_targets():
    """
    [v12.1 오버나잇 버전] 감시 대상 종목 조회 
    - 판다스를 이용한 중복 제거 및 안전한 DB 로드
    """
    targets = []
    try:
        conn = sqlite3.connect(CONF['DB_PATH'])
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 🚀 1. buy_time 컬럼이 없어서 뻗는 현상을 막기 위해 안전하게 SELECT * 사용
        query = "SELECT * FROM recommendation_history WHERE date=? OR status='HOLDING'"
        df = pd.read_sql(query, conn, params=(today,))
        conn.close()

        if df.empty:
            return targets

        # 🚀 2. [핵심] 중복 종목 완벽 제거 (Pandas 마법)
        df = df.sort_values(by='status').drop_duplicates(subset=['code'], keep='first')

        targets = df.to_dict('records')
        
        # 🚀 3. 엔진에서 에러가 나지 않도록 필수 키값 보장
        for t in targets:
            t['prob'] = t.get('prob', 0.75)       # DB에 없으면 기본 확신도 75%
            t['buy_qty'] = t.get('buy_qty', 0)    # DB에 없으면 수량 0
            
        return targets

    except Exception as e:
        # 🚀 4. 에러 발생 시 무시하지 않고 터미널에 원인을 출력하여 디버깅을 돕습니다.
        print(f"🔥 [DB 로드 에러] 감시 대상을 불러오는 중 문제가 발생했습니다: {e}")
        return targets

# --- [3. 실행 및 결과 검증 파트] ---
if __name__ == "__main__":
    db_path = CONF.get('DB_PATH', '경로 없음')
    print(f"🔍 [테스트 시작] DB 연동 및 타겟 로드 테스트 (DB: {db_path})")
    print("-" * 50)
    
    # 함수 실행
    results = get_active_targets()
    
    if not results:
        print("⚠️ 불러온 감시 대상 종목이 없습니다 (빈 리스트 반환).")
        print("   -> 오늘 추천된 종목이 없거나, HOLDING 중인 종목이 없는 상태입니다.")
    else:
        print(f"✅ 총 {len(results)}개의 종목을 성공적으로 불러왔습니다!\n")
        
        # 결과 예쁘게 출력
        for idx, t in enumerate(results, 1):
            name = t.get('name', '이름없음')
            code = t.get('code', '코드없음')
            status = t.get('status', '상태없음')
            # pos_tag = t.get('position_tag', '태그없음(MIDDLE)')
            buy_price = t.get('buy_price', 0)
            buy_qty = t.get('buy_qty', 0)
            
            print(f"[{idx}] {name} ({code})")
            print(f"    ┣ 📡 상태 : {status}")
            # print(f"    ┣ 🏷️ 위치 : {pos_tag}")
            
            # None이나 빈 문자열 방어 처리 후 출력
            bp_str = f"{int(buy_price):,}원" if pd.notnull(buy_price) and buy_price else "0원"
            print(f"    ┗ 💰 매수 : {bp_str} | 수량: {buy_qty}주\n")

    print("-" * 50)
    print("🏁 [테스트 종료]")