import sqlite3
import json
import os
import sys
from datetime import datetime

# 1. 설정 로드
config_path = 'config_prod.json'
if not os.path.exists(config_path):
    config_path = 'config.json'

try:
    with open(config_path, 'r', encoding='utf-8') as f:
        CONF = json.load(f)
except Exception as e:
    print(f"⚠️ 설정 파일 로드 실패: {e}")
    sys.exit(1)

def register_manual_stock(code, name):
    db_path = CONF.get('DB_PATH', 'trading_history.db')
    today = datetime.now().strftime('%Y-%m-%d')
    
    try:
        conn = sqlite3.connect(db_path)
        
        # 🚀 [핵심] type을 'MANUAL'로, status를 'WATCHING'으로 강제 주입
        sql = """
            INSERT INTO recommendation_history (date, code, name, buy_price, type, status, nxt, position_tag)
            VALUES (?, ?, ?, 0, 'MANUAL', 'WATCHING', NULL, 'MIDDLE')
            ON CONFLICT(date, code) DO UPDATE SET
                status = 'WATCHING',
                type = 'MANUAL'
        """
        conn.execute(sql, (today, str(code).zfill(6), name))
        conn.commit()
        conn.close()
        
        print(f"🎯 [명령 하달 완료] {name}({code}) 종목이 스나이퍼 타겟으로 등록되었습니다.")
        print("💡 (스나이퍼 봇을 재시작하면 즉시 감시가 시작됩니다.)")
        
    except Exception as e:
        print(f"🔥 DB 등록 중 에러 발생: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("🔫 스나이퍼 수동 타겟 등록기")
    print("=" * 50)
    
    input_code = input("👉 종목코드를 입력하세요 (예: 005930): ").strip()
    input_name = input("👉 종목명을 입력하세요 (예: 삼성전자): ").strip()
    
    if input_code and input_name:
        register_manual_stock(input_code, input_name)
    else:
        print("❌ 코드와 이름을 모두 입력하셔야 합니다.")   