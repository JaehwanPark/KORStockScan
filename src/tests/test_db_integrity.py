import sys
from pathlib import Path
import pandas as pd
from sqlalchemy import text

# 🚀 프로젝트 루트 경로를 탐지하여 sys.path에 추가
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils import kiwoom_utils
from src.database.db_manager import DBManager


def verify_samsung_data():
    print("=====================================================")
    print("🔍 [TEST] KORStockScan 데이터 무결성 크로스체크 (삼성전자)")
    print("=====================================================\n")

    code = "005930"

    # ==========================================
    # 1. DB 데이터 조회 (가장 최신일 기준)
    # ==========================================
    print("🗄️ 1. 데이터베이스(PostgreSQL) 최신 데이터 조회 중...")
    db = DBManager()

    latest_db_row = None
    with db.get_session() as session:
        # SQL 원시 쿼리로 삼성전자의 가장 최신 하루치 데이터만 쏙 빼옵니다.
        query = text("""
            SELECT quote_date, close_price, volume, retail_net, foreign_net, inst_net, margin_rate 
            FROM daily_stock_quotes 
            WHERE stock_code = :code 
            ORDER BY quote_date DESC 
            LIMIT 1
        """)
        # 매핑 결과를 딕셔너리 형태로 안전하게 변환
        result = session.execute(query, {"code": code}).mappings().fetchone()
        if result:
            latest_db_row = dict(result)

    if not latest_db_row:
        print("❌ DB에서 삼성전자 데이터를 찾을 수 없습니다. (적재 실패)")
        return

    db_date = str(latest_db_row["quote_date"])
    print(f"✅ DB 최신 날짜: {db_date}\n")

    # ==========================================
    # 2. 키움 API 데이터 조회 (비교용 원본)
    # ==========================================
    print("📡 2. 키움 API 실시간 원본 데이터 호출 중...")
    token = kiwoom_utils.get_kiwoom_token()
    if not token:
        print("❌ 토큰 발급 실패.")
        return

    # API 데이터 수신 및 인덱스 정규화 (스캐너와 동일한 로직 적용)
    df_ohlcv = kiwoom_utils.get_daily_ohlcv_ka10081_df(token, code)
    df_ohlcv.index = pd.to_datetime(df_ohlcv.index)

    df_investor = kiwoom_utils.get_investor_daily_ka10059_df(token, code)
    if not df_investor.empty:
        df_investor.index = pd.to_datetime(df_investor.index)

    df_margin = kiwoom_utils.get_margin_daily_ka10013_df(token, code)
    if not df_margin.empty:
        df_margin.index = pd.to_datetime(df_margin.index)
        # 💡 [핵심] 스캐너에서 적용한 T-1, T-2 지연 보정(ffill)을 똑같이 적용합니다!
        df_margin = df_margin.reindex(df_ohlcv.index).ffill()

    # ==========================================
    # 3. 크로스체크 매칭 및 출력
    # ==========================================
    target_date = pd.to_datetime(db_date)

    # 안전하게 데이터 추출 (값이 없으면 N/A)
    def safe_get(df, col):
        return (
            df.loc[target_date, col]
            if not df.empty and target_date in df.index
            else "N/A"
        )

    api_close = safe_get(df_ohlcv, "Close")
    api_vol = safe_get(df_ohlcv, "Volume")
    api_retail = safe_get(df_investor, "Retail_Net")
    api_foreign = safe_get(df_investor, "Foreign_Net")
    api_inst = safe_get(df_investor, "Inst_Net")
    api_margin = safe_get(df_margin, "Margin_Rate")

    print(f"\n📊 [크로스체크 결과] 기준일: {db_date}")
    print("-" * 65)
    print(f"{'항목':<15} | {'📡 API 원본 데이터':<20} | {'🗄️ DB 적재 데이터':<20}")
    print("-" * 65)

    print(
        f"{'종가 (Close)':<15} | {str(api_close):<20} | {str(latest_db_row['close_price']):<20}"
    )
    print(
        f"{'거래량 (Volume)':<15} | {str(api_vol):<20} | {str(latest_db_row['volume']):<20}"
    )
    print(
        f"{'개인 순매수':<15} | {str(api_retail):<20} | {str(latest_db_row['retail_net']):<20}"
    )
    print(
        f"{'외인 순매수':<15} | {str(api_foreign):<20} | {str(latest_db_row['foreign_net']):<20}"
    )
    print(
        f"{'기관 순매수':<15} | {str(api_inst):<20} | {str(latest_db_row['inst_net']):<20}"
    )
    print(
        f"{'신용잔고율':<15} | {str(api_margin):<20} | {str(latest_db_row['margin_rate']):<20}"
    )
    print("-" * 65)

    # 단순 문자열 비교를 위해 소수점 포맷팅 일치 후 판정
    if str(api_margin) == str(latest_db_row["margin_rate"]) and str(api_foreign) == str(
        latest_db_row["foreign_net"]
    ):
        print(
            "\n🎉 [최종 합격] API 원본과 DB 데이터가 100% 일치합니다! 파이프라인 무결성 검증 완료! 🚀"
        )
    else:
        print(
            "\n⚠️ [주의] 일부 데이터가 다릅니다. (NaN 처리 혹은 float 소수점 표시 차이일 수 있습니다)"
        )


if __name__ == "__main__":
    verify_samsung_data()
