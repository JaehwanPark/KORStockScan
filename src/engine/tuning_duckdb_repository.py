"""튜닝 모니터링 분석을 위한 DuckDB 리포지토리.

Parquet 파일을 직접 쿼리하거나 DuckDB 내부 테이블로 로드하여
집계 쿼리 및 리포트 생성을 제공.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import duckdb
import pandas as pd

from src.utils.constants import DATA_DIR

logger = logging.getLogger(__name__)

# DuckDB 파일 경로
DUCKDB_FILE = DATA_DIR / "analytics" / "duckdb" / "korstockscan_analytics.duckdb"
# Parquet 루트
PARQUET_ROOT = DATA_DIR / "analytics" / "parquet"


class TuningDuckDBRepository:
    """DuckDB 기반 분석 리포지토리."""

    def __init__(self, duckdb_path: Optional[Path] = None, read_only: bool = True):
        self.duckdb_path = duckdb_path or DUCKDB_FILE
        self.read_only = read_only
        self.conn = None
        self._ensure_db()

    def _ensure_db(self):
        """DuckDB 파일 및 디렉토리 생성."""
        self.duckdb_path.parent.mkdir(parents=True, exist_ok=True)
        # 연결
        self.conn = duckdb.connect(str(self.duckdb_path), read_only=self.read_only)
        # 설정
        self.conn.execute("SET enable_progress_bar = false;")
        self.conn.execute("SET threads TO 4;")

    def close(self):
        """연결 종료."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def register_parquet_dataset(self, dataset: str, partition_pattern: str = "date=*"):
        """Parquet 데이터셋을 DuckDB에 외부 테이블로 등록."""
        # 파티션 디렉토리: analytics/parquet/<dataset>/date=*
        dataset_dir = PARQUET_ROOT / dataset
        if not dataset_dir.exists():
            logger.warning("데이터셋 디렉토리 없음: %s", dataset_dir)
            return False
        # DuckDB는 파티션 디렉토리를 재귀적으로 읽을 수 있음
        # CREATE OR REPLACE VIEW <dataset> AS SELECT * FROM read_parquet('path/*/*.parquet')
        parquet_glob = str(dataset_dir / partition_pattern / "*.parquet")
        view_name = f"v_{dataset}"
        create_sql = f"""
        CREATE OR REPLACE VIEW {view_name} AS
        SELECT * FROM read_parquet('{parquet_glob}', union_by_name=true)
        """
        try:
            self.conn.execute(create_sql)
            logger.info("뷰 생성: %s -> %s", view_name, parquet_glob)
            return True
        except Exception as e:
            logger.error("뷰 생성 실패: %s", e)
            return False

    def query(self, sql: str, params: Optional[list] = None) -> pd.DataFrame:
        """SQL 쿼리 실행 후 DataFrame 반환."""
        if params:
            return self.conn.execute(sql, params).df()
        else:
            return self.conn.execute(sql).df()

    def get_trade_funnel(
        self, start_date: Union[str, date], end_date: Union[str, date]
    ) -> pd.DataFrame:
        """거래 퍼널 집계 (전체 거래 수 -> 체결 -> 완료)."""
        if isinstance(start_date, date):
            start_date = start_date.isoformat()
        if isinstance(end_date, date):
            end_date = end_date.isoformat()
        sql = """
        WITH base AS (
            SELECT
                emitted_date,
                pipeline,
                stage,
                fields_json
            FROM v_pipeline_events
            WHERE emitted_date BETWEEN ? AND ?
                AND pipeline IN ('SCALPING_PIPELINE', 'HOLDING_PIPELINE')
        )
        SELECT
            emitted_date,
            pipeline,
            COUNT(*) AS total_events,
            COUNT(CASE WHEN stage LIKE '%entry%' THEN 1 END) AS entry_events,
            COUNT(CASE WHEN stage LIKE '%fill%' THEN 1 END) AS fill_events,
            COUNT(CASE WHEN stage LIKE '%completed%' THEN 1 END) AS completed_events
        FROM base
        GROUP BY emitted_date, pipeline
        ORDER BY emitted_date, pipeline
        """
        return self.query(sql, [start_date, end_date])

    def get_blocker_counts(
        self, start_date: Union[str, date], end_date: Union[str, date]
    ) -> pd.DataFrame:
        """Blocker 4축별 집계."""
        if isinstance(start_date, date):
            start_date = start_date.isoformat()
        if isinstance(end_date, date):
            end_date = end_date.isoformat()
        # blocker 분류는 stage 및 fields_json에 의존
        # 예시: latency guard miss는 stage='latency_guard' AND fields_json->>'passed'='false'
        # 실제 필드명은 데이터에 맞게 조정 필요
        sql = """
        WITH blockers AS (
            SELECT
                emitted_date,
                pipeline,
                stage,
                fields_json,
                CASE
                    WHEN stage = 'latency_guard' AND fields_json->>'passed' = 'false'
                        THEN 'latency'
                    WHEN stage = 'liquidity_gate' AND fields_json->>'passed' = 'false'
                        THEN 'liquidity'
                    WHEN stage = 'ai_threshold' AND fields_json->>'passed' = 'false'
                        THEN 'ai_threshold'
                    WHEN stage = 'overbought_gate' AND fields_json->>'passed' = 'false'
                        THEN 'overbought'
                    ELSE 'other'
                END AS blocker_type
            FROM v_pipeline_events
            WHERE emitted_date BETWEEN ? AND ?
                AND pipeline = 'SCALPING_PIPELINE'
        )
        SELECT
            emitted_date,
            blocker_type,
            COUNT(*) AS blocker_count
        FROM blockers
        WHERE blocker_type != 'other'
        GROUP BY emitted_date, blocker_type
        ORDER BY emitted_date, blocker_type
        """
        return self.query(sql, [start_date, end_date])

    def get_fill_breakdown(
        self, start_date: Union[str, date], end_date: Union[str, date]
    ) -> pd.DataFrame:
        """full fill / partial fill 분리 집계."""
        if isinstance(start_date, date):
            start_date = start_date.isoformat()
        if isinstance(end_date, date):
            end_date = end_date.isoformat()
        sql = """
        SELECT
            emitted_date,
            pipeline,
            COUNT(*) AS total_fills,
            COUNT(CASE WHEN fields_json->>'fill_type' = 'full' THEN 1 END) AS full_fill,
            COUNT(CASE WHEN fields_json->>'fill_type' = 'partial' THEN 1 END) AS partial_fill
        FROM v_pipeline_events
        WHERE emitted_date BETWEEN ? AND ?
            AND stage LIKE '%fill%'
        GROUP BY emitted_date, pipeline
        ORDER BY emitted_date, pipeline
        """
        return self.query(sql, [start_date, end_date])

    def get_profit_rates(
        self, start_date: Union[str, date], end_date: Union[str, date]
    ) -> pd.DataFrame:
        """완료된 거래의 profit_rate 집계 (COMPLETED + valid profit_rate)."""
        if isinstance(start_date, date):
            start_date = start_date.isoformat()
        if isinstance(end_date, date):
            end_date = end_date.isoformat()
        sql = """
        SELECT
            emitted_date,
            pipeline,
            COUNT(*) AS completed_count,
            AVG(CAST(fields_json->>'profit_rate' AS DOUBLE)) AS avg_profit_rate,
            MIN(CAST(fields_json->>'profit_rate' AS DOUBLE)) AS min_profit_rate,
            MAX(CAST(fields_json->>'profit_rate' AS DOUBLE)) AS max_profit_rate
        FROM v_pipeline_events
        WHERE emitted_date BETWEEN ? AND ?
            AND stage = 'completed'
            AND fields_json->>'profit_rate' IS NOT NULL
            AND fields_json->>'profit_rate' != ''
            AND CAST(fields_json->>'profit_rate' AS DOUBLE) IS NOT NULL
        GROUP BY emitted_date, pipeline
        ORDER BY emitted_date, pipeline
        """
        return self.query(sql, [start_date, end_date])

    def get_missed_upside(
        self, start_date: Union[str, date], end_date: Union[str, date]
    ) -> pd.DataFrame:
        """미진입 기회비용 (missed upside) 추정."""
        if isinstance(start_date, date):
            start_date = start_date.isoformat()
        if isinstance(end_date, date):
            end_date = end_date.isoformat()
        # 예시: entry 신호 후 fill 없는 경우의 최대 잠재 수익
        # 실제 로직은 데이터 구조에 맞게 구현 필요
        sql = """
        WITH entry_signals AS (
            SELECT
                emitted_date,
                stock_code,
                fields_json->>'potential_profit' AS potential_profit
            FROM v_pipeline_events
            WHERE stage = 'entry_signal'
                AND emitted_date BETWEEN ? AND ?
        ),
        missing_fills AS (
            SELECT
                e.emitted_date,
                e.stock_code,
                e.potential_profit
            FROM entry_signals e
            LEFT JOIN v_pipeline_events f
                ON e.stock_code = f.stock_code
                    AND e.emitted_date = f.emitted_date
                    AND f.stage LIKE '%fill%'
            WHERE f.stock_code IS NULL
        )
        SELECT
            emitted_date,
            COUNT(*) AS missed_signals,
            SUM(CAST(potential_profit AS DOUBLE)) AS total_missed_upside
        FROM missing_fills
        WHERE potential_profit IS NOT NULL AND potential_profit != ''
        GROUP BY emitted_date
        ORDER BY emitted_date
        """
        return self.query(sql, [start_date, end_date])

    def get_dataset_coverage(self) -> pd.DataFrame:
        """Parquet 데이터셋의 날짜별 커버리지 확인."""
        sql = """
        SELECT
            'pipeline_events' AS dataset,
            MIN(emitted_date) AS min_date,
            MAX(emitted_date) AS max_date,
            COUNT(DISTINCT emitted_date) AS date_count,
            COUNT(*) AS total_rows
        FROM v_pipeline_events
        UNION ALL
        SELECT
            'post_sell' AS dataset,
            MIN(emitted_date) AS min_date,
            MAX(emitted_date) AS max_date,
            COUNT(DISTINCT emitted_date) AS date_count,
            COUNT(*) AS total_rows
        FROM v_post_sell
        UNION ALL
        SELECT
            'system_metric_samples' AS dataset,
            MIN(emitted_date) AS min_date,
            MAX(emitted_date) AS max_date,
            COUNT(DISTINCT emitted_date) AS date_count,
            COUNT(*) AS total_rows
        FROM v_system_metric_samples
        """
        return self.query(sql)

    def health_check(self) -> Dict[str, Any]:
        """DuckDB 및 Parquet 데이터 소스 상태 점검."""
        missing_datasets = []
        for dataset in ["pipeline_events", "post_sell", "system_metric_samples"]:
            try:
                self.conn.execute(f"SELECT 1 FROM v_{dataset} LIMIT 1")
            except:
                missing_datasets.append(dataset)
        # coverage는 뷰가 없을 수 있으므로 try-except
        try:
            coverage = self.get_dataset_coverage()
        except Exception as e:
            coverage = pd.DataFrame()
        return {
            "duckdb_file": str(self.duckdb_path),
            "parquet_root": str(PARQUET_ROOT),
            "coverage": coverage.to_dict(orient="records"),
            "missing_datasets": missing_datasets,
            "total_rows": int(coverage["total_rows"].sum() if not coverage.empty else 0),
        }


def create_analytics_views(duckdb_path: Optional[Path] = None):
    """모든 Parquet 데이터셋을 뷰로 등록 (일회성 초기화)."""
    with TuningDuckDBRepository(duckdb_path, read_only=False) as repo:
        for dataset in ["pipeline_events", "post_sell", "system_metric_samples"]:
            success = repo.register_parquet_dataset(dataset)
            logger.info("데이터셋 %s 등록 %s", dataset, "성공" if success else "실패")


if __name__ == "__main__":
    # 테스트 실행
    import sys
    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        create_analytics_views()
        print("뷰 생성 완료.")
    else:
        with TuningDuckDBRepository() as repo:
            print("커버리지:")
            print(repo.get_dataset_coverage())
            print("\n상태 점검:")
            print(repo.health_check())
