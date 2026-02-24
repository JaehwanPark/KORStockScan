import sqlite3
import pandas as pd
import numpy as np
import joblib
import requests
import os
import warnings
import json
import logging
import lightgbm as lgb
from datetime import datetime, timedelta
import FinanceDataReader as fdr
import kiwoom_utils

# --- [1. 설정 로드 엔진] ---
def load_config():
    """config.json 파일에서 설정 로드"""
    config_path = 'config.json'
    if not os.path.exists(config_path):
        print(f"❌ {config_path} 파일이 없습니다.")
        return None
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

CONF = load_config()

# --- [2. 시스템 초기 설정] ---
logging.basicConfig(
    filename='ensemble_scanner.log', 
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s', 
    encoding='utf-8'
)

class SilentLogger:
    def info(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass

warnings.filterwarnings('ignore')
lgb.register_logger(SilentLogger())
os.environ['LIGHTGBM_LOG_LEVEL'] = '-1'

# --- [3. DB 인프라 관리] ---
def init_history_db():
    conn = sqlite3.connect(CONF['DB_PATH'])
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(recommendation_history)")
    columns = cursor.fetchall()
    is_pk_set = any(col[5] > 0 for col in columns)
    
    if not columns or not is_pk_set:
        print("⚠️ DB 스키마가 구버전이거나 존재하지 않습니다. 테이블을 신규 생성합니다.")
        cursor.execute("DROP TABLE IF EXISTS recommendation_history")
        cursor.execute("""
            CREATE TABLE recommendation_history (
                date TEXT,
                code TEXT,
                name TEXT,
                buy_price INTEGER,
                type TEXT,
                status TEXT DEFAULT 'WATCHING', 
                buy_qty INTEGER DEFAULT 0,
                PRIMARY KEY (date, code)
            )
        """)
    conn.commit()
    conn.close()

def migrate_db():
    try:
        conn = sqlite3.connect(CONF['DB_PATH'])
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(recommendation_history)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'nxt' not in columns:
            cursor.execute("ALTER TABLE recommendation_history ADD COLUMN nxt REAL")
            print("✅ nxt 컬럼이 성공적으로 추가되었습니다.")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"⚠️ DB 마이그레이션 오류: {e}")

# --- [4. 성과 복기 엔진] ---
def get_performance_report():
    conn = sqlite3.connect(CONF['DB_PATH'])
    try:
        last_date_df = pd.read_sql("SELECT MAX(date) as last_date FROM recommendation_history", conn)
        last_date = last_date_df.iloc[0]['last_date']
        if not last_date: return "📊 신규 가동을 시작합니다.\n"

        history = pd.read_sql(f"SELECT * FROM recommendation_history WHERE date = '{last_date}'", conn)
        report_msg = f"📊 *[전일 성적표 ({last_date})]*\n"
        
        for r_type in ['MAIN', 'RUNNER']:
            subset = history[history['type'] == r_type]
            if subset.empty: continue
            
            profits = []
            for _, row in subset.iterrows():
                try:
                    df = fdr.DataReader(row['code'], start=last_date)
                    if not df.empty:
                        p = (df.iloc[-1]['Close'] / row['buy_price'] - 1) * 100
                        profits.append(p)
                except: continue
            
            if profits:
                win_rate = (len([p for p in profits if p > 0]) / len(profits)) * 100
                avg_p = sum(profits) / len(profits)
                label = "✅ 강력추천" if r_type == 'MAIN' else "🥈 아차상"
                report_msg += f"{label}: 승률 {win_rate:.0f}% / 수익 {avg_p:+.2f}%\n"
        return report_msg + "-"*20 + "\n"
    finally: conn.close()

# --- [5. 메인 스캐너 엔진 업데이트] ---
FEATURES_XGB = ['Return', 'MA_Ratio', 'MACD', 'MACD_Sig', 'VWAP', 'OBV', 'Up_Trend_2D', 'Dist_MA5']
FEATURES_LGBM = ['BB_Pos', 'RSI', 'RSI_Slope', 'Range_Ratio', 'Vol_Momentum', 'Vol_Change', 'ATR', 'BBB', 'BBP']

def run_integrated_scanner():
    print(f"=== KORStockScan v12.1 (Stacking Ensemble + Quality Filter) ===")
    init_history_db()
    migrate_db()

    try:
        m_xgb = joblib.load('hybrid_xgb_model.pkl') 
        m_lgbm = joblib.load('hybrid_lgbm_model.pkl')
        b_xgb = joblib.load('bull_xgb_model.pkl')
        b_lgbm = joblib.load('bull_lgbm_model.pkl')
        meta_model = joblib.load('stacking_meta_model.pkl')
        
        # 🚀 [추가] 코스피 지수의 최근 5일 수익률 계산 (상대강도 비교용)
        kospi_df = fdr.DataReader('KS11', start=(datetime.now() - timedelta(days=20)).strftime('%Y-%m-%d'))
        if len(kospi_df) >= 5:
            kospi_5d_return = (kospi_df['Close'].iloc[-1] / kospi_df['Close'].iloc[-5]) - 1
        else:
            kospi_5d_return = 0

        conn = sqlite3.connect(CONF['DB_PATH'])
        df_krx = fdr.StockListing('KOSPI')
        # 기초 유동성 필터: 시총 상위 200위 중 거래량 150위 (무거운 엉덩이 종목 배제)
        target_list = df_krx.sort_values(by='Marcap', ascending=False).head(200) 
        target_list = target_list.sort_values(by='Volume', ascending=False).head(150).to_dict('records') 
        
        all_results = []

        for stock in target_list:
            code, name = stock['Code'], stock['Name']
            df = pd.read_sql(f"SELECT * FROM daily_stock_quotes WHERE Code='{code}' ORDER BY Date DESC LIMIT 60", conn)
            if len(df) < 30: continue
            
            df = df.sort_values('Date')
            current_price = df.iloc[-1]['Close']
            
            # 🚀 [필터 1] 저가주(동전주) 및 5,000원 미만 잡주 제외
            if current_price < 5000:
                continue
                
            # 🚀 [필터 2] Quality 평가 (상대강도, 정배열, 매물대)
            stock_5d_return = (current_price / df.iloc[-5]['Close']) - 1
            ma5 = df['Close'].rolling(5).mean().iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            high_20d = df['High'].tail(20).max()
            
            cond_rs = stock_5d_return > kospi_5d_return          # 지수보다 강한 놈인가?
            cond_trend = (current_price > ma5) and (ma5 > ma20)  # 단기 추세가 살아있는가? (정배열)
            cond_resist = current_price >= (high_20d * 0.90)     # 매물대(20일 고점) 돌파 직전인가?
            
            # 위 3가지 '진짜 기회' 조건 중 2개 이상 만족하지 못하면 AI 분석도 안 함
            if sum([cond_rs, cond_trend, cond_resist]) < 2:
                continue

            # 지표 가공
            df['Vol_Change'] = df['Volume'].pct_change()
            df['MA_Ratio'] = df['Close'] / (df['MA20'] + 1e-9)
            df['BB_Pos'] = (df['Close'] - df['BBL']) / (df['BBU'] - df['BBL'] + 1e-9)
            df['RSI_Slope'] = df['RSI'].diff()
            df['Range_Ratio'] = (df['High'] - df['Low']) / (df['Close'] + 1e-9)
            df['Vol_Momentum'] = df['Volume'] / (df['Volume'].rolling(5).mean() + 1e-9)
            df['Dist_MA5'] = df['Close'] / (df['MA5'] + 1e-9)
            df['Up_Trend_2D'] = (df['Close'].diff(1) > 0) & (df['Close'].shift(1).diff(1) > 0)
            df['Up_Trend_2D'] = df['Up_Trend_2D'].astype(int)
            
            latest_row = df.iloc[[-1]].replace([np.inf, -np.inf], np.nan).fillna(0)
            
            p_m_x = m_xgb.predict_proba(latest_row[FEATURES_XGB])[0][1]
            p_m_l = m_lgbm.predict_proba(latest_row[FEATURES_LGBM])[0][1]
            p_b_x = b_xgb.predict_proba(latest_row[FEATURES_XGB])[0][1]
            p_b_l = b_lgbm.predict_proba(latest_row[FEATURES_LGBM])[0][1]
            
            meta_input = pd.DataFrame({
                'XGB_Prob': [p_m_x], 'LGBM_Prob': [p_m_l], 
                'Bull_XGB_Prob': [p_b_x], 'Bull_LGBM_Prob': [p_b_l]
            })
            p_final = meta_model.predict_proba(meta_input)[0][1]
            
            all_results.append({
                'Name': name, 
                'Prob': p_final, 
                'Price': int(df.iloc[-1]['Close']), 
                'Code': code
            })

        conn.close()

        msg = get_performance_report() + f"🏆 *[AI 콰트로 Stacking 리포트 (v12.1 정예 선별)]* {datetime.now().strftime('%Y-%m-%d')}\n"

        # 🚀 [필터 3] 문턱 상향 및 모수 제한
        main_picks = sorted([r for r in all_results if r['Prob'] >= 0.82], key=lambda x: x['Prob'], reverse=True)[:3]
        runner_ups = sorted([r for r in all_results if 0.75 <= r['Prob'] < 0.82], key=lambda x: x['Prob'], reverse=True)[:50] # 최대 50개 제한

        if main_picks:
            msg += "🏆 *[AI 강력 추천 종목]*\n"
            conn = sqlite3.connect(CONF['DB_PATH'])
            today = datetime.now().strftime('%Y-%m-%d')
            for r in main_picks:
                buy_p = int(r['Price']) # v12.1은 돌파 매매 성격이 강해 현재가 기준 진입
                msg += f"• *{r['Name']}* ({r['Prob']:.1%})\n"
                
                sql = """
                    INSERT INTO recommendation_history (date, code, name, buy_price, type, status, nxt)
                    VALUES (?, ?, ?, ?, 'MAIN', 'WATCHING', NULL)
                    ON CONFLICT(date, code) DO UPDATE SET
                        buy_price = excluded.buy_price,
                        type = excluded.type
                """
                conn.execute(sql, (today, r['Code'], r['Name'], buy_p))
            conn.commit(); conn.close()
        else:
            msg += "\n🧐 현재 기준을 통과한 강력 추천 종목이 없습니다.\n"

        if runner_ups:
            msg += "\n🥈 *[아차상: 정예 관심 종목 상위 10개]*\n"
            for r in runner_ups[:10]:
                msg += f"• {r['Name']} ({r['Prob']:.1%})\n"
            
            conn = sqlite3.connect(CONF['DB_PATH'])
            today = datetime.now().strftime('%Y-%m-%d')
            for r in runner_ups:
                buy_p = int(r['Price'])
                sql = """
                    INSERT INTO recommendation_history (date, code, name, buy_price, type, status, nxt)
                    VALUES (?, ?, ?, ?, 'RUNNER', 'WATCHING', NULL)
                    ON CONFLICT(date, code) DO UPDATE SET
                        buy_price = excluded.buy_price,
                        type = excluded.type
                """
                conn.execute(sql, (today, r['Code'], r['Name'], buy_p))
            conn.commit(); conn.close()

        for cid in CONF['CHAT_IDS']:
            requests.post(f"https://api.telegram.org/bot{CONF['TELEGRAM_TOKEN']}/sendMessage", data={"chat_id": cid, "text": msg, "parse_mode": "Markdown"})

    except Exception as e:
        print(f"❌ 시스템 에러: {e}")

if __name__ == "__main__":
    run_integrated_scanner()