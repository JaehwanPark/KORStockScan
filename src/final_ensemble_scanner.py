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
from signal_radar import SniperRadar  # 1. 레이더 모듈 추가

from constants import TRADING_RULES
from feature_engineer import calculate_all_features
from db_manager import DBManager

# ==========================================
# 1. 경로 설정 (상대 참조)
# ==========================================
# 현재 파일(final_ensemble_scanner.py)의 위치 기준 상위 data 폴더 지정
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..', 'data'))

# 주요 파일 절대 경로 정의
CONFIG_PATH = os.path.join(DATA_DIR, 'config_prod.json')
# DB 경로는 기본적으로 DATA_DIR 내부의 파일을 사용하도록 세팅
STOCK_DB_PATH = os.path.join(DATA_DIR, 'kospi_stock_data.db')
USER_DB_PATH = os.path.join(DATA_DIR, 'users.db')
LOG_PATH = os.path.join(DATA_DIR, 'ensemble_scanner.log')
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

# --- [1. 설정 로드 엔진 업데이트] ---
def load_config():
    """상대 경로를 사용하여 config_prod.json을 로드합니다."""
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ 설정 파일을 찾을 수 없습니다: {CONFIG_PATH}")
        exit()

CONF = load_config()

class SilentLogger:
    def info(self, msg): pass

    def warning(self, msg): pass

    def error(self, msg): pass

warnings.filterwarnings('ignore')
lgb.register_logger(SilentLogger())
os.environ['LIGHTGBM_LOG_LEVEL'] = '-1'


# ==========================================
# 2. DB 초기화 및 마이그레이션
# ==========================================
def init_and_migrate_db(db: DBManager):
    """DBManager를 활용하여 스키마 점검 및 마이그레이션을 수행합니다."""
    with db._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(recommendation_history)")
        columns = cursor.fetchall()
        is_pk_set = any(col[5] > 0 for col in columns)

        if not columns or not is_pk_set:
            print("⚠️ DB 스키마가 구버전이거나 존재하지 않습니다. 테이블을 신규 생성합니다.")
            cursor.execute("DROP TABLE IF EXISTS recommendation_history")
            cursor.execute("""
                CREATE TABLE recommendation_history (
                    date TEXT, code TEXT, name TEXT, buy_price INTEGER,
                    type TEXT, status TEXT DEFAULT 'WATCHING', buy_qty INTEGER DEFAULT 0,
                    PRIMARY KEY (date, code)
                )
            """)
        else:
            col_names = [info[1] for info in columns]
            if 'nxt' not in col_names:
                cursor.execute("ALTER TABLE recommendation_history ADD COLUMN nxt REAL")
            if 'position_tag' not in col_names:
                cursor.execute("ALTER TABLE recommendation_history ADD COLUMN position_tag TEXT DEFAULT 'MIDDLE'")
                print("✅ position_tag 컬럼이 성공적으로 추가되었습니다.")
        conn.commit()


# --- [4. 성과 복기 엔진] ---
def get_performance_report(db: DBManager):
    last_date = db.get_latest_history_date()

    if not last_date: return "📊 신규 가동을 시작합니다.\n"

    history = db.get_history_by_date(last_date)
    # 💡 마크다운(*) 대신 HTML(<b>) 태그 사용
    report_msg = f"📊 <b>[전일 성적표 ({last_date})]</b>\n"

    for r_type in ['MAIN', 'RUNNER']:
        subset = history[history['type'] == r_type]
        if subset.empty: continue

        profits = []
        for _, row in subset.iterrows():
            try:
                df = fdr.DataReader(row['code'], start=last_date)
                close_price = df.iloc[-1]['Close']
            except:
                db_last = db.get_stock_data(row['code'], limit=1)
                close_price = db_last.iloc[0]['Close'] if not db_last.empty else row['buy_price']

            p = (close_price / row['buy_price'] - 1) * 100
            profits.append(p)

        if profits:
            win_rate = (len([p for p in profits if p > 0]) / len(profits)) * 100
            avg_p = sum(profits) / len(profits)
            label = "✅ 강력추천" if r_type == 'MAIN' else "🥈 아차상"
            report_msg += f"{label}: 승률 {win_rate:.0f}% / 수익 {avg_p:+.2f}%\n"

    return report_msg + "-" * 20 + "\n"


# --- [5. 메인 스캐너 엔진 업데이트] ---
# [스캐너 엔진의 Features 교체]
FEATURES_XGB = ['Return', 'MA_Ratio', 'MACD', 'MACD_Sig', 'VWAP', 'OBV', 'Up_Trend_2D', 'Dist_MA5', 'Dual_Net_Buy', 'Foreign_Net_Roll5', 'Inst_Net_Roll5']
FEATURES_LGBM = ['BB_Pos', 'RSI', 'RSI_Slope', 'Range_Ratio', 'Vol_Momentum', 'Vol_Change', 'ATR', 'BBB', 'BBP', 'Foreign_Vol_Ratio', 'Inst_Vol_Ratio', 'Margin_Rate_Change', 'Margin_Rate_Roll5']


def run_integrated_scanner():
    print(f"=== KORStockScan v13 (Stacking Ensemble + Quality Filter) ===")
    db = DBManager()

    try:
        init_and_migrate_db(db)

        # 1. 모델 로드 및 Kiwoom 토큰 준비
        m_xgb = joblib.load(os.path.join(DATA_DIR, 'hybrid_xgb_model.pkl'))
        m_lgbm = joblib.load(os.path.join(DATA_DIR, 'hybrid_lgbm_model.pkl'))
        b_xgb = joblib.load(os.path.join(DATA_DIR, 'bull_xgb_model.pkl'))
        b_lgbm = joblib.load(os.path.join(DATA_DIR, 'bull_lgbm_model.pkl'))
        meta_model = joblib.load(os.path.join(DATA_DIR, 'stacking_meta_model.pkl'))

        kiwoom_token = None
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                CONF = json.load(f)
            kiwoom_token = kiwoom_utils.get_kiwoom_token(CONF)
        except Exception as e:
            print(f"⚠️ 키움 토큰 발급 생략 (FDR 단독 모드): {e}")

        # ==========================================
        # 2. 지수 상대강도(RS)용 지수 데이터 확보 (FDR 우선 -> Kiwoom ka20006 우회)
        # ==========================================
        kospi_5d_return = 0
        try:
            print("📈 FDR을 통해 최신 KOSPI 지수 데이터를 가져오는 중...")
            kospi_df = fdr.DataReader('KS11', start=(datetime.now() - timedelta(days=20)).strftime('%Y-%m-%d'))
            if not kospi_df.empty and len(kospi_df) >= 5:
                kospi_5d_return = (kospi_df['Close'].iloc[-1] / kospi_df['Close'].iloc[-5]) - 1
                print(f"✅ FDR 지수 로드 완료 (KOSPI 5일 수익률: {kospi_5d_return:.2%})")
            else:
                raise ValueError("FDR 데이터가 충분하지 않습니다.")
        except Exception as e:
            print(f"⚠️ FDR 지수 로드 실패({e}). Kiwoom API(ka20006) 우회 시도...")

            if kiwoom_token:
                # 🚀 로컬 DB를 버리고, 한 줄의 API 호출로 최신 및 과거 지수 확보!
                latest_prc, before_prc = kiwoom_utils.get_index_daily_ka20006(kiwoom_token, "001")

                if latest_prc and before_prc:
                    kospi_5d_return = (latest_prc / before_prc) - 1
                    print(f"✅ Kiwoom API 지수 RS 산출 완료 (수익률: {kospi_5d_return:.2%})")
                else:
                    print("⚠️ Kiwoom API 지수 로드 실패. 상대강도(RS)를 0으로 설정합니다.")
            else:
                print("⚠️ 키움 토큰이 없어 지수 우회가 불가합니다. 상대강도(RS)를 0으로 설정합니다.")

        # ==========================================
        # 3. 기초 유동성 필터 (FDR -> DB Fallback)
        # ==========================================
        print("🔍 [1/4] 분석 대상 종목 리스트 구성 중...")
        target_list = []
        try:
            df_krx = fdr.StockListing('KOSPI')
            top_m = df_krx.sort_values(by='Marcap', ascending=False).head(TRADING_RULES['TOP_N_MARCAP'])
            target_df = top_m.sort_values(by='Volume', ascending=False).head(TRADING_RULES['TOP_N_VOLUME'])
            target_list = [{'Code': r['Code'], 'Name': r['Name']} for _, r in target_df.iterrows()]
            print(f"✅ FDR을 통해 {len(target_list)}개 종목 확보.")
        except Exception as e:
            print(f"⚠️ FDR 리스트 수집 실패. 로컬 DB 시총 데이터로 우회합니다.")
            query = "SELECT Code, Name FROM daily_stock_quotes WHERE Date = (SELECT MAX(Date) FROM daily_stock_quotes) ORDER BY Marcap DESC LIMIT 200"
            with db._get_connection() as conn:
                db_targets = pd.read_sql(query, conn)
            target_list = db_targets.head(150).to_dict('records')

        # ==========================================
        # 4. AI 앙상블 스캐닝 루프 (💡 except 블록 밖으로 완벽 탈출!)
        # ==========================================
        print(f"🚀 [2/4] AI 콰트로 앙상블 분석 시작 ({len(target_list)} 종목)...")
        all_results = []
        
        # 💡 [추가] 누락되었던 '데이터 부족', '불량 종목(ETF 등)' 카운터 추가!
        drop_stats = {'short_data': 0, 'invalid_type': 0, 'low_price': 0, 'quality': 0, 'ai_prob': 0, 'trend': 0, 'supply': 0, 'error': 0}

        for stock in target_list:
            code = str(stock['Code']).strip().zfill(6)
            name = stock['Name']
            
            df = db.get_stock_data(code, limit=60)

            # 🚀 [추가] 데이터 부족으로 탈락한 종목 카운트
            if len(df) < 30: 
                drop_stats['short_data'] += 1
                continue

            df = df.sort_values('Date')
            current_price = df.iloc[-1]['Close']

            # 🚀 [추가] 저가주와 이름 불량(ETF, 스팩 등) 탈락 사유 세분화
            if not kiwoom_utils.is_valid_stock(code, name, current_price=current_price):
                if current_price < TRADING_RULES['MIN_PRICE']:
                    drop_stats['low_price'] += 1
                else:
                    drop_stats['invalid_type'] += 1
                continue

            # =================================================================
            # 🛡️ 기초품질(Quality) 필터: 하락 추세 및 소외주 1차 컷오프
            # 아래 3가지 모멘텀 조건 중 **단 1개도 만족하지 못하는(sum < 1)** 종목은 폐기
            #   1) 상대강도: 최근 5일 수익률이 코스피 지수 5일 수익률보다 높을 것
            #   2) 단기추세: 현재가 > 5일선 > 20일선 (단기 완전 정배열)
            #   3) 가격방어: 최근 20일(약 1달) 최고점 대비 하락폭이 -10% 이내일 것
            # =================================================================
            stock_5d_return = (current_price / df.iloc[-5]['Close']) - 1
            ma5, ma20 = df['Close'].rolling(5).mean().iloc[-1], df['Close'].rolling(20).mean().iloc[-1]
            high_20d = df['High'].tail(20).max()

            if sum([stock_5d_return > kospi_5d_return, (current_price > ma5 > ma20),
                    current_price >= (high_20d * 0.90)]) < 1:
                drop_stats['quality'] += 1  
                continue

            try:
                df = calculate_all_features(df)
                h60, l60 = df['High'].tail(60).max(), df['Low'].tail(60).min()
                pos_tag = 'BREAKOUT' if (current_price - l60) / (h60 - l60 + 1e-9) >= 0.8 else (
                    'BOTTOM' if (current_price - l60) / (h60 - l60 + 1e-9) <= 0.3 else 'MIDDLE')

                latest_row = df.iloc[[-1]].replace([np.inf, -np.inf], np.nan).fillna(0)
                preds = [m_xgb.predict_proba(latest_row[FEATURES_XGB])[0][1],
                            m_lgbm.predict_proba(latest_row[FEATURES_LGBM])[0][1],
                            b_xgb.predict_proba(latest_row[FEATURES_XGB])[0][1],
                            b_lgbm.predict_proba(latest_row[FEATURES_LGBM])[0][1]]

                p_final = meta_model.predict_proba(
                    pd.DataFrame([preds], columns=['XGB_Prob', 'LGBM_Prob', 'Bull_XGB_Prob', 'Bull_LGBM_Prob']))[0][
                    1]

                # 1. 완화된 AI 확신도 (0.70)
                if p_final < TRADING_RULES.get('PROB_RUNNER_PICK', 0.70):
                    drop_stats['ai_prob'] += 1  
                    continue

                # 3. [V3.1] 외국인/기관 매집 '가속도' 필터
                f_roll5 = latest_row['Foreign_Net_Roll5'].values[0]
                i_roll5 = latest_row['Inst_Net_Roll5'].values[0]
                f_accel = latest_row['Foreign_Net_Accel'].values[0]
                i_accel = latest_row['Inst_Net_Accel'].values[0]

                is_foreign_buying = (f_roll5 > 0 and f_accel > 0)
                is_inst_buying = (i_roll5 > 0 and i_accel > 0)

                if not (is_foreign_buying or is_inst_buying):
                    drop_stats['supply'] += 1
                    continue

                # 모든 필터를 뚫은 종목만 추가
                all_results.append(
                    {'Name': name, 'Prob': p_final, 'Price': int(current_price), 'Code': code, 'Position': pos_tag})

            except Exception as e:
                drop_stats['error'] += 1  
                continue

        # ==========================================
        # 💡 [핵심 수정] 여기서부터 for문 밖으로 완벽 탈출했습니다! (들여쓰기 8칸)
        # ==========================================
        # 1. 텔레그램 전송용 예쁜 마크다운 메시지 생성
        debug_msg = (
            f"🛑 *[스캐너 필터링 결과 분석]*\n"
            f"총 {len(target_list)}개 중 *{len(all_results)}개 생존*\n\n"
            f"📉 *탈락 사유 통계*\n"
            f" • 데이터 30일 미만: {drop_stats['short_data']}개\n"
            f" • ETF/우선주/스팩: {drop_stats['invalid_type']}개\n"
            f" • 동전주/저가주: {drop_stats['low_price']}개\n"
            f" • 기초 품질 미달: {drop_stats['quality']}개\n"
            f" • AI 확신도 부족(<70%): {drop_stats['ai_prob']}개\n"
            f" • 수급 부재(이탈): {drop_stats['supply']}개\n"
            f" • 데이터 계산 에러: {drop_stats['error']}개"
        )

        print("\n" + "=" * 50)
        print(debug_msg.replace('*', ''))
        print("=" * 50 + "\n")

        # 2. 텔레그램 관리자(ADMIN)에게 다이렉트 메시지 전송
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                conf = json.load(f)

            bot_token = conf.get('TELEGRAM_TOKEN')
            admin_id = conf.get('ADMIN_ID')

            if bot_token and admin_id:
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                payload = {
                    'chat_id': admin_id,
                    'text': debug_msg,
                    'parse_mode': 'Markdown'
                }
                requests.post(url, json=payload, timeout=5)
        except Exception as e:
            print(f"⚠️ 관리자 텔레그램 전송 실패: {e}")

        # ==========================================
        # 5. 결과 기록 및 전송
        # ==========================================
        print("📊 [3/4] 리포트 생성 및 전송 중...")
        today = datetime.now().strftime('%Y-%m-%d')
        main_picks = sorted([r for r in all_results if r['Prob'] >= TRADING_RULES['PROB_MAIN_PICK']],
                            key=lambda x: x['Prob'], reverse=True)[:3]
        runner_ups = sorted([r for r in all_results if
                             TRADING_RULES['PROB_RUNNER_PICK'] <= r['Prob'] < TRADING_RULES['PROB_MAIN_PICK']],
                            key=lambda x: x['Prob'], reverse=True)[:50]

        msg = get_performance_report(db) + f"🏆 <b>[AI 콰트로 Stacking 리포트]</b> {today}\n"
        msg += "\n🥇 <b>[적극 추천 종목]</b>\n"
        
        if main_picks:
            for r in main_picks:
                msg += f"• <b>{r['Name']}</b> ({r['Code']}) - 확신지수: {r['Prob']:.1%}\n"
                db.save_recommendation(today, r['Code'], r['Name'], r['Price'], 'MAIN', r['Position'],
                                       prob=r['Prob'])
        else:
            msg += "• 😅 오늘은 AI 기준을 완벽히 통과한 MAIN 추천 종목이 없습니다.\n"

        if runner_ups:
            msg += "\n🥈 <b>[정예 관심 종목]</b>\n"
            for r in runner_ups[:10]:
                msg += f"• <b>{r['Name']}</b> ({r['Code']}) - 확신지수: {r['Prob']:.1%}\n"
            for r in runner_ups:
                db.save_recommendation(today, r['Code'], r['Name'], r['Price'], 'RUNNER', r['Position'],
                                       prob=r['Prob'])

        chat_ids = db.get_telegram_chat_ids()
        for cid in chat_ids:
            try:
                requests.post(f"https://api.telegram.org/bot{CONF['TELEGRAM_TOKEN']}/sendMessage",
                              data={"chat_id": cid, "text": msg, "parse_mode": "HTML"}, timeout=5)
            except Exception as e:
                print(f"🚨 텔레그램 발송 실패: {e}")

    except Exception as e:
        print(f"❌ 시스템 에러 발생: {e}")
    finally:
        print("🏁 [4/4] 스캐닝 프로세스가 종료되었습니다.")
        

# --- [6. 🚀 신규: 장중 지능형 재스캔 엔진] ---
def run_intraday_scanner(token):
    """
    오늘 실시간 시세를 반영한 가상 일봉을 생성하여 AI 앙상블을 재구동하는 장중 스캐너
    """
    print("🔍 [장중 스캔] 실시간 급등주(주도주) 탐색을 시작합니다...")

    # ==========================================
    # 1. 실시간 주도주 목록 수집 (Kiwoom -> FDR 방어)
    # ==========================================
    raw_hot_stocks = SniperRadar(token).get_realtime_hot_stocks_ka00198(CONF, as_dict=True)
    hot_stocks = []

    # [1차 시도] 키움 API 결과 정제 (불순물 제거 및 🚀 가격 컷오프)
    if raw_hot_stocks:
        print("📈 키움 API를 통해 실시간 주도주 데이터를 확보했습니다.")
        for s in raw_hot_stocks:
            # 💡 수정: is_valid_stock을 통과하고, 동시에 가격이 설정한 최소 금액 이상인 종목만 발탁
            if kiwoom_utils.is_valid_stock(s['code'], s['name'], current_price=s['price']):
                hot_stocks.append(s)

    # [2차 시도 - Fallback] 키움 API 3회 모두 실패 시 FDR 실시간 거래량 상위 활용
    if not hot_stocks:
        print("⚠️ 키움 API 급등주 포착 실패. FDR 실시간 거래량 상위 종목으로 우회합니다...")
        try:
            df_krx = fdr.StockListing('KOSPI')
            # 장중 실시간 거래량 상위 100위 추출
            top_vol = df_krx.sort_values(by='Volume', ascending=False).head(100)

            for _, row in top_vol.iterrows():
                current_price = int(row['Close'])
                # 💡 수정: FDR 우회 시에도 가격 필터 동일하게 적용
                if kiwoom_utils.is_valid_stock(row['Code'], row['Name'], current_price=current_price):
                    hot_stocks.append({
                        'code': row['Code'],
                        'name': row['Name'],
                        'price': current_price,
                        'vol': int(row['Volume'])
                    })
            print(f"✅ FDR 우회 성공: {len(hot_stocks)}개 종목 확보")
        except Exception as e:
            print(f"🚨 FDR 우회 수집마저 실패했습니다: {e}")

    if not hot_stocks:
        print("⚠️ 조건에 맞는 실시간 급등주가 없어 스캔을 보류합니다.")
        return []

    print(f"✅ 최종 포착된 핫-종목 {len(hot_stocks)}개에 대한 AI 판독을 시작합니다.")

    # ==========================================
    # 2. AI 앙상블 모델 로드
    # ==========================================
    try:
        m_xgb = joblib.load(os.path.join(DATA_DIR, 'hybrid_xgb_model.pkl'))
        m_lgbm = joblib.load(os.path.join(DATA_DIR, 'hybrid_lgbm_model.pkl'))
        b_xgb = joblib.load(os.path.join(DATA_DIR, 'bull_xgb_model.pkl'))
        b_lgbm = joblib.load(os.path.join(DATA_DIR, 'bull_lgbm_model.pkl'))
        meta_model = joblib.load(os.path.join(DATA_DIR, 'stacking_meta_model.pkl'))
    except Exception as e:
        print(f"❌ AI 모델 로드 실패: {e}")
        return []

    # ==========================================
    # 3. 실시간 가상 일봉 생성 및 AI 판독 루프
    # ==========================================
    db = DBManager()  # 💡 [핵심 수정] DB 매니저 인스턴스를 여기서 생성해야 합니다!
    
    new_targets = []
    today_str: str = datetime.now().strftime('%Y-%m-%d')

    # 💡 [해결] 장중 스캐너용 통계 카운터 바구니 초기화!
    drop_stats = {'ai_prob': 0, 'trend': 0, 'supply': 0, 'error': 0}

    for stock in hot_stocks:
        code, name, curr_price, curr_vol = stock['code'], stock['name'], stock['price'], stock['vol']

        # 💡 DB 매니저로 종목 데이터 호출
        df = db.get_stock_data(code, limit=60)
        if len(df) < 30: continue

        df = df.sort_values('Date').reset_index(drop=True)

        # 🚀 가상 일봉(오늘) 추가 또는 덮어쓰기
        if df.iloc[-1]['Date'] != today_str:
            new_row = df.iloc[-1].copy()
            new_row['Date'] = today_str
            new_row['Close'] = curr_price
            if curr_vol > 0: new_row['Volume'] = curr_vol
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        else:
            df.at[df.index[-1], 'Close'] = curr_price
            if curr_vol > 0: df.at[df.index[-1], 'Volume'] = curr_vol

        # 💡 [핵심] 장중 스캐너 역시 feature_engineer로 단번에 계산!
        df = calculate_all_features(df)

        # 주가 위치 판독
        h60, l60 = df['High'].tail(60).max(), df['Low'].tail(60).min()
        pos_pct = (curr_price - l60) / (h60 - l60 + 1e-9)
        pos_tag = 'BREAKOUT' if pos_pct >= 0.8 else ('BOTTOM' if pos_pct <= 0.3 else 'MIDDLE')

        # AI 모델 예측
        latest_row = df.iloc[[-1]]
        try:
            preds = [
                m_xgb.predict_proba(latest_row[FEATURES_XGB])[0][1],
                m_lgbm.predict_proba(latest_row[FEATURES_LGBM])[0][1],
                b_xgb.predict_proba(latest_row[FEATURES_XGB])[0][1],
                b_lgbm.predict_proba(latest_row[FEATURES_LGBM])[0][1]
            ]

            p_final = meta_model.predict_proba(
                pd.DataFrame([preds], columns=['XGB_Prob', 'LGBM_Prob', 'Bull_XGB_Prob', 'Bull_LGBM_Prob']))[0][1]

            # ==========================================
            # 💡 [신규] 황금 임계값 및 스마트 머니 필터 장착
            # ==========================================
            # 1. 확신도 필터 (constants.py 동기화)
            if p_final < TRADING_RULES['PROB_INTRADAY_PICK']:
                drop_stats['ai_prob'] += 1  # 카운터 증가
                continue

            # 2. 20일 이동평균선 아래(역배열) 종목은 패스 (낙폭과대 발굴 시 주석 처리 가능)
            #latest_close = latest_row['Close'].values[0]
            #latest_ma20 = latest_row['MA20'].values[0]
            #if latest_close < latest_ma20:
            #    drop_stats['trend'] += 1  # 카운터 증가
            #    continue

            # 3. [V3.1] 외국인/기관 매집 '가속도' 필터
            f_roll5 = latest_row['Foreign_Net_Roll5'].values[0]
            i_roll5 = latest_row['Inst_Net_Roll5'].values[0]

            # 에러 방지를 위해 get() 메서드로 안전하게 호출
            f_accel = latest_row.get('Foreign_Net_Accel', pd.Series([0])).values[0]
            i_accel = latest_row.get('Inst_Net_Accel', pd.Series([0])).values[0]

            # 조건: 5일 누적이 양수이면서, 가속도(Accel)까지 플러스(+)로 전환된 곳이 한 곳이라도 있어야 통과!
            is_foreign_buying = (f_roll5 > 0 and f_accel > 0)
            is_inst_buying = (i_roll5 > 0 and i_accel > 0)

            if not (is_foreign_buying or is_inst_buying):
                drop_stats['supply'] += 1  # 🚨 에러가 발생했던 부분 완벽 해결!
                continue

            # 모든 필터를 뚫은 종목만 추가
            new_targets.append(
                {'Name': name, 'Prob': p_final, 'Price': int(curr_price), 'Code': code, 'Position': pos_tag}
            )
        except Exception as e:
            drop_stats['error'] += 1  # 카운터 증가
            continue

    # ==========================================
    # 4. 분석 결과 DB 기록 및 반환
    # ==========================================
    # 💡 [신규] 장중 스캐너도 터미널에 필터링 통계를 출력해 줍니다.
    print("\n" + "=" * 50)
    print(f"🛑 [장중 스캐너 필터링 결과] 총 {len(hot_stocks)}개 중 {len(new_targets)}개 생존")
    print(f"  - AI 확신도 부족(<{int(TRADING_RULES['PROB_INTRADAY_PICK'] * 100)}%): {drop_stats['ai_prob']}개")
    print(f"  - 역배열(20일선 아래) / 임시로 적용 제외중: {drop_stats['trend']}개")
    print(f"  - 수급 부재(매집 가속도 미달): {drop_stats['supply']}개")
    print(f"  - 데이터 계산 에러: {drop_stats['error']}개")
    print("=" * 50 + "\n")

    if new_targets:
        for t in new_targets:
            db.save_recommendation(today_str, t['Code'], t['Name'], t['Price'], 'MAIN', t['Position'], prob=t['Prob'])
        print(f"🎯 장중 AI 재스캔 완료! {len(new_targets)}개의 주도주가 스나이퍼 엔진에 전달됩니다.")

    return new_targets


# ==========================================
# 🚀 [신규 모듈] 외부 스캐너용 순수 AI 판독 함수 (모듈화)
# ==========================================
def load_models():
    """AI 모델들을 메모리에 한 번만 로드하여 튜플로 반환합니다."""
    try:
        m_xgb = joblib.load(os.path.join(DATA_DIR, 'hybrid_xgb_model.pkl'))
        m_lgbm = joblib.load(os.path.join(DATA_DIR, 'hybrid_lgbm_model.pkl'))
        b_xgb = joblib.load(os.path.join(DATA_DIR, 'bull_xgb_model.pkl'))
        b_lgbm = joblib.load(os.path.join(DATA_DIR, 'bull_lgbm_model.pkl'))
        meta_model = joblib.load(os.path.join(DATA_DIR, 'stacking_meta_model.pkl'))
        return (m_xgb, m_lgbm, b_xgb, b_lgbm, meta_model)
    except Exception as e:
        print(f"❌ AI 모델 로드 실패: {e}")
        return None


def predict_prob_for_df(df, models):
    """
    일봉 DataFrame을 입력받아 피처를 계산하고,
    최종 AI Stacking 확신지수(Prob)를 반환합니다.
    """
    m_xgb, m_lgbm, b_xgb, b_lgbm, meta_model = models

    # 🛡️ [절대 방어막] 수급/신용 데이터 누락 시 강제 주입
    for col in ['Retail_Net', 'Foreign_Net', 'Inst_Net', 'Margin_Rate']:
        if col not in df.columns:
            df[col] = 0.0

    # 1. 기술적 지표(피처) 일괄 계산
    df = calculate_all_features(df)

    # 2. 가장 최신 일자(오늘)의 데이터 한 줄만 추출
    latest_row = df.iloc[[-1]].replace([np.inf, -np.inf], np.nan).fillna(0)

    # 3. 개별 모델 예측
    preds = [
        m_xgb.predict_proba(latest_row[FEATURES_XGB])[0][1],
        m_lgbm.predict_proba(latest_row[FEATURES_LGBM])[0][1],
        b_xgb.predict_proba(latest_row[FEATURES_XGB])[0][1],
        b_lgbm.predict_proba(latest_row[FEATURES_LGBM])[0][1]
    ]

    # 4. 메타 모델(Stacking) 최종 예측
    p_final = meta_model.predict_proba(
        pd.DataFrame([preds], columns=['XGB_Prob', 'LGBM_Prob', 'Bull_XGB_Prob', 'Bull_LGBM_Prob'])
    )[0][1]

    return float(p_final)

if __name__ == "__main__":
    run_integrated_scanner()