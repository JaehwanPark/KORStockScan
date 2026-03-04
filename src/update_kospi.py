import os
import pandas as pd
import json
import time
import logging
from datetime import datetime, timedelta

# --- [내부 모듈만 사용] ---
import src.kiwoom_utils as kiwoom_utils
from src.db_manager import DBManager
from src.feature_engineer import calculate_all_features

# ==========================================
# 1. 경로 및 로깅 설정
# ==========================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..', 'data'))
os.makedirs(DATA_DIR, exist_ok=True)

CONFIG_PATH = os.path.join(DATA_DIR, 'config_prod.json')
# 💡 로그 파일명 변경 및 INFO 레벨로 조정 (에러 위주로만 조용하게 기록)
LOG_PATH = os.path.join(DATA_DIR, 'update_kospi.log')
TABLE_NAME = 'daily_stock_quotes'

logging.basicConfig(
    filename=LOG_PATH, level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8'
)


def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


# --- [2. DB 마이그레이션] ---
def migrate_db(db: DBManager):
    """DB 스키마 점검 및 누락 컬럼 자동 추가"""
    with db._get_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info({TABLE_NAME})")
        columns = [info[1] for info in cur.fetchall()]

        if not columns:
            conn.execute(f"""
                CREATE TABLE {TABLE_NAME} (
                    Date TEXT, Code TEXT, Name TEXT,
                    Open REAL, High REAL, Low REAL, Close REAL, Volume REAL,
                    MA5 REAL, MA20 REAL, MA60 REAL, MA120 REAL,
                    RSI REAL, MACD REAL, MACD_Sig REAL, MACD_Hist REAL,
                    BBL REAL, BBM REAL, BBU REAL, BBB REAL, BBP REAL,
                    VWAP REAL, OBV REAL, ATR REAL, Return REAL, 
                    Marcap INTEGER DEFAULT 0, Retail_Net REAL DEFAULT 0, 
                    Foreign_Net REAL DEFAULT 0, Inst_Net REAL DEFAULT 0, Margin_Rate REAL DEFAULT 0,
                    PRIMARY KEY (Date, Code)
                )
            """)
        else:
            if 'Marcap' not in columns: conn.execute(f"ALTER TABLE {TABLE_NAME} ADD COLUMN Marcap INTEGER DEFAULT 0")
            for col in ['Retail_Net', 'Foreign_Net', 'Inst_Net', 'Margin_Rate']:
                if col not in columns: conn.execute(f"ALTER TABLE {TABLE_NAME} ADD COLUMN {col} REAL DEFAULT 0")
        conn.commit()


# --- [3. 메인 업데이트 로직] ---
def process_and_save_stock(code, token, db: DBManager):
    """단일 종목 데이터를 키움 API로 병합하고 DB에 적재합니다."""
    try:
        # 1. API 병렬 호출
        df_ohlcv = kiwoom_utils.get_daily_ohlcv_ka10081_df(token, code)
        if df_ohlcv.empty: return False

        df_investor = kiwoom_utils.get_investor_daily_ka10059_df(token, code)
        df_margin = kiwoom_utils.get_margin_daily_ka10013_df(token, code)
        basic_info = kiwoom_utils.get_basic_info_ka10001(token, code)

        # 2. Date 기준 무결점 병합 (Join)
        df = df_ohlcv
        if not df_investor.empty:
            df = df.join(df_investor, how='left')
        else:
            df['Retail_Net'] = 0; df['Foreign_Net'] = 0; df['Inst_Net'] = 0

        if not df_margin.empty:
            df = df.join(df_margin, how='left')
        else:
            df['Margin_Rate'] = 0

        df.fillna({'Retail_Net': 0, 'Foreign_Net': 0, 'Inst_Net': 0, 'Margin_Rate': 0}, inplace=True)
        df = df.reset_index()
        df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')

        # 3. 보조 지표 계산
        df = calculate_all_features(df)

        df['Code'] = code
        df['Name'] = basic_info['Name']
        df['Marcap'] = basic_info['Marcap']

        # 4. DB 적재
        cutoff_date = (datetime.now() - timedelta(days=100)).strftime('%Y-%m-%d')
        new_rows = df[df['Date'] >= cutoff_date].copy()

        if not new_rows.empty:
            with db._get_connection() as conn:
                conn.execute(f"DELETE FROM {TABLE_NAME} WHERE Code='{code}' AND Date >= '{cutoff_date}'")
                cols = ['Date', 'Code', 'Name', 'Open', 'High', 'Low', 'Close', 'Volume',
                        'MA5', 'MA20', 'MA60', 'MA120', 'RSI', 'MACD', 'MACD_Sig', 'MACD_Hist',
                        'BBL', 'BBM', 'BBU', 'BBB', 'BBP', 'VWAP', 'OBV', 'ATR', 'Return',
                        'Marcap', 'Retail_Net', 'Foreign_Net', 'Inst_Net', 'Margin_Rate']
                new_rows[cols].dropna(subset=['Close']).to_sql(TABLE_NAME, conn, if_exists='append', index=False)
            return True
        return False

    except Exception as e:
        logging.error(f"[{code}] 시스템 에러 발생: {e}")
        return False


# --- [4. 전체 스케줄러] ---
def update_kospi_data():
    # 💡 휴장일 체크 로직 정상 복구
    print("📅 오늘이 주식시장 개장일인지 확인합니다...")
    is_open, reason = kiwoom_utils.is_trading_day()
    if not is_open:
        print(f"🛑 오늘은 {reason} 휴장일이므로 데이터베이스 업데이트를 종료합니다.")
        return

    print("=== KORStockScan 일일 데이터 수집 (Kiwoom API 전용 정식가동) ===")

    db = DBManager()
    conf = load_config()

    migrate_db(db)

    kiwoom_token = kiwoom_utils.get_kiwoom_token(conf)
    if not kiwoom_token:
        print("❌ 키움 토큰 발급 실패! 시스템을 종료합니다.")
        return

    kospi_codes = []
    try:
        with db._get_connection() as conn:
            df_codes = pd.read_sql(f"SELECT DISTINCT Code FROM {TABLE_NAME}", conn)

        if df_codes.empty:
            print("⚠️ DB가 완전히 비어있습니다! 기초 데이터 셋업이 필요합니다.")
            return
        else:
            kospi_codes = df_codes['Code'].tolist()
    except Exception as e:
        print(f"❌ DB 종목 수집 중 에러: {e}")
        return

    # 💡 100종목 제한 해제 (전체 종목 처리)
    total_count = len(kospi_codes)
    success_count = 0

    print(f"\n🚀 총 {total_count}개 종목 업데이트를 시작합니다. (약 10~20분 소요)\n")

    for i, code in enumerate(kospi_codes):
        if process_and_save_stock(code, kiwoom_token, db):
            success_count += 1

        # 💡 터미널 복잡도 완화: 50종목마다 한 줄씩만 진행률 표시
        if (i + 1) % 50 == 0:
            print(f" ⏳ 진행 상황: [{i + 1}/{total_count}] 완료...")

        # 키움 서버 부하 방지용 딜레이
        time.sleep(0.3)

    print(f"\n🎉 일일 업데이트 완료! (최종 성공: {success_count} / {total_count} 종목)")


if __name__ == "__main__":
    update_kospi_data()