# GitHub Projects + Google Calendar 동기화 설정 가이드

기준일: `2026-04-11`  
목표: `GitHub Projects`를 작업관리 단일 소스로 두고, `Google Calendar`로 일정 가시성을 자동 동기화한다.

---

## 1) 현재 자동 반영 완료 항목

아래 파일은 이미 생성되어 바로 사용할 수 있다.

- 워크플로우: `.github/workflows/sync_project_to_google_calendar.yml`
- 동기화 스크립트: `src/engine/sync_github_project_calendar.py`
- 워크플로우(문서 backlog -> Project): `.github/workflows/sync_docs_backlog_to_project.yml`
- 파싱/반영 스크립트: `src/engine/sync_docs_backlog_to_project.py`
- 워크플로우(Codex 일일 작업지시서): `.github/workflows/build_codex_daily_workorder.yml`
- 작업지시서 생성 스크립트: `src/engine/build_codex_daily_workorder.py`

동작 방식:

1. 30분마다(또는 수동 실행) GitHub Project 항목 조회
2. Due Date가 있는 항목만 Google Calendar 이벤트로 upsert
3. `Slot(PREOPEN/INTRADAY/POSTCLOSE)`이 있으면 시간 지정 이벤트 + 시작 알림으로 생성
4. 거래일에는 `TimeWindow` 필드가 있으면 캘린더 시간은 `TimeWindow`를 최우선 적용
5. 거래일에는 제목에 시간 범위(`13:20~13:35`)가 있으면 Slot 기본시간보다 우선 적용
6. `Slot`이 없고 제목/TimeWindow 시간도 없으면 종일(all-day) 이벤트로 생성
7. 항목 식별은 `extendedProperties.private.gh_project_item_id` 사용
8. 현재 Project 집합에 없는 기존 관리 이벤트는 다음 sync에서 삭제한다
9. 소스는 항상 GitHub, 캘린더는 표시/알림 레이어
10. 휴장일에는 `PREOPEN/POSTCLOSE`의 `TimeWindow`와 제목 명시시간도 무시하고 `INTRADAY` 기준으로 재매핑한다
11. 즉 휴장일 운영큐는 사실상 `INTRADAY` 단일 시간축으로 본다

문서 backlog 반영 동작:

1. `plan`, `4/13 체크리스트`, `스캘핑 로직`, `AI 프롬프트` 문서를 파싱
2. `Done/[x]` 항목 제외
3. 남은 항목만 GitHub Project Draft Item으로 upsert
4. 기존 같은 제목이 있으면 중복 생성하지 않고 skip
5. `sync_docs_backlog_to_project`가 생성한 관리 항목(` [Plan]/[Checklist0413]/[ScalpingLogic]/[AIPrompt] `)은
   문서 기준으로 `Status` 자동 동기화
   - 문서에 남아있음: `Todo`
   - 문서에서 제거됨(완료 처리): `Done`
6. `Slot`이 비어있는 관리 항목은 문서 sync 시 자동 추론하여 채움
   - 기본 규칙: `Plan/Checklist0413 -> PREOPEN`, `ScalpingLogic -> INTRADAY`, `AIPrompt -> POSTCLOSE`
   - 키워드 우선 규칙: `장전/PREOPEN`, `장중/INTRADAY`, `장후/EOD/리포트/검증` 매칭 시 트랙 기본값보다 우선

문서별 canonical 파싱 섹션:

1. `plan-korStockScanPerformanceOptimization.prompt.md`
   - `### 아직 남아있는 일`만 사용
   - `즉시 착수 체크리스트`는 요약/운영 메모로 보고 Project 항목 소스로는 쓰지 않는다
2. `2026-04-13-stage2-todo-checklist.md`
   - 미완료 체크박스(`- [ ]`)만 사용
3. `2026-04-10-scalping-ai-coding-instructions.md`
   - `#### 0-1b/2-1/2-2/3-1/3-2` 상세 단계만 사용
   - 상태 메모의 `잔여:` 요약은 중복 소스로 쓰지 않는다
4. `2026-04-11-scalping-ai-prompt-coding-instructions.md`
   - `## 작업 N.` 상세 작업만 사용
   - 우선순위 요약 표는 중복 소스로 쓰지 않는다
   - `P0` 작업은 `DOC_BACKLOG_TODAY` 또는 `Asia/Seoul` 오늘 날짜를 Due로 부여한다

운영 강제 원칙:

1. 지금 즉시 처리하지 않는 작업, 특정 시각에 실행할 작업, 익일/장후 재확인 작업은 답변 텍스트에만 남기지 않고 반드시 문서 backlog 항목으로 남긴다.
2. 시간 정보가 있으면 `Due`, `Slot`, `TimeWindow`까지 함께 잡아 `Project -> Calendar` 자동화 대상이 되게 유지한다.
3. env/권한이 있는 세션에서는 문서 수정 후 같은 턴에 `sync_docs_backlog_to_project`와 가능하면 `sync_github_project_calendar`까지 이어서 실행한다.

---

## 2) 사용자 개입이 필요한 필수 설정

아래는 계정 권한/보안정보가 필요해 자동 실행할 수 없다.

### Step A. Google Calendar API 준비

1. Google Cloud에서 Calendar API 활성화
2. Service Account 생성
3. Service Account JSON 키 발급
4. 동기화 대상 Google Calendar를 서비스계정 이메일에 공유  
   - 최소 권한: `일정 변경` 가능 권한

### Step B. GitHub 저장소 변수/시크릿 등록

Settings -> Secrets and variables -> Actions

#### Secrets

- `GH_PROJECT_TOKEN`
  - 권한: Project 조회 가능한 토큰(`read:project`)
- `GOOGLE_SERVICE_ACCOUNT_JSON`
  - Service Account JSON 전체 문자열
- `GOOGLE_CALENDAR_ID`
  - 대상 캘린더 ID (이메일 형식일 수 있음)

#### Variables

- `GH_PROJECT_OWNER`  
  - 예: `your-org` 또는 `your-user`
- `GH_PROJECT_NUMBER`  
  - 예: `12`
- `GH_PROJECT_DUE_FIELD_NAME`  
  - 기본: `Due`
- `GH_PROJECT_STATUS_FIELD_NAME`  
  - 기본: `Status`
- `GH_PROJECT_TRACK_FIELD_NAME`  
  - 기본: `Track`
- `GH_PROJECT_SLOT_FIELD_NAME`
  - 기본: `Slot`
  - 권장 옵션: `PREOPEN`, `INTRADAY`, `POSTCLOSE`
- `GH_PROJECT_TIME_WINDOW_FIELD_NAME`
  - 기본: `TimeWindow`
  - 권장 입력: `HH:MM~HH:MM`, `ALLDAY`, `UNSCHEDULED`
- `GH_PROJECT_SLOT_PREOPEN_OPTION_NAME`
  - 기본: `PREOPEN`
- `GH_PROJECT_SLOT_INTRADAY_OPTION_NAME`
  - 기본: `INTRADAY`
- `GH_PROJECT_SLOT_POSTCLOSE_OPTION_NAME`
  - 기본: `POSTCLOSE`
- `GH_PROJECT_AUTO_FILL_SLOT`
  - 기본: `true`
  - `sync_docs_backlog_to_project`에서 Slot 자동 채움 활성/비활성
- `GH_PROJECT_RECLASSIFY_SLOT`
  - 기본: `true`
  - `true`면 기존 Slot이 있어도 문서 기준 규칙으로 재분류
  - `false`면 빈 Slot만 채움
- `GH_PROJECT_AUTO_FILL_TIME_WINDOW`
  - 기본: `true`
  - 문서 동기화에서 TimeWindow 자동 채움 활성/비활성
- `GH_PROJECT_RECLASSIFY_TIME_WINDOW`
  - 기본: `true`
  - `true`면 기존 TimeWindow도 재산정 후 반영
  - `false`면 빈 TimeWindow만 채움
- `GH_SYNC_ONLY_STATUSES`  
  - 예: `Todo,In Progress,Blocked`  
  - 비우면 Due Date 있는 항목 전체 동기화
- `GCAL_EVENT_PREFIX`  
  - 예: `[KORStockScan]`
- `GCAL_EVENT_TIMEZONE`
  - 기본: `Asia/Seoul`
- `GCAL_USE_SLOT_TIME`
  - 기본: `true`
  - `true`면 Slot 기반 시간 이벤트 생성, `false`면 전부 종일 이벤트
- `GCAL_SLOT_PREOPEN_TIME`
  - 기본: `08:20`
- `GCAL_SLOT_INTRADAY_TIME`
  - 기본: `10:00`
- `GCAL_SLOT_POSTCLOSE_TIME`
  - 기본: `15:40`
- `GCAL_SLOT_DURATION_MINUTES`
  - 기본: `30`
  - 슬롯 일정 길이(분)
- `GCAL_SLOT_REMINDER_MINUTES`
  - 기본: `0`
  - 시작 시각 기준 알림 분(0이면 시작 시각 즉시)
- `SYNC_DRY_RUN`
  - 초기 검증 시 `true` 권장, 운영 시 `false`
- `GH_PROJECT_TODO_OPTION_NAME`
  - 기본: `Todo`
  - Project `Status` 필드의 기본 옵션명
- `GH_PROJECT_DONE_OPTION_NAME`
  - 기본: `Done`
  - 문서에서 빠진 관리 항목에 반영할 완료 옵션명
- `DOC_BACKLOG_SYNC_DRY_RUN`
  - `true`면 문서 파싱 후 생성 예정 수량만 출력
  - `false`면 실제 Project Draft Item 생성
- `DOC_BACKLOG_TODAY`
  - 선택값
  - 지정 시 문서 sync의 `오늘 Due` 기준일을 고정
- `DOC_BACKLOG_TIMEZONE`
  - 기본: `Asia/Seoul`
  - `DOC_BACKLOG_TODAY` 미지정 시 오늘 날짜 계산에 사용
- `GH_CODEX_WORKORDER_STATUSES`
  - 기본: `Todo,In Progress`
  - Codex 일일 작업지시서에 포함할 Status 목록
- `CODEX_WORKORDER_TARGET_DATE`
  - 기본: 로컬 오늘(`Asia/Seoul`)
  - Codex 일일 작업지시서의 Due 기준일
- `CODEX_WORKORDER_TIMEZONE`
  - 기본: `Asia/Seoul`
  - `CODEX_WORKORDER_TARGET_DATE` 미지정 시 오늘 날짜 계산에 사용
- `CODEX_WORKORDER_INCLUDE_OVERDUE`
  - 기본: `true`
  - `true`면 오늘 Due 이전 미완료 항목도 함께 포함
- `CODEX_WORKORDER_MAX_ITEMS`
  - 기본: `20`
  - 일일 작업지시서 최대 항목 수

---

## 3) 첫 실행(권장 순서)

### Step 1. Dry-run 검증

1. `SYNC_DRY_RUN=true` 설정
2. GitHub Actions에서 `Sync GitHub Project To Google Calendar`를 수동 실행(`workflow_dispatch`)
3. 실행 로그에서 아래 JSON 요약 확인
   - `items_with_due_date`
   - `dry_run=true`
   - `created=0`, `updated=0`, `dry_run_skipped>0`

### Step 2. 실동기화 전환

1. `SYNC_DRY_RUN=false`로 변경
2. 수동 실행 1회
3. Google Calendar에서 이벤트 생성 확인

### Step 3. 정기 운영

1. 스케줄(`*/30 * * * *`)로 자동 반영 확인
2. 모바일은 GitHub Mobile + Google Calendar 앱으로 모니터링
3. 작업 지시는 Issue/Project 코멘트로 유지

문서 backlog 정기 반영:

1. `Sync Docs Backlog To GitHub Project` 워크플로우는 `6시간 주기`(`15 */6 * * *`)로 자동 실행
2. 운영 초기에는 `DOC_BACKLOG_SYNC_DRY_RUN=true`로 1~2회 로그 검증
3. 검증 후 `DOC_BACKLOG_SYNC_DRY_RUN=false`로 전환

Codex 일일 작업지시서 자동 생성:

1. 워크플로우 `Build Codex Daily Workorder`를 수동 실행(`workflow_dispatch`)하거나
   슬롯별 스케줄 자동 실행 사용
   - `PREOPEN`: `20 23 * * *` (KST 08:20)
   - `INTRADAY`: `0 1,4 * * *` (KST 10:00, 13:00)
   - `POSTCLOSE`: `40 6 * * *` (KST 15:40)
2. 수동 실행 시 `target_date`를 비우면 KST 오늘 기준으로 생성하고, 필요하면 `YYYY-MM-DD`로 날짜를 직접 고정한다
3. `include_overdue=true`가 기본이며, target date 이전 미완료 항목까지 함께 포함한다
4. 휴장일에는 `PREOPEN/POSTCLOSE` 슬롯 실행을 건너뛰고 `INTRADAY` workorder 하나로 통합한다
5. 작업지시서는 기본적으로 `오늘 Due(+선택적으로 overdue)` 항목만 포함한다
6. 실행 완료 후 `Actions run summary`의 `Codex Daily Workorder` 섹션에서 본문을 복사
   - 본문에는 `Source`, `Section`, `Project Item ID`가 함께 포함돼 바로 Codex 지시문으로 사용할 수 있다
7. 복사한 본문을 Codex 대화에 붙여 실행 지시
8. 수동 실행 시 `slot`, `target_date`, `include_overdue` 입력을 함께 사용할 수 있다.

슬롯 운영 원칙:

1. Project 항목 생성 시 `Slot`을 반드시 지정한다.
2. 슬롯이 비어있는 항목은 슬롯 자동 작업지시서에 포함되지 않는다.
3. 휴장일에는 문서상 원래 슬롯과 무관하게 실행 큐는 `INTRADAY`로 본다.

---

## 4) 운영 규칙(권장)

1. 작업 일정의 소스는 GitHub Project만 사용한다.
2. 일정 변경은 `Due`, `Status`, `Track` 필드에서만 수행한다.
3. 캘린더에서 수정해도 원천이 아니므로 GitHub 기준으로 덮어쓴다.
4. 본서버 영향 작업은 반드시 `canary` 라벨 또는 `Track` 필드로 구분한다.

---

## 5) 트러블슈팅

### `project not found` 에러

- `GH_PROJECT_OWNER`, `GH_PROJECT_NUMBER`, `GH_PROJECT_TOKEN` 권한 재확인

### Google 인증 관련 에러

- `GOOGLE_SERVICE_ACCOUNT_JSON` 값이 JSON 문자열인지 확인
- 캘린더 공유 대상이 서비스계정 이메일인지 확인

### 이벤트가 안 생김

- 항목에 Due Date가 있는지 확인
- `GH_SYNC_ONLY_STATUSES` 필터가 과하게 좁지 않은지 확인
- `SYNC_DRY_RUN`이 `false`인지 확인

### 시간이 아니라 종일 이벤트로 생김

- `Slot` 값이 비어있지 않은지 확인
- `GH_PROJECT_SLOT_FIELD_NAME`이 실제 Project 필드명과 일치하는지 확인
- `GCAL_USE_SLOT_TIME=true`인지 확인
- `TimeWindow` 값이 `ALLDAY`/`UNSCHEDULED`로 들어가 있지 않은지 확인

### Slot 분류가 기대와 다름

- `Sync Docs Backlog To GitHub Project` 실행 로그에서 `slot_filled`, `slot_reclassified` 확인
- `GH_PROJECT_RECLASSIFY_SLOT=true`로 재실행하여 전체 재분류 적용

---

## 6) 로컬 수동 실행(선택)

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar --dry-run
```

필요 환경변수는 위 Step B와 동일하다.

로컬 workorder 생성:

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.build_codex_daily_workorder \
  --target-date 2026-04-12 \
  --output tmp/codex_daily_workorder_2026-04-12.md
```
