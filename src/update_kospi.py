import os
import pandas as pd
import FinanceDataReader as fdr
import json
import time
import logging
from datetime import datetime, timedelta

# --- [새로 분리한 커스텀 모듈] ---
from src.feature_engineer import calculate_all_features
from src.db_manager import DBManager
from src.data_client import DataClient
import src.kiwoom_utils as kiwoom_utils

# ==========================================
# 1. 경로 및 로깅 설정 (상대 참조)
# ==========================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..', 'data'))
os.makedirs(DATA_DIR, exist_ok=True)

CONFIG_PATH = os.path.join(DATA_DIR, 'config_prod.json')
LOG_PATH = os.path.join(DATA_DIR, 'update_kospi.log')

TABLE_NAME = 'daily_stock_quotes'
EXT_TABLE_NAME = 'external_indicators'

logging.basicConfig(
    filename=LOG_PATH, level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8'
)


def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


# --- [2. DB 마이그레이션: Marcap 컬럼 추가] ---
def migrate_db(db: DBManager, client: DataClient):
    """DB에 Marcap(시가총액) 및 수급, 신용잔고율 컬럼이 없는 경우 추가합니다."""
    with db._get_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info({TABLE_NAME})")
        columns = [info[1] for info in cur.fetchall()]

        # 1. Marcap 추가 및 과거 데이터 일괄 업데이트
        if 'Marcap' not in columns:
            print("⚠️ DB 스키마 업데이트: Marcap(시가총액) 컬럼을 추가합니다.")
            conn.execute(f"ALTER TABLE {TABLE_NAME} ADD COLUMN Marcap INTEGER DEFAULT 0")
            conn.commit()

            # 💡 [핵심] fdr 직접 호출 대신 DataClient 비서를 통해 우회 방어된 리스트를 받음!
            try:
                df_krx = client.get_kospi_symbols()
                if not df_krx.empty and 'Marcap' in df_krx.columns:
                    updates = []
                    for _, r in df_krx.iterrows():
                        c = r['Code']
                        m = r['Marcap'] if pd.notna(r['Marcap']) else 0
                        updates.append((int(m), c))
                    cur.executemany(f"UPDATE {TABLE_NAME} SET Marcap = ? WHERE Code = ?", updates)
                    conn.commit()
                    print("✅ 기존 데이터 Marcap 일괄 업데이트 완료.")
            except Exception as e:
                print(f"❌ Marcap 업데이트 실패: {e}")

        # 2. 신규 수급 & 신용잔고율 컬럼 추가
        new_cols = ['Retail_Net', 'Foreign_Net', 'Inst_Net', 'Margin_Rate']
        for col in new_cols:
            if col not in columns:
                print(f"⚠️ DB 스키마 업데이트: {col} 컬럼을 추가합니다.")
                conn.execute(f"ALTER TABLE {TABLE_NAME} ADD COLUMN {col} REAL DEFAULT 0")

        conn.commit()


# --- [3. 외부 지표 수집] ---
def update_external_indicators(db: DBManager):
    """환율 및 미국채 10년물 금리를 업데이트합니다."""
    print("🌍 외부 거시경제 지표 수집 중...")
    try:
        start_dt = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
        df_ex = fdr.DataReader('USD/KRW', start_dt)
        df_bond = fdr.DataReader('US10YT', start_dt)

        if not df_ex.empty and not df_bond.empty:
            df_ex = df_ex[['Close']].rename(columns={'Close': 'USD_KRW'})
            df_bond = df_bond[['Close']].rename(columns={'Close': 'US10YT'})

            df_merged = df_ex.join(df_bond, how='inner')

            with db._get_connection() as conn:
                df_merged.to_sql(EXT_TABLE_NAME, conn, if_exists='replace', index=True)
            print("✅ 외부 지표 업데이트 완료")
    except Exception as e:
        print(f"❌ 외부 지표 업데이트 실패: {e}")


# --- [4. 일일 데이터 업데이트 (메인)] ---
def update_kospi_data():
    print(f"=== KORStockScan 일일 데이터 수집 및 갱신 시작 ===")

    db = DBManager()
    conf = load_config()

    # 💡 [핵심] 마이그레이션에서도 방어막을 쓰기 위해 DataClient를 가장 먼저 생성
    kiwoom_token = kiwoom_utils.get_kiwoom_token(conf)
    if not kiwoom_token:
        print("⚠️ 키움 토큰 발급 실패. FDR 단독 모드로 수집을 시도합니다.")
    client = DataClient(kiwoom_token)

    # DB 초기 점검 및 외부 지표 갱신
    migrate_db(db, client)
    update_external_indicators(db)

    # 키움 토큰 발급 및 DataClient 초기화
    kiwoom_token = kiwoom_utils.get_kiwoom_token(conf)
    if not kiwoom_token:
        print("⚠️ 키움 토큰 발급 실패. FDR 단독 모드로 수집을 시도합니다.")
    client = DataClient(kiwoom_token)

    # 코스피 종목 목록 수집
    kospi_list = client.get_kospi_symbols()
    if kospi_list.empty:
        print("❌ 종목 리스트 수집 실패로 업데이트를 중단합니다.")
        return

    # 업데이트 기준일 설정 (60일치 확보 목적)
    cutoff_date = datetime.now() - timedelta(days=60)

    total_count = len(kospi_list)
    success_count = 0
    print(f"📊 총 {total_count}개 종목 업데이트를 시작합니다...")

    for index, row in kospi_list.iterrows():
        code, name = row['Code'], row['Name']
        marcap = row.get('Marcap', 0)
        if pd.isna(marcap): marcap = 0

        # 💡 [데이터 자가 치유(Auto-Healing) 방어막]
        # FDR 통신 에러 등으로 marcap이 0으로 수신되었다면,
        # 기존 DB를 뒤져서 0이 아닌 마지막 정상 시가총액을 찾아내어 복구합니다!
        if marcap == 0:
            try:
                with db._get_connection() as conn:
                    # 0을 건너뛰고 가장 최근에 저장된 정상적인 Marcap 조회
                    res = conn.execute(
                        f"SELECT Marcap FROM {TABLE_NAME} WHERE Code='{code}' AND Marcap > 0 ORDER BY Date DESC LIMIT 1").fetchone()
                    if res:
                        marcap = res[0]
            except Exception:
                pass  # DB에도 정상값이 없다면 어쩔 수 없이 0 유지

        try:
            # 기존 종목의 가장 최근 저장 날짜 조회
            last_date_str = db.get_last_date(TABLE_NAME, date_col='Date', code_col='Code', code=code)

            if last_date_str:
                last_date = datetime.strptime(last_date_str, '%Y-%m-%d')
                # 💡 [수정] 영업일수 120일 이상을 확실히 확보하기 위해 달력일수 200일을 뺍니다.
                fetch_start_date = last_date - timedelta(days=200)
            else:
                fetch_start_date = cutoff_date - timedelta(days=200)
                last_date_str = '1900-01-01'

            fetch_start_str = fetch_start_date.strftime('%Y-%m-%d')

            df = client.get_full_daily_data(code, fetch_start_str)

            # 💡 [수정] 신규 상장 종목 등도 통과할 수 있도록 최소 기준을 60으로 낮춥니다.
            # (MA120 등은 feature_engineer에서 알아서 bfill로 채워주므로 에러가 나지 않습니다.)
            if df.empty or len(df) < 60:
                continue

            # 💡 [FeatureEngineer 적용] 지표 계산
            df = calculate_all_features(df)
            df['Code'], df['Name'], df['Marcap'] = code, name, int(marcap)

            if pd.api.types.is_datetime64_any_dtype(df['Date']):
                df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')

                # 💡 [핵심 수정] 오늘 날짜만 넣는 것이 아니라, 최근 100일 치를 덮어쓰기(Overlap) 하여
                # 기존에 0으로 채워진 과거 데이터 구멍을 수급/신용 데이터로 꽉 메웁니다!
            overlap_date = (datetime.now() - timedelta(days=100)).strftime('%Y-%m-%d')
            new_rows = df[df['Date'] >= overlap_date]

            if not new_rows.empty:
                cols = [
                    'Date', 'Code', 'Name', 'Open', 'High', 'Low', 'Close', 'Volume',
                    'Retail_Net', 'Foreign_Net', 'Inst_Net', 'Margin_Rate',
                    'MA5', 'MA20', 'MA60', 'MA120', 'RSI', 'MACD', 'MACD_Sig', 'MACD_Hist',
                    'BBL', 'BBM', 'BBU', 'BBB', 'BBP', 'VWAP', 'OBV', 'ATR', 'Return', 'Marcap'
                ]
                with db._get_connection() as conn:
                    # 1. 0으로 빵꾸나 있는 최근 100일치 기존 데이터를 깔끔하게 삭제
                    conn.execute(f"DELETE FROM {TABLE_NAME} WHERE Code='{code}' AND Date >= '{overlap_date}'")
                    # 2. 키움 API에서 새로 긁어온 완벽한 데이터로 재삽입
                    new_rows[cols].dropna(subset=['Close']).to_sql(TABLE_NAME, conn, if_exists='append', index=False)

                # 터미널 창 복잡도 감소를 위해 print 대신 logging 활용 (또는 50개마다 출력)
            elif marcap > 0:
                # 새로운 행은 없지만 최신 행의 시총 업데이트
                db.execute_query(
                    f"UPDATE {TABLE_NAME} SET Marcap = ? WHERE Code = ? AND Date = (SELECT MAX(Date) FROM {TABLE_NAME} WHERE Code = ?)",
                    (int(marcap), code, code)
                )

            success_count += 1
            if success_count % 50 == 0:
                print(f"진행 상황: [{success_count}/{total_count}] 완료...")

                # [기존] time.sleep(0.5)
                time.sleep(1.0)  # 💡 1초로 늘려 서버 차단 확률을 대폭 낮춥니다.

        except Exception as e:
            logging.error(f"[{name}] 업데이트 에러: {e}")

    print(f"✅ 업데이트 완료! (성공: {success_count}개 종목)")


if __name__ == "__main__":
    update_kospi_data()