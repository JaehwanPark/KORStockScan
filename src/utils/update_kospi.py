import sys
from pathlib import Path

# ==========================================
# 🚀 [핵심 방어] 프로젝트 루트 경로를 sys.path에 동적으로 추가
# ==========================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

import os
import pandas as pd
import time
import logging
import json
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta
from sqlalchemy import text

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

# 전문 로거 세팅 (터미널+파일)
logger = logging.getLogger("KospiUpdater")
logger.setLevel(logging.INFO)

if not logger.handlers:
    file_handler = RotatingFileHandler(LOG_PATH, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
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
def process_and_save_stock(code, token, db: DBManager):
    """단일 종목 데이터를 키움 API로 병합하고 DB에 적재합니다."""
    # 💡 [핵심] 래퍼 함수가 알아서 재시도하므로, 낡은 외부 재시도 루프(for api_attempt)를 제거했습니다.
    try:
        # 1. API 순차 호출 (호출 사이에 숨고르기 추가)
        df_ohlcv = kiwoom_utils.get_daily_ohlcv_ka10081_df(token, code)
        if df_ohlcv.empty: return False

        # time.sleep(0.5) # 💡 [버퍼 추가] 10081 연속조회 후 키움 서버 진정시키기(모의투자용)
        # time.sleep(0.2) # 💡 [버퍼 추가] 10081 연속조회 후 키움 서버 진정시키기(실전서버용)
        df_investor = kiwoom_utils.get_investor_daily_ka10059_df(token, code)
        
        # time.sleep(0.5) # 💡 [버퍼 추가] 10059 연속조회 후 진정시키기(모의투자용)
        # time.sleep(0.2) # 💡 [버퍼 추가] 10081 연속조회 후 키움 서버 진정시키기(실전서버용)
        df_margin = kiwoom_utils.get_margin_daily_ka10013_df(token, code)
        
        # time.sleep(0.5) # 💡 [버퍼 추가] 10013 연속조회 후 진정시키기(모의투자용)
        # time.sleep(0.2) # 💡 [버퍼 추가] 10081 연속조회 후 키움 서버 진정시키기(실전서버용)
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
        df['Name'] = basic_info.get('Name', '이름없음')
        df['Marcap'] = basic_info.get('Marcap', 0)

        # 💡 [데이터 정제] 새 스키마 규격으로 옷 갈아입히기
        existing_cols = [col for col in COLUMN_MAPPING.keys() if col in df.columns]
        df = df[existing_cols].rename(columns=COLUMN_MAPPING)

        # 4. 최근 100일치만 잘라내어 반환 (DB I/O는 여기서 안 함!)
        cutoff_date = (datetime.now() - timedelta(days=100)).strftime('%Y-%m-%d')
        new_rows = df[df['quote_date'] >= cutoff_date].copy()

        # 안전한 최종 컬럼 필터링 (모델 스키마와 완벽 동기화)
        final_cols = [col for col in COLUMN_MAPPING.values() if col in new_rows.columns]
        return new_rows[final_cols].dropna(subset=['close_price'])

    except Exception as e:
        # 💡 429 처리 로직도 제거됨 (kiwoom_utils가 알아서 하므로)
        logger.error(f"❌ [{code}] 처리 중 치명적 에러: {e}")
        return False
        
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

    event_bus.publish('TELEGRAM_BROADCAST', {'message': "🔄 KOSPI 전 종목 일일 데이터 갱신을 시작합니다. (약 15분 소요)", 'audience': 'ADMIN_ONLY'})

    kospi_codes = []
    try:
        with db.engine.connect() as conn:
            # 💡 [PostgreSQL 최적화] 쌍따옴표 제거, stock_code 적용
            df_codes = pd.read_sql(text(f"SELECT DISTINCT stock_code FROM {TABLE_NAME}"), conn)

        if df_codes.empty:
            logger.warning("⚠️ DB가 완전히 비어있습니다! 기초 데이터 셋업이 필요합니다.")
            return
        else:
            kospi_codes = df_codes['stock_code'].tolist()
    except Exception as e:
        logger.error(f"❌ DB 종목 수집 중 에러: {e}", exc_info=True)
        return

    total_count = len(kospi_codes)
    successful_codes = []
    
    # 💡 [핵심] 900개 종목의 데이터를 담을 거대한 빈 리스트
    all_stocks_data = []

    logger.info(f"\n📦 총 {total_count}개 종목 메모리 적재를 시작합니다.\n")

    # [PHASE 1] 메모리에 데이터 차곡차곡 모으기
    for i, code in enumerate(kospi_codes):
        df_stock = process_and_save_stock(code, kiwoom_token)
        
        if df_stock is not None and not df_stock.empty:
            all_stocks_data.append(df_stock)
            successful_codes.append(code)

        if (i + 1) % 50 == 0:
            logger.info(f" ⏳ 수집 진행 상황: [{i + 1}/{total_count}] 완료...")

        time.sleep(0.3) # API 제재 방지용 대기

    # [PHASE 2] 대망의 일괄 DB 삽입 (Bulk Insert)
    if all_stocks_data:
        logger.info("\n🚀 모든 데이터 수집 완료! PostgreSQL로 일괄 전송(Bulk-Insert)을 시작합니다...")
        
        # 모든 데이터프레임을 하나로 합치기
        final_bulk_df = pd.concat(all_stocks_data, ignore_index=True)
        cutoff_date = (datetime.now() - timedelta(days=100)).strftime('%Y-%m-%d')
        
        try:
            # 💡 [트랜잭션 최적화] 삭제와 삽입을 하나의 논리적 흐름으로 묶어버림
            with db.engine.begin() as conn:
                # 1. 대상 종목들의 최근 100일치 데이터를 한방에 지움
                delete_query = text(f"DELETE FROM {TABLE_NAME} WHERE quote_date >= :date AND stock_code IN :codes")
                conn.execute(delete_query, {'date': cutoff_date, 'codes': tuple(successful_codes)})
                
                # 2. 수만 건의 데이터를 고속으로 밀어넣기 (method='multi' 가 핵심 부스터)
                final_bulk_df.to_sql(TABLE_NAME, con=conn, if_exists='append', index=False, chunksize=2000, method='multi')
            
            logger.info(f"✅ DB 일괄 삽입 성공! (총 {len(final_bulk_df)}행 적재 완료)")
        except Exception as e:
            logger.error(f"🔥 DB 일괄 삽입 중 치명적 에러 발생: {e}")
    else:
        logger.warning("⚠️ 수집된 데이터가 없어 DB 작업을 건너뜁니다.")

    logger.info(f"\n🎉 일일 업데이트 최종 완료! (성공: {len(successful_codes)} / {total_count} 종목)")
    
    finish_msg = f"✅ **KOSPI 일일 데이터 갱신 완료**\n총 **{len(successful_codes)} / {total_count}** 종목의 캔들 및 수급 데이터가 DB에 일괄 적재되었습니다."
    event_bus.publish('TELEGRAM_BROADCAST', {'message': finish_msg, 'audience': 'ADMIN_ONLY', 'parse_mode': 'Markdown'})


if __name__ == "__main__":
    update_kospi_data()