import os
import sqlite3
import pandas as pd
import numpy as np
from itertools import product
from tqdm import tqdm

# --- 경로 설정 ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..', 'data'))
DB_PATH = os.path.join(DATA_DIR, 'kospi_stock_data.db')
PRED_PATH = os.path.join(DATA_DIR, 'ai_predictions.csv')

INITIAL_CAPITAL = 10_000_000
MAX_POSITIONS = 5
INVEST_PER_TRADE = 0.20


def load_data():
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT Date, Code, Name, Open, High, Low, Close, Volume, MA20, MA60, Foreign_Net, Inst_Net FROM daily_stock_quotes ORDER BY Date ASC"
    df = pd.read_sql(query, conn)
    conn.close()

    df['Date'] = pd.to_datetime(df['Date'])
    df_pred = pd.read_csv(PRED_PATH)
    df_pred['Date'] = pd.to_datetime(df_pred['Date'])

    return pd.merge(df, df_pred[['Date', 'Code', 'Stacking_Prob']], on=['Date', 'Code'], how='inner')


def run_simulation(df, dates, prob_th, trail_trigger, trail_drop, sl_bull):
    cash = INITIAL_CAPITAL
    portfolio = {}
    history = []

    sl_bear = sl_bull - 0.005  # 하락장은 상승장보다 0.5% 더 타이트하게 손절

    for current_date in dates:
        daily_data = df[df['Date'] == current_date].set_index('Code')

        # 1. 매도 로직
        sold_codes = []
        for code, pos in portfolio.items():
            if code not in daily_data.index: continue

            today = daily_data.loc[code]
            pos['days'] += 1
            pos['max_price'] = max(pos['max_price'], today['High'])

            sell_price = 0

            # (1) 트레일링 익절
            if pos['max_price'] >= pos['buy_price'] * trail_trigger:
                trailing_stop_price = pos['max_price'] * (1.0 - trail_drop)
                if today['Low'] <= trailing_stop_price:
                    sell_price = trailing_stop_price

            # (2) 손절
            if not sell_price:
                stop_loss_rate = sl_bull if pos['regime'] == 'BULL' else sl_bear
                stop_price = pos['buy_price'] * stop_loss_rate
                if today['Low'] <= stop_price:
                    sell_price = stop_price

            # (3) 3일 시간 청산
            if not sell_price and pos['days'] >= 3:
                sell_price = today['Close']

            # 갭하락 보정
            if sell_price > 0 and today['Open'] < sell_price and pos['days'] < 3:
                sell_price = today['Open']

            if sell_price > 0:
                revenue = sell_price * pos['qty']
                fee_tax = revenue * 0.0023
                cash += (revenue - fee_tax)
                profit_rate = ((revenue - fee_tax) - (pos['buy_price'] * pos['qty'])) / (
                            pos['buy_price'] * pos['qty']) * 100
                history.append(profit_rate)
                sold_codes.append(code)

        for code in sold_codes:
            del portfolio[code]

        # 2. 총 자산 평가
        stock_value = sum(
            [daily_data.loc[c, 'Close'] * p['qty'] if c in daily_data.index else p['buy_price'] * p['qty'] for c, p in
             portfolio.items()])
        total_asset = cash + stock_value

        # 3. 신규 매수
        available_slots = MAX_POSITIONS - len(portfolio)
        if available_slots > 0:
            buy_candidates = daily_data[
                (~daily_data.index.isin(portfolio.keys())) &
                (daily_data['Stacking_Prob'] >= prob_th) &
                (daily_data['Close'] > daily_data['MA20']) &
                ((daily_data['Foreign_Net'] > 0) | (daily_data['Inst_Net'] > 0))
                ].sort_values(by='Stacking_Prob', ascending=False)

            for code, row in buy_candidates.head(available_slots).iterrows():
                invest_amount = total_asset * INVEST_PER_TRADE
                if cash >= invest_amount:
                    buy_price = row['Close']
                    qty = int(invest_amount // buy_price)
                    if qty > 0:
                        regime = 'BULL' if row['MA20'] > row['MA60'] else 'BEAR'
                        portfolio[code] = {'buy_price': buy_price, 'qty': qty, 'max_price': buy_price, 'days': 0,
                                           'regime': regime}
                        cash -= (buy_price * qty)

    # 잔존 주식 가치 합산
    final_stock_value = sum([p['qty'] * p['buy_price'] for p in portfolio.values()])
    final_total_asset = cash + final_stock_value

    roi = (final_total_asset - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100
    win_rate = sum(1 for p in history if p > 0) / len(history) * 100 if history else 0
    avg_profit = sum(history) / len(history) if history else 0

    return roi, win_rate, len(history), avg_profit


def main():
    print("📥 데이터 로드 중...")
    df = load_data()
    dates = sorted(df['Date'].unique())

    # 🎯 테스트할 파라미터 조합 설정
    # 1. AI 진입 임계값: 60%, 65%, 70%
    prob_thresholds = [0.60, 0.65, 0.70]

    # 2. 방어선(트레일링 스탑) 가동 조건: +3.5%, +4.0%, +5.0% 상승 시
    trail_triggers = [1.035, 1.040, 1.050]

    # 3. 고점 대비 하락 익절 폭: -1.5%, -2.0% (조금 더 넉넉하게 견디기)
    trail_drops = [0.015, 0.020]

    # 4. 기본 손절선: -3.0%, -4.0%
    sl_bulls = [0.970, 0.960]

    combinations = list(product(prob_thresholds, trail_triggers, trail_drops, sl_bulls))
    print(f"🚀 총 {len(combinations)}가지 전략의 시뮬레이션을 시작합니다. (약 1~2분 소요)")

    results = []
    for prob, t_trig, t_drop, sl in tqdm(combinations):
        roi, win_rate, trades, avg_profit = run_simulation(df, dates, prob, t_trig, t_drop, sl)
        results.append({
            '진입확률': f"{prob:.2f}",
            '트레일링가동': f"{(t_trig - 1) * 100:.1f}%",
            '고점대비익절': f"-{t_drop * 100:.1f}%",
            '기본손절': f"-{(1 - sl) * 100:.1f}%",
            '수익률(%)': round(roi, 2),
            '승률(%)': round(win_rate, 2),
            '매매횟수': trades,
            '평균손익(%)': round(avg_profit, 2)
        })

    df_results = pd.DataFrame(results)
    df_results = df_results.sort_values(by='수익률(%)', ascending=False).reset_index(drop=True)

    print("\n" + "=" * 70)
    print("🏆 [최적화 완료] 가장 수익률이 높은 TOP 5 매매 전략")
    print("=" * 70)
    print(df_results.head(5).to_string(index=False))


if __name__ == "__main__":
    main()