import sqlite3
import pandas as pd
import numpy as np
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score
import warnings
warnings.filterwarnings('ignore')

def load_data_for_stacking():
    print("[1/4] 메타 모델 학습용 데이터 로드 및 v12.1 지표/타겟 생성 중...")
    conn = sqlite3.connect('kospi_stock_data.db')
    query = "SELECT * FROM daily_stock_quotes WHERE Date >= '2025-08-01' ORDER BY Date ASC"
    raw_df = pd.read_sql(query, conn)
    conn.close()

    all_processed_data = []
    for code in raw_df['Code'].unique():
        df = raw_df[raw_df['Code'] == code].copy()
        if len(df) < 60: continue

        # 공통 지표 생성
        df['Vol_Change'] = df['Volume'].pct_change()
        df['MA_Ratio'] = df['Close'] / (df['MA20'] + 1e-9)
        df['BB_Pos'] = (df['Close'] - df['BBL']) / (df['BBU'] - df['BBL'] + 1e-9)
        df['RSI_Slope'] = df['RSI'].diff()
        df['Range_Ratio'] = (df['High'] - df['Low']) / (df['Close'] + 1e-9)
        df['Vol_Momentum'] = df['Volume'] / (df['Volume'].rolling(window=5).mean() + 1e-9)
        df['Dist_MA5'] = df['Close'] / (df['MA5'] + 1e-9)
        
        df['Up_Trend_2D'] = (df['Close'].diff(1) > 0) & (df['Close'].shift(1).diff(1) > 0)
        df['Up_Trend_2D'] = df['Up_Trend_2D'].astype(int)

        # 익일 데이터 생성
        df['Next_Open'] = df['Open'].shift(-1)
        df['Next_High'] = df['High'].shift(-1)
        df['Next_Low'] = df['Low'].shift(-1)
        df['Next_Close'] = df['Close'].shift(-1)

        # ==========================================
        # 🚀 [v12.1 완화된 정답지] 메타 모델용 타겟
        # ==========================================
        hit_target = (df['Next_High'] / (df['Next_Open'] + 1e-9)) >= 1.020   
        no_stop_loss = (df['Next_Low'] / (df['Next_Open'] + 1e-9)) >= 0.975  
        solid_close = df['Next_Close'] > df['Next_Open']                     

        df['Target'] = np.where(hit_target & no_stop_loss & solid_close, 1, 0)
        # ==========================================
        
        df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=['Target', 'Next_Open', 'Next_High', 'Next_Low', 'Next_Close'])
        df = df.dropna()
        if not df.empty:
            all_processed_data.append(df)
    
    return pd.concat(all_processed_data) if all_processed_data else pd.DataFrame()

def train_stacking_ensemble():
    total_df = load_data_for_stacking()
    if total_df.empty: return

    features_xgb = ['Return', 'MA_Ratio', 'MACD', 'MACD_Sig', 'VWAP', 'OBV', 'Up_Trend_2D', 'Dist_MA5']
    features_lgbm = ['BB_Pos', 'RSI', 'RSI_Slope', 'Range_Ratio', 'Vol_Momentum', 'Vol_Change', 'ATR', 'BBB', 'BBP']
    
    total_df = total_df.sort_values(by='Date')
    split_idx = int(len(total_df) * 0.8)
    train_df, test_df = total_df.iloc[:split_idx], total_df.iloc[split_idx:]
    y_train, y_test = train_df['Target'], test_df['Target']

    print("[2/4] 전공이 분리된 4개의 베이스 모델 불러오는 중...")
    xgb_model = joblib.load('hybrid_xgb_model.pkl')
    lgbm_model = joblib.load('hybrid_lgbm_model.pkl')
    bull_xgb = joblib.load('bull_xgb_model.pkl')
    bull_lgbm = joblib.load('bull_lgbm_model.pkl')

    print("[3/4] 각 전문가에게 질문하여 확률(Probability) 추출 중...")
    meta_X_train = pd.DataFrame({
        'XGB_Prob': xgb_model.predict_proba(train_df[features_xgb])[:, 1],
        'LGBM_Prob': lgbm_model.predict_proba(train_df[features_lgbm])[:, 1],
        'Bull_XGB_Prob': bull_xgb.predict_proba(train_df[features_xgb])[:, 1],
        'Bull_LGBM_Prob': bull_lgbm.predict_proba(train_df[features_lgbm])[:, 1]
    })
    
    meta_X_test = pd.DataFrame({
        'XGB_Prob': xgb_model.predict_proba(test_df[features_xgb])[:, 1],
        'LGBM_Prob': lgbm_model.predict_proba(test_df[features_lgbm])[:, 1],
        'Bull_XGB_Prob': bull_xgb.predict_proba(test_df[features_xgb])[:, 1],
        'Bull_LGBM_Prob': bull_lgbm.predict_proba(test_df[features_lgbm])[:, 1]
    })

    print("[4/4] 최종 결정권자(Meta-Model) 학습 및 임계값 테스트 중...")
    # 🚀 핵심: 메타 모델도 데이터 불균형을 고려하도록 class_weight='balanced' 적용
    meta_model = LogisticRegression(class_weight='balanced', random_state=42)
    meta_model.fit(meta_X_train, y_train)
    
    meta_pred_proba = meta_model.predict_proba(meta_X_test)[:, 1]
    
    print("\n[전문가 의견 상관관계 분석]")
    print(meta_X_test.corr().round(3))
    
    thresholds = [0.5, 0.6, 0.7, 0.75, 0.8, 0.85]
    print("\n=============================================")
    print("   임계값(Th) | 정밀도(Precision) | 매수횟수(Test)")
    print("---------------------------------------------")
    for th in thresholds:
        meta_pred = (meta_pred_proba >= th).astype(int)
        if sum(meta_pred) == 0: continue
        precision = precision_score(y_test, meta_pred, zero_division=0)
        print(f"      {th:.2f}    |      {precision * 100:.2f}%      |   {sum(meta_pred)}건")
    print("=============================================")
    
    joblib.dump(meta_model, 'stacking_meta_model.pkl')
    print("\n✅ v12.1 완전체 스태킹 모델 저장 완료!")

if __name__ == "__main__":
    train_stacking_ensemble()