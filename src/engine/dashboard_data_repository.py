"""통합대시보드 데이터 DB 저장소 모듈.

기존 파일 기반(`json`, `jsonl`) 대시보드/모니터링 데이터를 PostgreSQL DB로 이관하고,
과거 데이터는 DB를 canonical source로, 당일 데이터는 파일+DB 병행 조회를 지원합니다.
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Any

import psycopg2
from psycopg2.extras import Json
from psycopg2.sql import SQL, Identifier

from src.utils.constants import DATA_DIR, POSTGRES_URL

logger = logging.getLogger(__name__)

# 파일 기반 저장 경로 (기존 코드와 호환)
PIPELINE_EVENTS_DIR = DATA_DIR / "pipeline_events"
MONITOR_SNAPSHOT_DIR = DATA_DIR / "report" / "monitor_snapshots"


def get_db_connection():
    """PostgreSQL 연결을 생성하여 반환."""
    return psycopg2.connect(POSTGRES_URL)


def ensure_tables():
    """필요한 테이블이 없으면 생성 (부트스트랩)."""
    create_pipeline_events = """
    CREATE TABLE IF NOT EXISTS dashboard_pipeline_events (
        id BIGSERIAL PRIMARY KEY,
        event_date DATE NOT NULL,
        pipeline VARCHAR(64) NOT NULL,
        stock_code VARCHAR(6) NOT NULL,
        stage VARCHAR(64) NOT NULL,
        emitted_at TIMESTAMP WITH TIME ZONE NOT NULL,
        record_id INTEGER,
        fields_json JSONB,
        raw_payload_json JSONB NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        UNIQUE (event_date, pipeline, stock_code, stage, emitted_at, record_id)
    );
    CREATE INDEX IF NOT EXISTS idx_dashboard_pipeline_events_date
        ON dashboard_pipeline_events (event_date);
    CREATE INDEX IF NOT EXISTS idx_dashboard_pipeline_events_pipeline_stage
        ON dashboard_pipeline_events (pipeline, stage);
    """

    create_monitor_snapshots = """
    CREATE TABLE IF NOT EXISTS dashboard_monitor_snapshots (
        id BIGSERIAL PRIMARY KEY,
        snapshot_kind VARCHAR(128) NOT NULL,
        target_date DATE NOT NULL,
        schema_version INTEGER DEFAULT 1,
        saved_snapshot_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        payload_json JSONB NOT NULL,
        UNIQUE (snapshot_kind, target_date)
    );
    CREATE INDEX IF NOT EXISTS idx_dashboard_monitor_snapshots_date
        ON dashboard_monitor_snapshots (target_date);
    CREATE INDEX IF NOT EXISTS idx_dashboard_monitor_snapshots_kind
        ON dashboard_monitor_snapshots (snapshot_kind);
    """

    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(create_pipeline_events)
            cur.execute(create_monitor_snapshots)
        conn.commit()
        logger.info("Dashboard DB tables ensured.")
    except Exception as e:
        logger.error("Failed to ensure dashboard tables: %s", e)
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


def upsert_pipeline_event_rows(target_date: str, rows: list[dict]) -> int:
    """여러 pipeline event 행을 DB에 업서트.

    Args:
        target_date: YYYY-MM-DD 형식의 날짜.
        rows: 각 행은 pipeline_event_logger.emit_pipeline_event가 생성한 raw_payload_json 형식.

    Returns:
        실제 삽입/갱신된 행 수 (중복 제외).
    """
    ensure_tables()
    conn = None
    inserted = 0
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            for row in rows:
                # raw_payload_json이 이미 모든 필드를 포함하고 있음.
                # 필요한 컬럼 추출
                event_date = row.get("emitted_date") or target_date
                pipeline = row.get("pipeline", "")
                stock_code = row.get("stock_code", "")
                stage = row.get("stage", "")
                emitted_at = row.get("emitted_at")
                if not emitted_at:
                    continue
                record_id = row.get("record_id")
                fields = row.get("fields", {})
                # 유니크 키 충돌 시 무시 (ON CONFLICT DO NOTHING)
                cur.execute("""
                    INSERT INTO dashboard_pipeline_events
                        (event_date, pipeline, stock_code, stage, emitted_at,
                         record_id, fields_json, raw_payload_json)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (event_date, pipeline, stock_code, stage, emitted_at, record_id)
                    DO NOTHING
                    """,
                    (event_date, pipeline, stock_code, stage, emitted_at,
                     record_id, Json(fields), Json(row))
                )
                if cur.rowcount > 0:
                    inserted += 1
        conn.commit()
    except Exception as e:
        logger.error("Failed to upsert pipeline events: %s", e)
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()
    return inserted


def upsert_monitor_snapshot(kind: str, target_date: str, payload: dict) -> None:
    """모니터 스냅샷을 DB에 저장 (갱신)."""
    ensure_tables()
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO dashboard_monitor_snapshots
                    (snapshot_kind, target_date, payload_json)
                VALUES (%s, %s, %s)
                ON CONFLICT (snapshot_kind, target_date)
                DO UPDATE SET
                    payload_json = EXCLUDED.payload_json,
                    saved_snapshot_at = NOW()
                """,
                (kind, target_date, Json(payload))
            )
        conn.commit()
        logger.debug("Upserted monitor snapshot %s for %s", kind, target_date)
    except Exception as e:
        logger.error("Failed to upsert monitor snapshot: %s", e)
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


def load_monitor_snapshot_prefer_db(kind: str, target_date: str) -> dict | None:
    """과거 날짜는 DB 우선, 당일은 파일 우선으로 스냅샷 로드.

    규칙:
        - target_date < today: DB 조회 (없으면 파일 조회)
        - target_date == today: 파일 조회 (없으면 DB 조회)
        - target_date > today: None 반환

    Returns:
        스냅샷 payload 또는 None.
    """
    today = date.today().isoformat()
    target = target_date
    # 날짜 비교를 위해 문자열을 date 객체로 변환
    try:
        target_dt = date.fromisoformat(target)
        today_dt = date.fromisoformat(today)
    except ValueError:
        # 날짜 형식이 잘못된 경우 None 반환
        logger.warning("Invalid date format: %s", target_date)
        return None

    # 당일 여부
    if target_dt == today_dt:
        # 당일: 파일 우선
        snapshot = _load_monitor_snapshot_from_file(kind, target_date)
        if snapshot is not None:
            snapshot["meta"] = snapshot.get("meta", {})
            snapshot["meta"]["source"] = "file"
            return snapshot
        # 파일 없으면 DB 조회
        snapshot = _load_monitor_snapshot_from_db(kind, target_date)
        if snapshot is not None:
            snapshot["meta"] = snapshot.get("meta", {})
            snapshot["meta"]["source"] = "db"
        return snapshot
    elif target_dt < today_dt:
        # 과거: DB 우선
        snapshot = _load_monitor_snapshot_from_db(kind, target_date)
        if snapshot is not None:
            snapshot["meta"] = snapshot.get("meta", {})
            snapshot["meta"]["source"] = "db"
            return snapshot
        # DB 없으면 파일 조회 (fallback)
        snapshot = _load_monitor_snapshot_from_file(kind, target_date)
        if snapshot is not None:
            snapshot["meta"] = snapshot.get("meta", {})
            snapshot["meta"]["source"] = "file"
        return snapshot
    else:
        # 미래 날짜
        return None


def _load_monitor_snapshot_from_file(kind: str, target_date: str) -> dict | None:
    """파일 시스템에서 모니터 스냅샷 로드."""
    import json
    import logging
    logger = logging.getLogger(__name__)
    path = MONITOR_SNAPSHOT_DIR / f"{kind}_{target_date}.json"
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error("Failed to load monitor snapshot from file %s: %s", path, e)
        return None


def _load_monitor_snapshot_from_db(kind: str, target_date: str) -> dict | None:
    """DB에서 모니터 스냅샷 로드."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT payload_json FROM dashboard_monitor_snapshots
                WHERE snapshot_kind = %s AND target_date = %s
                """,
                (kind, target_date)
            )
            row = cur.fetchone()
            if row:
                return row[0]
    except Exception as e:
        logger.error("Failed to load monitor snapshot from DB: %s", e)
    finally:
        if conn:
            conn.close()
    return None


def _list_snapshot_kinds(target_date: str) -> list[str]:
    """주어진 날짜에 존재하는 모니터 스냅샷 종류(kind) 목록을 반환."""
    import re
    kinds = set()
    for path in MONITOR_SNAPSHOT_DIR.glob(f"*_{target_date}.json"):
        stem = path.stem  # "{kind}_{target_date}"
        # target_date 부분 제거
        maybe_kind = stem[:-(len(target_date) + 1)]  # '_' 제거
        if maybe_kind:
            kinds.add(maybe_kind)
    return sorted(kinds)


def load_pipeline_events(target_date: str, *, include_file_for_today: bool = True) -> list[dict]:
    """특정 날짜의 pipeline event 목록을 반환.

    규칙:
        - target_date < today: DB 조회 (DB에 없으면 파일 조회)
        - target_date == today: include_file_for_today=True 이면 파일+DB 병합,
          False이면 DB만 조회.
        - target_date > today: 빈 목록 반환.

    Returns:
        raw_payload_json 목록 (정렬 보장 안 됨).
    """
    today = date.today().isoformat()
    target = target_date
    try:
        target_dt = date.fromisoformat(target)
        today_dt = date.fromisoformat(today)
    except ValueError:
        logger.warning("Invalid date format: %s", target_date)
        return []

    events = []
    # DB 조회
    db_events = _load_pipeline_events_from_db(target_date)
    events.extend(db_events)

    if target_dt == today_dt:
        # 당일: include_file_for_today 플래그에 따라 파일 병합
        if include_file_for_today:
            file_events = _load_pipeline_events_from_file(target_date)
            # 중복 제거: emitted_at + pipeline + stock_code + stage + record_id 기준
            seen = set()
            deduped = []
            for ev in events + file_events:
                key = (
                    ev.get("emitted_at"),
                    ev.get("pipeline"),
                    ev.get("stock_code"),
                    ev.get("stage"),
                    ev.get("record_id"),
                )
                if key not in seen:
                    seen.add(key)
                    deduped.append(ev)
            events = deduped
            source = "mixed"
        else:
            source = "db"
    elif target_dt < today_dt:
        # 과거: DB에 데이터가 있으면 반환, 없으면 파일 fallback
        if not events:
            file_events = _load_pipeline_events_from_file(target_date)
            events.extend(file_events)
            source = "file" if file_events else "db"
        else:
            source = "db"
    else:
        # 미래 날짜
        return []

    # 메타 정보 추가 (필요 시)
    # 현재는 원본 raw_payload_json을 그대로 반환.
    # 호출자가 필요하면 각 이벤트에 메타를 추가할 수 있지만 지금은 생략.
    return events


def _load_pipeline_events_from_file(target_date: str) -> list[dict]:
    """파일에서 pipeline event 로드."""
    import json
    path = PIPELINE_EVENTS_DIR / f"pipeline_events_{target_date}.jsonl"
    events = []
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            logger.error("Failed to read pipeline events file %s: %s", path, e)
    return events


def _load_pipeline_events_from_db(target_date: str) -> list[dict]:
    """DB에서 pipeline event 로드."""
    conn = None
    events = []
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT raw_payload_json FROM dashboard_pipeline_events
                WHERE event_date = %s
                ORDER BY emitted_at
                """,
                (target_date,)
            )
            for row in cur:
                events.append(row[0])
    except Exception as e:
        logger.error("Failed to load pipeline events from DB: %s", e)
    finally:
        if conn:
            conn.close()
    return events


def backfill_dashboard_files(until_date: str, dry_run: bool = False) -> dict:
    """지정 날짜까지의 모든 파일 데이터를 DB로 백필.

    Args:
        until_date: YYYY-MM-DD 형식, 이 날짜 포함 이전까지 백필.
                   보통 오늘보다 하루 전까지.
        dry_run: 실제 DB 작업 없이 스캔만 수행.

    Returns:
        통계 dict.
    """
    from datetime import datetime, timedelta

    if not dry_run:
        ensure_tables()
    stats = {
        "pipeline_events": {"scanned": 0, "inserted": 0, "skipped": 0, "would_insert": 0},
        "monitor_snapshots": {"scanned": 0, "inserted": 0, "skipped": 0, "would_insert": 0},
        "failed_dates": [],
    }

    today = date.today()
    try:
        until_dt = date.fromisoformat(until_date)
    except ValueError:
        logger.error("Invalid until_date: %s", until_date)
        return stats

    # 파일 시스템 스캔하여 존재하는 날짜 수집
    existing_dates = set()
    
    # pipeline events 파일 날짜 추출
    for path in PIPELINE_EVENTS_DIR.glob("pipeline_events_*.jsonl"):
        stem = path.stem  # "pipeline_events_YYYY-MM-DD"
        try:
            file_date = date.fromisoformat(stem.split("_")[-1])
        except (ValueError, IndexError):
            continue
        existing_dates.add(file_date)
    
    # monitor snapshot 파일 날짜 추출
    for path in MONITOR_SNAPSHOT_DIR.glob("*_*.json"):
        stem = path.stem  # "{kind}_YYYY-MM-DD"
        try:
            file_date = date.fromisoformat(stem.split("_")[-1])
        except (ValueError, IndexError):
            continue
        existing_dates.add(file_date)
    
    if not existing_dates:
        logger.info("백필할 파일이 없습니다.")
        return stats
    
    earliest_date = min(existing_dates)
    # earliest_date부터 until_dt까지 순회 (until_dt 이후는 제외)
    current = earliest_date
    while current <= until_dt:
        # 오늘은 백필하지 않음 (당일 파일은 야간 후크에서 처리)
        if current == today:
            current += timedelta(days=1)
            continue
        target = current.isoformat()
        
        # pipeline events 백필
        file_path = PIPELINE_EVENTS_DIR / f"pipeline_events_{target}.jsonl"
        if file_path.exists():
            stats["pipeline_events"]["scanned"] += 1
            events = _load_pipeline_events_from_file(target)
            if events:
                if dry_run:
                    # dry‑run에서는 삽입 건수를 이벤트 수로 가정 (실제로는 0)
                    stats["pipeline_events"]["inserted"] += 0
                    stats["pipeline_events"]["skipped"] += len(events)
                    stats["pipeline_events"]["would_insert"] += len(events)
                else:
                    inserted = upsert_pipeline_event_rows(target, events)
                    stats["pipeline_events"]["inserted"] += inserted
                    stats["pipeline_events"]["skipped"] += len(events) - inserted
                    stats["pipeline_events"]["would_insert"] += inserted
            else:
                stats["pipeline_events"]["skipped"] += 1
        
        # monitor snapshots 백필
        snapshot_kinds = _list_snapshot_kinds(target)
        for kind in snapshot_kinds:
            snapshot = _load_monitor_snapshot_from_file(kind, target)
            if snapshot is not None:
                stats["monitor_snapshots"]["scanned"] += 1
                if dry_run:
                    stats["monitor_snapshots"]["inserted"] += 0
                    stats["monitor_snapshots"]["skipped"] += 1
                    stats["monitor_snapshots"]["would_insert"] += 1
                else:
                    upsert_monitor_snapshot(kind, target, snapshot)
                    stats["monitor_snapshots"]["inserted"] += 1
                    stats["monitor_snapshots"]["would_insert"] += 1
                    stats["monitor_snapshots"]["skipped"] += 0
            else:
                stats["monitor_snapshots"]["skipped"] += 1
        
        current += timedelta(days=1)
    
    return stats


def upload_today_dashboard_files() -> dict:
    """당일 생성된 대시보드 파일을 DB에 업로드 (야간 후크용).

    주로 update_kospi.py 종료 후 호출.
    """
    today = date.today().isoformat()
    stats = {
        "pipeline_events": {"scanned": 0, "inserted": 0, "would_insert": 0},
        "monitor_snapshots": {"scanned": 0, "inserted": 0, "would_insert": 0},
    }
    # pipeline events
    events = _load_pipeline_events_from_file(today)
    if events:
        stats["pipeline_events"]["scanned"] = 1
        inserted = upsert_pipeline_event_rows(today, events)
        stats["pipeline_events"]["inserted"] = inserted
        stats["pipeline_events"]["would_insert"] = inserted
    # monitor snapshots
    snapshot_kinds = _list_snapshot_kinds(today)
    for kind in snapshot_kinds:
        snapshot = _load_monitor_snapshot_from_file(kind, today)
        if snapshot is not None:
            stats["monitor_snapshots"]["scanned"] += 1
            upsert_monitor_snapshot(kind, today, snapshot)
            stats["monitor_snapshots"]["inserted"] += 1
    return stats