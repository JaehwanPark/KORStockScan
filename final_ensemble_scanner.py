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
                buy_qty INTEGER DEFAULT 0,
                PRIMARY KEY (date, code)
            )
        """)
    
    conn.commit()
    conn.close()

def migrate_db():
    """기존 테이블에 nxt 컬럼을 추가하고 초기화합니다."""
    try:
        conn = sqlite3.connect(CONF['DB_PATH'])
        cursor = conn.cursor()
        
        # 현재 테이블의 컬럼 정보 조회
        cursor.execute("PRAGMA table_info(recommendation_history)")
        columns = [info[1] for info in cursor.fetchall()]
        
        # buy_time 컬럼이 없으면 추가
        if 'nxt' not in columns:
            cursor.execute("ALTER TABLE recommendation_history ADD COLUMN nxt REAL")
            print("✅ nxt 컬럼이 성공적으로 추가되었습니다.")
            
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"⚠️ DB 마이그레이션 오류: {e}")

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

# --- [5. 메인 스캐너 엔진 업데이트] ---

# 전공 지표 리스트 정의 (반드시 학습 시와 일치해야 함)
FEATURES_XGB = ['Return', 'MA_Ratio', 'MACD', 'MACD_Sig', 'VWAP', 'OBV', 'Up_Trend_2D', 'Dist_MA5']
FEATURES_LGBM = ['BB_Pos', 'RSI', 'RSI_Slope', 'Range_Ratio', 'Vol_Momentum', 'Vol_Change', 'ATR', 'BBB', 'BBP']

def run_integrated_scanner():
    print(f"=== 콰트로 v11.0 (스태킹 앙상블) ===")
    init_history_db()
    migrate_db()

    try:
        # [수정] 모델 로드 파일명 및 메타 모델 추가
        m_xgb = joblib.load('hybrid_xgb_model.pkl') 
        m_lgbm = joblib.load('hybrid_lgbm_model.pkl')
        b_xgb = joblib.load('bull_xgb_model.pkl')
        b_lgbm = joblib.load('bull_lgbm_model.pkl')
        meta_model = joblib.load('stacking_meta_model.pkl') # 메타 모델 추가 로드
        
        conn = sqlite3.connect(CONF['DB_PATH'])
        # 1. 분석 대상 확대 (시총 상위 500개 중 거래량 상위 400개 추출)
        df_krx = fdr.StockListing('KOSPI')
        target_list = df_krx.sort_values(by='Marcap', ascending=False).head(500) # 200 -> 500
        target_list = target_list.sort_values(by='Volume', ascending=False).head(400).to_dict('records') # 100 -> 400
        
        all_results = []

        for stock in target_list:
            code, name = stock['Code'], stock['Name']
            # [체크] DB에서 VWAP, OBV 등 모든 컬럼을 가져와야 함 (SELECT * 사용 유지)
            df = pd.read_sql(f"SELECT * FROM daily_stock_quotes WHERE Code='{code}' ORDER BY Date DESC LIMIT 60", conn)
            if len(df) < 30: continue
            
            df = df.sort_values('Date')
            
            # [수정] 지표 가공 로직 (훈련 시와 동일하게)
            df['Vol_Change'] = df['Volume'].pct_change()
            df['MA_Ratio'] = df['Close'] / (df['MA20'] + 1e-9)
            df['BB_Pos'] = (df['Close'] - df['BBL']) / (df['BBU'] - df['BBL'] + 1e-9)
            df['RSI_Slope'] = df['RSI'].diff()
            df['Range_Ratio'] = (df['High'] - df['Low']) / (df['Close'] + 1e-9)
            df['Vol_Momentum'] = df['Volume'] / (df['Volume'].rolling(5).mean() + 1e-9)
            df['Dist_MA5'] = df['Close'] / (df['MA5'] + 1e-9)
            
            # [신규 추가] 2일 연속 상승 추세
            df['Up_Trend_2D'] = (df['Close'].diff(1) > 0) & (df['Close'].shift(1).diff(1) > 0)
            df['Up_Trend_2D'] = df['Up_Trend_2D'].astype(int)
            
            # 최신 행 추출 및 무한대 처리
            latest_row = df.iloc[[-1]].replace([np.inf, -np.inf], np.nan).fillna(0)
            
            # [수정] 각 전문가에게 전공 지표로 질문
            p_m_x = m_xgb.predict_proba(latest_row[FEATURES_XGB])[0][1]
            p_m_l = m_lgbm.predict_proba(latest_row[FEATURES_LGBM])[0][1]
            p_b_x = b_xgb.predict_proba(latest_row[FEATURES_XGB])[0][1]
            p_b_l = b_lgbm.predict_proba(latest_row[FEATURES_LGBM])[0][1]
            
            # [수정] 스태킹 메타 모델을 이용한 최종 확률 계산
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

        # [수정] 메시지 조립 및 필터링 로직
        msg = get_performance_report() + get_sell_signals() + f"🏆 *[AI 콰트로 Stacking 리포트]* {datetime.now().strftime('%Y-%m-%d')}\n"

        # 임계값 0.80 이상만 강력 추천 (훈련 시 정밀도 58.94% 구간)
        main_picks = sorted([r for r in all_results if r['Prob'] >= 0.80], key=lambda x: x['Prob'], reverse=True)[:3]
        
        # [:20] 제거: 조건에 맞는 모든 종목을 우선 다 담습니다.
        runner_ups = sorted([r for r in all_results if 0.65 <= r['Prob'] < 0.80], key=lambda x: x['Prob'], reverse=True)

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

        # 2. 아차상 기록 (기존 20개 제한을 풀고 더 많이 저장)
        if runner_ups:
            # 리포트용 메시지는 여전히 상위 10개만 표시 (가독성)
            msg += "\n🥈 *[아차상: 관심 종목 상위 10개]*\n"
            for r in runner_ups[:10]:
                msg += f"• {r['Name']} ({r['Prob']:.1%})\n"
            
            # DB 저장 (최대 300개)
            conn = sqlite3.connect(CONF['DB_PATH'])
            today = datetime.now().strftime('%Y-%m-%d')
            
            for r in runner_ups[:300]: # 여기서 최대 300개까지 저장됨
                buy_p = int(r['Price'] * 0.995)
                sql = """
                    INSERT INTO recommendation_history (date, code, name, buy_price, type, status, nxt)
                    VALUES (?, ?, ?, ?, 'RUNNER', 'WATCHING', NULL)
                    ON CONFLICT(date, code) DO UPDATE SET
                        buy_price = excluded.buy_price,
                        type = excluded.type
                """
                conn.execute(sql, (today, r['Code'], r['Name'], buy_p))
            conn.commit()
            conn.close()

        # 전송
        for cid in CONF['CHAT_IDS']:
            requests.post(f"https://api.telegram.org/bot{CONF['TELEGRAM_TOKEN']}/sendMessage", data={"chat_id": cid, "text": msg, "parse_mode": "Markdown"})

    except Exception as e:
        print(f"❌ 시스템 에러: {e}")

if __name__ == "__main__":
    run_integrated_scanner()