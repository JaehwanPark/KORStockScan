import os
import pandas as pd
import numpy as np
from itertools import product
from tqdm import tqdm
from sqlalchemy import create_engine, text
import warnings

warnings.filterwarnings('ignore')

# --- 경로 설정 ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..'))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
PRED_PATH = os.path.join(DATA_DIR, 'ai_predictions.csv')

# 🎯 PostgreSQL 연결 설정
DB_URL = os.getenv("DATABASE_URL", "postgresql://quant_admin:quant_password_123!@localhost:5432/korstockscan")
engine = create_engine(DB_URL)

INITIAL_CAPITAL = 10_000_000
MAX_POSITIONS = 5
INVEST_PER_TRADE = 0.20


def load_data():
    cols = "quote_date, stock_code, stock_name, open_price, high_price, low_price, close_price, volume, ma20, ma60"
    query = f"SELECT {cols} FROM daily_stock_quotes ORDER BY quote_date ASC"
    
    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)

    rename_map = {
        'quote_date': 'Date', 'stock_code': 'Code', 'stock_name': 'Name',
        'open_price': 'Open', 'high_price': 'High', 'low_price': 'Low', 'close_price': 'Close',
        'volume': 'Volume', 'ma20': 'MA20', 'ma60': 'MA60'
    }
    df.rename(columns=rename_map, inplace=True)
    
    df['Date'] = pd.to_datetime(df['Date']).dt.normalize()
    df['Code'] = df['Code'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.zfill(6)
    
    df_pred = pd.read_csv(PRED_PATH)
    df_pred['Date'] = pd.to_datetime(df_pred['Date']).dt.normalize()
    df_pred['Code'] = df_pred['Code'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.zfill(6)

    min_date = df_pred['Date'].min()
    df = df[df['Date'] >= min_date].copy()
    
    df_merged = pd.merge(df, df_pred[['Date', 'Code', 'Stacking_Prob']], on=['Date', 'Code'], how='left')
    df_merged['Stacking_Prob'] = df_merged['Stacking_Prob'].fillna(0)
    
    return df_merged


def run_simulation(df, dates, prob_th, tp_rate, sl_bull):
    cash = INITIAL_CAPITAL
    portfolio = {}
    history = []

    sl_bear = sl_bull - 0.005  # 하락장은 손절선 0.5% 더 타이트하게

    # 💡 일자별 순회 (T+1 매수를 위해 i 인덱스 사용)
    for i in range(1, len(dates)):
        today_date = dates[i]
        yesterday_date = dates[i-1] # 어제(시그널 발생일)
        
        today_data = df[df['Date'] == today_date].set_index('Code')
        yesterday_data = df[df['Date'] == yesterday_date].set_index('Code')

        # 1. 매도 로직 (오늘 장중 가격 기준)
        sold_codes = []
        for code, pos in list(portfolio.items()):
            if code not in today_data.index: continue

            today = today_data.loc[code]
            pos['days'] += 1
            sell_price = 0
            sell_reason = ""

            # (1) 목표가 익절 (고정 Take Profit)
            tp_price = pos['buy_price'] * (1.0 + tp_rate)
            if today['High'] >= tp_price:
                sell_price = tp_price
                sell_reason = "TP"

            # (2) 손절 (Stop Loss) - 당일 장중 휩소 감안
            stop_loss_rate = sl_bull if pos['regime'] == 'BULL' else sl_bear
            sl_price = pos['buy_price'] * stop_loss_rate
            
            if not sell_price and today['Low'] <= sl_price:
                sell_price = sl_price
                sell_reason = "SL"

            # (3) 3일 시간 청산 (Time Stop)
            if not sell_price and pos['days'] >= 3:
                sell_price = today['Close']
                sell_reason = "TIME"

            # 💡 갭 보정: 시가가 이미 목표가/손절가를 훌쩍 넘어서 시작한 경우
            if sell_price > 0:
                if sell_reason == "TP" and today['Open'] > sell_price:
                    sell_price = today['Open']
                elif sell_reason == "SL" and today['Open'] < sell_price:
                    sell_price = today['Open']

            # 매도 실행
            if sell_price > 0:
                revenue = sell_price * pos['qty']
                fee_tax = revenue * 0.0023  # 수수료 0.23% 적용
                cash += (revenue - fee_tax)
                
                profit_rate = ((revenue - fee_tax) - (pos['buy_price'] * pos['qty'])) / (pos['buy_price'] * pos['qty']) * 100
                history.append(profit_rate)
                sold_codes.append(code)

        # 매도된 종목 포트폴리오에서 제거
        for code in sold_codes:
            del portfolio[code]

        # 2. 총 자산 평가 (현재 자금 + 보유 주식 평가금)
        stock_value = sum([today_data.loc[c, 'Close'] * p['qty'] if c in today_data.index else p['buy_price'] * p['qty'] for c, p in portfolio.items()])
        total_asset = cash + stock_value

        # 3. 신규 매수 (💡 어제 발생한 시그널을 바탕으로, 오늘 아침 시가(Open)에 매수)
        available_slots = MAX_POSITIONS - len(portfolio)
        if available_slots > 0:
            
            # 어제 자 데이터 기준 AI 시그널 확인
            buy_candidates = yesterday_data[
                (~yesterday_data.index.isin(portfolio.keys())) &
                (yesterday_data['Stacking_Prob'] >= prob_th)
            ].sort_values(by='Stacking_Prob', ascending=False)

            for code, row in buy_candidates.head(available_slots).iterrows():
                if code in today_data.index: # 오늘 거래되는 주식만
                    invest_amount = total_asset * INVEST_PER_TRADE
                    if cash >= invest_amount:
                        buy_price = today_data.loc[code, 'Open'] # 💡 오늘 시가에 체결!
                        if buy_price == 0: continue
                        
                        qty = int(invest_amount // buy_price)
                        if qty > 0:
                            regime = 'BULL' if row['MA20'] > row['MA60'] else 'BEAR'
                            portfolio[code] = {
                                'buy_price': buy_price, 
                                'qty': qty, 
                                'days': 0,
                                'regime': regime
                            }
                            cash -= (buy_price * qty)

    # 최종 잔존 가치 합산
    final_stock_value = sum([p['qty'] * p['buy_price'] for p in portfolio.values()])
    final_total_asset = cash + final_stock_value

    roi = (final_total_asset - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100
    win_rate = sum(1 for p in history if p > 0) / len(history) * 100 if history else 0
    avg_profit = sum(history) / len(history) if history else 0

    return roi, win_rate, len(history), avg_profit


def main():
    print("📥 데이터 로드 및 전처리 중...")
    df = load_data()
    dates = sorted(df['Date'].unique())

    # 🎯 실전 단기 스윙 파라미터 조합 설정
    # prob_thresholds = [0.65, 0.70]          # 진입 임계값
    prob_thresholds = [0.52, 0.54, 0.56, 0.58, 0.60]
    tp_rates = [0.040, 0.045, 0.050]        # 익절선 (+4.0%, +4.5%, +5.0%)
    sl_bulls = [0.975, 0.970, 0.965]        # 기본 손절선 (-2.5%, -3.0%, -3.5%)

    combinations = list(product(prob_thresholds, tp_rates, sl_bulls))
    print(f"🚀 총 {len(combinations)}가지 고정 익절/손절 전략 시뮬레이션 시작! (현실 반영 100%)")

    results = []
    for prob, tp, sl in tqdm(combinations):
        roi, win_rate, trades, avg_profit = run_simulation(df, dates, prob, tp, sl)
        results.append({
            '진입확률': f"{prob:.2f}",
            '목표익절': f"+{tp * 100:.1f}%",
            '기본손절': f"-{(1 - sl) * 100:.1f}%",
            '수익률(%)': round(roi, 2),
            '승률(%)': round(win_rate, 2),
            '매매횟수': trades,
            '건당손익(%)': round(avg_profit, 2)
        })

    df_results = pd.DataFrame(results)
    df_results = df_results.sort_values(by='수익률(%)', ascending=False).reset_index(drop=True)

    print("\n" + "=" * 70)
    print("🏆 [최적화 완료] 가장 수익을 많이 낸 TOP 5 실전 매매 전략")
    print("=" * 70)
    print(df_results.head(5).to_string(index=False))


if __name__ == "__main__":
    main()