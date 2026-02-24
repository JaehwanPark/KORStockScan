import FinanceDataReader as fdr
import sqlite3
import pandas as pd
import numpy as np
import joblib
from lightgbm import LGBMClassifier, early_stopping, log_evaluation
from sklearn.metrics import precision_score
import matplotlib.pyplot as plt

# 1. 하이브리드 종목 필터링 (기존 로직 유지)
def get_hybrid_top_codes():
    print("[1/5] 우량 대장주 필터링 중 (LGBM 버전)...")
    df_krx = fdr.StockListing('KOSPI')
    top_200 = df_krx.sort_values(by='Marcap', ascending=False).head(200)
    hybrid_top = top_200.sort_values(by='Volume', ascending=False).head(100)
    return hybrid_top['Code'].tolist()

# 2. 데이터 가공 및 지표 생성 (XGBoost와 동일하게 유지하여 비교 가능하게 함)
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

        # 익일 데이터 생성
        df['Next_Open'] = df['Open'].shift(-1)
        df['Next_High'] = df['High'].shift(-1)
        df['Next_Low'] = df['Low'].shift(-1)
        df['Next_Close'] = df['Close'].shift(-1)

        # ==========================================
        # 🚀 [v12.1 완화된 정답지] 현실적인 KOSPI 타겟팅
        # ==========================================
        
        # 1. 고가가 +2.0% 도달 (기존 2.5%에서 완화)
        hit_target = (df['Next_High'] / (df['Next_Open'] + 1e-9)) >= 1.020   
        
        # 2. 저가가 -2.5% 미만으로 안 빠짐 (기존 -1.5%에서 대폭 완화하여 흔들림 허용)
        no_stop_loss = (df['Next_Low'] / (df['Next_Open'] + 1e-9)) >= 0.975  
        
        # 3. 시가보다 높은 양봉 마감 (유지)
        solid_close = df['Next_Close'] > df['Next_Open']                     

        # 3개 조건을 모두 만족(&)해야만 1(정답), 아니면 0(오답)
        df['Target'] = np.where(hit_target & no_stop_loss & solid_close, 1, 0)
        # ==========================================

        # 무한대 및 결측치 제거 (Next_Low, Next_Close 필드 추가 확인!)
        df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=['Target', 'Next_Open', 'Next_High', 'Next_Low', 'Next_Close'])
        df = df.dropna()
        all_data.append(df) # (Bull 파일의 경우 all_processed_data.append(df))
    
    conn.close()
    return pd.concat(all_data, axis=0) if all_data else pd.DataFrame()

# 3. LightGBM 메인 학습 함수
def train_hybrid_lgbm():
    target_codes = get_hybrid_top_codes()
    total_df = load_and_preprocess(target_codes)
    
    # 변동성 및 지표 강도 위주
    features = ['BB_Pos', 'RSI', 'RSI_Slope', 'Range_Ratio', 'Vol_Momentum', 'Vol_Change', 'ATR', 'BBB', 'BBP']
    
    unique_dates = sorted(total_df['Date'].unique())
    split_date = unique_dates[int(len(unique_dates) * 0.8)]
    
    train_df = total_df[total_df['Date'] < split_date]
    test_df = total_df[total_df['Date'] >= split_date]

    X_train, y_train = train_df[features], train_df['Target']
    X_test, y_test = test_df[features], test_df['Target']

    # --- [수정] 데이터 분할 이후, 모델 정의 바로 앞부분에 추가 ---
    
    # 1. 훈련 데이터의 실제 정답 개수 확인 및 동적 가중치 계산
    neg_count = (y_train == 0).sum()
    pos_count = (y_train == 1).sum()
    
    print(f"\n📊 [학습 데이터 현황] 일반(0): {neg_count}개 | 스나이퍼 타겟(1): {pos_count}개")
    
    if pos_count == 0:
        print("🚨 [비상] 정답(1) 데이터가 0개입니다! 데이터 가공 함수의 Target 조건을 낮춰야 합니다.")
        dynamic_weight = 1.0
    else:
        # 오답이 정답보다 몇 배 많은지 계산하여 그대로 가중치로 사용 (예: 99개/1개 = 99배)
        dynamic_weight = neg_count / pos_count
        print(f"⚖️ [처방] 정답 예측에 {dynamic_weight:.1f}배의 가중치를 부여합니다.\n")

    # 2. LightGBM 모델 정의 (가중치 파라미터 추가)
    model = LGBMClassifier(
        n_estimators=2000,
        learning_rate=0.005,
        num_leaves=31,
        max_depth=5,
        min_child_samples=20,
        feature_fraction=0.8,
        bagging_fraction=0.8,
        subsample_freq=5,
        lambda_l1=0.1,
        lambda_l2=0.1,
        
        # 🚀 핵심: 계산된 동적 가중치를 모델에 주입!
        scale_pos_weight=dynamic_weight, 
        
        random_state=42,
        n_jobs=-1,
        force_col_wise=True,
        importance_type='gain'
    )

    print("[3/5] LightGBM 모델 학습 시작...")
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        eval_metric='logloss',
        callbacks=[
            early_stopping(stopping_rounds=100), # 100회 성능 개선 없을 시 중단
            log_evaluation(period=100)           # 100회마다 결과 출력
        ]
    )

    # --- [수정] 모델 예측 및 평가 부분 ---
    print("\n[4/5] 테스트 데이터로 성능 검증 중...")
    
    # 1. 단순 0,1 예측이 아니라 '확률(%)'을 가져옵니다.
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    max_prob = y_pred_proba.max()
    print(f"💡 [AI의 최고 확신도] 가장 정답일 것 같은 종목의 확률: {max_prob * 100:.2f}%")
    
    # 2. 유연한 임계값(Threshold) 적용
    threshold = 0.50
    if max_prob < 0.50:
        # AI가 50% 넘게 확신하는 게 하나도 없다면, 임계값을 최고 확신도의 90% 수준으로 임시 하향
        threshold = max_prob * 0.9
        print(f"⚠️ 50% 이상 확신하는 종목이 없어, 임계값을 {threshold:.3f}로 낮춰서 채점합니다.")
        
    y_pred = (y_pred_proba >= threshold).astype(int)
    
    # 3. 경고 메시지를 끄는 파라미터(zero_division=0) 추가
    precision = precision_score(y_test, y_pred, zero_division=0)
    
    print(f"✅ LightGBM 검증 정밀도 (임계값 {threshold:.3f} 기준): {precision:.2%}")

    # 모델 저장
    joblib.dump(model, 'hybrid_lgbm_model.pkl')
    joblib.dump(features, 'lgbm_features.pkl')
    print("[5/5] 모델 파일 저장 완료: hybrid_lgbm_model.pkl")

if __name__ == "__main__":
    train_hybrid_lgbm()