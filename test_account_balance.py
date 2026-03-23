#!/usr/bin/env python3
"""
계좌 잔고 조회 테스트 스크립트
real_inventory = kiwoom_utils.get_account_balance_kt00005(KIWOOM_TOKEN, "ALL") 값을 출력합니다.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

import os
import json
from datetime import datetime
from src.utils import kiwoom_utils
from src.utils.logger import log_error

def load_system_config():
    from src.utils.constants import CONFIG_PATH, DEV_PATH
    target = CONFIG_PATH if CONFIG_PATH.exists() else DEV_PATH
    try:
        with open(target, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        log_error(f"설정 로드 실패: {e}")
        return {}

def main():
    print("🔍 계좌 잔고 조회 테스트 시작")
    CONF = load_system_config()
    if not CONF:
        print("❌ 설정 파일을 불러올 수 없습니다.")
        return
    
    token = kiwoom_utils.get_kiwoom_token(CONF)
    if not token:
        print("❌ KIWOOM_TOKEN 발급 실패")
        return
    
    print(f"✅ 토큰 획득 (길이: {len(str(token))})")
    print("📊 계좌 잔고 조회 중...")
    
    real_inventory = kiwoom_utils.get_account_balance_kt00005(token, "ALL")
    print(f"real_inventory 타입: {type(real_inventory)}")
    if real_inventory is None:
        print("⚠️ real_inventory is None (API 오류 또는 연결 실패)")
        return
    
    if isinstance(real_inventory, list):
        print(f"조회된 보유 종목 수: {len(real_inventory)}")
        for idx, item in enumerate(real_inventory):
            print(f"  [{idx}] 코드: {item.get('code')}, 종목명: {item.get('name')}, 수량: {item.get('qty')}, 매입가: {item.get('buy_price')}")
    else:
        print(f"예상치 못한 반환 형식: {real_inventory}")
    
    # 추가 디버그: raw 출력 (일부 제한)
    import pprint
    print("\n--- raw real_inventory (최대 5개) ---")
    pprint.pprint(real_inventory[:5] if isinstance(real_inventory, list) and len(real_inventory) > 5 else real_inventory)

if __name__ == "__main__":
    main()