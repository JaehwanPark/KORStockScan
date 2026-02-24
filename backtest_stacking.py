import sqlite3
import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import FinanceDataReader as fdr

def generate_features(df):
    df = df.copy()
    df['Vol_Change'] = df['Volume'].pct_change()
    df['MA_Ratio'] = df['Close'] / (df['MA20'] + 1e-9)
    df['BB_Pos'] = (df['Close'] - df['BBL']) / (df['BBU'] - df['BBL'] + 1e-9)
    df['RSI_Slope'] = df['RSI'].diff()
    df['Range_Ratio'] = (df['High'] - df['Low']) / (df['Close'] + 1e-9)
    df['Vol_Momentum'] = df['Volume'] / (df['Volume'].rolling(5).mean() + 1e-9)
    df['Dist_MA5'] = df['Close'] / (df['MA5'] + 1e-9)
    df['Up_Trend_2D'] = (df['Close'].diff(1) > 0) & (df['Close'].shift(1).diff(1) > 0)
    df['Up_Trend_2D'] = df['Up_Trend_2D'].astype(int)
    return df

def run_backtest():
    print("🚀 [1/4] 데이터 로드 및 v12.1 앙상블 모델 불러오기...")
    conn = sqlite3.connect('kospi_stock_data.db')
    query = "SELECT * FROM daily_stock_quotes WHERE Date >= '2025-08-01' ORDER BY Date ASC"
    raw_df = pd.read_sql(query, conn)
    conn.close()

    m_xgb = joblib.load('hybrid_xgb_model.pkl')
    m_lgbm = joblib.load('hybrid_lgbm_model.pkl')
    b_xgb = joblib.load('bull_xgb_model.pkl')
    b_lgbm = joblib.load('bull_lgbm_model.pkl')
    meta_model = joblib.load('stacking_meta_model.pkl')

    features_xgb = ['Return', 'MA_Ratio', 'MACD', 'MACD_Sig', 'VWAP', 'OBV', 'Up_Trend_2D', 'Dist_MA5']
    features_lgbm = ['BB_Pos', 'RSI', 'RSI_Slope', 'Range_Ratio', 'Vol_Momentum', 'Vol_Change', 'ATR', 'BBB', 'BBP']

    kospi = fdr.DataReader('KS11', '2025-07-01')
    kospi['MA5'] = kospi['Close'].rolling(5).mean()

    print("🚀 [2/4] 종목별 시뮬레이션 시작...")
    all_trades = []
    
    for code in raw_df['Code'].unique():
        df = raw_df[raw_df['Code'] == code].copy().sort_values('Date')
        if len(df) < 40: continue
        
        df = generate_features(df)
        
        # 1. 모델 예측
        p_m_x = m_xgb.predict_proba(df[features_xgb])[:, 1]
        p_m_l = m_lgbm.predict_proba(df[features_lgbm])[:, 1]
        p_b_x = b_xgb.predict_proba(df[features_xgb])[:, 1]
        p_b_l = b_lgbm.predict_proba(df[features_lgbm])[:, 1]

        meta_input = pd.DataFrame({
            'XGB_Prob': p_m_x, 'LGBM_Prob': p_m_l, 
            'Bull_XGB_Prob': p_b_x, 'Bull_LGBM_Prob': p_b_l
        })
        
        # 2. 메타 모델의 최종 확신도 도출
        df['Final_Prob'] = meta_model.predict_proba(meta_input)[:, 1]
        df['Disparity'] = df['Close'] / (df['MA20'] + 1e-9)

        # 3. 익일 데이터 (미래 참조 방지)
        df['Next_Open'] = df['Open'].shift(-1)
        df['Next_High'] = df['High'].shift(-1)
        df['Next_Low'] = df['Low'].shift(-1)
        df['Next_Close'] = df['Close'].shift(-1)
        df = df.dropna(subset=['Next_Open', 'Next_High', 'Next_Low', 'Next_Close']) 

        # 4. 신호 필터링: 메타 확신도 0.75 이상 + 이격도 5% 이내 과열 방지
        signals = df[(df['Final_Prob'] >= 0.75) & (df['Disparity'] <= 1.05)]

        for _, sig in signals.iterrows():
            # [필터] 코스피 지수가 5일선 위에 있을 때만 진입 (하락장 방어)
            curr_date = sig['Date']
            if curr_date not in kospi.index or kospi.loc[curr_date, 'Close'] < kospi.loc[curr_date, 'MA5']:
                continue

            # 🚀 [v12.1 스나이퍼 매매 로직]
            entry_p = sig['Next_Open']
            target_p = entry_p * 1.020  # 익절 +2.0%
            stop_p = entry_p * 0.975    # 손절 -2.5%

            # 보수적 판정: 고가가 목표가에 닿았더라도, 저가가 손절가에 먼저 닿았다고 가정 (최악의 시나리오 기준)
            if sig['Next_Low'] <= stop_p:
                profit = -2.5
            elif sig['Next_High'] >= target_p:
                profit = 2.0
            else:
                profit = (sig['Next_Close'] / entry_p - 1) * 100
            
            # 수수료/세금/슬리피지 0.25% 일괄 차감
            all_trades.append({'Date': sig['Date'], 'Profit': profit - 0.25})

    print("🚀 [4/4] 결과 분석 중...")
    res_df = pd.DataFrame(all_trades)
    if res_df.empty:
        print("⚠️ 포착된 신호가 없습니다. (장이 너무 안 좋았거나 기준이 높음)")
        return

    res_df['Date'] = pd.to_datetime(res_df['Date'])
    res_df = res_df.sort_values('Date')
    res_df['Cum_Profit'] = res_df['Profit'].cumsum()

    win_rate = (res_df['Profit'] > 0).mean() * 100
    mdd = (res_df['Cum_Profit'].cummax() - res_df['Cum_Profit']).max()
    avg_profit = res_df['Profit'].mean()

    print("\n" + "="*45)
    print(f"📊 v12.1 스태킹 스나이퍼 백테스트 (2025-08~)")
    print(f" - 총 매매 횟수: {len(res_df)}회")
    print(f" - 승률 (Win Rate): {win_rate:.2f}%")
    print(f" - 누적 수익률: {res_df['Profit'].sum():.2f}%")
    print(f" - 회당 평균 수익: {avg_profit:.2f}%")
    print(f" - 최대 낙폭 (MDD): {mdd:.2f}%")
    print("="*45)

    plt.figure(figsize=(10, 5))
    plt.plot(res_df['Date'], res_df['Cum_Profit'], label='Cumulative Profit (%)', color='blue')
    plt.title('v12.1 Stacking Sniper Backtest')
    plt.grid(True)
    plt.legend()
    plt.show()

if __name__ == "__main__":
    run_backtest()