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
    conn = sqlite3.connect('kospi_stock_data.db')
    all_data = []
    for code in codes:
        df = pd.read_sql(f"SELECT * FROM daily_stock_quotes WHERE Code = '{code}' ORDER BY Date ASC", conn)
        if len(df) < 150: continue
        
        df['Next_Day_Return'] = df['Return'].shift(-1)
        df['Target'] = (df['Next_Day_Return'] > 0.003).astype(int)
        df['Vol_Change'] = df['Volume'].pct_change()
        df['MA_Ratio'] = df['Close'] / (df['MA20'] + 1e-9)
        df['BB_Pos'] = (df['Close'] - df['BBL']) / (df['BBU'] - df['BBL'] + 1e-9)
        df['RSI_Slope'] = df['RSI'].diff()
        df['Range_Ratio'] = (df['High'] - df['Low']) / (df['Close'] + 1e-9)
        df['Vol_Momentum'] = df['Volume'] / (df['Volume'].rolling(window=5).mean() + 1e-9)
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['Dist_MA5'] = df['Close'] / (df['MA5'] + 1e-9)
        
        df = df.replace([np.inf, -np.inf], np.nan).dropna()
        all_data.append(df)
    conn.close()
    return pd.concat(all_data, axis=0)

# 3. LightGBM 메인 학습 함수
def train_hybrid_lgbm():
    target_codes = get_hybrid_top_codes()
    total_df = load_and_preprocess(target_codes)
    
    features = ['Return', 'Vol_Change', 'MA_Ratio', 'BB_Pos', 'RSI', 'MACD', 'MACD_Sig', 
                'RSI_Slope', 'Range_Ratio', 'Vol_Momentum', 'Dist_MA5']
    
    unique_dates = sorted(total_df['Date'].unique())
    split_date = unique_dates[int(len(unique_dates) * 0.8)]
    
    train_df = total_df[total_df['Date'] < split_date]
    test_df = total_df[total_df['Date'] >= split_date]

    X_train, y_train = train_df[features], train_df['Target']
    X_test, y_test = test_df[features], test_df['Target']

    # --- [핵심] LightGBM 모델 설정 ---
    model = LGBMClassifier(
        n_estimators=2000,
        learning_rate=0.005,      # XGBoost보다 더 낮게 잡아도 속도가 빠릅니다.
        num_leaves=31,            # 트리의 복잡도 조절 (중요 파라미터)
        max_depth=5,              # 과적합 방지용 깊이 제한
        min_child_samples=20,     # 한 잎사귀에 들어갈 최소 데이터 수
        feature_fraction=0.8,     # 학습 시 사용할 지표 비중
        bagging_fraction=0.8,     # 학습 시 사용할 데이터 비중
        subsample_freq=5,           # 5번 학습마다 데이터를 새로 샘플링
        lambda_l1=0.1,            # L1 규제
        lambda_l2=0.1,            # L2 규제
        random_state=42,
        n_jobs=-1,
        force_col_wise=True,       # 대량 데이터 처리 최적화
        importance_type='gain' # 중요도 계산 방식을 더 정확하게 바꿀 때 유용
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

    y_pred = model.predict(X_test)
    precision = precision_score(y_test, y_pred)
    
    print(f"\n✅ LightGBM 검증 정밀도: {precision:.2%}")

    # 모델 저장 (파일명을 다르게 하여 XGBoost와 구분합니다)
    joblib.dump(model, 'hybrid_lgbm_model.pkl')
    joblib.dump(features, 'lgbm_features.pkl')
    print("[5/5] 모델 파일 저장 완료: hybrid_lgbm_model.pkl")

if __name__ == "__main__":
    train_hybrid_lgbm()