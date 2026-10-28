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
from datetime import date, datetime, timedelta
from sqlalchemy import text, func, and_, case, or_
import FinanceDataReader as fdr

# --- [Level 2: 공통 모듈 명시적 상대 경로 반영] ---
from src.utils import kiwoom_utils
from src.model.common_v2 import calculate_all_features
from src.database.db_manager import DBManager
from src.database.models import DailyStockQuote
from src.utils.constants import LOGS_DIR
from src.engine.infrastructure.market_eligibility_source import (
    store_market_eligibility_rows as _store_market_eligibility_rows,
)
from src.core.event_bus import EventBus

# ==========================================
# 1. 경로 및 로깅 설정
# ==========================================
LOG_DIR = str(LOGS_DIR)
os.makedirs(LOG_DIR, exist_ok=True)

LOG_PATH = os.path.join(LOG_DIR, "update_kospi_error.log")
TABLE_NAME = "daily_stock_quotes"
STATUS_DIR = PROJECT_ROOT / "data" / "runtime" / "update_kospi_status"
STATUS_VERSION = 1

# Constants
CUTOFF_DAYS = 100
API_DELAY_SECONDS = 0.3
LOG_MAX_BYTES = 5 * 1024 * 1024
LOG_BACKUP_COUNT = 3
BULK_CHUNKSIZE = 500
PROGRESS_INTERVAL = 50
MIN_FEATURE_BARS = 20
LISTED_SHARE_MARKETS = frozenset({"KOSPI", "KOSDAQ", "KOSDAQ GLOBAL", "KONEX"})

# 전문 로거 세팅 (터미널+파일)
logger = logging.getLogger("KospiUpdater")
logger.setLevel(logging.INFO)

if not logger.handlers:
    file_handler = RotatingFileHandler(
        LOG_PATH, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT, encoding="utf-8"
    )
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(console_handler)

logger.info("🧠 Nightly feature source: src.model.common_v2.calculate_all_features")


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _update_kospi_status_path(target_date: str | None = None) -> Path:
    run_date = target_date or _today_str()
    return STATUS_DIR / f"update_kospi_{run_date}.json"


def _write_update_kospi_status(payload: dict, path: Path | None = None) -> Path:
    status_path = path or _update_kospi_status_path(
        str(payload.get("target_date") or _today_str())
    )
    status_path.parent.mkdir(parents=True, exist_ok=True)
    status_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    return status_path


def _load_latest_quote_state() -> dict:
    try:
        db = DBManager()
        with db.engine.connect() as conn:
            latest_quote_date = conn.execute(
                text(f"SELECT MAX(quote_date) FROM {TABLE_NAME}")
            ).scalar()
            rows_on_latest_date = 0
            if latest_quote_date is not None:
                rows_on_latest_date = conn.execute(
                    text(
                        f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE quote_date = :latest_quote_date"
                    ),
                    {"latest_quote_date": latest_quote_date},
                ).scalar()
        return {
            "db_state_status": "available",
            "latest_quote_date": (
                str(latest_quote_date) if latest_quote_date is not None else None
            ),
            "rows_on_latest_date": int(rows_on_latest_date or 0),
        }
    except Exception as e:
        return {
            "db_state_status": "unavailable",
            "error": str(e),
        }


def _step(name: str, status: str, **details) -> dict:
    payload = {
        "name": name,
        "status": status,
        "finished_at": _now_iso(),
    }
    payload.update({k: v for k, v in details.items() if v is not None})
    return payload


# 💡 [핵심 매핑] 모델 스키마와 완벽 동기화 (Return -> daily_return 포함)
COLUMN_MAPPING = {
    "Date": "quote_date",
    "Code": "stock_code",
    "Name": "stock_name",
    "Open": "open_price",
    "High": "high_price",
    "Low": "low_price",
    "Close": "close_price",
    "Volume": "volume",
    "MA5": "ma5",
    "MA20": "ma20",
    "MA60": "ma60",
    "MA120": "ma120",
    "RSI": "rsi",
    "MACD": "macd",
    "MACD_Sig": "macd_sig",
    "MACD_Hist": "macd_hist",
    "BBL": "bbl",
    "BBM": "bbm",
    "BBU": "bbu",
    "BBB": "bbb",
    "BBP": "bbp",
    "VWAP": "vwap",
    "OBV": "obv",
    "ATR": "atr",
    "Return": "daily_return",  # 💡 예약어 충돌 회피
    "Marcap": "marcap",
    "Retail_Net": "retail_net",
    "Foreign_Net": "foreign_net",
    "Inst_Net": "inst_net",
    "Margin_Rate": "margin_rate",
    "Is_NXT": "is_nxt",
}


def _normalize_feature_output_columns(df: pd.DataFrame) -> pd.DataFrame:
    """feature 함수 출력 컬럼을 nightly update 스키마에 맞게 정규화합니다."""
    rename_map = {
        "return": "Return",
        "return_1d": "Return",
        "ma5": "MA5",
        "ma20": "MA20",
        "ma60": "MA60",
        "ma120": "MA120",
        "rsi": "RSI",
        "macd": "MACD",
        "macd_sig": "MACD_Sig",
        "macd_hist": "MACD_Hist",
        "bbl": "BBL",
        "bbm": "BBM",
        "bbu": "BBU",
        "bbb": "BBB",
        "bbp": "BBP",
        "vwap20": "VWAP",
        "vwap": "VWAP",
        "obv": "OBV",
        "atr": "ATR",
        "date": "Date",
        "code": "Code",
        "name": "Name",
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close",
        "volume": "Volume",
        "foreign_net": "Foreign_Net",
        "inst_net": "Inst_Net",
        "margin_rate": "Margin_Rate",
        "is_nxt": "Is_NXT",
    }
    applicable = {
        k: v for k, v in rename_map.items() if k in df.columns and v not in df.columns
    }
    return df.rename(columns=applicable)


def _prepare_feature_input_columns(df: pd.DataFrame) -> pd.DataFrame:
    """nightly update 원본 컬럼을 common_v2 feature 입력 스키마에 맞춥니다."""
    out = df.copy()
    rename_map = {
        "Date": "quote_date",
        "Code": "stock_code",
        "Name": "stock_name",
        "Open": "open_price",
        "High": "high_price",
        "Low": "low_price",
        "Close": "close_price",
        "Volume": "volume",
        "Foreign_Net": "foreign_net",
        "Inst_Net": "inst_net",
        "Margin_Rate": "margin_rate",
        "Is_NXT": "is_nxt",
    }
    for source, target in rename_map.items():
        if source in out.columns and target not in out.columns:
            out[target] = out[source]
    return out


def _sanitize_daily_input(df: pd.DataFrame, code_str: str) -> pd.DataFrame:
    """Validate received OHLCV independently of indicator warm-up."""
    out = df.copy().rename(columns={"index": "Date"})
    out["Date"] = pd.to_datetime(out["Date"], errors="coerce")
    prices = ["Open", "High", "Low", "Close"]
    required = prices + ["Volume"]
    for col in required + ["Retail_Net", "Foreign_Net", "Inst_Net", "Margin_Rate"]:
        out[col] = pd.to_numeric(out.get(col, np.nan), errors="coerce")
    out = out.replace([np.inf, -np.inf], np.nan)
    valid = (
        out["Date"].notna()
        & out[required].notna().all(axis=1)
        & out[prices].gt(0).all(axis=1)
        & out["Volume"].ge(0)
        & out["High"].ge(out[prices].max(axis=1))
        & out["Low"].le(out[prices].min(axis=1))
    )
    out = out.loc[valid].sort_values("Date").drop_duplicates("Date", keep=False)
    if len(out) != len(df):
        logger.warning(
            "[%s] invalid or duplicate daily source rows: %s",
            code_str,
            len(df) - len(out),
        )
    return out.reset_index(drop=True)


# ==========================================
# 2. 공통 코드 정규화 헬퍼
# ==========================================
def _normalize_stock_code(code) -> str:
    return kiwoom_utils.normalize_stock_code(code)


def _collect_and_store_market_eligibility(
    db: DBManager,
    session,
    *,
    token: str,
    stock_codes: list[str],
    trade_date: date,
) -> tuple[dict[str, bool], dict]:
    source_rows, source_meta = kiwoom_utils.get_stock_eligibility_map_ka10099(
        token,
        stock_codes,
        mrkt_tps=("0", "10"),
        trade_date=trade_date,
    )
    storage = _store_market_eligibility_rows(
        session,
        trade_date=trade_date,
        source_rows=source_rows,
    )
    nxt_map = {
        code: bool(row["nxt_eligible"])
        for code, row in source_rows.items()
        if row.get("nxt_eligible") is not None and row.get("complete") is True
    }
    missing_nxt_codes = sorted(set(stock_codes) - set(nxt_map))
    if missing_nxt_codes:
        nxt_map.update(db.get_latest_is_nxt_map(missing_nxt_codes))
    return nxt_map, {**source_meta, **storage}


# ==========================================
# 3. 메인 업데이트 로직
# ==========================================
def process_and_save_stock(code, token, session, is_nxt=False) -> pd.DataFrame:
    """Prepare validated source rows; indicator readiness never owns intake.

    ``session`` remains the existing caller interface; persistence is batched
    by update_kospi_data after the independent listing transaction commits.
    """
    try:
        code_str = _normalize_stock_code(code)
        if not kiwoom_utils.is_canonical_stock_code(code_str):
            raise ValueError("unsupported_listing_code")
        raw = kiwoom_utils.get_daily_ohlcv_ka10081_df(token, code_str)
        if raw.empty:
            return pd.DataFrame()
        raw = raw.copy()
        raw.index = pd.to_datetime(raw.index, errors="coerce")
        for fetch, columns in (
            (
                kiwoom_utils.get_investor_daily_ka10059_df,
                ["Retail_Net", "Foreign_Net", "Inst_Net"],
            ),
            (kiwoom_utils.get_margin_daily_ka10013_df, ["Margin_Rate"]),
        ):
            auxiliary = fetch(token, code_str, is_nxt=is_nxt)
            if not auxiliary.empty:
                auxiliary = auxiliary.copy()
                auxiliary.index = pd.to_datetime(auxiliary.index, errors="coerce")
                raw = raw.join(auxiliary, how="left")
            for column in columns:
                if column not in raw:
                    raw[column] = np.nan
                # Preserve the existing dated carry; unknown stays NULL in DB.
                raw[column] = raw[column].ffill()
        basic_info = kiwoom_utils.get_basic_info_ka10001(token, code_str) or {}
        raw = _sanitize_daily_input(raw.rename_axis("Date").reset_index(), code_str)
        if raw.empty:
            return pd.DataFrame()
        raw["Code"] = code_str
        raw["Name"] = basic_info.get("Name")
        raw["Marcap"] = basic_info.get("Marcap", np.nan)
        raw["Is_NXT"] = bool(is_nxt)
        metadata = basic_info.get("StrategyMetadata")
        if isinstance(metadata, dict) and metadata.get("stock_code") == code_str:
            from src.engine.scalping.mechanistic_entry_runtime_policy import (
                _atomic_write_json,
            )

            _atomic_write_json(
                PROJECT_ROOT
                / "data/runtime/entry_strategy_metadata"
                / f"{code_str}.json",
                metadata,
            )

        feature_status, feature_error = "insufficient_history", None
        calculated = raw.copy()
        if len(raw) >= MIN_FEATURE_BARS:
            try:
                feature_input = _prepare_feature_input_columns(raw)
                # Keep historical model input semantics without fabricating source rows.
                auxiliary_columns = [
                    "Retail_Net",
                    "Foreign_Net",
                    "Inst_Net",
                    "Margin_Rate",
                    "foreign_net",
                    "inst_net",
                    "margin_rate",
                    "Marcap",
                ]
                for column in auxiliary_columns:
                    if column in feature_input:
                        feature_input[column] = feature_input[column].fillna(0.0)
                calculated = _normalize_feature_output_columns(
                    calculate_all_features(feature_input)
                )
                if (
                    len(calculated) != len(raw)
                    or "Date" not in calculated
                    or any(
                        not pd.to_datetime(calculated[column], errors="coerce")
                        .reset_index(drop=True)
                        .equals(raw["Date"])
                        for column in ("Date", "date", "quote_date")
                        if column in calculated
                    )
                    or any(
                        not calculated[column].eq(code_str).all()
                        for column in ("Code", "code", "stock_code")
                        if column in calculated
                    )
                ):
                    raise ValueError("feature_source_identity_changed")
                calculated = calculated.reset_index(drop=True)
                for column in raw:
                    calculated[column] = raw[column]
                if "Return" not in calculated:
                    calculated["Return"] = raw["Close"].pct_change().fillna(0.0)
                feature_status = "calculated"
            except Exception as exc:
                feature_status, feature_error = "failed", type(exc).__name__
                calculated = raw.copy()
                logger.error(
                    "[%s] indicator calculation failed; retaining source: %s",
                    code_str,
                    exc,
                )

        # Explicit NULL prevents schema defaults from inventing unobserved values.
        for column in COLUMN_MAPPING:
            if column not in calculated:
                calculated[column] = np.nan
        result = calculated[list(COLUMN_MAPPING)].rename(columns=COLUMN_MAPPING)
        cutoff = pd.Timestamp(
            date.fromisoformat(_today_str()) - timedelta(days=CUTOFF_DAYS)
        )
        result = result.loc[result["quote_date"] >= cutoff].copy()
        result["quote_date"] = pd.to_datetime(result["quote_date"]).dt.date
        result = result.replace([np.inf, -np.inf], np.nan)
        result.attrs.update(
            feature_status=feature_status,
            feature_error=feature_error,
            valid_source_rows=len(raw),
            minimum_feature_bars=MIN_FEATURE_BARS,
        )
        return result
    except Exception as exc:
        logger.error(
            "[%s] daily source preparation failed: %s", code, exc, exc_info=True
        )
        return pd.DataFrame()


# ==========================================
# 3. 전체 스케줄러 (배치 메인)
# ==========================================
def _upsert_daily_quote_batch(conn, frame: pd.DataFrame) -> int:
    """Refresh received keys atomically without deleting unreceived history."""
    if frame.empty:
        return 0
    keys = ["quote_date", "stock_code"]
    if frame[keys].isna().any().any() or frame.duplicated(keys).any():
        raise ValueError("daily_quote_batch_invalid_or_duplicate_identity")
    if conn.dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
    elif conn.dialect.name == "sqlite":
        from sqlalchemy.dialects.sqlite import insert
    else:
        raise ValueError("daily_quote_batch_unsupported_dialect")
    table = DailyStockQuote.__table__
    if set(frame.columns) - set(table.columns.keys()):
        raise ValueError("daily_quote_batch_unknown_columns")
    columns = [column for column in frame.columns if column not in keys]
    source_columns = {"open_price", "high_price", "low_price", "close_price", "volume"}
    optional_source_columns = {
        "marcap",
        "retail_net",
        "foreign_net",
        "inst_net",
        "margin_rate",
    }
    for start in range(0, len(frame), BULK_CHUNKSIZE):
        chunk = frame.iloc[start : start + BULK_CHUNKSIZE].astype(object)
        records = chunk.where(pd.notna(chunk), None).to_dict("records")
        statement = insert(table).values(records)
        incoming = statement.excluded
        # Changed source cannot inherit indicators from previously observed bytes.
        same_source = and_(
            True,
            *[
                (
                    or_(
                        incoming[column].is_(None),
                        table.c[column].is_not_distinct_from(incoming[column]),
                    )
                    if column in optional_source_columns
                    else table.c[column].is_not_distinct_from(incoming[column])
                )
                for column in columns
                if column in source_columns | optional_source_columns
            ],
        )
        if columns:
            statement = statement.on_conflict_do_update(
                index_elements=keys,
                set_={
                    column: (
                        func.coalesce(incoming[column], table.c[column])
                        if column in optional_source_columns
                        else (
                            func.coalesce(
                                incoming[column],
                                case((same_source, table.c[column]), else_=None),
                            )
                            if column not in source_columns | {"stock_name", "is_nxt"}
                            else incoming[column]
                        )
                    )
                    for column in columns
                },
            )
        else:
            statement = statement.on_conflict_do_nothing(index_elements=keys)
        conn.execute(statement)
    return len(frame)


def update_kospi_data():
    logger.info("📅 오늘이 주식시장 개장일인지 확인합니다...")

    is_open, reason = kiwoom_utils.is_trading_day()
    # is_open, reason = True, "정상거래일 (MOCK)"

    event_bus = EventBus()

    if not is_open:
        logger.info(
            f"🛑 오늘은 {reason} 휴장일이므로 데이터베이스 업데이트를 종료합니다."
        )
        return {"status": "skipped_non_trading_day", "reason": reason}

    logger.info("=== KORStockScan 일일 데이터 수집 (PostgreSQL 정식가동) ===")

    db = DBManager()
    db.init_db()

    kiwoom_token = kiwoom_utils.get_kiwoom_token()
    if not kiwoom_token:
        logger.error("❌ 키움 토큰 발급 실패! 시스템을 종료합니다.")
        event_bus.publish(
            "TELEGRAM_BROADCAST",
            {
                "message": "🚨 [데이터 갱신 실패] 키움 토큰 발급 오류",
                "audience": "ADMIN_ONLY",
            },
        )
        return {"status": "failed", "reason": "kiwoom_token_failed"}

    event_bus.publish(
        "TELEGRAM_BROADCAST",
        {
            "message": "🔄 전 종목 일일 데이터 갱신을 시작합니다. (약 15분 소요)",
            "audience": "ADMIN_ONLY",
        },
    )

    kospi_codes = []
    # ========================================================
    # 💡 [1순위] FinanceDataReader를 통해 최신 KOSPI/KOSDAQ 종목 수집
    # ========================================================
    try:
        logger.info("🔍 FinanceDataReader를 통해 최신 상장 종목 리스트를 수집합니다...")
        df_krx = fdr.StockListing("KRX")

        if not df_krx.empty:
            # Catalog intake includes every listed share market; no trading authority.
            df_filtered = df_krx[df_krx["Market"].isin(LISTED_SHARE_MARKETS)]
            kospi_codes = df_filtered["Code"].tolist()
            logger.info(
                f"✅ FDR 종목 수집 성공! 총 {len(kospi_codes)}개 (상장 주식) 종목"
            )
        else:
            raise ValueError("FDR에서 빈 데이터를 반환했습니다.")

    except Exception as e:
        logger.warning(
            f"⚠️ FDR 종목 수집 실패 ({e}). 기존 DB 조회 방식으로 Fallback 합니다."
        )

        # ========================================================
        # 💡 [2순위 (Fallback)] 기존 방식: DB에서 수집된 이력이 있는 종목들 가져오기
        # ========================================================
        try:
            with db.engine.connect() as conn:
                # PostgreSQL 최적화 쿼리 유지
                df_codes = pd.read_sql(
                    text(f"SELECT DISTINCT stock_code FROM {TABLE_NAME}"), conn
                )

            if df_codes.empty:
                logger.warning(
                    "⚠️ DB가 완전히 비어있고 FDR도 실패했습니다! 기초 데이터 셋업이 필요합니다."
                )
                return {"status": "failed", "reason": "symbol_source_empty"}
            else:
                kospi_codes = df_codes["stock_code"].tolist()
                logger.info(f"✅ DB에서 종목 수집 성공! 총 {len(kospi_codes)}개 종목")

        except Exception as db_e:
            logger.error(f"❌ DB 종목 수집 중 에러: {db_e}", exc_info=True)
            return {
                "status": "failed",
                "reason": "symbol_source_db_failed",
                "error": str(db_e),
            }

    source_codes = kospi_codes
    excluded_symbol_identities = []
    kospi_codes = []
    for raw_code in source_codes:
        identity = kiwoom_utils.kiwoom_stock_code_identity(raw_code)
        if kiwoom_utils.is_canonical_stock_code(identity["canonical_code"]):
            kospi_codes.append(identity["canonical_code"])
        else:
            excluded_symbol_identities.append(
                {
                    "raw_code": str(raw_code),
                    "canonical_code": identity["canonical_code"],
                    "reason": "unsupported_equity_namespace",
                }
            )
    kospi_codes = sorted(set(kospi_codes))
    if not kospi_codes:
        return {
            "status": "failed",
            "reason": "supported_symbol_source_empty",
            "excluded_symbol_identities": excluded_symbol_identities,
        }
    total_count = len(kospi_codes)
    successful_codes = []
    target_date = date.fromisoformat(_today_str())
    target_date_codes = []
    inserted_rows = 0
    update_status = "completed"
    update_reason = None

    # 💡 [핵심] 900개 종목의 데이터를 담을 거대한 빈 리스트
    all_stocks_data = []
    feature_results = {}

    logger.info(f"\n📦 총 {total_count}개 종목 메모리 적재를 시작합니다.\n")

    # Commit listing evidence independently of subsequent quote/feature work.
    with db.get_session() as session:
        nxt_map, eligibility_summary = _collect_and_store_market_eligibility(
            db,
            session,
            token=kiwoom_token,
            stock_codes=kospi_codes,
            trade_date=target_date,
        )
    nxt_count = int(sum(1 for value in nxt_map.values() if value))
    logger.info(
        "✅ [ka10099] 날짜별 자격 ledger 저장: "
        f"{eligibility_summary.get('stored_count', 0)}개 "
        f"(status={eligibility_summary.get('status')}, NXT={nxt_count})"
    )
    if eligibility_summary.get("status") != "pass":
        update_status = "completed_with_warnings"
        update_reason = "market_eligibility_partial"
    for i, code in enumerate(kospi_codes):
        code_str = _normalize_stock_code(code)
        df_stock = process_and_save_stock(
            code_str, kiwoom_token, None, is_nxt=nxt_map.get(code_str, False)
        )

        if df_stock is not None and not df_stock.empty:
            feature_results[code_str] = {
                "status": df_stock.attrs.get("feature_status", "unreported"),
                "error": df_stock.attrs.get("feature_error"),
            }
            all_stocks_data.append(df_stock)
            successful_codes.append(code_str)
            if (df_stock["quote_date"] == target_date).any():
                target_date_codes.append(code_str)

        if (i + 1) % PROGRESS_INTERVAL == 0:
            logger.info(f" ⏳ 수집 진행 상황: [{i + 1}/{total_count}] 완료...")

        time.sleep(API_DELAY_SECONDS)  # API 제재 방지용 대기

    # [PHASE 2] 대망의 일괄 DB 삽입 (Bulk Insert)
    if all_stocks_data:
        logger.info(
            "\n🚀 모든 데이터 수집 완료! PostgreSQL로 일괄 전송(Bulk-Insert)을 시작합니다..."
        )

        # 모든 데이터프레임을 하나로 합치기
        final_bulk_df = pd.concat(all_stocks_data, ignore_index=True)
        # Conflict handling keeps both received history and unreceived keys.
        max_retries = 2
        inserted = False
        for attempt in range(max_retries):
            try:
                with db.engine.begin() as conn:
                    written_rows = _upsert_daily_quote_batch(conn, final_bulk_df)

                logger.info(
                    f"✅ DB 일괄 삽입 성공! (총 {len(final_bulk_df)}행 적재 완료)"
                )
                inserted_rows = written_rows
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
            update_status = "failed"
            update_reason = "bulk_insert_failed"
    else:
        logger.warning("⚠️ 수집된 데이터가 없어 DB 작업을 건너뜁니다.")
        update_status = "failed"
        update_reason = "no_collected_rows"

    missing_target_codes = sorted(set(kospi_codes) - set(target_date_codes))
    if update_status != "failed" and not target_date_codes:
        update_status = "failed"
        update_reason = "target_date_rows_missing"
    elif update_status != "failed" and missing_target_codes:
        update_status = "completed_with_warnings"
        update_reason = update_reason or "target_date_symbol_gaps"

    feature_failed_codes = sorted(
        code for code, result in feature_results.items() if result["status"] == "failed"
    )
    if update_status != "failed" and feature_failed_codes:
        update_status = "completed_with_warnings"
        update_reason = update_reason or "indicator_calculation_failed"

    logger.info(
        f"\n🎉 일일 업데이트 최종 완료! (성공: {len(successful_codes)} / {total_count} 종목)"
    )

    finish_msg = f"{'🚨' if update_status == 'failed' else '✅'} **KOSPI 일일 데이터 갱신: {update_status}**\n수신 **{len(successful_codes)} / {total_count}** 종목, 대상일 **{len(target_date_codes)}** 종목, 저장 **{inserted_rows}**행.\n🟣 NXT 대상 플래그 반영: **{nxt_count}개**"
    event_bus.publish(
        "TELEGRAM_BROADCAST",
        {"message": finish_msg, "audience": "ADMIN_ONLY", "parse_mode": "Markdown"},
    )
    return {
        "status": update_status,
        "reason": update_reason,
        "total_count": int(total_count),
        "successful_count": int(len(successful_codes)),
        "inserted_rows": inserted_rows,
        "target_date": target_date.isoformat(),
        "target_date_symbol_count": len(target_date_codes),
        "missing_target_date_codes": missing_target_codes,
        "unreceived_codes": sorted(set(kospi_codes) - set(successful_codes)),
        "excluded_symbol_identities": excluded_symbol_identities,
        "storage_contract": "received_key_upsert_preserve_unreceived_history_v1",
        "nxt_count": int(nxt_count),
        "eligibility": eligibility_summary,
        "feature_results": feature_results,
        "feature_failed_codes": feature_failed_codes,
    }


def _resolve_latest_report_date() -> str:
    latest_report_date = _today_str()
    diagnostic_path = (
        PROJECT_ROOT / "data" / "daily_recommendations_v2_diagnostics.json"
    )
    try:
        if diagnostic_path.exists():
            latest_report_date = str(
                json.loads(diagnostic_path.read_text(encoding="utf-8")).get(
                    "latest_date"
                )
                or latest_report_date
            )
    except Exception as e:
        logger.warning(f"⚠️ 추천 진단 날짜 로드 실패, calendar date 사용: {e}")
    return latest_report_date


def _swing_postclose_reports_enabled() -> bool:
    """Return whether the operator explicitly enabled Swing postclose work."""
    return str(
        os.getenv("KORSTOCKSCAN_SWING_POSTCLOSE_OPERATOR_OVERRIDE", "false")
    ).strip().lower() in {"1", "true", "on", "yes"}


def _run_bottom_rebound_sim_auto_loop(report_date: str) -> dict:
    if str(
        os.getenv("KORSTOCKSCAN_RUN_BOTTOM_REBOUND_SIM_AUTO_LOOP", "true")
    ).lower() in {"0", "false", "off", "no"}:
        return {"status": "skipped_disabled"}
    commands = [
        [
            sys.executable,
            "-m",
            "src.engine.swing.bottom_rebound_pattern_research",
            "--as-of",
            report_date,
        ],
        [
            sys.executable,
            "-m",
            "src.engine.swing.bottom_rebound_policy_auto_loop",
            "--date",
            report_date,
        ],
        [
            sys.executable,
            "-m",
            "src.engine.swing.bottom_rebound_candidate_source",
            "--date",
            report_date,
            "--require-sim-auto-policy",
        ],
        [
            sys.executable,
            "-m",
            "src.engine.swing_strategy_discovery_sim",
            "--date",
            report_date,
            "--include-bottom-rebound-source",
        ],
    ]
    completed: list[str] = []
    for command in commands:
        subprocess.run(command, check=True, cwd=PROJECT_ROOT)
        completed.append(" ".join(command[2:]))
    return {
        "status": "completed",
        "report_date": report_date,
        "decision_authority": "swing_bottom_rebound_sim_policy_auto_approval",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "broker_order_forbidden": True,
        "commands": completed,
    }


def run_update_kospi_chain() -> dict:
    target_date = _today_str()
    started_at = _now_iso()
    steps: list[dict] = []
    logger.info(
        f"[START] update_kospi target_date={target_date} started_at={started_at}"
    )

    try:
        update_summary = update_kospi_data() or {"status": "completed"}
        steps.append(
            _step(
                "update_kospi_data",
                str(update_summary.get("status", "completed")),
                details=update_summary,
            )
        )
    except Exception as e:
        logger.exception(f"❌ update_kospi_data 실행 중 치명적 오류: {e}")
        steps.append(_step("update_kospi_data", "failed", error=str(e)))
        payload = _build_update_kospi_status(target_date, started_at, steps)
        status_path = _write_update_kospi_status(payload)
        logger.error(
            f"[FAIL] update_kospi target_date={target_date} finished_at={payload['finished_at']} status_path={status_path}"
        )
        raise

    if steps[0]["status"] == "failed":
        payload = _build_update_kospi_status(target_date, started_at, steps)
        status_path = _write_update_kospi_status(payload)
        logger.error(
            f"[FAIL] update_kospi target_date={target_date} finished_at={payload['finished_at']} status_path={status_path}"
        )
        return payload

    logger.info("🚀 추천 모델(recommend_daily_v2.py)을 이어서 실행합니다...")
    try:
        subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "src/model/recommend_daily_v2.py")],
            check=True,
            cwd=PROJECT_ROOT,
        )
        steps.append(_step("recommend_daily_v2", "completed"))
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ 추천 모델 실행 중 에러 발생: {e}")
        steps.append(
            _step("recommend_daily_v2", "failed", returncode=e.returncode, error=str(e))
        )

    latest_report_date = _resolve_latest_report_date()
    if _swing_postclose_reports_enabled():
        logger.info("📈 스윙 일일 시뮬레이션 및 선정 funnel 리포트 생성 시작...")
        try:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "src.engine.swing_daily_simulation_report",
                    "--date",
                    latest_report_date,
                ],
                check=True,
            )
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "src.engine.swing_selection_funnel_report",
                    latest_report_date,
                ],
                check=True,
            )
            logger.info(f"✅ 스윙 일일 리포트 생성 완료: {latest_report_date}")
            steps.append(
                _step(
                    "swing_daily_reports", "completed", report_date=latest_report_date
                )
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ 스윙 일일 리포트 생성 실패 (무시하고 진행): {e}")
            steps.append(
                _step(
                    "swing_daily_reports",
                    "failed",
                    report_date=latest_report_date,
                    returncode=e.returncode,
                    error=str(e),
                )
            )

        logger.info("🧪 바닥 반등 스윙 sim-only 자동승인 루프 실행 시작...")
        try:
            loop_summary = _run_bottom_rebound_sim_auto_loop(latest_report_date)
            logger.info(
                f"✅ 바닥 반등 sim-only 자동승인 루프 완료: {loop_summary.get('status')}"
            )
            steps.append(
                _step(
                    "bottom_rebound_sim_auto_loop",
                    str(loop_summary.get("status", "completed")),
                    details=loop_summary,
                )
            )
        except subprocess.CalledProcessError as e:
            logger.error(
                f"❌ 바닥 반등 sim-only 자동승인 루프 실패 (무시하고 진행): {e}"
            )
            steps.append(
                _step(
                    "bottom_rebound_sim_auto_loop",
                    "failed",
                    report_date=latest_report_date,
                    returncode=e.returncode,
                    error=str(e),
                )
            )
    else:
        logger.info("⏭️ Swing postclose reports skipped: operator override is disabled")
        steps.append(
            _step(
                "swing_daily_reports",
                "skipped_disabled",
                report_date=latest_report_date,
                operator_override="KORSTOCKSCAN_SWING_POSTCLOSE_OPERATOR_OVERRIDE",
                runtime_effect=False,
            )
        )
        steps.append(
            _step(
                "bottom_rebound_sim_auto_loop",
                "skipped_disabled",
                report_date=latest_report_date,
                operator_override="KORSTOCKSCAN_SWING_POSTCLOSE_OPERATOR_OVERRIDE",
                runtime_effect=False,
            )
        )

    payload = _build_update_kospi_status(target_date, started_at, steps)
    status_path = _write_update_kospi_status(payload)
    log_marker = "[FAIL]" if payload["status"] == "failed" else "[DONE]"
    logger.info(
        f"{log_marker} update_kospi target_date={target_date} finished_at={payload['finished_at']} status={payload['status']} status_path={status_path}"
    )
    return payload


def _build_update_kospi_status(
    target_date: str, started_at: str, steps: list[dict]
) -> dict:
    update_status = steps[0].get("status") if steps else "failed"
    failed_steps = [s["name"] for s in steps if s.get("status") == "failed"]
    warning_steps = [
        s["name"] for s in steps if s.get("status") == "completed_with_warnings"
    ]

    if update_status == "failed" or failed_steps:
        status = "failed"
    elif warning_steps:
        status = "completed_with_warnings"
    elif update_status == "skipped_non_trading_day":
        status = "skipped_non_trading_day"
    else:
        status = "completed"

    return {
        "schema_version": STATUS_VERSION,
        "target_date": target_date,
        "started_at": started_at,
        "finished_at": _now_iso(),
        "status": status,
        "feature_source": "src.model.common_v2.calculate_all_features",
        "db_state": _load_latest_quote_state(),
        "steps": steps,
        "failed_steps": failed_steps,
        "warning_steps": warning_steps,
    }


def main():
    # Register notification receivers only at the executable boundary. Feature
    # consumers and test collection must not load credentials or start a bot.
    import src.notify.telegram_manager  # noqa: F401

    chain_status = run_update_kospi_chain()
    if chain_status.get("status") == "failed":
        sys.exit(1)


if __name__ == "__main__":
    main()
