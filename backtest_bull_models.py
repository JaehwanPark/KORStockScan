import sqlite3
import pandas as pd
import numpy as np
import joblib
import warnings
from sklearn.metrics import precision_score

warnings.filterwarnings('ignore')

def calculate_indicators(df):
    """모델이 요구하는 11가지 지표를 계산하는 함수"""
    df = df.sort_values('Date').copy()
    
    # 지표 계산 로직 (Training 코드와 100% 일치해야 함)
    df['Next_Day_Return'] = df['Return'].shift(-1)
    df['Target'] = (df['Next_Day_Return'] > 0.005).astype(int) # 0.5% 이상 상승 시 1
    
    df['Vol_Change'] = df['Volume'].pct_change()
    df['MA_Ratio'] = df['Close'] / (df['MA20'] + 1e-9)
    df['BB_Pos'] = (df['Close'] - df['BBL']) / (df['BBU'] - df['BBL'] + 1e-9)
    df['RSI_Slope'] = df['RSI'].diff()
    df['Range_Ratio'] = (df['High'] - df['Low']) / (df['Close'] + 1e-9)
    df['Vol_Momentum'] = df['Volume'] / (df['Volume'].rolling(window=5).mean() + 1e-9)
    df['MA5'] = df['Close'].rolling(window=5).mean()
    df['Dist_MA5'] = df['Close'] / (df['MA5'] + 1e-9)
    
    # 결측치 제거 및 불필요한 행 삭제
    df = df.replace([np.inf, -np.inf], np.nan).dropna()
    return df

def run_bull_backtest():
    print("🔍 상승장 전용 모델 백테스팅 및 정밀도 보정 시작...")
    
    # 1. 테스트 데이터 로드 (최근 3개월 구간)
    conn = sqlite3.connect('kospi_stock_data.db')
    query = "SELECT * FROM daily_stock_quotes WHERE Date > '2026-01-15' ORDER BY Date ASC"
    raw_df = pd.read_sql(query, conn)
    conn.close()

    # 2. 종목별로 지표 계산 적용
    processed_list = []
    for code in raw_df['Code'].unique():
        stock_df = raw_df[raw_df['Code'] == code]
        if len(stock_df) < 20: continue
        processed_list.append(calculate_indicators(stock_df))
    
    if not processed_list:
        print("[-] 테스트할 데이터가 부족합니다.")
        return

    test_df = pd.concat(processed_list)
    
    # 3. 모델 로드
    b_xgb = joblib.load('bull_xgb_model.pkl')
    b_lgbm = joblib.load('bull_lgbm_model.pkl')
    features = ['Return', 'Vol_Change', 'MA_Ratio', 'BB_Pos', 'RSI', 'MACD', 'MACD_Sig', 
                'RSI_Slope', 'Range_Ratio', 'Vol_Momentum', 'Dist_MA5']

    X_test = test_df[features]
    y_true = test_df['Target']

    # 4. 모델별/문턱값별 정밀도 측정
    for name, model in [("Bull-XGB", b_xgb), ("Bull-LGBM", b_lgbm)]:
        print(f"\n--- [{name}] 검증 결과 ---")
        y_prob = model.predict_proba(X_test)[:, 1]
        
        for th in [0.5, 0.53, 0.55, 0.58, 0.6]:
            y_pred = (y_prob >= th).astype(int)
            # 정밀도 계산 공식: $$Precision = \frac{TP}{TP + FP}$$
            precision = precision_score(y_true, y_pred, zero_division=0)
            count = sum(y_pred)
            print(f"문턱값 {th:.2f} | 정밀도: {precision:.1%} | 추천: {count}건")

if __name__ == "__main__":
    run_bull_backtest()