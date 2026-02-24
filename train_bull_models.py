import sqlite3
import pandas as pd
import numpy as np
import joblib
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from sklearn.metrics import precision_score
import warnings
warnings.filterwarnings('ignore')

def load_and_preprocess_bull():
    print("[1/3] 상승장 데이터 로드 및 최신 지표 생성 중...")
    conn = sqlite3.connect('kospi_stock_data.db')
    # 최근 상승 국면 데이터
    query = "SELECT * FROM daily_stock_quotes WHERE Date >= '2025-08-01' AND Date <= '2026-01-15' ORDER BY Date ASC"
    raw_df = pd.read_sql(query, conn)
    conn.close()

    all_processed_data = []
    for code in raw_df['Code'].unique():
        df = raw_df[raw_df['Code'] == code].copy()
        if len(df) < 60: continue

        # 기존 지표 및 신규 지표 생성
        df['Vol_Change'] = df['Volume'].pct_change()
        df['MA_Ratio'] = df['Close'] / (df['MA20'] + 1e-9)
        df['BB_Pos'] = (df['Close'] - df['BBL']) / (df['BBU'] - df['BBL'] + 1e-9)
        df['RSI_Slope'] = df['RSI'].diff()
        df['Range_Ratio'] = (df['High'] - df['Low']) / (df['Close'] + 1e-9)
        df['Vol_Momentum'] = df['Volume'] / (df['Volume'].rolling(window=5).mean() + 1e-9)
        df['Dist_MA5'] = df['Close'] / (df['MA5'] + 1e-9)

        # 필수 특징 생성
        df['Up_Trend_2D'] = (df['Close'].diff(1) > 0) & (df['Close'].shift(1).diff(1) > 0)
        df['Up_Trend_2D'] = df['Up_Trend_2D'].astype(int)

        # 익일 데이터 생성
        df['Next_Open'] = df['Open'].shift(-1)
        df['Next_High'] = df['High'].shift(-1)
        df['Next_Low'] = df['Low'].shift(-1)
        df['Next_Close'] = df['Close'].shift(-1)

        # ==========================================
        # 🚀 [v12.1 완화된 정답지] 현실적인 KOSPI 타겟팅
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

def train_bull_specialists():
    total_df = load_and_preprocess_bull()
    if total_df.empty: return

    features_xgb = ['Return', 'MA_Ratio', 'MACD', 'MACD_Sig', 'VWAP', 'OBV', 'Up_Trend_2D', 'Dist_MA5']
    features_lgbm = ['BB_Pos', 'RSI', 'RSI_Slope', 'Range_Ratio', 'Vol_Momentum', 'Vol_Change', 'ATR', 'BBB', 'BBP']
    
    # 시간순 정렬 및 데이터 분할
    total_df = total_df.sort_values(by='Date')
    split_idx = int(len(total_df) * 0.8)
    train_df, test_df = total_df.iloc[:split_idx], total_df.iloc[split_idx:]
    y_train, y_test = train_df['Target'], test_df['Target']

    # --- 동적 가중치 계산 ---
    neg_count = (y_train == 0).sum()
    pos_count = (y_train == 1).sum()
    dynamic_weight = 1.0 if pos_count == 0 else neg_count / pos_count
    print(f"\n📊 [데이터 현황] 오답: {neg_count}개 | 정답: {pos_count}개 (가중치: {dynamic_weight:.1f}배)")

    # --- [Bull XGBoost: 추세 전문가] ---
    print(f"\n[2/3] Bull XGBoost 학습 중...")
    bull_xgb = XGBClassifier(
        n_estimators=1000, learning_rate=0.01, max_depth=6, 
        scale_pos_weight=dynamic_weight, random_state=42, n_jobs=-1
    )
    bull_xgb.fit(train_df[features_xgb], y_train)
    
    prob_x = bull_xgb.predict_proba(test_df[features_xgb])[:, 1]
    max_x = prob_x.max()
    th_x = 0.50 if max_x >= 0.50 else max_x * 0.9
    pred_x = (prob_x >= th_x).astype(int)
    print(f"💡 [Bull XGB] 최고 확신도: {max_x*100:.2f}% | 정밀도: {precision_score(y_test, pred_x, zero_division=0):.2%}")
    joblib.dump(bull_xgb, 'bull_xgb_model.pkl')

    # --- [Bull LightGBM: 변동성 전문가] ---
    print(f"\n[3/3] Bull LightGBM 학습 중...")
    bull_lgbm = LGBMClassifier(
        n_estimators=1000, learning_rate=0.01, max_depth=6, 
        scale_pos_weight=dynamic_weight, random_state=42, n_jobs=-1, force_col_wise=True
    )
    bull_lgbm.fit(train_df[features_lgbm], y_train)

    prob_l = bull_lgbm.predict_proba(test_df[features_lgbm])[:, 1]
    max_l = prob_l.max()
    th_l = 0.50 if max_l >= 0.50 else max_l * 0.9
    pred_l = (prob_l >= th_l).astype(int)
    print(f"💡 [Bull LGBM] 최고 확신도: {max_l*100:.2f}% | 정밀도: {precision_score(y_test, pred_l, zero_division=0):.2%}")
    joblib.dump(bull_lgbm, 'bull_lgbm_model.pkl')
    
    print("\n✅ 상승장 전용 모델 2종 갱신 완료!")

if __name__ == "__main__":
    train_bull_specialists()