# DeepSeek 실행 프롬프트: 통합대시보드 DB 전환 및 API 정비

아래 문서를 먼저 읽고 그 기준만 따라 작업하라.

## Source / Section

- Source 1: `docs/workorder-integrated-dashboard-db-migration.md`
- Source 2: `docs/plan-korStockScanPerformanceOptimization.prompt.md`
- Section: `판정`, `절대 제약`, `작업 범위`, `현재 코드 기준 문맥`, `설계 원칙`, `구현 요구사항`, `테스트 요구사항`, `제출 형식`

## 역할

너는 KORStockScan 저장소에서 `통합대시보드 데이터 DB 전환 및 API 정비`를 수행하는 AI 코딩 에이전트다.

이번 작업의 목적은 새 대시보드를 만드는 것이 아니라, 현재 파일 기반(`json`, `jsonl`) 모니터링/대시보드 저장소를 DB 중심 구조로 재정렬하는 것이다.

## 최우선 목표

1. 현재 관찰축을 유지한 채 통합대시보드/모니터링 데이터를 DB화한다.
2. 전일 이전 데이터는 DB를 canonical source로 사용하게 만든다.
3. 당일 데이터는 파일 최신성과 DB 누적값을 함께 활용할 수 있게 만든다.
4. 통합대시보드 API가 DB 조회를 지원하게 만든다.
5. `update_kospi.py` 실행 시 파일 산출물 DB 업로드가 이어지게 만든다.

## 절대 제약

1. 해석 기준 변경 금지
   - 손익은 `COMPLETED + valid profit_rate`만 사용
   - `NULL`, 미완료, fallback 정규화 값은 손익 집계에서 제외
2. 코호트 혼합 금지
   - `full fill`, `partial fill`, `split-entry`, `same_symbol_repeat` 혼합 해석 금지
3. BUY 후 미진입은 최소 아래 blocker 축을 유지
   - `latency guard miss`
   - `liquidity gate miss`
   - `AI threshold miss`
   - `overbought gate miss`
4. 실전 매매 로직 변경 금지
5. 패키지 설치/업그레이드/제거 금지
6. 기존 파일 산출물 즉시 제거 금지
   - 1차는 `DB + 파일 병행`

## 작업 범위

반드시 아래 5개를 이번 작업 범위로 처리하라.

1. 통합대시보드 API 응답 구조를 현재 관찰축 기준으로 정비
2. 당일 제외 과거 `json`, `jsonl` 파일을 DB로 백필
3. `update_kospi.py` 종료 후 대시보드 파일 DB 업로드 후크 연결
4. 모니터링/분석 코드가 `과거 DB + 당일 파일` 병행 조회를 지원하도록 수정
5. 통합대시보드가 DB를 직접 조회하도록 저장소 계층 추가

## 우선 구현 대상 파일

우선순위는 아래 순서로 잡아라.

1. 신규 저장소 모듈
   - `src/engine/dashboard_data_repository.py`
2. 백필 CLI
   - `src/engine/backfill_dashboard_db.py`
3. 저장/조회 계층 수정
   - `src/engine/log_archive_service.py`
   - `src/utils/pipeline_event_logger.py`
4. 리포트 read path 수정
   - `src/engine/sniper_performance_tuning_report.py`
   - 필요 시 `src/engine/sniper_missed_entry_counterfactual.py`
   - 필요 시 `src/engine/watching_prompt_75_shadow_report.py`
5. API 수정
   - `src/web/app.py`
6. 야간 후크
   - `src/utils/update_kospi.py`
7. 테스트
   - `src/tests/test_dashboard_data_repository.py`
   - 관련 기존 테스트 보강

## 구현 원칙

1. 과거 날짜(`target_date < today`)는 DB 우선 조회
2. 당일(`target_date == today`)은 파일 최신본 + DB 누적본 병행 허용
3. API shape는 최대한 유지하고 신규 메타는 `meta` 아래에만 추가
4. API 메타에 가능하면 아래를 포함
   - `source=db|file|mixed`
   - `metric_order`
   - `blocker_axes`
5. DB 스키마는 기존 PostgreSQL에 안전하게 추가
   - `dashboard_pipeline_events`
   - `dashboard_monitor_snapshots`
6. 마이그레이션 도구가 없으면 `CREATE TABLE IF NOT EXISTS` 수준의 부트스트랩 사용
7. 기존 운영 테이블은 건드리지 말 것

## 완료 조건

아래가 모두 충족돼야 완료다.

1. 과거 파일 백필 CLI가 재실행 가능하게 동작
2. 통합대시보드/리포트 코드가 과거 날짜 DB 조회 가능
3. 당일은 파일/DB 병행 읽기 가능
4. `update_kospi.py` 후크가 추가됨
5. 관련 테스트 추가 또는 보강
6. 테스트 결과를 제출 메시지에 포함

## 작업 방식

1. 먼저 현재 코드 읽기
2. 저장소 계층부터 구현
3. 백필 CLI 구현
4. 읽기 경로 전환
5. API 메타 추가
6. 야간 후크 연결
7. 테스트 실행
8. 문서에 적힌 제출 형식으로 결과 보고

## 제출 형식

최종 답변은 반드시 아래 순서만 사용하라.

1. 판정
2. 근거
3. 다음 액션

그리고 아래를 반드시 포함하라.

- 변경 파일 목록
- 실행한 테스트 명령
- DB 백필/업로드 결과 요약

## 금지

1. 불필요한 구조개편
2. 대시보드 UI 전면 재디자인
3. 운영 로직 의미 변경
4. 손익/퍼널/체결품질/미진입 blocker 기준 변경
5. 문서만 수정하고 코드 미구현 상태로 종료
