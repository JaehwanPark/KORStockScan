# 검토보고서: 통합대시보드 DB 전환 작업 코드리뷰

작성일: 2026-04-19  
검토자: Codex  
대상 작업: `docs/workorder-integrated-dashboard-db-migration.md` 기준 구현분

---

## 1. 판정

**조건부 반려(수정 후 재검토 필요)**  
핵심 요구사항 중 `전일자까지 전체 백필`과 `테스트 통과`가 현재 코드 상태에서 충족되지 않았습니다.

---

## 2. 주요 결함 (심각도 순)

### [High] 백필 범위가 `until 이전 전체`가 아니라 `until~today`로 역방향 구현됨

- 위치: [dashboard_data_repository.py](/home/ubuntu/KORStockScan/src/engine/dashboard_data_repository.py:404)
- 근거:
  - `current = until_dt` 후 `while current <= today`로 증가시키는 로직이라,
  - `--until 2026-04-18` 실행 시 사실상 `2026-04-18`(및 today skip)만 처리됨
  - 작업지시서의 `당일 제외 전일자까지 json/jsonl DB 전환`과 불일치
- 영향:
  - 과거 누적 데이터가 DB로 완전 이관되지 않아 API/리포트 기준선 왜곡 가능
- 권고:
  - 시작점을 `earliest_detected_date` 또는 파일 스캔 기반 최소일로 잡고 `<= until_dt`까지 순회
  - 최소 단위테스트 추가: 다일자 파일(예: 04-10, 04-11, 04-12)에서 `until=04-12` 시 3일 모두 처리 검증

### [High] 신규 테스트 스위트 실패 (`2 failed`)

- 위치: [test_dashboard_data_repository.py](/home/ubuntu/KORStockScan/src/tests/test_dashboard_data_repository.py:47), [test_dashboard_data_repository.py](/home/ubuntu/KORStockScan/src/tests/test_dashboard_data_repository.py:140)
- 근거:
  - 실제 실행 결과: `2 failed, 3 passed`
  - 실패 원인 로그: `'Mock' object does not support the context manager protocol`
- 영향:
  - 감리보고서의 “기존 테스트 스위트 통과/회귀 없음” 주장을 그대로 신뢰할 수 없음
- 권고:
  - DB 커넥션 mock을 `MagicMock`/context manager 대응으로 수정
  - 날짜 하드코딩(`2026-04-19`) 제거 후 `today` 동적값과 일치시키도록 테스트 데이터 생성

### [Medium] `--dry-run`이 사실상 미구현

- 위치: [backfill_dashboard_db.py](/home/ubuntu/KORStockScan/src/engine/backfill_dashboard_db.py:53)
- 근거:
  - 코드에 `# 구현 생략` 주석이 있고, 실제 파일 스캔/예상 통계 출력 없음
- 영향:
  - 운영 전 검증 루틴(dry-run)으로 백필 영향도 확인 불가
- 권고:
  - 실백필과 동일한 파일 탐색 경로를 타되 DB write만 건너뛰고 `scanned/eligible/invalid` 통계 출력

### [Medium] API `meta.source` 보장은 “스냅샷 경로”에만 적용

- 위치: [app.py](/home/ubuntu/KORStockScan/src/web/app.py:140), [app.py](/home/ubuntu/KORStockScan/src/web/app.py:165), [app.py](/home/ubuntu/KORStockScan/src/web/app.py:192)
- 근거:
  - 저장 스냅샷이 없어서 report를 build하는 경로에서는 `meta.source`를 강제 주입하지 않음
  - 감리보고서의 “모든 대시보드 API 응답에 포함” 표현은 과장됨
- 영향:
  - 클라이언트가 source 필드 존재를 전제하면 분기 누락 가능
- 권고:
  - `_load_or_build_*` 함수에서 build 경로에도 `meta.source="live_build"` 또는 `meta.source="computed"` 보강

---

## 3. 확인된 양호 사항

1. 파일 저장 경로는 유지하면서 DB 업서트를 병행하는 구조는 요구사항 방향과 일치
2. `load_monitor_snapshot_prefer_db`의 당일/과거 분기 아이디어 자체는 타당
3. `update_kospi.py`에서 DB 업로드 실패를 본 작업 rollback으로 전이하지 않는 처리 방향은 적절
4. 기존 테스트 일부는 통과
   - `src/tests/test_log_archive_service.py`
   - `src/tests/test_performance_tuning_report.py`

---

## 4. 검증 결과

실행 명령:

```bash
PYTHONPATH=. .venv/bin/pytest -q src/tests/test_dashboard_data_repository.py
PYTHONPATH=. .venv/bin/pytest -q src/tests/test_log_archive_service.py src/tests/test_performance_tuning_report.py
```

결과 요약:

1. `test_dashboard_data_repository.py`: **2 failed, 3 passed**
2. `test_log_archive_service.py` + `test_performance_tuning_report.py`: **11 passed**

---

## 5. 작업자 전달용 수정 우선순위

1. `backfill_dashboard_files()` 날짜 순회 로직 수정 (전체 과거 범위 백필 보장)
2. `test_dashboard_data_repository.py` 실패 2건 수정 후 녹색화
3. `--dry-run` 실기능 구현
4. build 경로 API 응답에 `meta.source` 주입 보강
5. 재검증
   - 신규/기존 관련 테스트 전부 실행
   - 백필 dry-run 및 실실행 결과 첨부

---

## 6. 다음 액션

1. 작업자는 위 1~4번 수정 후 테스트 로그를 첨부해 재제출
2. 재제출 시 감리보고서의 “테스트 통과” 문구를 실제 수치로 교정
3. 재검토 완료 전 운영 반영은 보류
