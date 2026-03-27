import sys
import os
import argparse
import logging
from pathlib import Path
from datetime import datetime

import pandas as pd
from sqlalchemy import text, bindparam

# ==========================================
# 프로젝트 루트 경로 등록
# ==========================================
THIS_FILE = Path(__file__).resolve()
CANDIDATES = [THIS_FILE.parent]
CANDIDATES.extend(THIS_FILE.parents)
PROJECT_ROOT = None
for p in CANDIDATES:
    if (p / 'src').exists():
        PROJECT_ROOT = p
        break

if PROJECT_ROOT is None:
    env_root = os.environ.get('KORSTOCKSCAN_PROJECT_ROOT')
    if env_root and (Path(env_root) / 'src').exists():
        PROJECT_ROOT = Path(env_root)

if PROJECT_ROOT is None:
    raise RuntimeError(
        "프로젝트 루트를 찾지 못했습니다. "
        "스크립트를 프로젝트 하위에서 실행하거나 KORSTOCKSCAN_PROJECT_ROOT 환경변수를 설정하세요."
    )

sys.path.append(str(PROJECT_ROOT))

from src.utils import kiwoom_utils  # noqa: E402
from src.database.db_manager import DBManager  # noqa: E402

TABLE_NAME = 'daily_stock_quotes'


def build_logger() -> logging.Logger:
    logger = logging.getLogger('UpdateDailyStockQuotesIsNxtOnce')
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(handler)
    return logger


logger = build_logger()


def normalize_code(code: str) -> str:
    raw = str(code or '').strip().upper().replace('.0', '')
    if raw.endswith('_AL'):
        raw = raw[:-3]
    if raw.startswith('A') and len(raw) >= 7:
        raw = raw[1:]
    digits = ''.join(ch for ch in raw if ch.isdigit())
    return digits[-6:].zfill(6) if digits else raw


def get_target_date(db: DBManager, explicit_date: str | None) -> str:
    if explicit_date:
        return explicit_date

    with db.engine.connect() as conn:
        latest = conn.execute(text(f"SELECT MAX(quote_date) FROM {TABLE_NAME}")).scalar()
    if latest is None:
        raise RuntimeError(f"{TABLE_NAME} 테이블에 데이터가 없습니다.")
    return str(latest)


def load_target_rows(db: DBManager, target_date: str | None, update_all_dates: bool) -> pd.DataFrame:
    query = f"""
        SELECT quote_date, stock_code, is_nxt
        FROM {TABLE_NAME}
    """
    params = {}
    if not update_all_dates:
        query += " WHERE quote_date = :target_date"
        params['target_date'] = target_date

    with db.engine.connect() as conn:
        df = pd.read_sql(text(query), conn, params=params)

    if df.empty:
        scope = '전체 기간' if update_all_dates else f'quote_date={target_date}'
        raise RuntimeError(f"업데이트 대상 행이 없습니다. ({scope})")

    df['stock_code'] = df['stock_code'].astype(str).map(normalize_code)
    df['is_nxt'] = df['is_nxt'].fillna(False).astype(bool)
    return df


def build_nxt_flag_map(target_codes: list[str], mrkt_tps: tuple[str, ...]) -> dict[str, bool]:
    token = kiwoom_utils.get_kiwoom_token()
    if not token:
        raise RuntimeError('키움 토큰 발급 실패')

    nxt_map = kiwoom_utils.get_nxt_flag_map_ka10099(token, target_codes=target_codes, mrkt_tps=mrkt_tps)
    if not nxt_map:
        raise RuntimeError('[ka10099] NXT 플래그 맵 생성 실패: 빈 결과')

    return {normalize_code(k): bool(v) for k, v in nxt_map.items()}


def prepare_updates(df_rows: pd.DataFrame, nxt_map: dict[str, bool]) -> tuple[list[dict], pd.DataFrame]:
    work = df_rows.copy()
    work['new_is_nxt'] = work['stock_code'].map(lambda c: bool(nxt_map.get(c, False)))
    changed = work[work['is_nxt'] != work['new_is_nxt']].copy()

    payloads = [
        {
            'quote_date': row.quote_date,
            'stock_code': row.stock_code,
            'is_nxt': bool(row.new_is_nxt),
        }
        for row in changed.itertuples(index=False)
    ]
    return payloads, changed


def apply_updates(db: DBManager, payloads: list[dict]) -> int:
    if not payloads:
        return 0

    update_sql = text(f"""
        UPDATE {TABLE_NAME}
           SET is_nxt = :is_nxt
         WHERE quote_date = :quote_date
           AND stock_code = :stock_code
           AND is_nxt IS DISTINCT FROM :is_nxt
    """).bindparams(
        bindparam('quote_date'),
        bindparam('stock_code'),
        bindparam('is_nxt'),
    )

    with db.engine.begin() as conn:
        result = conn.execute(update_sql, payloads)
    return int(result.rowcount or 0)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='ka10099 기반으로 daily_stock_quotes.is_nxt를 1회성 갱신합니다.'
    )
    parser.add_argument('--date', help='대상 quote_date (YYYY-MM-DD). 미지정 시 테이블 최신일')
    parser.add_argument('--all-dates', action='store_true', help='테이블 전체 기간을 갱신')
    parser.add_argument('--mrkt-tp', nargs='*', default=['0', '10'], help='ka10099 mrkt_tp 목록. 기본값: 0 10')
    parser.add_argument('--dry-run', action='store_true', help='실제 UPDATE 없이 변경 예정 건수만 확인')
    parser.add_argument('--sample', type=int, default=20, help='미리보기 최대 행 수. 기본값: 20')
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.date:
        try:
            datetime.strptime(args.date, '%Y-%m-%d')
        except ValueError as e:
            raise SystemExit(f'--date 형식 오류: {e}')

    db = DBManager()
    target_date = None if args.all_dates else get_target_date(db, args.date)

    if args.all_dates:
        logger.info('🔄 대상 범위: 전체 quote_date')
    else:
        logger.info(f'🔄 대상 범위: quote_date = {target_date}')

    df_rows = load_target_rows(db, target_date=target_date, update_all_dates=args.all_dates)
    target_codes = sorted(df_rows['stock_code'].dropna().astype(str).unique().tolist())
    logger.info(f'📌 대상 행 수: {len(df_rows):,} / 대상 종목 수: {len(target_codes):,}')

    nxt_map = build_nxt_flag_map(target_codes, tuple(str(x) for x in args.mrkt_tp))
    true_count = sum(1 for v in nxt_map.values() if v)
    false_count = len(nxt_map) - true_count
    logger.info(f'✅ [ka10099] NXT 가능 종목: {true_count:,} / 비대상: {false_count:,}')

    payloads, changed = prepare_updates(df_rows, nxt_map)
    logger.info(f'🧮 변경 대상 행 수: {len(payloads):,}')

    if not changed.empty:
        preview = changed[['quote_date', 'stock_code', 'is_nxt', 'new_is_nxt']].head(max(args.sample, 0))
        logger.info('--- 변경 미리보기 ---')
        logger.info(preview.to_string(index=False))

    if args.dry_run:
        logger.info('🧪 dry-run 모드이므로 DB UPDATE는 수행하지 않았습니다.')
        return 0

    updated = apply_updates(db, payloads)
    logger.info(f'🎉 UPDATE 완료: {updated:,}행 반영')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
