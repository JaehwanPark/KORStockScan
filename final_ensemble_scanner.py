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
    config_path = 'config_prod.json'
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
        
        # 🚀 [신규] 포지션 태그 컬럼 추가
        if 'position_tag' not in columns:
            cursor.execute("ALTER TABLE recommendation_history ADD COLUMN position_tag TEXT DEFAULT 'MIDDLE'")
            print("✅ position_tag 컬럼이 성공적으로 추가되었습니다.")
            
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"⚠️ DB 마이그레이션 오류: {e}")

# --- [신규: 불순물 종목 필터링 엔진] ---
def is_valid_stock(code, name):
    """
    우선주, ETF, ETN, 스팩 등 AI 판독을 방해하는 종목을 걸러냅니다.
    """
    # 1. 우선주 필터링: 종목코드 끝자리가 '0'이 아니면 무조건 제외!
    if str(code)[-1] != '0':
        return False
        
    # 2. ETF / ETN / 스팩 등 펀드성 종목 필터링
    bad_keywords = ['KODEX', 'TIGER', 'KINDEX', 'KBSTAR', 'ARIRANG', 'KOSEF', 'HANARO', 'ACE', '스팩', 'ETN']
    if any(keyword in str(name) for keyword in bad_keywords):
        return False
        
    return True

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

            # 🚀 [추가] 불순물 종목이면 AI 분석 안 하고 즉시 패스!
            if not is_valid_stock(code, name):
                continue
            
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
            
            # 🚀 [신규] 60일 기준 현재 주가 위치(Position) 판독
            high_60 = df['High'].tail(60).max()
            low_60 = df['Low'].tail(60).min()
            position_pct = (current_price - low_60) / (high_60 - low_60 + 1e-9)
            
            if position_pct >= 0.80:
                pos_tag = 'BREAKOUT' # 전고점 돌파형 (상위 20%)
            elif position_pct <= 0.30:
                pos_tag = 'BOTTOM'   # 바닥 턴어라운드형 (하위 30%)
            else:
                pos_tag = 'MIDDLE'   # 허리 (추세 진행)

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
                'Code': code,
                'Position': pos_tag # 🚀 태그 추가
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
                    INSERT INTO recommendation_history (date, code, name, buy_price, type, status, nxt, position_tag)
                    VALUES (?, ?, ?, ?, ?, 'WATCHING', NULL, ?)
                    ON CONFLICT(date, code) DO UPDATE SET
                        buy_price = excluded.buy_price,
                        type = excluded.type,
                        position_tag = excluded.position_tag
                """
                # VALUES에 r['Position'] 추가 (MAIN, RUNNER 구분값 맞추기)
                conn.execute(sql, (today, r['Code'], r['Name'], buy_p, 'MAIN', r['Position']))
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
                    INSERT INTO recommendation_history (date, code, name, buy_price, type, status, nxt, position_tag)
                    VALUES (?, ?, ?, ?, ?, 'RUNNER', NULL, ?)
                    ON CONFLICT(date, code) DO UPDATE SET
                        buy_price = excluded.buy_price,
                        type = excluded.type,
                        position_tag = excluded.position_tag
                """
                # VALUES에 r['Position'] 추가 (MAIN, RUNNER 구분값 맞추기)
                conn.execute(sql, (today, r['Code'], r['Name'], buy_p, 'MAIN', r['Position']))
            conn.commit(); conn.close()
        
        chat_ids = []

        try:
            # userd.db 파일 경로 연결
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            
            # 🚀 실제 DB의 테이블명과 컬럼명으로 변경해 주세요 (예: users 테이블의 chat_id 컬럼)
            cursor.execute("SELECT chat_id FROM users WHERE chat_id IS NOT NULL")
            rows = cursor.fetchall()
            
            # [(12345,), (67890,)] 형태의 튜플 결과를 리스트 [12345, 67890] 형태로 변환
            chat_ids = [row[0] for row in rows]
            
        except Exception as e:
            print(f"⚠️ [알림 발송] userd.db 조회 중 에러 발생: {e}")
        finally:
            if 'conn' in locals() and conn:
                conn.close()

        # 2. 조회된 모든 사용자에게 메시지를 발송합니다.
        if chat_ids:
            for cid in chat_ids:
                try:
                    requests.post(
                        f"https://api.telegram.org/bot{CONF['TELEGRAM_TOKEN']}/sendMessage", 
                        data={"chat_id": cid, "text": msg, "parse_mode": "Markdown"},
                        timeout=5  # 🚀 타임아웃을 걸어두면 한 사용자 발송이 지연될 때 전체가 멈추는 것을 방지합니다.
                    )
                except Exception as e:
                    print(f"⚠️ [알림 발송] ID {cid}로 메시지 전송 실패: {e}")
        else:
            print("ℹ️ 알림을 수신할 사용자가 DB에 없습니다.")

    except Exception as e:
        print(f"❌ 시스템 에러: {e}")

# --- [6. 🚀 신규: 장중 지능형 재스캔 엔진] ---
def run_intraday_scanner(token):
    """
    오늘 실시간 시세를 반영한 가상 일봉을 생성하여 AI 앙상블을 재구동하는 장중 스캐너
    """
    print("🔍 [장중 스캔] 실시간 급등주(주도주) 탐색을 시작합니다...")
    
    # 1. ka00198 API 호출을 통해 거래량 터진 급등주 추출
    url = "https://api.kiwoom.com/api/dostk/stkinfo"
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'cont-yn': 'N',
        'api-id': 'ka00198'
    }
    payload = {'qry_tp': '4'} # 당일 누적 주도주
    
    hot_stocks = []
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=5)
        data = res.json()
        if res.status_code == 200 and data.get('return_code') == '0':
            for item in data.get('item_inq_rank', []):
                stk_cd = str(item.get('stk_cd'))[:6]
                stk_nm = item.get('stk_nm', '') # 🚀 API에서 종목명도 같이 빼옵니다.
                price = item.get('past_curr_prc')
                vol = item.get('acml_vol', 0)
                
                # 🚀 [추가] 급등주 목록 중 불순물은 리스트에 넣지도 않고 쳐냅니다.
                if stk_cd and price and is_valid_stock(stk_cd, stk_nm):
                    hot_stocks.append({
                        'code': stk_cd, 
                        'name': stk_nm,  # 🚀 이름 저장
                        'price': abs(int(price)), 
                        'vol': int(vol)
                    })
    except Exception as e:
        print(f"⚠️ 급등주 조회 실패: {e}")
        return []

    if not hot_stocks:
        print("⚠️ 조건에 맞는 실시간 급등주가 없어 스캔을 보류합니다.")
        return []
        
    print(f"✅ 포착된 핫-종목 {len(hot_stocks)}개에 대한 AI 판독을 시작합니다.")
    
    # 모델 로드
    try:
        m_xgb = joblib.load('hybrid_xgb_model.pkl') 
        m_lgbm = joblib.load('hybrid_lgbm_model.pkl')
        b_xgb = joblib.load('bull_xgb_model.pkl')
        b_lgbm = joblib.load('bull_lgbm_model.pkl')
        meta_model = joblib.load('stacking_meta_model.pkl')
    except Exception as e:
        print(f"❌ 모델 로드 에러: {e}")
        return []

    conn = sqlite3.connect(CONF['DB_PATH'])
    new_targets = []
    
    for stock in hot_stocks:
        code = stock['code']
        df = pd.read_sql(f"SELECT * FROM daily_stock_quotes WHERE Code='{code}' ORDER BY Date DESC LIMIT 60", conn)
        if len(df) < 30: continue
        
        df = df.sort_values('Date').reset_index(drop=True)
        
        # 🚀 [핵심 1] 오늘 실시간 시세를 가상의 '오늘 일봉'으로 추가
        today_str = datetime.now().strftime('%Y-%m-%d')
        if df.iloc[-1]['Date'] != today_str:
            new_row = df.iloc[-1].copy()
            new_row['Date'] = today_str
            new_row['Close'] = stock['price']
            if stock['vol'] > 0:
                new_row['Volume'] = stock['vol']
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        else:
            # 이미 오늘 날짜가 있다면 실시간 시세로 덮어쓰기
            df.at[df.index[-1], 'Close'] = stock['price']
            if stock['vol'] > 0:
                df.at[df.index[-1], 'Volume'] = stock['vol']
        
        # 🚀 [핵심 2] 추가된 실시간 가격을 바탕으로 주요 기술적 지표 실시간 갱신
        df['MA5'] = df['Close'].rolling(5).mean()
        df['MA20'] = df['Close'].rolling(20).mean()
        df['STD20'] = df['Close'].rolling(20).std()
        df['BBU'] = df['MA20'] + 2 * df['STD20']
        df['BBL'] = df['MA20'] - 2 * df['STD20']
        
        # RSI 재계산
        delta = df['Close'].diff()
        gain = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
        loss = -delta.clip(upper=0).ewm(alpha=1/14, adjust=False).mean()
        rs = gain / (loss + 1e-9)
        df['RSI'] = 100 - (100 / (1 + rs))
        df['RSI_Slope'] = df['RSI'].diff()
        
        # MACD 재계산
        ema12 = df['Close'].ewm(span=12, adjust=False).mean()
        ema26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = ema12 - ema26
        df['MACD_Sig'] = df['MACD'].ewm(span=9, adjust=False).mean()
        
        # AI 모델 필수 입력 Features 계산
        df['Vol_Change'] = df['Volume'].pct_change()
        df['MA_Ratio'] = df['Close'] / (df['MA20'] + 1e-9)
        df['BB_Pos'] = (df['Close'] - df['BBL']) / (df['BBU'] - df['BBL'] + 1e-9)
        df['Range_Ratio'] = (df['High'] - df['Low']) / (df['Close'] + 1e-9)
        df['Vol_Momentum'] = df['Volume'] / (df['Volume'].rolling(5).mean() + 1e-9)
        df['Dist_MA5'] = df['Close'] / (df['MA5'] + 1e-9)
        df['Up_Trend_2D'] = ((df['Close'].diff(1) > 0) & (df['Close'].shift(1).diff(1) > 0)).astype(int)
        
        # 장중 결측치는 이전 값으로 안전하게 채움
        df = df.ffill().fillna(0)
        latest_row = df.iloc[[-1]]
        
        # 🚀 [신규] 60일 기준 현재 주가 위치(Position) 판독
        current_price = stock['price']  # 👈 이 줄을 추가합니다!
        high_60 = df['High'].tail(60).max()
        low_60 = df['Low'].tail(60).min()
        position_pct = (current_price - low_60) / (high_60 - low_60 + 1e-9)
         
        if position_pct >= 0.80:
            pos_tag = 'BREAKOUT' # 전고점 돌파형 (상위 20%)
        elif position_pct <= 0.30:
            pos_tag = 'BOTTOM'   # 바닥 턴어라운드형 (하위 30%)
        else:
            pos_tag = 'MIDDLE'   # 허리 (추세 진행)
        
        # 🚀 [핵심 3] AI 앙상블 판독 (오늘 시세 기준)
        try:
            p_m_x = m_xgb.predict_proba(latest_row[FEATURES_XGB])[0][1]
            p_m_l = m_lgbm.predict_proba(latest_row[FEATURES_LGBM])[0][1]
            p_b_x = b_xgb.predict_proba(latest_row[FEATURES_XGB])[0][1]
            p_b_l = b_lgbm.predict_proba(latest_row[FEATURES_LGBM])[0][1]
            
            meta_input = pd.DataFrame({
                'XGB_Prob': [p_m_x], 'LGBM_Prob': [p_m_l], 
                'Bull_XGB_Prob': [p_b_x], 'Bull_LGBM_Prob': [p_b_l]
            })
            p_final = meta_model.predict_proba(meta_input)[0][1]
            
            # 장중 돌파 수급이 반영된 점수가 80점 이상이면 발탁
            if p_final >= 0.80:
                name = kiwoom_utils.get_stock_name_ka10001(code, token) if hasattr(kiwoom_utils, 'get_stock_name_ka10001') else code
                new_targets.append({
                    'code': code,
                    'name': name,
                    'prob': p_final,
                    'status': 'WATCHING',
                    'Position': pos_tag # 🚀 태그 추가
                })
        except Exception as e:
            continue

    # 4. DB 업데이트 (봇 상태조회 시 노출되도록)
    if new_targets:
        today = datetime.now().strftime('%Y-%m-%d')
        for t in new_targets:
            buy_p = [s['price'] for s in hot_stocks if s['code'] == t['code']][0]
            sql = """
                    INSERT INTO recommendation_history (date, code, name, buy_price, type, status, nxt, position_tag)
                    VALUES (?, ?, ?, ?, ?, 'WATCHING', NULL, ?)
                    ON CONFLICT(date, code) DO UPDATE SET
                        buy_price = excluded.buy_price,
                        type = excluded.type,
                        position_tag = excluded.position_tag
                """
            # 👈 'MAIN' 이라는 문자열을 추가하여 물음표 6개와 짝을 맞춰줍니다!
            conn.execute(sql, (today, t['code'], t['name'], buy_p, 'MAIN', t['Position']))
        conn.commit()
        print(f"🎯 장중 AI 재스캔 완료! {len(new_targets)}개의 주도주가 스나이퍼 엔진에 전달됩니다.")
        
    conn.close()
    return new_targets

if __name__ == "__main__":
    run_integrated_scanner()