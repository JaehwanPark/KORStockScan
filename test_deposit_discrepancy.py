#!/usr/bin/env python3
"""
키움 API의 예수금(주문가능금액)과 HTS 화면의 값을 비교하는 테스트 스크립트.
실제 주문 가능 금액이 HTS와 얼마나 차이나는지 확인합니다.
"""
import sys
import os
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.utils import kiwoom_utils
from src.engine import kiwoom_orders
from src.utils.constants import CONFIG_PATH, DEV_PATH
import json

def load_config():
    target = CONFIG_PATH if CONFIG_PATH.exists() else DEV_PATH
    try:
        with open(target, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ 설정 로드 실패: {e}")
        return {}

def main():
    print("🔍 키움 예수금 조회 테스트 시작")
    print("=" * 60)
    
    # 1. 토큰 발급
    config = load_config()
    token = kiwoom_utils.get_kiwoom_token(config)
    if not token:
        print("❌ 토큰 발급 실패. config 파일 확인 필요.")
        return
    
    print(f"✅ 토큰 발급 성공 (길이: {len(token) if token else 0})")
    
    # 2. 예수금 조회 (주문가능금액)
    deposit = kiwoom_orders.get_deposit(token)
    print(f"📊 API 주문가능금액 (ord_alow_amt): {deposit:,} 원")
    
    # 3. calc_buy_qty 테스트
    # 예시 가격: 10,000원, 비율 10%
    test_price = 10000
    ratio = 0.1
    buy_qty = kiwoom_orders.calc_buy_qty(test_price, deposit, ratio)
    print(f"📈 계산된 매수 수량 (가격 {test_price:,}원, 비율 {ratio*100}%): {buy_qty:,} 주")
    
    # 4. 다른 비율로도 계산
    ratios = [0.05, 0.15, 0.2]
    for r in ratios:
        qty = kiwoom_orders.calc_buy_qty(test_price, deposit, r)
        print(f"   - 비율 {r*100:3.0f}% -> {qty:,} 주")
    
    print("=" * 60)
    print("💡 HTS 화면의 '주문가능금액'과 위의 'API 주문가능금액'을 비교해주세요.")
    print("   차이가 크다면 아래 사항을 확인하세요:")
    print("   1. API가 반환하는 ord_alow_amt 필드가 예수금이 아닐 수 있습니다.")
    print("   2. HTS는 미체결 주문 금액을 차감한 값을 보여줄 수 있습니다.")
    print("   3. API와 HTS의 조회 시점이 다를 수 있습니다.")
    print("   4. 계좌의 총자산(예수금+주식평가금액)과 예수금을 혼동할 수 있습니다.")
    print()
    print("🔧 HTS 값을 직접 비교하려면 아래와 같이 계산하세요:")
    print(f"   API 값: {deposit:,} 원")
    print(f"   HTS 값: (HTS에서 확인한 주문가능금액)")
    print(f"   차이: API - HTS = {deposit:,} - HTS")
    print()
    print("✅ 테스트 완료. 자금 부족 메시지가 나오면 위 차이를 확인하세요.")

if __name__ == "__main__":
    main()