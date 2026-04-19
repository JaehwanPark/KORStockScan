"""대시보드 파일 데이터를 DB로 백필하는 CLI."""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date, timedelta
from pathlib import Path

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.engine.dashboard_data_repository import backfill_dashboard_files, ensure_tables

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(
        description="대시보드 파일(pipeline_events, monitor_snapshots)을 PostgreSQL DB로 백필."
    )
    parser.add_argument(
        "--until",
        default=(date.today() - timedelta(days=1)).isoformat(),
        help="백필 종료 날짜 (YYYY-MM-DD, 기본값: 어제)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="실제 DB 작업 없이 스캔만 수행",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    until_date = args.until
    dry_run = args.dry_run

    logger.info("대시보드 DB 백필 시작 (until=%s, dry_run=%s)", until_date, dry_run)

    # 테이블 보장
    if not dry_run:
        try:
            ensure_tables()
            logger.info("테이블 확인 완료")
        except Exception as e:
            logger.error("테이블 생성 실패: %s", e)
            sys.exit(1)

    if dry_run:
        # 실제 백필 로직을 모방하는 dry-run 수행
        stats = backfill_dashboard_files(until_date, dry_run=True)
        logger.info("DRY RUN 통계:")
        logger.info("  Pipeline Events: scanned=%d, inserted=%d, skipped=%d, would_insert=%d",
                    stats["pipeline_events"]["scanned"],
                    stats["pipeline_events"]["inserted"],
                    stats["pipeline_events"]["skipped"],
                    stats["pipeline_events"]["would_insert"])
        logger.info("  Monitor Snapshots: scanned=%d, inserted=%d, skipped=%d, would_insert=%d",
                    stats["monitor_snapshots"]["scanned"],
                    stats["monitor_snapshots"]["inserted"],
                    stats["monitor_snapshots"]["skipped"],
                    stats["monitor_snapshots"]["would_insert"])
        if stats["failed_dates"]:
            logger.warning("실패한 날짜: %s", stats["failed_dates"])
        logger.info("DRY RUN 완료")
        sys.exit(0)

    stats = backfill_dashboard_files(until_date)
    logger.info("백필 통계:")
    logger.info("  Pipeline Events: scanned=%d, inserted=%d, skipped=%d, would_insert=%d",
                stats["pipeline_events"]["scanned"],
                stats["pipeline_events"]["inserted"],
                stats["pipeline_events"]["skipped"],
                stats["pipeline_events"]["would_insert"])
    logger.info("  Monitor Snapshots: scanned=%d, inserted=%d, skipped=%d, would_insert=%d",
                stats["monitor_snapshots"]["scanned"],
                stats["monitor_snapshots"]["inserted"],
                stats["monitor_snapshots"]["skipped"],
                stats["monitor_snapshots"]["would_insert"])
    if stats["failed_dates"]:
        logger.warning("실패한 날짜: %s", stats["failed_dates"])
    logger.info("백필 완료")


if __name__ == "__main__":
    main()