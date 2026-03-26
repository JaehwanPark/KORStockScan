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
import re
import requests
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta
from sqlalchemy import text
import FinanceDataReader as fdr
from bs4 import BeautifulSoup

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
BULK_CHUNKSIZE = 500
PROGRESS_INTERVAL = 50
NXT_TARGET_URL = "https://www.nextrade.co.kr/menu/transactionStatusMain/menuList.do"
NXT_MARKETDATA_URL = "https://www.nextrade.co.kr/menu/marketData/menuList.do"
MIN_EXPECTED_NXT_CODES = 100
HTTP_TIMEOUT_SECONDS = 10

NXT_TARGET_KEYWORDS = [
    r"매매체결대상종목",
    r"정규시장.*매매체결대상종목",
    r"매매체결대상종목.*안내",
    r"매매체결대상종목.*확대",
    r"매매체결대상종목.*편입",
]
NXT_EXCLUSION_KEYWORDS = [
    r"매매체결 제외 종목",
    r"매매체결대상종목.*축소",
    r"한도 관리",
]

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
    'Margin_Rate': 'margin_rate',
    'Is_NXT': 'is_nxt'
}

# ==========================================
# 2. NXT 대상 종목 수집 / 적재 헬퍼
# ==========================================
def _normalize_stock_code(code) -> str:
    raw = str(code or "").strip().upper().replace('.0', '')
    if raw.endswith('_AL'):
        raw = raw[:-3]
    if raw.startswith('A') and len(raw) >= 7:
        raw = raw[1:]
    digits = ''.join(ch for ch in raw if ch.isdigit())
    return digits[-6:].zfill(6) if digits else raw


def _extract_codes_from_table(html: str) -> set[str]:
    codes: set[str] = set()
    soup = BeautifulSoup(html, 'html.parser')

    for tr in soup.find_all('tr'):
        row_text = ' '.join(td.get_text(' ', strip=True) for td in tr.find_all(['td', 'th']))
        if not row_text:
            continue
        m = re.search(r'\bA?(\d{6})\b', row_text)
        if m:
            code = _normalize_stock_code(m.group(1))
            if code and code.isdigit() and len(code) == 6:
                codes.add(code)
    return codes


def _extract_codes_from_scripts(html: str) -> set[str]:
    patterns = [
        r'\bA(\d{6})\b',
        r'"isuSrdCd"\s*:\s*"A?(\d{6})"',
        r'"stockCode"\s*:\s*"(\d{6})"',
        r'"isuCd"\s*:\s*"A?(\d{6})"',
    ]
    codes: set[str] = set()
    soup = BeautifulSoup(html, 'html.parser')

    for script in soup.find_all('script'):
        script_text = script.get_text(' ', strip=True) or ''
        if not script_text:
            continue
        for pattern in patterns:
            for match in re.findall(pattern, script_text):
                code = _normalize_stock_code(match)
                if code and code.isdigit() and len(code) == 6:
                    codes.add(code)
    return codes


def _extract_codes_by_regex(html: str) -> set[str]:
    codes: set[str] = set()
    for pattern in [r'\bA(\d{6})\b', r'\b(\d{6})\b']:
        for match in re.findall(pattern, html):
            code = _normalize_stock_code(match)
            if code and code.isdigit() and len(code) == 6:
                codes.add(code)
    return codes


def _find_latest_announcement_url(base_url: str, keywords: list[str]) -> str:
    """공지 목록 페이지에서 주어진 키워드를 포함하는 가장 최근 공지의 URL을 반환합니다."""
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.nextrade.co.kr/"}
    try:
        res = requests.get(base_url, headers=headers, timeout=HTTP_TIMEOUT_SECONDS)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        for link in soup.find_all('a', href=True):
            link_text = link.get_text(strip=True)
            if any(keyword in link_text for keyword in keywords):
                href = link['href']
                if href.startswith('http'):
                    return href
                else:
                    from urllib.parse import urljoin
                    return urljoin(base_url, href)
    except Exception as e:
        logger.warning(f"⚠️ 공지 목록 조회 실패 ({base_url}): {e}")
    return ""


def _extract_xlsx_url_from_html(html: str) -> str:
    """공지 상세 HTML에서 XLSX 첨부파일 URL을 추출합니다."""
    soup = BeautifulSoup(html, 'html.parser')
    # 전략 1: href에 .xlsx가 직접 포함된 링크
    for link in soup.find_all('a', href=True):
        href = link['href']
        if '.xlsx' in href.lower():
            return href
    # 전략 2: onclick에 .xlsx가 포함된 링크
    for link in soup.find_all('a', onclick=True):
        onclick = link['onclick']
        if '.xlsx' in onclick.lower():
            import re
            match = re.search(r'\"([^\"]+\.xlsx)\"', onclick)
            if match:
                return match.group(1)
    # 전략 3: 느슨한 fallback
    for link in soup.find_all('a', href=True):
        href = link['href']
        if 'download' in href.lower() or 'file' in href.lower():
            return href
    return ""


def _download_xlsx_and_extract_codes(xlsx_url: str) -> set[str]:
    """XLSX 파일을 다운로드하여 모든 셀에서 종목코드를 추출합니다."""
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.nextrade.co.kr/"}
    try:
        res = requests.get(xlsx_url, headers=headers, timeout=HTTP_TIMEOUT_SECONDS)
        res.raise_for_status()
        import io
        import pandas as pd
        df = pd.read_excel(io.BytesIO(res.content), sheet_name=None, header=None, engine='openpyxl')
        codes = set()
        for sheet_name, sheet_df in df.items():
            for col in sheet_df.columns:
                for cell in sheet_df[col].astype(str):
                    import re
                    matches = re.findall(r'(?:KR\d{10}|A\d{6}|\d{6})(?:_AL)?', cell.upper())
                    for match in matches:
                        code = _normalize_stock_code(match)
                        if code and code.isdigit() and len(code) == 6:
                            codes.add(code)
        return codes
    except Exception as e:
        logger.warning(f"⚠️ XLSX 다운로드/파싱 실패 ({xlsx_url}): {e}")
        return set()


def _fetch_nxt_target_codes_via_xlsx() -> set[str]:
    """공식 NXT 대상종목 및 제외종목 XLSX를 파싱하여 최종 NXT 대상 종목 코드 집합을 반환합니다."""
    target_url = _find_latest_announcement_url(NXT_TARGET_URL, NXT_TARGET_KEYWORDS)
    if not target_url:
        logger.warning("⚠️ NXT 대상종목 공지를 찾을 수 없습니다.")
        return set()
    target_html = requests.get(target_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=HTTP_TIMEOUT_SECONDS).text
    xlsx_url = _extract_xlsx_url_from_html(target_html)
    if not xlsx_url:
        logger.warning("⚠️ 대상종목 XLSX URL 추출 실패")
        return set()
    target_codes = _download_xlsx_and_extract_codes(xlsx_url)
    if len(target_codes) < MIN_EXPECTED_NXT_CODES:
        logger.warning(f"⚠️ 대상종목 XLSX 코드 수가 너무 적습니다: {len(target_codes)}개")
        return set()
    
    exclusion_url = _find_latest_announcement_url(NXT_TARGET_URL, NXT_EXCLUSION_KEYWORDS)
    exclusion_codes = set()
    if exclusion_url:
        exclusion_html = requests.get(exclusion_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=HTTP_TIMEOUT_SECONDS).text
        excl_xlsx_url = _extract_xlsx_url_from_html(exclusion_html)
        if excl_xlsx_url:
            exclusion_codes = _download_xlsx_and_extract_codes(excl_xlsx_url)
    
    final_codes = target_codes - exclusion_codes
    logger.info(f"✅ NXT 대상 종목 XLSX 파싱 성공: 대상 {len(target_codes)}개, 제외 {len(exclusion_codes)}개, 최종 {len(final_codes)}개")
    return final_codes


def fetch_nxt_target_codes() -> set[str]:
    """넥스트레이드 공식 거래대상종목 페이지를 source of truth로 사용해 NXT 대상 종목 코드를 수집합니다.

    파싱 전략:
    1) 공식 NXT 대상종목/제외종목 XLSX 첨부파일 파싱 (우선)
    2) HTML table row 기반
    3) inline script / JSON-like 데이터
    4) 전체 regex fallback
    """
    # 1. XLSX 우선 시도
    xlsx_codes = _fetch_nxt_target_codes_via_xlsx()
    if xlsx_codes and len(xlsx_codes) >= MIN_EXPECTED_NXT_CODES:
        logger.info(f"✅ NXT 대상 종목 목록 XLSX 파싱 성공: {len(xlsx_codes)}개")
        return xlsx_codes
    else:
        logger.warning("⚠️ NXT XLSX 파싱 실패 또는 코드 수 부족. HTML 파싱으로 폴백합니다.")
    
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.nextrade.co.kr/",
    }
    
    strategies = [
        ('table', _extract_codes_from_table),
        ('scripts', _extract_codes_from_scripts),
        ('regex', _extract_codes_by_regex),
    ]
    
    for url in [NXT_MARKETDATA_URL, NXT_TARGET_URL]:
        try:
            res = requests.get(url, headers=headers, timeout=HTTP_TIMEOUT_SECONDS)
            res.raise_for_status()
            html = res.text
            
            best_codes = set()
            best_strategy = None
            for name, extractor in strategies:
                try:
                    codes = extractor(html)
                except Exception as e:
                    logger.warning(f"⚠️ NXT {name} 파싱 중 예외: {e}")
                    continue
                
                if len(codes) > len(best_codes):
                    best_codes = codes
                    best_strategy = name
                
                if len(codes) >= MIN_EXPECTED_NXT_CODES:
                    logger.info(f"✅ NXT 대상 종목 목록 수집 성공: {len(codes)}개 (strategy: {name}, source: {url})")
                    return codes
            
            # 어떤 전략도 임계치를 넘지 못한 경우
            if best_codes:
                logger.warning(
                    f"⚠️ NXT 코드 수집 결과가 비정상적으로 적음: {len(best_codes)}개 "
                    f"(best_strategy: {best_strategy}, source: {url})"
                )
            else:
                logger.warning(f"⚠️ NXT 코드 수집 실패 (source: {url})")
                
        except Exception as e:
            logger.warning(f"⚠️ NXT 대상 종목 목록 수집 실패 ({url}): {e}")
            continue
    
    # 모든 URL 실패
    logger.warning("⚠️ NXT 공식 목록 수집 실패. 모든 소스에서 파싱 불가.")
    return set()


def resolve_nxt_map(db: DBManager, target_codes: list[str]) -> dict:
    """공식 NXT 대상 종목 목록을 우선 사용하고, 실패 시 최신 거래일 DB 플래그로 폴백합니다."""
    normalized = [_normalize_stock_code(c) for c in (target_codes or []) if c]
    nxt_target_codes = fetch_nxt_target_codes()

    if nxt_target_codes:
        return {code: (code in nxt_target_codes) for code in normalized}

    logger.warning("⚠️ NXT 공식 목록 수집 실패. 최신 거래일 DB is_nxt 플래그로 폴백합니다.")
    return db.get_latest_is_nxt_map(normalized)


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
        df['Is_NXT'] = bool(is_nxt)

        # 💡 [핵심 복구 2] 지표 계산 전 원본 데이터 완벽 백업
        backup_df = df.copy()
        original_cols = df.columns.tolist()

        # Convert any None values to NaN for numeric columns (prevent NoneType errors)
        for col in df.columns:
            if df[col].dtype == object:
                # Replace None with NaN (keeps other values unchanged)
                df[col] = df[col].apply(lambda x: np.nan if x is None else x)
            elif df[col].dtype.kind in 'biufc':  # numeric types
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # 3. 보조 지표 계산 (Return 컬럼 생성)
        df = calculate_all_features(df)

        # 🚨 [중요] feature_engineer가 소문자 'return'을 줬다면 대문자로 통일
        if 'return' in df.columns and 'Return' not in df.columns:
            df.rename(columns={'return': 'Return'}, inplace=True)

        # 💡 [핵심 복구 3] 원본 컬럼 강제 복원 (지표 계산기가 0으로 덮어쓰는 것 원천 차단)
        for col in original_cols:
            if col in ['Marcap', 'Margin_Rate', 'Retail_Net', 'Foreign_Net', 'Inst_Net', 'Code', 'Name', 'Is_NXT']:
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
        # Fill NaN with appropriate defaults per column type
        # Ensure numeric columns are numeric (convert object dtype)
        numeric_cols = ['open_price', 'high_price', 'low_price', 'close_price', 'volume',
                        'ma5', 'ma20', 'ma60', 'ma120', 'rsi', 'macd', 'macd_sig', 'macd_hist',
                        'bbl', 'bbm', 'bbu', 'bbb', 'bbp', 'vwap', 'obv', 'atr', 'daily_return',
                        'marcap', 'retail_net', 'foreign_net', 'inst_net', 'margin_rate']
        for col in numeric_cols:
            if col in new_rows.columns:
                new_rows[col] = pd.to_numeric(new_rows[col], errors='coerce')
        # Boolean column
        if 'is_nxt' in new_rows.columns:
            new_rows['is_nxt'] = new_rows['is_nxt'].astype(bool)
        
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
    nxt_map = resolve_nxt_map(db, kospi_codes)
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