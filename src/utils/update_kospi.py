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
import time
import logging
import json
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta
from sqlalchemy import text
import FinanceDataReader as fdr

# --- [Level 2: 공통 모듈 명시적 상대 경로 반영] ---
from src.utils import kiwoom_utils
from src.model.feature_engineer import calculate_all_features
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
BULK_CHUNKSIZE = 2000
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
    'Margin_Rate': 'margin_rate'
}

# ==========================================
# 2. 메인 업데이트 로직
# ==========================================
def process_and_save_stock(code, token, session) -> pd.DataFrame:
    """단일 종목 데이터를 키움 API로 병합하고 DB에 적재합니다."""
    try:
        # 💡 [안전 장치 1] Margin_Rate API(ka10013)는 무조건 6자리 문자열을 요구합니다.
        code_str = str(code).zfill(6)

        # 1. API 순차 호출
        df_ohlcv = kiwoom_utils.get_daily_ohlcv_ka10081_df(token, code_str)
        if df_ohlcv.empty: return pd.DataFrame()
        # 💡 [안전 장치 2] 조인(Join) 실패를 막기 위해 인덱스를 날짜형(Datetime)으로 강제 통일
        df_ohlcv.index = pd.to_datetime(df_ohlcv.index)

        df_investor = kiwoom_utils.get_investor_daily_ka10059_df(token, code_str)
        if not df_investor.empty:
            df_investor.index = pd.to_datetime(df_investor.index)

        df_margin = kiwoom_utils.get_margin_daily_ka10013_df(token, code_str)
        if not df_margin.empty:
            df_margin.index = pd.to_datetime(df_margin.index)

        basic_info = kiwoom_utils.get_basic_info_ka10001(token, code_str)
        
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
            
        df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')

        # 💡 [핵심 복구 1] 종목 코드, 이름, 그리고 시가총액(Marcap) 주입!
        df['Code'] = code_str
        df['Name'] = basic_info.get('Name', '이름없음')
        df['Marcap'] = basic_info.get('Marcap', 0)  # 잘 들어오던 로직 그대로 유지!

        # 💡 [핵심 복구 2] 지표 계산 전 원본 데이터 완벽 백업
        backup_df = df.copy()
        original_cols = df.columns.tolist()

        # 3. 보조 지표 계산 (Return 컬럼 생성)
        df = calculate_all_features(df)

        # 🚨 [중요] feature_engineer가 소문자 'return'을 줬다면 대문자로 통일
        if 'return' in df.columns and 'Return' not in df.columns:
            df.rename(columns={'return': 'Return'}, inplace=True)

        # 💡 [핵심 복구 3] 원본 컬럼 강제 복원 (지표 계산기가 0으로 덮어쓰는 것 원천 차단)
        for col in original_cols:
            if col in ['Marcap', 'Margin_Rate', 'Retail_Net', 'Foreign_Net', 'Inst_Net', 'Code', 'Name']:
                df[col] = backup_df[col]
            elif col not in df.columns:
                df[col] = backup_df[col]

        # Ensure 'Return' column exists for mapping
        if 'Return' not in df.columns:
            # Compute daily return as percentage change of close_price
            if 'Close' in df.columns:
                df['Return'] = df['Close'].pct_change().fillna(0)
            else:
                df['Return'] = 0.0

        # 4. DB 컬럼명으로 최종 변환
        final_valid_cols = [col for col in COLUMN_MAPPING.keys() if col in df.columns]
        df = df[final_valid_cols].rename(columns=COLUMN_MAPPING)

        # 5. 최근 100일치 슬라이싱
        cutoff_date = (datetime.now() - timedelta(days=CUTOFF_DAYS)).strftime('%Y-%m-%d')
        new_rows = df[df['quote_date'] >= cutoff_date].copy()

        # 💡 [핵심 복구 4] 결측치(NaN) 완벽 제거 및 0 채우기 (PostgreSQL 에러 원천 차단)
        new_rows = new_rows.dropna(subset=['close_price', 'daily_return'])
        new_rows = new_rows.fillna(0)

        # 안전한 최종 컬럼 필터링
        final_cols = [col for col in COLUMN_MAPPING.values() if col in new_rows.columns]

        return new_rows[final_cols]

    except Exception as e:
        logger.error(f"❌ [{code}] 처리 중 치명적 에러: {e}")
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

    total_count = len(kospi_codes)
    successful_codes = []
    
    # 💡 [핵심] 900개 종목의 데이터를 담을 거대한 빈 리스트
    all_stocks_data = []

    logger.info(f"\n📦 총 {total_count}개 종목 메모리 적재를 시작합니다.\n")

    # [PHASE 1] 메모리에 데이터 차곡차곡 모으기
    with db.get_session() as session:
        for i, code in enumerate(kospi_codes):
            df_stock = process_and_save_stock(code, kiwoom_token, session)
            
            if df_stock is not None and not df_stock.empty:
                all_stocks_data.append(df_stock)
                successful_codes.append(code)

            if (i + 1) % PROGRESS_INTERVAL == 0:
                logger.info(f" ⏳ 수집 진행 상황: [{i + 1}/{total_count}] 완료...")

            time.sleep(API_DELAY_SECONDS) # API 제재 방지용 대기

    # [PHASE 2] 대망의 일괄 DB 삽입 (Bulk Insert)
    if all_stocks_data:
        logger.info("\n🚀 모든 데이터 수집 완료! PostgreSQL로 일괄 전송(Bulk-Insert)을 시작합니다...")
        
        # 모든 데이터프레임을 하나로 합치기
        final_bulk_df = pd.concat(all_stocks_data, ignore_index=True)
        cutoff_date = (datetime.now() - timedelta(days=CUTOFF_DAYS)).strftime('%Y-%m-%d')
        
        try:
            # 💡 [트랜잭션 최적화] 삭제와 삽입을 하나의 논리적 흐름으로 묶어버림
            with db.engine.begin() as conn:
                # 1. 대상 종목들의 최근 100일치 데이터를 한방에 지움
                delete_query = text(f"DELETE FROM {TABLE_NAME} WHERE quote_date >= :date AND stock_code = ANY(:codes)")
                conn.execute(delete_query, {'date': cutoff_date, 'codes': successful_codes})
                
                # 2. 수만 건의 데이터를 고속으로 밀어넣기 (method='multi' 가 핵심 부스터)
                final_bulk_df.to_sql(TABLE_NAME, con=conn, if_exists='append', index=False, chunksize=BULK_CHUNKSIZE, method='multi')
            
            logger.info(f"✅ DB 일괄 삽입 성공! (총 {len(final_bulk_df)}행 적재 완료)")
        except Exception as e:
            logger.error(f"🔥 DB 일괄 삽입 중 치명적 에러 발생: {e}")
    else:
        logger.warning("⚠️ 수집된 데이터가 없어 DB 작업을 건너뜁니다.")

    logger.info(f"\n🎉 일일 업데이트 최종 완료! (성공: {len(successful_codes)} / {total_count} 종목)")
    
    finish_msg = f"✅ **KOSPI 일일 데이터 갱신 완료**\n총 **{len(successful_codes)} / {total_count}** 종목의 캔들 및 수급 데이터가 DB에 일괄 적재되었습니다."
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