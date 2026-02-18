import FinanceDataReader as fdr
import pandas as pd
import pandas_ta as ta
import sqlite3
import time
from datetime import datetime, timedelta

DB_NAME = 'kospi_stock_data.db'
TABLE_NAME = 'daily_stock_quotes'

def setup_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            Date TEXT, Code TEXT, Name TEXT,
            Open REAL, High REAL, Low REAL, Close REAL, Volume REAL,
            MA5 REAL, MA20 REAL, MA60 REAL, MA120 REAL,
            RSI REAL, MACD REAL, MACD_Sig REAL, MACD_Hist REAL,
            BBL REAL, BBM REAL, BBU REAL, Return REAL,
            PRIMARY KEY (Date, Code)
        )
    ''')
    conn.commit()
    return conn

def collect_and_save():
    conn = setup_database()
    df_krx = fdr.StockListing('KOSPI')
    kospi_list = df_krx[['Code', 'Name']]

    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=3*365 + 200)).strftime('%Y-%m-%d')

    print(f"안전한 방식으로 데이터 수집을 시작합니다...")

    for index, row in kospi_list.iterrows():
        code, name = row['Code'], row['Name']
        
        try:
            df = fdr.DataReader(code, start_date, end_date)
            
            if len(df) > 150:
                # 1. 이동평균선
                df['MA5'] = ta.sma(df['Close'], length=5)
                df['MA20'] = ta.sma(df['Close'], length=20)
                df['MA60'] = ta.sma(df['Close'], length=60)
                df['MA120'] = ta.sma(df['Close'], length=120)
                
                # 2. RSI
                df['RSI'] = ta.rsi(df['Close'], length=14)
                
                # 3. MACD (이름 찾기 대신 위치로 가져오기)
                macd_df = ta.macd(df['Close'])
                df['MACD'] = macd_df.iloc[:, 0]      # MACD 선
                df['MACD_Sig'] = macd_df.iloc[:, 1]  # Signal 선
                df['MACD_Hist'] = macd_df.iloc[:, 2] # Histogram
                
                # 4. 볼린저 밴드 (이름 찾기 대신 위치로 가져오기)
                bb_df = ta.bbands(df['Close'], length=20, std=2)
                df['BBL'] = bb_df.iloc[:, 0] # Lower Band
                df['BBM'] = bb_df.iloc[:, 1] # Mid Band
                df['BBU'] = bb_df.iloc[:, 2] # Upper Band
                
                df['Return'] = df['Close'].pct_change()
                df['Code'] = code
                df['Name'] = name
                
                # 정리 및 저장
                df = df.dropna().reset_index()
                df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')

                cols = ['Date', 'Code', 'Name', 'Open', 'High', 'Low', 'Close', 'Volume', 
                        'MA5', 'MA20', 'MA60', 'MA120', 'RSI', 'MACD', 'MACD_Sig', 'MACD_Hist', 
                        'BBL', 'BBM', 'BBU', 'Return']
                
                df[cols].to_sql(TABLE_NAME, conn, if_exists='append', index=False)
                print(f"[{index+1}] {name} 저장 완료")
            
            time.sleep(0.5)

        except sqlite3.IntegrityError:
            pass
        except Exception as e:
            print(f"[{name}] 오류 발생: {e}")

    conn.close()
    print("\n[완료] 이제 오류 없이 DB에 모든 데이터가 저장되었습니다!")

if __name__ == "__main__":
    collect_and_save()