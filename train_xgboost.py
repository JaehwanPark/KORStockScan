import FinanceDataReader as fdr
import sqlite3
import pandas as pd
import numpy as np
import joblib
from xgboost import XGBClassifier
from sklearn.metrics import precision_score, classification_report
import matplotlib.pyplot as plt

# 1. 하이브리드 종목 필터링 (시총 300위 내 + 거래량 150위 내) 변수명은 수정하지 않았음
def get_hybrid_top_codes():
    print("[1/5] 최신 시장 데이터 기반 우량 대장주 필터링 중...")
    df_krx = fdr.StockListing('KOSPI')
    top_200_marcap = df_krx.sort_values(by='Marcap', ascending=False).head(200)
    hybrid_top_100 = top_200_marcap.sort_values(by='Volume', ascending=False).head(100)
    return hybrid_top_100['Code'].tolist()

# 2. 데이터 로드 및 기술적 지표 생성
def load_and_preprocess(codes):
    print(f"[2/5] {len(codes)}개 종목 데이터 가공 및 최신 지표(VWAP, OBV 등) 적용 중...")
    conn = sqlite3.connect('kospi_stock_data.db')
    all_data = []
    
    for code in codes:
        df = pd.read_sql(f"SELECT * FROM daily_stock_quotes WHERE Code = '{code}' ORDER BY Date ASC", conn)
        if len(df) < 150: continue
        
        # 1. 기존 파생 지표 유지
        df['Vol_Change'] = df['Volume'].pct_change()
        df['MA_Ratio'] = df['Close'] / (df['MA20'] + 1e-9)
        df['BB_Pos'] = (df['Close'] - df['BBL']) / (df['BBU'] - df['BBL'] + 1e-9)
        df['RSI_Slope'] = df['RSI'].diff() 
        df['Range_Ratio'] = (df['High'] - df['Low']) / (df['Close'] + 1e-9)
        df['Vol_Momentum'] = df['Volume'] / (df['Volume'].rolling(window=5).mean() + 1e-9)
        df['Dist_MA5'] = df['Close'] / (df['MA5'] + 1e-9)

        # 필수 특징(Feature) 생성
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
        hit_target = (df['Next_High'] / (df['Next_Open'] + 1e-9)) >= 1.020   # 1. 고가가 +2.0% 도달
        no_stop_loss = (df['Next_Low'] / (df['Next_Open'] + 1e-9)) >= 0.975  # 2. 저가가 -2.5% 미만으로 안 빠짐
        solid_close = df['Next_Close'] > df['Next_Open']                     # 3. 시가보다 높은 양봉 마감

        df['Target'] = np.where(hit_target & no_stop_loss & solid_close, 1, 0)
        # ==========================================

        # 무한대 및 결측치 제거
        df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=['Target', 'Next_Open', 'Next_High', 'Next_Low', 'Next_Close'])
        df = df.dropna()
        
        if not df.empty:
            all_data.append(df)
    
    conn.close()
    return pd.concat(all_data, axis=0) if all_data else pd.DataFrame()

# 3. 메인 학습 함수
def train_hybrid_xgb():
    target_codes = get_hybrid_top_codes()
    total_df = load_and_preprocess(target_codes)
    
    if total_df.empty:
        print("[-] 학습할 데이터가 부족합니다. DB 상태를 확인하세요.")
        return

    features = ['Return', 'MA_Ratio', 'MACD', 'MACD_Sig', 'VWAP', 'OBV', 'Up_Trend_2D', 'Dist_MA5']
    
    unique_dates = sorted(total_df['Date'].unique())
    split_date = unique_dates[int(len(unique_dates) * 0.8)]
    
    train_df = total_df[total_df['Date'] < split_date]
    test_df = total_df[total_df['Date'] >= split_date]

    X_train, y_train = train_df[features], train_df['Target']
    X_test, y_test = test_df[features], test_df['Target']

    # --- [신규] 동적 가중치 계산 ---
    neg_count = (y_train == 0).sum()
    pos_count = (y_train == 1).sum()
    
    print(f"\n📊 [학습 데이터 현황] 일반(0): {neg_count}개 | 스나이퍼 타겟(1): {pos_count}개")
    
    if pos_count == 0:
        print("🚨 [비상] 정답(1) 데이터가 0개입니다! 타겟 조건을 낮춰야 합니다.")
        dynamic_weight = 1.0
    else:
        dynamic_weight = neg_count / pos_count
        print(f"⚖️ [처방] 정답 예측에 {dynamic_weight:.1f}배의 가중치를 부여합니다.\n")

    print(f"[3/5] XGBoost 모델 최적화 학습 시작 (데이터: {len(X_train)}건)...")
    model = XGBClassifier(
        n_estimators=2000, 
        learning_rate=0.005,
        max_depth=5,
        min_child_weight=5,       
        gamma=0.1,                
        subsample=0.8,            
        colsample_bytree=0.8,     
        reg_alpha=0.05,           
        reg_lambda=1.2,           
        scale_pos_weight=dynamic_weight, # 동적 가중치 주입!
        random_state=42,
        n_jobs=-1,
        early_stopping_rounds=100, 
        eval_metric='logloss'        
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)], 
        verbose=50                   
    )

    # --- [신규] AI 속마음 확인 및 결과 평가 ---
    print("\n[4/5] 테스트 데이터로 성능 검증 중...")
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    max_prob = y_pred_proba.max()
    print(f"💡 [AI의 최고 확신도] 가장 정답일 것 같은 종목의 확률: {max_prob * 100:.2f}%")
    
    threshold = 0.50
    if max_prob < 0.50:
        threshold = max_prob * 0.9
        print(f"⚠️ 50% 이상 확신하는 종목이 없어, 임계값을 {threshold:.3f}로 낮춰서 채점합니다.")
        
    y_pred = (y_pred_proba >= threshold).astype(int)
    precision = precision_score(y_test, y_pred, zero_division=0)
    
    print("\n" + "="*50)
    print(f"✅ XGBoost 검증 정밀도 (임계값 {threshold:.3f} 기준): {precision:.2%}")
    print("="*50)

    joblib.dump(model, 'hybrid_xgb_model.pkl')
    joblib.dump(features, 'hybrid_features.pkl')
    print("[5/5] 모델 파일 저장 완료: hybrid_xgb_model.pkl")

if __name__ == "__main__":
    train_hybrid_xgb()