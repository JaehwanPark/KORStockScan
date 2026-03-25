import FinanceDataReader as fdr

def test_fdr_stock_list():
    print("🔍 FinanceDataReader를 통해 KRX 상장 종목 데이터를 요청합니다...")
    try:
        # KRX 전체 상장 종목 가져오기
        df_krx = fdr.StockListing('KRX')
        
        if df_krx.empty:
            print("❌ 데이터를 가져오지 못했습니다. (빈 데이터프레임)")
            return

        # KOSPI, KOSDAQ 종목만 필터링
        df_filtered = df_krx[df_krx['Market'].isin(['KOSPI', 'KOSDAQ'])]
        kospi_codes = df_filtered['Code'].tolist()
        
        print(f"\n✅ 수집 성공! 총 {len(kospi_codes)}개의 KOSPI/KOSDAQ 종목을 찾았습니다.")
        print("\n[데이터 샘플 확인 (상위 5개)]")
        print(df_filtered[['Code', 'Name', 'Market']].head())
        
        print("\n[데이터 샘플 확인 (하위 5개)]")
        print(df_filtered[['Code', 'Name', 'Market']].tail())

    except Exception as e:
        print(f"🚨 에러 발생: {e}")

if __name__ == "__main__":
    test_fdr_stock_list()