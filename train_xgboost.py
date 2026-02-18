import FinanceDataReader as fdr
import sqlite3
import pandas as pd
import numpy as np
import joblib
from xgboost import XGBClassifier
from sklearn.metrics import precision_score, classification_report
import matplotlib.pyplot as plt

# 1. 하이브리드 종목 필터링 (시총 200위 내 + 거래량 100위 내)
def get_hybrid_top_codes():
    print("[1/5] 최신 시장 데이터 기반 우량 대장주 필터링 중...")
    df_krx = fdr.StockListing('KOSPI')
    # 시총 200위 선별
    top_200_marcap = df_krx.sort_values(by='Marcap', ascending=False).head(200)
    # 그 중 거래량 상위 100위 최종 선별
    hybrid_top_100 = top_200_marcap.sort_values(by='Volume', ascending=False).head(100)
    return hybrid_top_100['Code'].tolist()

# 2. 데이터 로드 및 기술적 지표 생성
def load_and_preprocess(codes):
    print(f"[2/5] {len(codes)}개 종목 데이터 가공 및 지표 강화 중...")
    conn = sqlite3.connect('kospi_stock_data.db')
    all_data = []
    
    for code in codes:
        df = pd.read_sql(f"SELECT * FROM daily_stock_quotes WHERE Code = '{code}' ORDER BY Date ASC", conn)
        if len(df) < 150: continue
        
        # --- [기존 지표] ---
        df['Next_Day_Return'] = df['Return'].shift(-1)
        df['Target'] = (df['Next_Day_Return'] > 0.003).astype(int)
        df['Vol_Change'] = df['Volume'].pct_change()
        df['MA_Ratio'] = df['Close'] / (df['MA20'] + 1e-9)
        df['BB_Pos'] = (df['Close'] - df['BBL']) / (df['BBU'] - df['BBL'] + 1e-9)
        
        # --- [새로 추가하는 강화 지표] ---
        # 1. RSI 기울기: 현재 힘이 붙고 있는가?
        df['RSI_Slope'] = df['RSI'].diff() 
        
        # 2. 변동성 비율: 오늘 얼마나 요동쳤는가?
        df['Range_Ratio'] = (df['High'] - df['Low']) / (df['Close'] + 1e-9)
        
        # 3. 거래량 에너기: 최근 5일 평균 대비 오늘 얼마나 터졌는가?
        df['Vol_Momentum'] = df['Volume'] / (df['Volume'].rolling(window=5).mean() + 1e-9)
        
        # 4. 이격도: 5일 이평선과 얼마나 떨어져 있는가? (단기 과열 확인)
        # (DB에 MA5가 없다면 여기서 직접 계산하거나 MA20을 활용하세요)
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['Dist_MA5'] = df['Close'] / (df['MA5'] + 1e-9)

        # 무한대 및 결측치 제거 (지표 계산 후 발생하는 NaN 제거)
        df = df.replace([np.inf, -np.inf], np.nan).dropna()
        all_data.append(df)
    
    conn.close()
    return pd.concat(all_data, axis=0) if all_data else pd.DataFrame()

# 3. 메인 학습 함수
def train_hybrid_xgb():
    # 데이터 준비
    target_codes = get_hybrid_top_codes()
    total_df = load_and_preprocess(target_codes)
    
    if total_df.empty:
        print("[-] 학습할 데이터가 부족합니다. DB 상태를 확인하세요.")
        return

    features = [
        'Return', 'Vol_Change', 'MA_Ratio', 'BB_Pos', 'RSI', 'MACD', 'MACD_Sig',
        'RSI_Slope', 'Range_Ratio', 'Vol_Momentum', 'Dist_MA5'
    ]
    
    # 데이터 분할 (날짜 기준 8:2)
    unique_dates = sorted(total_df['Date'].unique())
    split_date = unique_dates[int(len(unique_dates) * 0.8)]
    
    train_df = total_df[total_df['Date'] < split_date]
    test_df = total_df[total_df['Date'] >= split_date]

    X_train, y_train = train_df[features], train_df['Target']
    X_test, y_test = test_df[features], test_df['Target']

    # 4. XGBoost 모델 설정 (Early Stopping을 생성자에 포함)
    print(f"[3/5] XGBoost 모델 최적화 학습 시작 (데이터: {len(X_train)}건)...")
    model = XGBClassifier(
        n_estimators=2000, 
        learning_rate=0.005,      # 더 천천히, 더 꼼꼼하게 학습 (0.01 -> 0.005)
        max_depth=5,              # 나무의 두뇌 회전 속도를 살짝 올림 (4 -> 5)
        min_child_weight=5,       # 패턴을 더 세밀하게 포착하도록 기준 완화 (10 -> 5)
        gamma=0.1,                # 가지치기 기준을 낮춰 더 많은 시도를 허용 (0.3 -> 0.1)
        subsample=0.8,            # 학습 데이터 활용 비중 상향 (0.7 -> 0.8)
        colsample_bytree=0.8,     # 지표 활용 비중 상향 (0.7 -> 0.8)
        reg_alpha=0.05,           # 규제를 살짝 완화하여 유연성 확보
        reg_lambda=1.2,           # 안정성은 유지
        random_state=42,
        n_jobs=-1,
        early_stopping_rounds=100, # 성능 개선을 기다려주는 시간을 늘림
        eval_metric='logloss'
    )

    # 모델 학습
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)], # 검증 데이터셋 제공
        verbose=50                   # 50번 학습마다 로그 출력
    )

    # 5. 결과 검증 및 저장
    y_pred = model.predict(X_test)
    precision = precision_score(y_test, y_pred)
    
    print("\n" + "="*50)
    print(f"✅ 학습 완료! 최종 검증 정밀도: {precision:.2%}")
    print("="*50)

    # 모델 및 특성 이름 저장
    joblib.dump(model, 'hybrid_xgb_model.pkl')
    joblib.dump(features, 'hybrid_features.pkl')
    print("[5/5] 모델 파일 저장 완료: hybrid_xgb_model.pkl")

    # 지표 중요도 출력
    plt.figure(figsize=(10, 6))
    plt.barh(features, model.feature_importances_)
    plt.title("XGBoost Feature Importance")
    plt.show()

if __name__ == "__main__":
    train_hybrid_xgb()