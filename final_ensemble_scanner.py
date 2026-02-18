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
from datetime import datetime
import FinanceDataReader as fdr

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
    
    # 1. 기존 테이블 정보 확인
    cursor.execute("PRAGMA table_info(recommendation_history)")
    columns = cursor.fetchall()
    
    # 2. 만약 테이블이 없거나, PK 설정이 제대로 안 되어 있다면 재생성
    # (단순히 존재 여부만 체크하는게 아니라 PK가 있는지 확인하는 로직)
    is_pk_set = any(col[5] > 0 for col in columns) # 5번째 인덱스가 PK 여부
    
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
                PRIMARY KEY (date, code)
            )
        """)
    
    conn.commit()
    conn.close()

# --- [4. 성과 복기 및 매도 엔진] ---

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

def get_sell_signals():
    conn = sqlite3.connect(CONF['DB_PATH'])
    try:
        history = pd.read_sql("SELECT * FROM recommendation_history WHERE status='HOLDING' AND type='MAIN'", conn)
        if history.empty: return ""
        sell_items = []
        for _, row in history.iterrows():
            try:
                df = fdr.DataReader(row['code']).tail(5)
                if df.empty: continue
                curr_p = df.iloc[-1]['Close']
                profit = (curr_p / row['buy_price'] - 1) * 100
                ma5 = df['Close'].rolling(5).mean().iloc[-1]
                
                reason = ""
                if profit >= 7.0: reason = "🎯 익절"
                elif profit <= -3.5: reason = "🛑 손절"
                elif curr_p < ma5 * 0.98: reason = "⚠️ 추세이탈"
                if reason: sell_items.append(f"• {row['name']}: {reason}({profit:+.1f}%)")
            except: continue
        return "📢 *[보유종목 매도신호]*\n" + "\n".join(sell_items) + "\n" + "-"*20 + "\n" if sell_items else ""
    finally: conn.close()

# --- [5. 메인 스캐너 엔진] ---

def run_integrated_scanner():
    print(f"=== 콰트로 v10.0 ===")
    init_history_db()

    try:
        # 모델 로드
        m_xgb = joblib.load('hybrid_xgb_model.pkl'); m_lgbm = joblib.load('hybrid_lgbm_model.pkl')
        b_xgb = joblib.load('bull_xgb_model.pkl'); b_lgbm = joblib.load('bull_lgbm_model.pkl')
        features = joblib.load('hybrid_features.pkl')
        
        conn = sqlite3.connect(CONF['DB_PATH'])
        df_krx = fdr.StockListing('KOSPI')
        target_list = df_krx.sort_values(by='Marcap', ascending=False).head(200)
        target_list = target_list.sort_values(by='Volume', ascending=False).head(100).to_dict('records')
        
        all_results = []

        for stock in target_list:
            code, name = stock['Code'], stock['Name']
            df = pd.read_sql(f"SELECT * FROM daily_stock_quotes WHERE Code='{code}' ORDER BY Date DESC LIMIT 30", conn)
            if len(df) < 20: continue
            
            df = df.sort_values('Date')
            # 지표 가공
            df['Vol_Change'] = df['Volume'].pct_change(); df['MA_Ratio'] = df['Close'] / (df['MA20'] + 1e-9)
            df['BB_Pos'] = (df['Close'] - df['BBL']) / (df['BBU'] - df['BBL'] + 1e-9); df['RSI_Slope'] = df['RSI'].diff()
            df['Range_Ratio'] = (df['High'] - df['Low']) / (df['Close'] + 1e-9); df['Vol_Momentum'] = df['Volume'] / (df['Volume'].rolling(5).mean() + 1e-9)
            df['MA5'] = df['Close'].rolling(5).mean(); df['Dist_MA5'] = df['Close'] / (df['MA5'] + 1e-9)
            
            X_input = df.iloc[[-1]][features].replace([np.inf, -np.inf], np.nan).fillna(0)
            
            p_m_x = m_xgb.predict_proba(X_input)[0][1]; p_m_l = m_lgbm.predict_proba(X_input, verbose=-1)[0][1]
            p_b_x = b_xgb.predict_proba(X_input)[0][1]; p_b_l = b_lgbm.predict_proba(X_input, verbose=-1)[0][1]
            
            # 2:8 가중치 확률 및 보수적 문턱값
            p_final = ((p_m_x + p_m_l)/2 * 0.2) + ((p_b_x + p_b_l)/2 * 0.8)
            v_b_x = p_b_x > 0.58
            votes = sum([p_m_x > 0.52, p_m_l > 0.51, v_b_x, p_b_l > 0.52])
            
            all_results.append({'Name': name, 'Prob': p_final, 'Bull_XGB': p_b_x, 'Votes': votes, 'Price': int(df.iloc[-1]['Close']), 'Code': code})

        conn.close()

        # 메시지 조립
        msg = get_performance_report() + get_sell_signals() + f"🏆 *[AI 콰트로 리포트]* {datetime.now().strftime('%Y-%m-%d')}\n"

        main_picks = sorted([r for r in all_results if r['Prob'] > 0.55 and r['Bull_XGB'] > 0.58 and r['Votes'] >= 2], key=lambda x: x['Prob'], reverse=True)[:3]
        runner_ups = sorted([r for r in all_results if r['Name'] not in [m['Name'] for m in main_picks]], key=lambda x: x['Prob'], reverse=True)[:5]

        # 1. 강력 추천 기록
        # 1. 강력 추천 기록 (수정된 UPSERT 로직)
        if main_picks:
            msg += "🏆 *[AI 강력 추천 종목]*\n"
            conn = sqlite3.connect(CONF['DB_PATH'])
            today = datetime.now().strftime('%Y-%m-%d')
            for r in main_picks:
                buy_p = int(r['Price'] * 0.995)
                msg += f"• *{r['Name']}* ({r['Prob']:.1%})\n  🔹 매수: {buy_p:,}원 | 🎯 목표: {int(buy_p*1.07):,}원\n"
                
                # 중복 시(CONFLICT) 가격과 타입만 업데이트 (status는 보존)
                sql = """
                    INSERT INTO recommendation_history (date, code, name, buy_price, type, status)
                    VALUES (?, ?, ?, ?, 'MAIN', 'WATCHING')
                    ON CONFLICT(date, code) DO UPDATE SET
                        buy_price = excluded.buy_price,
                        type = excluded.type
                """
                conn.execute(sql, (today, r['Code'], r['Name'], buy_p))
            conn.commit(); conn.close()
        else:
            msg += "\n🧐 현재 기준을 통가한 강력 추천 종목이 없습니다.\n"

        # 2. 아차상 기록 (오답 노트용 저장 포함)
        # 2. 아차상 기록 (수정된 UPSERT 로직)
        if runner_ups:
            msg += "\n🥈 *[아차상: 관심 종목]*\n"
            conn = sqlite3.connect(CONF['DB_PATH'])
            today = datetime.now().strftime('%Y-%m-%d')
            for r in runner_ups:
                fail = "확신도부족" if r['Prob'] <= 0.55 else ("Bull-XGB미달" if r['Bull_XGB'] <= 0.58 else "합의부족")
                msg += f"• {r['Name']} ({r['Prob']:.1%}) - _{fail}_\n"
                
                buy_p = int(r['Price'] * 0.995)
                # 중복 시(CONFLICT) 가격과 타입만 업데이트 (status는 보존)
                sql = """
                    INSERT INTO recommendation_history (date, code, name, buy_price, type, status)
                    VALUES (?, ?, ?, ?, 'RUNNER', 'WATCHING')
                    ON CONFLICT(date, code) DO UPDATE SET
                        buy_price = excluded.buy_price,
                        type = excluded.type
                """
                conn.execute(sql, (today, r['Code'], r['Name'], buy_p))
            conn.commit(); conn.close()

        # 전송
        for cid in CONF['CHAT_IDS']:
            requests.post(f"https://api.telegram.org/bot{CONF['TELEGRAM_TOKEN']}/sendMessage", data={"chat_id": cid, "text": msg, "parse_mode": "Markdown"})

    except Exception as e:
        print(f"❌ 시스템 에러: {e}")

if __name__ == "__main__":
    run_integrated_scanner()