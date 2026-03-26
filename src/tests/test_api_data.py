import sys
from pathlib import Path
import pandas as pd

# 🚀 프로젝트 루트 경로를 탐지하여 sys.path에 추가
# .parent를 세 번 써서 완벽하게 KORStockScan2 루트로 도달!
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT)) # append 대신 insert(0, ...)를 쓰면 우선순위가 가장 높아져 더 안전합니다.

from src.utils import kiwoom_utils

def test_investor_and_margin_api():
    print("=====================================================")
    print("🔍 [TEST] 투자자 수급(ka10059) 및 신용잔고(ka10013) 점검")
    print("=====================================================\n")
    
    # 1. 키움 토큰 발급
    print("🔑 키움 API 토큰 발급 중...")
    token = kiwoom_utils.get_kiwoom_token()
    if not token:
        print("❌ 토큰 발급 실패. 설정 파일이나 환경 변수를 확인하세요.")
        return
    print("✅ 토큰 발급 성공!\n")

    # 2. 테스트 종목 설정 (삼성전자)
    test_code = "005930_AL"
    print(f"🎯 테스트 대상 종목: 삼성전자 ({test_code})")

    # ==========================================
    # 📊 1. 투자자별 수급 데이터 (ka10059)
    # ==========================================
    print("\n[1] 📈 투자자별 일별 수급 데이터 (ka10059) 요청 중...")
    try:
        df_investor = kiwoom_utils.get_investor_daily_ka10059_df(token, test_code)
        
        if df_investor.empty:
            print("⚠️ [결과] DataFrame이 비어 있습니다. (Empty)")
        else:
            print(f"✅ [결과] 총 {len(df_investor)}일치 데이터 수신 성공!")
            # 컬럼 타입 및 결측치 확인용 info 출력
            print("\n[데이터 구조 확인]")
            print(df_investor.dtypes)
            print("\n[최근 5일치 데이터 미리보기]")
            print(df_investor.tail(5)) # 정렬이 (과거->최신)이므로 tail이 최근 데이터
            
    except Exception as e:
        print(f"🚨 수급 데이터 호출 중 에러 발생: {e}")

    # ==========================================
    # 📊 2. 신용 잔고율 데이터 (ka10013)
    # ==========================================
    print("\n-----------------------------------------------------")
    print("\n[2] 💳 신용 잔고율 데이터 (ka10013) 요청 중...")
    try:
        df_margin = kiwoom_utils.get_margin_daily_ka10013_df(token, test_code)
        
        if df_margin.empty:
            print("⚠️ [결과] DataFrame이 비어 있습니다. (Empty)")
        else:
            print(f"✅ [결과] 총 {len(df_margin)}일치 데이터 수신 성공!")
            print("\n[데이터 구조 확인]")
            print(df_margin.dtypes)
            print("\n[최근 5일치 데이터 미리보기]")
            print(df_margin.tail(5))
            
    except Exception as e:
        print(f"🚨 신용 데이터 호출 중 에러 발생: {e}")

def test_program_buying_ka90008():
    print("=====================================================")
    print("🔍 [TEST] 프로그램 수급 (ka90008) 점검")
    print("=====================================================\n")
    
    # 1. 키움 토큰 발급
    print("🔑 키움 API 토큰 발급 중...")
    token = kiwoom_utils.get_kiwoom_token()
    if not token:
        print("❌ 토큰 발급 실패. 설정 파일이나 환경 변수를 확인하세요.")
        return
    print("✅ 토큰 발급 성공!\n")
    
    # 2. 테스트 종목 설정 (삼성전자)
    test_code = "005930"
    print(f"🎯 테스트 대상 종목: 삼성전자 ({test_code})")
    
    print("\n[1] 📊 프로그램 수급 데이터 (ka90008) 요청 중...")
    try:
        program_data = kiwoom_utils.check_program_buying_ka90008(token, test_code)
        
        # 결과 출력
        print(f"✅ 프로그램 수급 데이터 수신 성공!")
        print("\n[데이터 구조 확인]")
        for key, value in program_data.items():
            print(f"  {key}: {value}")
        
        # 기본 검증
        expected_keys = ['is_buying', 'net_amt', 'net_qty', 'buy_amt', 'sell_amt', 'buy_qty', 'sell_qty', 'net_irds_amt']
        missing_keys = [k for k in expected_keys if k not in program_data]
        if missing_keys:
            print(f"⚠️  필드 누락: {missing_keys}")
        else:
            print("✅ 모든 필드 존재함.")
        
        # 데이터가 있을 경우 간단한 판정 출력
        if program_data['net_amt'] != 0 or program_data['net_qty'] != 0:
            print(f"\n💡 프로그램 순매수 금액: {program_data['net_amt']:,} 원")
            print(f"💡 프로그램 순매수 수량: {program_data['net_qty']:,} 주")
            if program_data['is_buying']:
                print("🟢 프로그램 순매수 상태 (is_buying=True)")
            else:
                print("🔴 프로그램 순매수 아님 (is_buying=False)")
        else:
            print("\n📭 프로그램 수급 데이터가 없거나 0입니다.")
            
    except Exception as e:
        print(f"🚨 프로그램 수급 데이터 호출 중 에러 발생: {e}")

if __name__ == "__main__":
    # Pandas 출력 옵션 설정 (잘림 방지)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    
    test_investor_and_margin_api()
    print("\n" + "="*60)
    test_program_buying_ka90008()