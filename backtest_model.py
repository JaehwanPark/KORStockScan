import sqlite3
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_score
import matplotlib.pyplot as plt

def run_flexible_backtest(stock_code):
    conn = sqlite3.connect('kospi_stock_data.db')
    df = pd.read_sql(f"SELECT * FROM daily_stock_quotes WHERE Code = '{stock_code}' ORDER BY Date ASC", conn)
    conn.close()

    if df.empty: return

    # 타겟: 0.3%로 약간 완화 (신호가 너무 안 나올 경우를 대비)
    df['Next_Day_Return'] = df['Return'].shift(-1)
    df['Target'] = (df['Next_Day_Return'] > 0.003).astype(int)
    df['Vol_Change'] = df['Volume'].pct_change()
    
    features = ['Open', 'High', 'Low', 'Close', 'Volume', 'Vol_Change',
                'MA5', 'MA20', 'MA60', 'RSI', 'MACD', 'BBL', 'BBU']
    
    df_clean = df.dropna().iloc[:-1]
    split_idx = int(len(df_clean) * 0.8)
    train_df = df_clean.iloc[:split_idx]
    test_df = df_clean.iloc[split_idx:].copy()

    # 모델 규제 완화
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=6,             # 깊이를 조금 더 낮춰 일반화 유도
        min_samples_leaf=5,      # 리프 노드 기준 완화 (신호 생성 유도)
        class_weight='balanced', # [중요] 상승/하락 데이터 불균형 해결
        random_state=42
    )
    model.fit(train_df[features], train_df['Target'])

    # --- [개선 포인트] 단순 predict 대신 확률(predict_proba) 사용 ---
    # 상승(1)할 확률이 50% 이상이면 신호 발생
    probabilities = model.predict_proba(test_df[features])[:, 1]
    test_df['Prob'] = probabilities
    
    # 만약 확률이 너무 낮게 형성된다면, 상위 20% 지점을 문턱값(Threshold)으로 설정
    threshold = np.percentile(probabilities, 80) 
    test_df['Signal'] = (test_df['Prob'] >= threshold).astype(int)

    # 수익률 계산
    test_df['Strategy_Return'] = test_df['Signal'] * test_df['Next_Day_Return']
    test_df['Cum_Strategy'] = (1 + test_df['Strategy_Return'].fillna(0)).cumprod()
    test_df['Cum_Market'] = (1 + test_df['Next_Day_Return'].fillna(0)).cumprod()

    print(f"\n--- {stock_code} 신호 생성 모델 결과 ---")
    print(f"매수 신호 횟수: {test_df['Signal'].sum()}회 / 전체 {len(test_df)}일")
    
    if test_df['Signal'].sum() > 0:
        print(f"정밀도(Precision): {precision_score(y_true=test_df['Target'], y_pred=test_df['Signal']):.2%}")
    else:
        print("여전히 매수 신호가 생성되지 않았습니다. 데이터를 더 늘려야 합니다.")

    test_df.plot(x='Date', y=['Cum_Strategy', 'Cum_Market'], title=f"Flexible Model: {stock_code}")
    plt.show()

if __name__ == "__main__":
    run_improved_backtest = run_flexible_backtest # 함수 교체
    run_improved_backtest('005930')