import os
import sqlite3
import pandas as pd
import numpy as np
from tqdm import tqdm

# --- 경로 설정 ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..', 'data'))
DB_PATH = os.path.join(DATA_DIR, 'kospi_stock_data.db')
PRED_PATH = os.path.join(DATA_DIR, 'ai_predictions.csv')

# --- 백테스트 설정 ---
INITIAL_CAPITAL = 10_000_000  # 1천만 원
MAX_POSITIONS = 5  # 최대 5종목
INVEST_PER_TRADE = 0.20  # 총 자산의 20%씩 베팅 (복리 적용)
PROB_THRESHOLD = 0.70  # AI 확신도 70% 이상


def load_data_for_backtest():
    print("📥 DB 과거 데이터와 AI 예측값(CSV)을 융합합니다...")

    conn = sqlite3.connect(DB_PATH)
    query = """
            SELECT Date, Code, Name, Open, High, Low, Close, Volume, MA20, MA60, Foreign_Net, Inst_Net
            FROM daily_stock_quotes
            ORDER BY Date ASC \
            """
    df = pd.read_sql(query, conn)
    conn.close()
    df['Date'] = pd.to_datetime(df['Date'])

    if not os.path.exists(PRED_PATH):
        raise FileNotFoundError(f"❌ AI 예측 파일이 없습니다: {PRED_PATH}")

    df_pred = pd.read_csv(PRED_PATH)
    df_pred['Date'] = pd.to_datetime(df_pred['Date'])

    # Date와 Code 기준으로 완벽 병합
    df_merged = pd.merge(df, df_pred[['Date', 'Code', 'Stacking_Prob']], on=['Date', 'Code'], how='inner')
    return df_merged


def run_backtest():
    try:
        df = load_data_for_backtest()
    except Exception as e:
        print(e)
        return

    dates = sorted(df['Date'].unique())

    cash = INITIAL_CAPITAL
    portfolio = {}  # {code: {'buy_price', 'qty', 'max_price', 'days', 'name', 'regime'}}
    history = []

    print(f"🚀 스윙 백테스트 V3.1 시작 (기간: {dates[0].strftime('%Y-%m-%d')} ~ {dates[-1].strftime('%Y-%m-%d')})")

    for i, current_date in enumerate(tqdm(dates)):
        daily_data = df[df['Date'] == current_date].set_index('Code')

        # ==========================================
        # 1. 보유 종목 매도 (청산)
        # ==========================================
        sold_codes = []
        for code, pos in portfolio.items():
            if code not in daily_data.index: continue

            today = daily_data.loc[code]
            pos['days'] += 1
            pos['max_price'] = max(pos['max_price'], today['High'])

            sell_price = 0
            sell_reason = ""

            # (1) 트레일링 스탑 (수익 보존)
            if pos['max_price'] >= pos['buy_price'] * 1.035:
                trailing_stop_price = pos['max_price'] * 0.985
                if today['Low'] <= trailing_stop_price:
                    sell_price = trailing_stop_price
                    sell_reason = "트레일링 익절"

            # (2) 장세 맞춤 손절 (-3.0% / -2.5%)
            if not sell_price:
                stop_loss_rate = 0.970 if pos['regime'] == 'BULL' else 0.975
                stop_price = pos['buy_price'] * stop_loss_rate
                if today['Low'] <= stop_price:
                    sell_price = stop_price
                    sell_reason = "손절"

            # (3) 3일 시간 청산
            if not sell_price and pos['days'] >= 3:
                sell_price = today['Close']
                sell_reason = "3일 시간청산"

            # 오버나잇 갭하락 현실 반영
            if sell_price > 0 and today['Open'] < sell_price and sell_reason != "3일 시간청산":
                sell_price = today['Open']

            # 매도 정산
            if sell_price > 0:
                revenue = sell_price * pos['qty']
                fee_tax = revenue * 0.0023  # 세금+수수료
                net_revenue = revenue - fee_tax

                profit = net_revenue - (pos['buy_price'] * pos['qty'])
                profit_rate = (profit / (pos['buy_price'] * pos['qty'])) * 100

                cash += net_revenue
                sold_codes.append(code)

                history.append({
                    'Sell_Date': current_date.strftime('%Y-%m-%d'),
                    'Name': pos['name'], 'Buy_Price': pos['buy_price'], 'Sell_Price': sell_price,
                    'Hold_Days': pos['days'], 'Reason': sell_reason, 'Profit_Rate': round(profit_rate, 2)
                })

        for code in sold_codes:
            del portfolio[code]

        # ==========================================
        # 2. 당일 총 자산(Total Asset) 평가
        # ==========================================
        stock_value = 0
        for code, pos in portfolio.items():
            if code in daily_data.index:
                stock_value += daily_data.loc[code, 'Close'] * pos['qty']
            else:
                stock_value += pos['buy_price'] * pos['qty']

        total_asset = cash + stock_value

        # ==========================================
        # 3. 신규 매수 (종가 베팅)
        # ==========================================
        available_slots = MAX_POSITIONS - len(portfolio)
        if available_slots > 0:
            # 💡 [핵심 버그 수정] 이미 들고 있는 종목(~isin)은 매수 후보에서 완전히 제외시킵니다!
            buy_candidates = daily_data[
                (~daily_data.index.isin(portfolio.keys())) &
                (daily_data['Stacking_Prob'] >= PROB_THRESHOLD) &
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
                        portfolio[code] = {
                            'buy_price': buy_price, 'qty': qty, 'max_price': buy_price,
                            'days': 0, 'name': row['Name'], 'regime': regime
                        }
                        cash -= (buy_price * qty)

    # ==========================================
    # 4. 마지막 날 미청산 종목 강제 환산
    # ==========================================
    # 마지막 날 들고 있는 주식은 그날의 종가로 가치 평가
    final_stock_value = 0
    if len(dates) > 0:
        last_date = dates[-1]
        last_daily_data = df[df['Date'] == last_date].set_index('Code')
        for code, pos in portfolio.items():
            if code in last_daily_data.index:
                final_stock_value += last_daily_data.loc[code, 'Close'] * pos['qty']
            else:
                final_stock_value += pos['buy_price'] * pos['qty']

    final_total_asset = cash + final_stock_value

    # ==========================================
    # 5. 결과 리포트
    # ==========================================
    df_hist = pd.DataFrame(history)
    print("\n" + "=" * 50)
    print("📊 [KORStockScan V3.1] 3일 스윙 정밀 백테스트 결과")
    print("=" * 50)

    if df_hist.empty:
        print("조건을 만족하는 매매 내역이 없습니다.")
        return

    win_rate = len(df_hist[df_hist['Profit_Rate'] > 0]) / len(df_hist) * 100
    avg_profit = df_hist['Profit_Rate'].mean()

    print(f"🔹 최종 총 자산(현금+주식): {final_total_asset:,.0f} 원 (초기: {INITIAL_CAPITAL:,.0f} 원)")
    print(f"🔹 누적 수익률: {((final_total_asset - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100):.2f}%")
    print(f"🔹 총 거래 횟수: {len(df_hist)} 회 (현재 보유 중: {len(portfolio)} 종목)")
    print(f"🔹 승률 (Win Rate): {win_rate:.2f}%")
    print(f"🔹 1회 평균 손익률: {avg_profit:.2f}%")
    print("\n💡 [매도 사유별 통계]")
    print(df_hist['Reason'].value_counts())

    result_path = os.path.join(DATA_DIR, 'backtest_swing_result.xlsx')
    df_hist.to_excel(result_path, index=False)
    print(f"\n📂 상세 거래 내역이 저장되었습니다: {result_path}")


if __name__ == "__main__":
    run_backtest()