import sqlite3
import pandas as pd
import numpy as np
import joblib
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from sklearn.metrics import precision_score

def load_and_preprocess_bull():
    print("[1/3] 상승장 데이터 로드 및 지표 생성 중...")
    conn = sqlite3.connect('kospi_stock_data.db')
    
    # 최근 데이터(상승 국면)를 가져옵니다.
    query = "SELECT * FROM daily_stock_quotes WHERE Date >= '2025-08-01' AND Date <= '2026-01-15' ORDER BY Date ASC"
    raw_df = pd.read_sql(query, conn)
    conn.close()

    all_processed_data = []
    # 종목별로 루프를 돌며 지표를 계산해야 '데이터 오염'이 없습니다.
    for code in raw_df['Code'].unique():
        df = raw_df[raw_df['Code'] == code].copy()
        if len(df) < 60: continue # 데이터가 너무 적은 종목은 제외

        # --- [지표 생성 로직] ---
        df['Next_Day_Return'] = df['Return'].shift(-1)
        df['Target'] = (df['Next_Day_Return'] > 0.005).astype(int) # 상승장용 공격적 타겟(0.5%)
        
        df['Vol_Change'] = df['Volume'].pct_change()
        df['MA_Ratio'] = df['Close'] / (df['MA20'] + 1e-9)
        df['BB_Pos'] = (df['Close'] - df['BBL']) / (df['BBU'] - df['BBL'] + 1e-9)
        df['RSI_Slope'] = df['RSI'].diff()
        df['Range_Ratio'] = (df['High'] - df['Low']) / (df['Close'] + 1e-9)
        df['Vol_Momentum'] = df['Volume'] / (df['Volume'].rolling(window=5).mean() + 1e-9)
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['Dist_MA5'] = df['Close'] / (df['MA5'] + 1e-9)
        
        # 결측치 제거
        df = df.replace([np.inf, -np.inf], np.nan).dropna()
        all_processed_data.append(df)
    
    return pd.concat(all_processed_data) if all_processed_data else pd.DataFrame()

def train_bull_specialists():
    total_df = load_and_preprocess_bull()
    
    if total_df.empty:
        print("[-] 학습할 데이터가 부족합니다. 날짜 설정을 확인하세요.")
        return

    features = ['Return', 'Vol_Change', 'MA_Ratio', 'BB_Pos', 'RSI', 'MACD', 'MACD_Sig', 
                'RSI_Slope', 'Range_Ratio', 'Vol_Momentum', 'Dist_MA5']
    
    X = total_df[features]
    y = total_df['Target']

    # --- [Bull XGBoost] ---
    print(f"[2/3] Bull XGBoost 학습 중... (데이터: {len(X)}건)")
    bull_xgb = XGBClassifier(
        n_estimators=1000, learning_rate=0.01, max_depth=6, 
        subsample=0.8, colsample_bytree=0.8, random_state=42
    )
    bull_xgb.fit(X, y)
    joblib.dump(bull_xgb, 'bull_xgb_model.pkl')

    # --- [Bull LightGBM] ---
    print(f"[3/3] Bull LGBM 학습 중... (데이터: {len(X)}건)")
    bull_lgbm = LGBMClassifier(
        n_estimators=1000, learning_rate=0.01, num_leaves=63, 
        max_depth=7, random_state=42, verbosity=-1
    )
    bull_lgbm.fit(X, y)
    joblib.dump(bull_lgbm, 'bull_lgbm_model.pkl')
    # 지표 리스트도 별도 저장
    joblib.dump(features, 'bull_features.pkl')

    print("\n✅ 상승장 전용 모델(Bull Models) 2종 생성 완료!")

if __name__ == "__main__":
    train_bull_specialists()