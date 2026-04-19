# 작업지시서: 통합대시보드 데이터 DB 전환 및 API 정비

작성일: 2026-04-19  
대상: DeepSeek (AI 코딩 에이전트)  
목표: 현재 파일 기반(`json`, `jsonl`) 통합대시보드/모니터링 데이터를 관찰축 중심으로 DB화하고, 과거 DB 데이터와 당일 파일 데이터를 함께 조회하는 구조로 전환한다.

---

## 1. 판정

1. 현재 `plan-korStockScanPerformanceOptimization.prompt.md` 기준 실행안에는 `통합대시보드 데이터 DB화`가 명시적 작업항목으로 독립 등록되어 있지 않다.
2. 다만 현재 관찰축이 `거래수 -> 퍼널 -> blocker -> 체결품질 -> missed_upside -> 손익` 순으로 고정돼 있고, `performance-tuning` 확장 필요성은 이미 문서에 존재한다.
3. 따라서 이번 작업은 `새 대시보드 신규 구축`이 아니라 `기존 통합대시보드/API/모니터링 저장소를 DB 기반으로 재정렬`하는 과제로 정의한다.

---

## 2. 절대 제약

1. 운영 해석 기준을 바꾸지 않는다.
   - 손익은 `COMPLETED + valid profit_rate`만 사용한다.
   - `NULL`, 미완료, fallback 정규화 값은 손익 집계에 포함하지 않는다.
2. `full fill`, `partial fill`, `split-entry`, `same_symbol_repeat` 코호트 혼합 금지.
3. BUY 후 미진입은 최소 아래 blocker 축으로 분리 유지:
   - `latency guard miss`
   - `liquidity gate miss`
   - `AI threshold miss`
   - `overbought gate miss`
4. 기존 파일 산출물은 즉시 제거하지 않는다.
   - 1차는 `DB + 파일 병행`, 2차에서 읽기 우선순위 전환.
5. 실전 로직 변경 금지.
   - 이번 작업은 저장/조회/API/리포트 계층 정비가 범위다.
6. 패키지 설치 금지.
   - 프로젝트 `.venv`와 현재 repo 의존성만 사용한다.

---

## 3. 작업 범위

### 3-1. 1차 우선 구현 범위

1. 현재 관찰축에 맞춰 통합대시보드 API 응답 구조를 정리한다.
2. 당일을 제외한 전일자까지의 `json`, `jsonl` 파일을 DB로 이관한다.
3. `update_kospi.py` 실행 시 당일 생성/갱신된 파일 데이터도 DB에 업로드되도록 후크를 건다.
4. 모니터링/분석 코드는 `과거=DB`, `당일=파일+DB 병행`으로 읽을 수 있게 수정한다.
5. 통합대시보드가 DB를 직접 조회할 수 있게 저장소 계층을 추가한다.

### 3-2. 이번 턴 범위 밖

1. 원격 서버까지 자동 배포
2. 대시보드 UI 전면 개편
3. PostgreSQL 스키마 대수술
4. 과거 모든 리포트 포맷의 일괄 재생성

---

## 4. 현재 코드 기준 문맥

### 4-1. 현재 파일 기반 저장/조회 지점

- `src/utils/pipeline_event_logger.py`
  - `data/pipeline_events/pipeline_events_<date>.jsonl` 기록
- `src/engine/log_archive_service.py`
  - `data/report/monitor_snapshots/<kind>_<date>.json` 저장/조회
- `src/engine/sniper_performance_tuning_report.py`
  - `pipeline_events_<date>.jsonl` 우선 파싱
- `src/web/app.py`
  - `load_monitor_snapshot(...)`으로 `performance_tuning`, `trade_review`, `post_sell_feedback` 스냅샷 조회
- `src/utils/update_kospi.py`
  - 야간 일봉/수급 DB 적재만 수행, 대시보드 파일 DB 업로드 후크 없음

### 4-2. 기존 계획 문맥

1. 현 계획에는 `reason code`, `blocker 분포`, `sig_delta` 확장 니즈는 있으나 저장소 DB화 과제는 명시되지 않았다.
2. 따라서 이번 작업은 `현재 관찰축 유지`를 전제로 저장 경로를 정규화하는 기반작업이다.
3. 새 기준은 `파일은 당일 fallback/source-of-truth 보조`, `전일 이전은 DB canonical`이다.

---

## 5. 설계 원칙

### 5-1. 저장소 전략

1. `pipeline_events jsonl`과 `monitor_snapshots json`를 별도 테이블로 저장한다.
2. 테이블은 원본 payload 보존 + 주요 조회키 컬럼 분리를 동시에 가져간다.
3. 전일 이전 조회는 DB 우선, 당일은 파일 우선 또는 병합 허용으로 설계한다.

### 5-2. 당일/과거 읽기 규칙

1. `target_date < today`
   - DB를 canonical source로 사용
   - 파일이 있어도 기본은 DB
2. `target_date == today`
   - 파일 기반 최신성 유지
   - 필요 시 DB 누적값과 병합
3. UI/API는 이 규칙을 내부에서 처리하고 호출자는 날짜만 넘기게 한다.

### 5-3. 관찰축 정합성

API/리포트는 최소 아래 축을 손상 없이 유지해야 한다.

1. 거래수
2. 퍼널
3. blocker 분포
4. 체결품질
5. missed_upside / HOLDING 품질
6. 손익

---

## 6. 구현 요구사항

### 6-1. 신규 저장소 모듈 추가

신규 파일 후보:

- `src/engine/dashboard_data_repository.py`

필수 책임:

1. `pipeline_events` 업서트/조회
2. `monitor_snapshots` 업서트/조회
3. 날짜별 백필(backfill) 유틸
4. 당일 파일 + 과거 DB 병합 조회 유틸

권장 인터페이스 예시:

```python
def upsert_pipeline_event_rows(target_date: str, rows: list[dict]) -> int: ...
def upsert_monitor_snapshot(kind: str, target_date: str, payload: dict) -> None: ...
def load_monitor_snapshot_prefer_db(kind: str, target_date: str) -> dict | None: ...
def load_pipeline_events(target_date: str, *, include_file_for_today: bool = True) -> list[dict]: ...
def backfill_dashboard_files(until_date: str) -> dict: ...
```

### 6-2. DB 스키마

기존 PostgreSQL 사용을 우선한다. 신규 테이블 2개를 추가한다.

1. `dashboard_pipeline_events`
   - `event_date`
   - `pipeline`
   - `stock_code`
   - `stage`
   - `emitted_at`
   - `record_id`
   - `fields_json`
   - `raw_payload_json`
   - 유니크 키: 가능하면 `event_date + pipeline + stock_code + stage + emitted_at + record_id`

2. `dashboard_monitor_snapshots`
   - `snapshot_kind`
   - `target_date`
   - `schema_version`
   - `saved_snapshot_at`
   - `payload_json`
   - 유니크 키: `snapshot_kind + target_date`

중요:

1. JSONB가 가능하면 사용한다.
2. 마이그레이션 프레임워크가 없으면 `CREATE TABLE IF NOT EXISTS` 수준의 안전한 부트스트랩 함수로 처리한다.
3. 기존 운영 테이블(`recommendation_history`, `daily_stock_quotes`)은 건드리지 않는다.

### 6-3. 백필 스크립트

신규 CLI 후보:

- `src/engine/backfill_dashboard_db.py`

필수 동작:

1. `today`를 제외한 과거 날짜 파일을 탐색한다.
2. 대상:
   - `data/pipeline_events/pipeline_events_<date>.jsonl`
   - `data/report/monitor_snapshots/*_<date>.json`
3. 날짜별 업로드 건수, skip 건수, 파싱 실패 건수를 출력한다.
4. 재실행 가능해야 한다.
   - 동일 날짜 중복 삽입 금지
   - upsert 또는 delete+insert 허용

### 6-4. update_kospi 후크

`src/utils/update_kospi.py` 종료부에 아래 순서로 후크를 추가한다.

1. 일봉/수급 DB 적재
2. 대시보드 파일 DB 업로드 실행
3. 추천 모델 실행

주의:

1. 대시보드 업로드 실패가 일봉 적재 성공을 rollback시키면 안 된다.
2. 대신 실패 로그는 명확히 남겨야 한다.
3. 실행 메시지에 다음을 포함한다.
   - pipeline event 업로드 건수
   - monitor snapshot 업로드 건수
   - 실패 건수

### 6-5. 리포트/분석 코드 수정

우선 수정 대상:

- `src/engine/sniper_performance_tuning_report.py`
- 필요 시 `src/engine/sniper_missed_entry_counterfactual.py`
- 필요 시 `src/engine/watching_prompt_75_shadow_report.py`

필수 요구:

1. 과거 날짜는 DB 조회 우선
2. 당일은 파일 최신본과 DB 누적본을 함께 읽을 수 있어야 함
3. 기존 결과 shape는 최대한 유지
4. 관찰축 집계 기준은 바꾸지 않는다

### 6-6. 통합대시보드 API 수정

우선 수정 대상:

- `src/web/app.py`
- `src/engine/log_archive_service.py`

필수 요구:

1. `load_monitor_snapshot(...)` 성격의 함수가 DB 우선 조회를 지원해야 한다.
2. `performance_tuning`, `trade_review`, `post_sell_feedback`는 과거 날짜에 DB에서 바로 열려야 한다.
3. API 응답에는 source 메타를 남긴다.
   - 예: `source=db`, `source=file`, `source=mixed`
4. 가능하면 `performance-tuning` API에 관찰축 메타를 명시한다.
   - 예: `metric_order`, `cohort_rules`, `blocker_axes`

---

## 7. API 정비 기준

### 7-1. 유지해야 할 응답 관례

1. 화면이 깨지지 않도록 기존 주요 키는 유지한다.
2. 신규 메타는 `meta` 아래에 추가한다.

예시:

```json
{
  "meta": {
    "schema_version": 4,
    "source": "db",
    "metric_order": [
      "trade_count",
      "funnel",
      "blocker",
      "fill_quality",
      "missed_upside",
      "realized_pnl"
    ],
    "blocker_axes": [
      "latency_guard_miss",
      "liquidity_gate_miss",
      "ai_threshold_miss",
      "overbought_gate_miss"
    ]
  }
}
```

### 7-2. 관찰축별 표시 기준

1. `trade_count`: total/completed/valid cohort
2. `funnel`: `AI BUY -> entry_armed -> budget_pass -> submitted -> filled`
3. `blocker`: 4대 blocker + 기타 보조 blocker
4. `fill_quality`: `full_fill`, `partial_fill`, `rebase`, `same_symbol_repeat`
5. `missed_upside`: post-sell feedback/HOLDING 품질
6. `realized_pnl`: 마지막 섹션

---

## 8. 테스트 요구사항

### 8-1. 필수 테스트

1. `jsonl -> DB backfill` 테스트
2. `json snapshot -> DB backfill` 테스트
3. 과거 날짜 조회 시 DB 우선 테스트
4. 당일 조회 시 file/db 혼합 테스트
5. `update_kospi.py` 후크 테스트 또는 최소 smoke test
6. 대시보드 API 기존 shape 유지 테스트

### 8-2. 수정/추가 후보 테스트 파일

- `src/tests/test_pipeline_event_logger.py`
- `src/tests/test_log_archive_service.py`
- `src/tests/test_performance_tuning_report.py`
- `src/tests/test_api_data.py`
- 신규 `src/tests/test_dashboard_data_repository.py`

---

## 9. 산출물

필수 산출물:

1. 코드
   - 저장소 모듈
   - 백필 CLI
   - API/리포트 read path 수정
   - `update_kospi.py` 업로드 후크
2. 문서
   - 이 작업지시서 기준 실제 구현 차이 요약 1부
   - 백필/운영 실행 명령 예시
3. 검증 결과
   - 실행한 테스트 목록
   - 통과/실패
   - 미실행 항목과 이유

---

## 10. 제출 형식

최종 보고는 아래 순서만 사용:

1. 판정
2. 근거
3. 다음 액션

필수 포함:

1. 변경 파일 목록
2. 실행한 테스트 명령
3. DB 백필/업로드 결과 요약

---

## 11. DeepSeek 실행 순서 제안

1. 신규 저장소 모듈/테이블 부트스트랩 구현
2. 과거 파일 백필 CLI 구현
3. `log_archive_service`와 `pipeline_event_logger` DB 저장 연결
4. `sniper_performance_tuning_report` 읽기 경로 DB 우선화
5. `web/app.py` API source 메타 반영
6. `update_kospi.py` 후크 연결
7. 테스트/스모크 실행

## 12. 운영 고정 결과 (2026-04-19 반영)

1. `DB 적재 확인 + D+N 경과 파일 자동압축` 스크립트 추가
   - `src/engine/compress_db_backfilled_files.py`
2. cron wrapper 추가
   - `deploy/run_dashboard_db_archive_cron.sh`
3. crontab 등록
   - `10 23 * * 1-5 /home/ubuntu/KORStockScan/deploy/run_dashboard_db_archive_cron.sh 1 >> /home/ubuntu/KORStockScan/logs/dashboard_db_archive_cron.log 2>&1 # DASHBOARD_DB_ARCHIVE_2310`
4. 운영 기준
   - DB에 해당 날짜 레코드가 확인된 파일만 압축
   - 미검증 파일은 `skipped_unverified`로 남기고 보존

---

## 참고 문서

- [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)
- [plan-korStockScanPerformanceOptimization.qna.md](./plan-korStockScanPerformanceOptimization.qna.md)
- [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md)
- [prompt-deepseek-integrated-dashboard-db-migration.md](./prompt-deepseek-integrated-dashboard-db-migration.md)
- [2026-04-18-nextweek-validation-axis-table-audited.md](./2026-04-18-nextweek-validation-axis-table-audited.md)
- [2026-04-17-midterm-tuning-performance-report.md](./2026-04-17-midterm-tuning-performance-report.md)
- [web_api_spec_guide.md](./web_api_spec_guide.md)
