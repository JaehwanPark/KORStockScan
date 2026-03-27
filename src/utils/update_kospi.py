import sys
import subprocess
from pathlib import Path

# ==========================================
# 🚀 [핵심 방어] 프로젝트 루트 경로를 sys.path에 동적으로 추가
# ==========================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

import os
import pandas as pd
import numpy as np
from pandas.api.types import is_string_dtype, is_bool_dtype, is_numeric_dtype
import time
import logging
import json
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta
from sqlalchemy import text
import FinanceDataReader as fdr

# --- [Level 2: 공통 모듈 명시적 상대 경로 반영] ---
from src.utils import kiwoom_utils
from src.model.ml_v2_common import calculate_all_features
from src.database.db_manager import DBManager 
from src.database.models import DailyStockQuote  
from src.core.event_bus import EventBus

# 💡 [핵심 교정] 텔레그램 매니저를 초대해야 수신기가 EventBus에 정상 등록됩니다!
import src.notify.telegram_manager as telegram_manager

# ==========================================
# 1. 경로 및 로깅 설정
# ==========================================
LOG_DIR = os.path.join(PROJECT_ROOT, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

LOG_PATH = os.path.join(LOG_DIR, 'update_kospi_error.log')
TABLE_NAME = 'daily_stock_quotes'

# Constants
CUTOFF_DAYS = 100
API_DELAY_SECONDS = 0.3
LOG_MAX_BYTES = 5 * 1024 * 1024
LOG_BACKUP_COUNT = 3
BULK_CHUNKSIZE = 500
PROGRESS_INTERVAL = 50

# 전문 로거 세팅 (터미널+파일)
logger = logging.getLogger("KospiUpdater")
logger.setLevel(logging.INFO)

if not logger.handlers:
    file_handler = RotatingFileHandler(LOG_PATH, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(console_handler)

logger.info("🧠 Nightly feature source: src.model.ml_v2_common.calculate_all_features")

# 💡 [핵심 매핑] 모델 스키마와 완벽 동기화 (Return -> daily_return 포함)
COLUMN_MAPPING = {
    'Date': 'quote_date',
    'Code': 'stock_code',
    'Name': 'stock_name',
    'Open': 'open_price',
    'High': 'high_price',
    'Low': 'low_price',
    'Close': 'close_price',
    'Volume': 'volume',
    'MA5': 'ma5',
    'MA20': 'ma20',
    'MA60': 'ma60',
    'MA120': 'ma120',
    'RSI': 'rsi',
    'MACD': 'macd',
    'MACD_Sig': 'macd_sig',
    'MACD_Hist': 'macd_hist',
    'BBL': 'bbl',
    'BBM': 'bbm',
    'BBU': 'bbu',
    'BBB': 'bbb',
    'BBP': 'bbp',
    'VWAP': 'vwap',
    'OBV': 'obv',
    'ATR': 'atr',
    'Return': 'daily_return',  # 💡 예약어 충돌 회피
    'Marcap': 'marcap',
    'Retail_Net': 'retail_net',
    'Foreign_Net': 'foreign_net',
    'Inst_Net': 'inst_net',
    'Margin_Rate': 'margin_rate',
    'Is_NXT': 'is_nxt'
}

def _normalize_feature_output_columns(df: pd.DataFrame) -> pd.DataFrame:
    """feature 함수 출력 컬럼을 nightly update 스키마에 맞게 정규화합니다."""
    rename_map = {
        'return': 'Return',
        'return_1d': 'Return',
        'ma5': 'MA5',
        'ma20': 'MA20',
        'ma60': 'MA60',
        'ma120': 'MA120',
        'rsi': 'RSI',
        'macd': 'MACD',
        'macd_sig': 'MACD_Sig',
        'macd_hist': 'MACD_Hist',
        'bbl': 'BBL',
        'bbm': 'BBM',
        'bbu': 'BBU',
        'bbb': 'BBB',
        'bbp': 'BBP',
        'vwap20': 'VWAP',
        'vwap': 'VWAP',
        'obv': 'OBV',
        'atr': 'ATR',
        'date': 'Date',
        'code': 'Code',
        'name': 'Name',
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume',
        'foreign_net': 'Foreign_Net',
        'inst_net': 'Inst_Net',
        'margin_rate': 'Margin_Rate',
        'is_nxt': 'Is_NXT',
    }
    applicable = {k: v for k, v in rename_map.items() if k in df.columns and v not in df.columns}
    return df.rename(columns=applicable)

def _sanitize_daily_input(df: pd.DataFrame, code_str: str) -> pd.DataFrame:
    """지표 계산 전에 Datetime/숫자 입력을 정규화합니다."""
    out = df.copy()
    if 'index' in out.columns and 'Date' not in out.columns:
        out = out.rename(columns={'index': 'Date'})

    out['Date'] = pd.to_datetime(out['Date'], errors='coerce')
    numeric_cols = ['Open', 'High', 'Low', 'Close', 'Volume', 'Retail_Net', 'Foreign_Net', 'Inst_Net', 'Margin_Rate']
    for col in numeric_cols:
        if col not in out.columns:
            out[col] = 0.0
        out[col] = pd.to_numeric(out[col], errors='coerce')

    raw_rows = len(out)
    diag_cols = [c for c in ['Date', 'Open', 'High', 'Low', 'Close', 'Volume'] if c in out.columns]
    if len(diag_cols) == 6:
        null_diag = out[diag_cols].isnull().sum().to_dict()
    else:
        null_diag = {"missing_cols": [c for c in ['Date', 'Open', 'High', 'Low', 'Close', 'Volume'] if c not in out.columns]}

    out = out.sort_values('Date').dropna(subset=['Date', 'Open', 'High', 'Low', 'Close', 'Volume']).copy()
    out[['Retail_Net', 'Foreign_Net', 'Inst_Net', 'Margin_Rate']] = out[['Retail_Net', 'Foreign_Net', 'Inst_Net', 'Margin_Rate']].fillna(0.0)

    if len(out) < 20:
        logger.warning(
            f"⚠️ [{code_str}] 유효 OHLCV 부족으로 종목 스킵 "
            f"(원본 {raw_rows}행 -> 정제 후 {len(out)}행, nulls={null_diag})"
        )
        return pd.DataFrame()

    return out

# ==========================================
# 2. 공통 코드 정규화 헬퍼
# ==========================================
def _normalize_stock_code(code) -> str:
    raw = str(code or "").strip().upper().replace('.0', '')
    if raw.endswith('_AL'):
        raw = raw[:-3]
    if raw.startswith('A') and len(raw) >= 7:
        raw = raw[1:]
    digits = ''.join(ch for ch in raw if ch.isdigit())
    return digits[-6:].zfill(6) if digits else raw

# ==========================================
# 3. 메인 업데이트 로직
# ==========================================
def process_and_save_stock(code, token, session, is_nxt=False) -> pd.DataFrame:
    """단일 종목 데이터를 키움 API로 병합하고 DB에 적재합니다."""
    try:
        # 💡 [안전 장치 1] Margin_Rate API(ka10013)는 무조건 6자리 문자열을 요구합니다.
        code_str = str(code).zfill(6)

        # 1. API 순차 호출
        df_ohlcv = kiwoom_utils.get_daily_ohlcv_ka10081_df(token, code_str)
        if df_ohlcv.empty: return pd.DataFrame()
        # 💡 [안전 장치 2] 조인(Join) 실패를 막기 위해 인덱스를 날짜형(Datetime)으로 강제 통일
        df_ohlcv.index = pd.to_datetime(df_ohlcv.index, errors='coerce')

        df_investor = kiwoom_utils.get_investor_daily_ka10059_df(token, code_str, is_nxt=is_nxt)
        if not df_investor.empty:
            df_investor.index = pd.to_datetime(df_investor.index, errors='coerce')

        df_margin = kiwoom_utils.get_margin_daily_ka10013_df(token, code_str, is_nxt=is_nxt)
        if not df_margin.empty:
            df_margin.index = pd.to_datetime(df_margin.index, errors='coerce')

        basic_info = kiwoom_utils.get_basic_info_ka10001(token, code_str) or {}
        
        # 2. Date 기준 무결점 병합 (Join)
        df = df_ohlcv
        if not df_investor.empty:
            df = df.join(df_investor, how='left')
        else:
            for col in ['Retail_Net', 'Foreign_Net', 'Inst_Net']: df[col] = np.nan

        if not df_margin.empty:
            df = df.join(df_margin, how='left')
        else:
            df['Margin_Rate'] = np.nan

        # 💡 [안전 장치 3] 0으로 덮어버리기 전에, 어제 발표된 Margin_Rate를 오늘 빈칸으로 끌어내림 (ffill)
        # Forward fill only for missing investor and margin data
        cols_to_ffill = ['Margin_Rate', 'Retail_Net', 'Foreign_Net', 'Inst_Net']
        for col in cols_to_ffill:
            if col in df.columns:
                df[col] = df[col].ffill()
        # 그 뒤에 진짜로 데이터가 없는 상장 초기 빈칸들만 0으로 채움
        df.fillna({'Retail_Net': 0, 'Foreign_Net': 0, 'Inst_Net': 0, 'Margin_Rate': 0}, inplace=True)
        
        df = df.reset_index()
        
        # 인덱스 이름 보정 (reset_index 후 이름이 index가 될 수 있음)
        if 'index' in df.columns and 'Date' not in df.columns:
            df.rename(columns={'index': 'Date'}, inplace=True)
        
        # 3. 지표 계산 전 입력 정제
        df = _sanitize_daily_input(df, code_str)
        if df.empty:
            return pd.DataFrame()

        # 💡 [핵심 복구 1] 종목 코드, 이름, 그리고 시가총액(Marcap) 주입!
        df['Code'] = code_str
        df['Name'] = basic_info.get('Name') or '이름없음'
        df['Marcap'] = basic_info.get('Marcap') or 0
        df['Is_NXT'] = bool(is_nxt)

        # 💡 [핵심 복구 2] 지표 계산 전 원본 데이터 완벽 백업
        backup_df = df.copy()
        original_cols = df.columns.tolist()

        # 4. feature 계산 (nightly SSOT)
        # ml_v2_common.calculate_all_features는 quote_date, stock_code 컬럼을 기대함
        df_feat = df.rename(columns={'Date': 'quote_date', 'Code': 'stock_code'})
        df_feat = calculate_all_features(df_feat)
        df = _normalize_feature_output_columns(df_feat)

        # 💡 [핵심 복구 3] 원본 컬럼 강제 복원 (지표 계산기가 0으로 덮어쓰는 것 원천 차단)
        for col in original_cols:
            if col in ['Marcap', 'Margin_Rate', 'Retail_Net', 'Foreign_Net', 'Inst_Net', 'Code', 'Name', 'Is_NXT']:
                df[col] = backup_df[col].values
            elif col not in df.columns:
                df[col] = backup_df[col].values

        # Ensure 'Return' column exists for mapping
        if 'Return' not in df.columns:
            # Compute daily return as percentage change of close_price
            if 'Close' in df.columns:
                df['Return'] = pd.to_numeric(df['Close'], errors='coerce').pct_change().fillna(0.0)
            else:
                df['Return'] = 0.0

        if 'Date' not in df.columns:
            raise ValueError(f'[{code_str}] feature 출력에 Date 컬럼이 없습니다.')
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

        # 5. DB 컬럼명으로 최종 변환
        final_valid_cols = [col for col in COLUMN_MAPPING.keys() if col in df.columns]
        df = df[final_valid_cols].rename(columns=COLUMN_MAPPING)

        # 6. 최근 100일치 슬라이싱
        cutoff_ts = pd.Timestamp(datetime.now().date() - timedelta(days=CUTOFF_DAYS))
        new_rows = df[df['quote_date'] >= cutoff_ts].copy()

        # 7. DB 적재 전 정리
        if 'quote_date' in new_rows.columns:
            new_rows['quote_date'] = pd.to_datetime(new_rows['quote_date'], errors='coerce').dt.date
        if 'is_nxt' in new_rows.columns:
            new_rows['is_nxt'] = new_rows['is_nxt'].fillna(False).astype(bool)

        new_rows = new_rows.dropna(subset=['quote_date', 'close_price', 'daily_return'])
        new_rows = new_rows.replace([np.inf, -np.inf], np.nan)

        # 💡 [핵심 복구 4] 결측치(NaN) 완벽 제거 및 0 채우기 (PostgreSQL 에러 원천 차단)
        # Fill NaN with appropriate defaults per column type
        # Ensure numeric columns are numeric (convert object dtype)
        numeric_cols = ['open_price', 'high_price', 'low_price', 'close_price', 'volume',
                        'ma5', 'ma20', 'ma60', 'ma120', 'rsi', 'macd', 'macd_sig', 'macd_hist',
                        'bbl', 'bbm', 'bbu', 'bbb', 'bbp', 'vwap', 'obv', 'atr', 'daily_return',
                        'marcap', 'retail_net', 'foreign_net', 'inst_net', 'margin_rate']
        for col in numeric_cols:
            if col in new_rows.columns:
                new_rows[col] = pd.to_numeric(new_rows[col], errors='coerce')
        
        for col in new_rows.columns:
            if is_numeric_dtype(new_rows[col]):
                new_rows[col] = new_rows[col].fillna(0)
            elif is_string_dtype(new_rows[col]):
                new_rows[col] = new_rows[col].fillna('')
            elif is_bool_dtype(new_rows[col]):
                new_rows[col] = new_rows[col].fillna(False)
            else:
                # fallback: fill with empty string
                new_rows[col] = new_rows[col].fillna('')

        # 안전한 최종 컬럼 필터링
        final_cols = [col for col in COLUMN_MAPPING.values() if col in new_rows.columns]

        return new_rows[final_cols]

    except Exception as e:
        logger.error(f"❌ [{code}] 처리 중 치명적 에러: {e}", exc_info=True)
        return pd.DataFrame()
        
# ==========================================
# 3. 전체 스케줄러 (배치 메인)
# ==========================================
def update_kospi_data():
    logger.info("📅 오늘이 주식시장 개장일인지 확인합니다...")
    
    is_open, reason = kiwoom_utils.is_trading_day()
    # is_open, reason = True, "정상거래일 (MOCK)"
    
    event_bus = EventBus()
    
    if not is_open:
        logger.info(f"🛑 오늘은 {reason} 휴장일이므로 데이터베이스 업데이트를 종료합니다.")
        return

    logger.info("=== KORStockScan 일일 데이터 수집 (PostgreSQL 정식가동) ===")
    
    db = DBManager()
    db.init_db()

    kiwoom_token = kiwoom_utils.get_kiwoom_token()
    if not kiwoom_token:
        logger.error("❌ 키움 토큰 발급 실패! 시스템을 종료합니다.")
        event_bus.publish('TELEGRAM_BROADCAST', {'message': "🚨 [데이터 갱신 실패] 키움 토큰 발급 오류", 'audience': 'ADMIN_ONLY'})
        return

    event_bus.publish('TELEGRAM_BROADCAST', {'message': "🔄 전 종목 일일 데이터 갱신을 시작합니다. (약 15분 소요)", 'audience': 'ADMIN_ONLY'})

    kospi_codes = []
    # ========================================================
    # 💡 [1순위] FinanceDataReader를 통해 최신 KOSPI/KOSDAQ 종목 수집
    # ========================================================
    try:
        logger.info("🔍 FinanceDataReader를 통해 최신 상장 종목 리스트를 수집합니다...")
        df_krx = fdr.StockListing('KRX')
        
        if not df_krx.empty:
            # 코스피, 코스닥 시장만 필터링 (코넥스 등 제외)
            df_filtered = df_krx[df_krx['Market'].isin(['KOSPI', 'KOSDAQ'])]
            kospi_codes = df_filtered['Code'].tolist()
            logger.info(f"✅ FDR 종목 수집 성공! 총 {len(kospi_codes)}개 (KOSPI/KOSDAQ) 종목")
        else:
            raise ValueError("FDR에서 빈 데이터를 반환했습니다.")
            
    except Exception as e:
        logger.warning(f"⚠️ FDR 종목 수집 실패 ({e}). 기존 DB 조회 방식으로 Fallback 합니다.")
        
        # ========================================================
        # 💡 [2순위 (Fallback)] 기존 방식: DB에서 수집된 이력이 있는 종목들 가져오기
        # ========================================================
        try:
            with db.engine.connect() as conn:
                # PostgreSQL 최적화 쿼리 유지
                df_codes = pd.read_sql(text(f"SELECT DISTINCT stock_code FROM {TABLE_NAME}"), conn)

            if df_codes.empty:
                logger.warning("⚠️ DB가 완전히 비어있고 FDR도 실패했습니다! 기초 데이터 셋업이 필요합니다.")
                return
            else:
                kospi_codes = df_codes['stock_code'].tolist()
                logger.info(f"✅ DB에서 종목 수집 성공! 총 {len(kospi_codes)}개 종목")
                
        except Exception as db_e:
            logger.error(f"❌ DB 종목 수집 중 에러: {db_e}", exc_info=True)
            return

    kospi_codes = sorted({_normalize_stock_code(c) for c in kospi_codes if c})
    total_count = len(kospi_codes)
    successful_codes = []

    nxt_map = kiwoom_utils.get_nxt_flag_map_ka10099(kiwoom_token, kospi_codes, mrkt_tps=("0", "10"))
    if nxt_map:
        nxt_count = int(sum(1 for v in nxt_map.values() if v))
        logger.info(f"✅ [ka10099] NXT 가능 종목 매핑 완료: {nxt_count}개")
    else:
        logger.warning("⚠️ [ka10099] NXT 가능 종목 매핑 실패. 최신 거래일 DB is_nxt 플래그로 폴백합니다.")
        nxt_map = db.get_latest_is_nxt_map(kospi_codes)
        nxt_count = int(sum(1 for v in nxt_map.values() if v))
    
    # 💡 [핵심] 900개 종목의 데이터를 담을 거대한 빈 리스트
    all_stocks_data = []

    logger.info(f"\n📦 총 {total_count}개 종목 메모리 적재를 시작합니다.\n")

    # [PHASE 1] 메모리에 데이터 차곡차곡 모으기
    with db.get_session() as session:
        for i, code in enumerate(kospi_codes):
            code_str = _normalize_stock_code(code)
            df_stock = process_and_save_stock(code_str, kiwoom_token, session, is_nxt=nxt_map.get(code_str, False))
            
            if df_stock is not None and not df_stock.empty:
                all_stocks_data.append(df_stock)
                successful_codes.append(code_str)

            if (i + 1) % PROGRESS_INTERVAL == 0:
                logger.info(f" ⏳ 수집 진행 상황: [{i + 1}/{total_count}] 완료...")

            time.sleep(API_DELAY_SECONDS) # API 제재 방지용 대기

    # [PHASE 2] 대망의 일괄 DB 삽입 (Bulk Insert)
    if all_stocks_data:
        logger.info("\n🚀 모든 데이터 수집 완료! PostgreSQL로 일괄 전송(Bulk-Insert)을 시작합니다...")
        
        # 모든 데이터프레임을 하나로 합치기
        final_bulk_df = pd.concat(all_stocks_data, ignore_index=True)
        cutoff_date = (datetime.now() - timedelta(days=CUTOFF_DAYS)).strftime('%Y-%m-%d')
        
        # Filter out rows that already exist in DB to avoid duplicate key errors
        existing_keys = set()
        if not final_bulk_df.empty and successful_codes:
            with db.engine.connect() as conn:
                # Build query for existing keys using same condition as delete
                query = text(f"""
                    SELECT quote_date, stock_code
                    FROM {TABLE_NAME}
                    WHERE quote_date >= :cutoff
                      AND stock_code = ANY(:codes)
                """)
                result = conn.execute(query, {'cutoff': cutoff_date, 'codes': successful_codes})
                existing_keys.update((row.quote_date, row.stock_code) for row in result)
        
        # Filter final_bulk_df
        if existing_keys:
            mask = final_bulk_df.apply(
                lambda row: (row['quote_date'], row['stock_code']) not in existing_keys, axis=1
            )
            final_bulk_df = final_bulk_df[mask].copy()
            logger.info(f"⏩ Filtered out {len(existing_keys)} existing rows, {len(final_bulk_df)} new rows to insert")
        
        # Attempt bulk insert with retry and fallback
        max_retries = 2
        inserted = False
        for attempt in range(max_retries):
            try:
                with db.engine.begin() as conn:
                    # 1. Delete existing data for these codes within cutoff
                    delete_query = text(f"DELETE FROM {TABLE_NAME} WHERE quote_date >= :date AND stock_code = ANY(:codes)")
                    conn.execute(delete_query, {'date': cutoff_date, 'codes': successful_codes})
                    
                    # 2. Insert new data with adaptive method
                    if attempt == 0:
                        # First attempt: multi-row insert with configured chunk size
                        final_bulk_df.to_sql(TABLE_NAME, con=conn, if_exists='append', index=False,
                                             chunksize=BULK_CHUNKSIZE, method='multi')
                    else:
                        # Fallback: single-row inserts (slower but reliable)
                        final_bulk_df.to_sql(TABLE_NAME, con=conn, if_exists='append', index=False,
                                             chunksize=BULK_CHUNKSIZE, method=None)
                
                logger.info(f"✅ DB 일괄 삽입 성공! (총 {len(final_bulk_df)}행 적재 완료)")
                inserted = True
                break
            except Exception as e:
                logger.warning(f"⚠️ DB 일괄 삽입 시도 {attempt+1} 실패: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"🔥 DB 일괄 삽입 중 치명적 에러 발생: {e}")
                else:
                    # Optionally reduce chunk size for next attempt
                    pass
        
        if not inserted:
            logger.error("🚨 DB 삽입 실패로 데이터가 저장되지 않았습니다.")
    else:
        logger.warning("⚠️ 수집된 데이터가 없어 DB 작업을 건너뜁니다.")

    logger.info(f"\n🎉 일일 업데이트 최종 완료! (성공: {len(successful_codes)} / {total_count} 종목)")
    
    finish_msg = f"✅ **KOSPI 일일 데이터 갱신 완료**\n총 **{len(successful_codes)} / {total_count}** 종목의 캔들 및 수급 데이터가 DB에 일괄 적재되었습니다.\n🟣 NXT 대상 플래그 반영: **{nxt_count}개**"
    event_bus.publish('TELEGRAM_BROADCAST', {'message': finish_msg, 'audience': 'ADMIN_ONLY', 'parse_mode': 'Markdown'})

if __name__ == "__main__":
    # 1. 데이터 업데이트 실행
    update_kospi_data()
    
    # 2. 업데이트가 끝난 후 V2 추천 스크립트 실행
    logger.info("🚀 추천 모델(recommend_daily_v2.py)을 이어서 실행합니다...")
    try:
        # check=True는 에러 발생 시 프로세스를 중단시킵니다.
        subprocess.run([sys.executable, "src/model/recommend_daily_v2.py"], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ 추천 모델 실행 중 에러 발생: {e}")