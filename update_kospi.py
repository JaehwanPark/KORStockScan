import FinanceDataReader as fdr
import pandas as pd
import pandas_ta as ta
import sqlite3
import time
import os
from datetime import datetime, timedelta

# --- 설정 ---
DB_NAME = 'kospi_stock_data.db'
TABLE_NAME = 'daily_stock_quotes'
EXT_TABLE_NAME = 'external_indicators' # 외부 지표 테이블명

def get_last_date(conn, table, date_col='Date', code_col=None, code=None):
    """DB에서 마지막 저장 날짜를 가져옵니다."""
    query = f"SELECT MAX({date_col}) FROM {table}"
    if code_col and code:
        query += f" WHERE {code_col} = '{code}'"
    
    try:
        df = pd.read_sql(query, conn)
        return df.iloc[0, 0]
    except:
        return None

def update_external_indicators(conn):
    """나스닥, S&P500, 환율 등 외부 경제 지표 업데이트 (중복 방지 강화)"""
    print("\n🌐 외부 거시 지표 업데이트 확인 중...")
    
    indicators = {
        'Nasdaq': 'IXIC',
        'S&P500': 'US500',
        'USD_KRW': 'USD/KRW',
        'US_10Y': 'US10YT',
        'VIX': 'VIX'
    }
    
    # 1. DB에서 마지막 업데이트 날짜 확인
    last_date_str = get_last_date(conn, EXT_TABLE_NAME, date_col='date')
    
    # 수집 시작일 설정 (마지막 날짜부터 오늘까지)
    if last_date_str:
        fetch_start = last_date_str # 마지막 날짜를 포함해서 가져온 뒤 아래에서 필터링
    else:
        fetch_start = '2022-01-01'
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 2. 데이터 수집
    df_ext = pd.DataFrame()
    for name, ticker in indicators.items():
        try:
            data = fdr.DataReader(ticker, fetch_start, today)['Close']
            if not data.empty:
                df_ext[name] = data
        except Exception as e:
            print(f"⚠️ {name}({ticker}) 수집 중 오류: {e}")

    if not df_ext.empty:
        # 3. 데이터 정제 및 날짜 포맷 변환
        df_ext.index.name = 'date'
        df_ext.reset_index(inplace=True)
        df_ext['date'] = pd.to_datetime(df_ext['date']).dt.strftime('%Y-%m-%d')
        
        # --- [핵심: 중복 제거 필터링] ---
        # DB에 저장된 마지막 날짜보다 큰(이후의) 데이터만 남깁니다.
        if last_date_str:
            df_ext = df_ext[df_ext['date'] > last_date_str]
        # ------------------------------

        if not df_ext.empty:
            # 최신 Pandas 문법 적용
            df_ext = df_ext.ffill().bfill()
            
            # 4. DB 저장
            try:
                df_ext.to_sql(EXT_TABLE_NAME, conn, if_exists='append', index=False)
                print(f"✅ 외부 지표 {len(df_ext)}일치 신규 데이터 추가 완료.")
            except sqlite3.IntegrityError:
                print("⚠️ 중복 데이터가 감지되어 삽입을 건너뛰었습니다.")
        else:
            print("✨ 외부 지표가 이미 최신 상태입니다.")
    else:
        print("ℹ️ 업데이트할 신규 외부 지표 데이터가 없습니다.")

def update_database():
    conn = sqlite3.connect(DB_NAME)
    
    # --- [Part 1: 코스피 종목 업데이트] ---
    print("최신 코스피 종목 리스트 확인 중...")
    df_krx = fdr.StockListing('KOSPI')
    kospi_list = df_krx[['Code', 'Name']]
    
    today = datetime.now().strftime('%Y-%m-%d')
    print(f"업데이트 기준일: {today}")

    for index, row in kospi_list.iterrows():
        code, name = row['Code'], row['Name']
        try:
            last_date_str = get_last_date(conn, TABLE_NAME, date_col='Date', code_col='Code', code=code)
            
            if last_date_str:
                last_date = datetime.strptime(last_date_str, '%Y-%m-%d')
                if last_date_str >= today:
                    continue
                fetch_start = (last_date - timedelta(days=150)).strftime('%Y-%m-%d')
            else:
                fetch_start = (datetime.now() - timedelta(days=3*365)).strftime('%Y-%m-%d')
                last_date_str = '1900-01-01'

            df = fdr.DataReader(code, fetch_start, today)
            
            if len(df) > 0:
                # [기존 코드] 이동평균선 및 RSI
                df['MA5'] = ta.sma(df['Close'], length=5)
                df['MA20'] = ta.sma(df['Close'], length=20)
                df['MA60'] = ta.sma(df['Close'], length=60)
                df['MA120'] = ta.sma(df['Close'], length=120)
                df['RSI'] = ta.rsi(df['Close'], length=14)
                
                # [기존 코드] MACD
                macd_df = ta.macd(df['Close'])
                if macd_df is not None:
                    df['MACD'] = macd_df.iloc[:, 0]
                    df['MACD_Sig'] = macd_df.iloc[:, 1]
                    df['MACD_Hist'] = macd_df.iloc[:, 2]
                
                # [기존 코드 보완] Bollinger Bands & Bandwidth (%B) 추가
                bb_df = ta.bbands(df['Close'], length=20, std=2)
                if bb_df is not None:
                    df['BBL'] = bb_df.iloc[:, 0]
                    df['BBM'] = bb_df.iloc[:, 1]
                    df['BBU'] = bb_df.iloc[:, 2]
                    # 추가 지표 1: Bollinger Bandwidth (밴드 폭)
                    df['BBB'] = bb_df.iloc[:, 3] 
                    # 추가 지표 2: Bollinger %B (밴드 내 주가 위치)
                    df['BBP'] = bb_df.iloc[:, 4]

                # ==========================================
                # 🚀 [신규 추가 지표] VWAP, OBV, ATR
                # ==========================================
                
                # 추가 지표 3: VWAP (거래량 가중 평균 가격)
                # FinanceDataReader는 기본적으로 일봉(Daily) 데이터를 가져옵니다. 
                # 일봉 단위의 VWAP은 의미가 약할 수 있으므로, 보통 누적(Cumulative)이나 
                # 특정 기간(예: 14일)의 VWAP을 사용합니다. pandas_ta는 기본적으로 전체 누적을 계산합니다.
                df['VWAP'] = ta.vwap(high=df['High'], low=df['Low'], close=df['Close'], volume=df['Volume'])

                # 추가 지표 4: OBV (On-Balance Volume - 세력 매집 파악)
                df['OBV'] = ta.obv(close=df['Close'], volume=df['Volume'])

                # 추가 지표 5: ATR (Average True Range - 변동성 파악)
                # length=14가 가장 표준적인 설정입니다.
                df['ATR'] = ta.atr(high=df['High'], low=df['Low'], close=df['Close'], length=14)
                # ==========================================

                # [기존 코드] 기본 정보 세팅
                df['Return'] = df['Close'].pct_change()
                df['Code'] = code
                df['Name'] = name
                
                df = df.reset_index()
                df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
                new_rows = df[df['Date'] > last_date_str]
                
                if not new_rows.empty:
                    # DB에 저장할 컬럼 목록 업데이트 (새로 만든 지표들 추가!)
                    cols = ['Date', 'Code', 'Name', 'Open', 'High', 'Low', 'Close', 'Volume', 
                            'MA5', 'MA20', 'MA60', 'MA120', 'RSI', 'MACD', 'MACD_Sig', 'MACD_Hist', 
                            'BBL', 'BBM', 'BBU', 'BBB', 'BBP', 'VWAP', 'OBV', 'ATR', 'Return']
                    
                    new_rows[cols].dropna(subset=['Close']).to_sql(TABLE_NAME, conn, if_exists='append', index=False)
                    print(f"[{index+1}] {name}({code}) - {len(new_rows)}일치 추가 완료")
            
            time.sleep(0.3) 

        except Exception as e:
            print(f"[{name}] 업데이트 중 오류 발생: {e}")

    # --- [Part 2: 외부 지표 업데이트 통합] ---
    update_external_indicators(conn)

    conn.close()
    print("\n[알림] 모든 데이터(코스피 + 외부지표) 업데이트가 완료되었습니다.")

if __name__ == "__main__":
    update_database()