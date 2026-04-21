# 작업지시서: 튜닝 모니터링 로그 아키텍처 재설계 (DeepSeek 전용)

작성일: 2026-04-21  
대상: DeepSeek AI (코딩 에이전트)  
범위: `튜닝 모니터링 로그 데이터 경로` 한정

---

## 1. 판정

1. 기존 `json/jsonl -> PostgreSQL 대량 적재` 중심 구조는 튜닝/감사 반복에서 스키마 경직성과 운영비를 키운다.
2. 원본 이벤트 보존과 분석 질의를 분리해야 기대값 개선 속도를 높일 수 있다.
3. 목표 구조는 `원본 jsonl 보관 + 분석 parquet/DuckDB + PostgreSQL 핵심 메타데이터` 3계층 분리다.
4. 운영 기준 과거 전체 누적 데이터(기존 보유 전기간)는 parquet/DuckDB에서 조회 가능해야 하며, 기존 DB raw 적재 테이블/데이터는 컷오버 후 제거한다.

---

## 2. 근거

1. 튜닝 모니터링은 고빈도 append 로그를 다루며, 전체 raw payload를 RDB에 계속 적재하면 스키마 변경/인덱스/백필 비용이 커진다.
2. 분석 질의의 대부분은 날짜/축 단위 집계이며, columnar 파일(`parquet`) + 로컬 분석엔진(`DuckDB`)이 비용/속도 면에서 유리하다.
3. 운영 관제/이력 추적은 전체 raw보다 `실행 단위 메타`와 `품질 지표 요약`이 핵심이므로 PostgreSQL에는 메타데이터만 남겨도 목적을 달성할 수 있다.

---

## 3. 절대 제약

1. 손익 집계는 `COMPLETED + valid profit_rate`만 사용한다.
2. `NULL`, 미완료, fallback 정규화 값은 손익 계산에서 제외한다.
3. `full fill`/`partial fill`은 절대 합치지 않고 분리 리포트한다.
4. BUY 후 미진입은 아래 4축으로 분리한다.
   - `latency guard miss`
   - `liquidity gate miss`
   - `AI threshold miss`
   - `overbought gate miss`
5. 평가 우선순위는 `거래수 -> 퍼널 -> blocker 분포 -> 체결 품질 -> 손익`으로 유지한다.
6. 실전 로직 변경은 한 번에 한 축 canary만 허용하고, 가능하면 `shadow-only`와 롤백 가드를 둔다.
7. 원인 귀속이 불명확하면 먼저 `리포트 정합성 -> 이벤트 복원 -> 집계 품질`을 점검한다.
8. 패키지 설치/업그레이드는 사용자 승인 없이는 수행하지 않는다.

---

## 4. 목표 아키텍처

### 4-1. 저장 계층

1. **Raw Layer (Source of Truth)**
   - 위치: `data/pipeline_events/*.jsonl`, `data/post_sell/*.jsonl`, `logs/system_metric_samples.jsonl`
   - 정책: append-only, 원본 보존

2. **Analytics Layer (Parquet + DuckDB)**
   - 위치: `data/analytics/parquet/<dataset>/date=YYYY-MM-DD/*.parquet`
   - 정책: 파티션 기반 재생성 가능, 집계/분석 전용

3. **Metadata Layer (PostgreSQL)**
   - 용도: 적재 실행이력, 품질지표, 데이터셋 매니페스트
   - 금지: raw event 전체 payload 상시 저장

### 4-2. 읽기 규칙

1. 당일(`target_date == today`): `jsonl + parquet` 병행 허용(최신성 우선)
2. 과거(`target_date < today`): `parquet/DuckDB`를 운영 canonical source로 강제한다.
3. PostgreSQL은 `run_id`, `dataset_date`, `row_count`, `quality_flags`, `checksum`, `schema_version` 조회만 담당
4. 운영 전환 완료 후 과거 조회에서 legacy DB raw 테이블 fallback은 허용하지 않는다.

---

## 5. 구현 범위 (이번 작업)

1. JSONL -> Parquet 변환 파이프라인 추가 (재실행 가능, idempotent)
2. DuckDB 조회 유틸 추가 (핵심 리포트 read path에 연결)
3. PostgreSQL 메타데이터 테이블 도입 및 기존 대량 raw 적재 경로 분리
4. 튜닝 모니터링 리포트에서 `분석계층 우선, 원본 fallback` 규칙 적용
5. 검증 리포트에 `기회비용(missed entry)`과 `blocker 4축`을 고정 출력
6. `analysis` 분석랩 2종(`gemini/claude_scalping_pattern_lab`)의 입력 소스 우선순위를 신규 데이터 흐름에 맞춰 일치시킨다.
7. 과거 전체 누적 기간 parquet backfill을 완료하고, DuckDB에서 전기간 조회 가능 상태를 완료조건으로 고정한다.
8. 운영 혼선을 막기 위해 기존 DB raw 적재 테이블/데이터를 제거한다.

이번 범위 밖:

1. 실거래 주문 경로 변경
2. 대시보드 UI 전면 개편
3. 원격 배포 자동화 확장

---

## 6. 파일 단위 작업지시

### 6-1. 신규 파일

1. `src/engine/build_tuning_monitoring_parquet.py`
   - JSONL 입력을 읽어 Parquet 파티션으로 변환
   - 중복 방지 키(`event_id` 또는 복합키) 기준 dedupe 지원
2. `src/engine/tuning_duckdb_repository.py`
   - DuckDB 연결/뷰 생성/집계 쿼리 제공
3. `src/tests/test_build_tuning_monitoring_parquet.py`
4. `src/tests/test_tuning_duckdb_repository.py`

### 6-2. 수정 파일

1. `src/engine/sniper_performance_tuning_report.py`
   - 과거 데이터 기본 읽기를 JSONL에서 DuckDB 집계로 전환
2. `src/engine/sniper_missed_entry_counterfactual.py`
   - blocker 4축 및 기회비용 계산 입력을 parquet/DuckDB 경로 지원
3. `src/engine/dashboard_data_repository.py`
   - raw 적재 중심 코드를 메타데이터 저장 중심으로 축소
4. `src/engine/backfill_dashboard_db.py`
   - raw 백필이 아니라 메타/카탈로그 동기화 중심으로 역할 재정의
5. `src/engine/decommission_legacy_dashboard_tables.py` (신규)
   - legacy raw 테이블 drop/archive를 실행하는 관리 스크립트 추가
   - dry-run 지원, 대상 테이블 목록 출력, 실행 이력 로그 남김

### 6-3. 분석랩 연계 수정 (필수)

1. `analysis/gemini_scalping_pattern_lab/build_dataset.py`
   - 입력 우선순위를 `parquet/DuckDB -> jsonl(.gz)`로 전환한다.
   - 기존 `dashboard_data_repository.load_pipeline_events` 경로는 메타 조회 전용으로 축소하고, 실분석 입력은 DuckDB 경유로 고정한다.
2. `analysis/gemini_scalping_pattern_lab/config.py`
   - `data/analytics/parquet` 루트 및 DuckDB 파일 경로를 명시한다.
3. `analysis/gemini_scalping_pattern_lab/README.md`
   - 입력 데이터 설명을 `Raw(jsonl) 보관 / Analytics(parquet+DuckDB) 우선 / PostgreSQL 메타` 구조로 갱신한다.
4. `analysis/claude_scalping_pattern_lab/prepare_dataset.py`
   - `pipeline events` 로딩을 `parquet/DuckDB 우선, jsonl(.gz) fallback`으로 전환한다.
   - 스트리밍 JSONL 경로는 fallback으로 유지하되 동일 집계 검증(diff)을 필수 출력한다.
5. `analysis/claude_scalping_pattern_lab/config.py`
   - 분석 기간 외에 analytics source 선택 플래그(`USE_DUCKDB_PRIMARY`)를 둔다.
6. `analysis/claude_scalping_pattern_lab/README.md`
   - 입력 소스 우선순위 표를 신규 아키텍처로 갱신하고 shadow 비교 절차를 추가한다.
7. `analysis/gemini_scalping_pattern_lab/run.sh`, `analysis/claude_scalping_pattern_lab/run_all.sh`
   - 실행 전 `analytics source health check`를 넣고 실패 시 `jsonl fallback + warning`으로 동작하게 한다.
8. `analysis/*/outputs/run_manifest.json`
   - `history_coverage_start`, `history_coverage_end`, `history_coverage_ok`를 기록해 전기간 누락 여부를 확인한다.

---

## 7. PostgreSQL 메타데이터 스키마

아래 2개 테이블만 유지/추가한다.

1. `tuning_dataset_runs`
   - `run_id`, `dataset_name`, `target_date`, `source_path`, `row_count`, `created_at`, `status`, `error_message`
2. `tuning_dataset_quality`
   - `run_id`, `target_date`, `trade_count`, `completed_count`, `full_fill_count`, `partial_fill_count`, `blocker_latency_count`, `blocker_liquidity_count`, `blocker_ai_threshold_count`, `blocker_overbought_count`, `quality_flags_json`

주의:

1. raw payload JSON 대량 저장 테이블은 신규 생성하지 않는다.
2. 운영 컷오버 승인 후 legacy raw 테이블/데이터는 제거한다.
3. 제거 전 필수 조건:
   - parquet backfill 전기간 완료
   - DuckDB 집계/리포트 shadow diff 합격
   - `drop 대상 테이블 목록 + row_count 증적` 문서화
4. 제거 대상(기본):
   - `dashboard_pipeline_events`
   - `dashboard_monitor_snapshots`
   - 기타 dashboard raw 적재 목적 legacy 테이블
5. PostgreSQL에는 `tuning_dataset_runs`, `tuning_dataset_quality`만 유지한다.

---

## 8. 검증 요구사항

1. 동일 날짜 재실행 시 parquet row_count가 안정적으로 동일해야 한다.
2. `거래수/퍼널/blocker/체결품질` 집계가 기존 대비 허용오차 0(정수 집계)이어야 한다.
3. `full_fill`과 `partial_fill` 혼합 집계가 없는지 테스트로 고정한다.
4. `COMPLETED + valid profit_rate` 외 손익 포함이 없는지 테스트로 고정한다.
5. 장중 누적 파일에서도 파서 실패 없이 증분 반영되어야 한다.
6. 분석랩 2종 결과(`trade_fact/funnel_fact/sequence_fact`)가 동일 날짜에서 기존 JSONL 기준 대비 정수 집계 오차 0이어야 한다.
7. 분석랩 2종의 `run_manifest`에 `data_source_mode(duckdb_primary|jsonl_fallback|mixed)`를 기록해야 한다.
8. 과거 전체 누적 기간(`history_start~yesterday`)에서 DuckDB 조회 누락일 0건이어야 한다.
9. legacy DB raw 테이블 제거 후 리포트/분석/분석랩 실행이 모두 성공해야 한다.

필수 테스트 명령(예시):

```bash
PYTHONPATH=. .venv/bin/pytest -q src/tests/test_build_tuning_monitoring_parquet.py src/tests/test_tuning_duckdb_repository.py src/tests/test_performance_tuning_report.py src/tests/test_missed_entry_counterfactual.py
```

분석랩 스모크 검증 명령(예시):

```bash
PYTHONPATH=. .venv/bin/python analysis/gemini_scalping_pattern_lab/build_dataset.py
PYTHONPATH=. .venv/bin/python analysis/claude_scalping_pattern_lab/prepare_dataset.py
```

legacy 테이블 제거 검증 명령(예시):

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.decommission_legacy_dashboard_tables --dry-run
PYTHONPATH=. .venv/bin/python -m src.engine.decommission_legacy_dashboard_tables --execute
```

---

## 9. 실행 순서 (Canary)

1. `shadow-only`로 JSONL 기반 기존 리포트와 DuckDB 리포트를 동시 생성
2. 1일차는 read path 전환 없이 diff 리포트만 기록
3. 2일차에 지표 일치 시 과거 날짜 조회만 DuckDB 우선으로 전환
4. 3일차에 전기간 커버리지 검증 통과 시 legacy DB raw 테이블 제거 실행
5. 롤백 가드:
   - blocker 4축 중 하나라도 집계 불일치 발생
   - full/partial 분리 집계 훼손
   - `profit_rate` 유효성 규칙 위반
6. 롤백 시 즉시 기존 JSONL 집계 경로로 복귀

---

## 10. DeepSeek 제출 형식 (강제)

최종 답변은 아래 순서만 사용한다.

1. 판정
2. 근거
3. 다음 액션

반드시 포함:

1. 변경 파일 목록
2. 실행한 테스트 명령과 결과
3. `shadow diff` 핵심 수치 (`trade_count`, `funnel`, `blocker 4축`, `full/partial`, `missed_upside`)
