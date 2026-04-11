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

동작 방식:

1. 30분마다(또는 수동 실행) GitHub Project 항목 조회
2. Due Date가 있는 항목만 Google Calendar 이벤트로 upsert
3. 항목 식별은 `extendedProperties.private.gh_project_item_id` 사용
4. 소스는 항상 GitHub, 캘린더는 표시/알림 레이어

문서 backlog 반영 동작:

1. `plan`, `4/13 체크리스트`, `스캘핑 로직`, `AI 프롬프트` 문서를 파싱
2. `Done/[x]` 항목 제외
3. 남은 항목만 GitHub Project Draft Item으로 upsert
4. 기존 같은 제목이 있으면 중복 생성하지 않고 skip
5. `sync_docs_backlog_to_project`가 생성한 관리 항목(` [Plan]/[Checklist0413]/[ScalpingLogic]/[AIPrompt] `)은
   문서 기준으로 `Status` 자동 동기화
   - 문서에 남아있음: `Todo`
   - 문서에서 제거됨(완료 처리): `Done`

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
- `GH_SYNC_ONLY_STATUSES`  
  - 예: `Todo,In Progress,Blocked`  
  - 비우면 Due Date 있는 항목 전체 동기화
- `GCAL_EVENT_PREFIX`  
  - 예: `[KORStockScan]`
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

---

## 6) 로컬 수동 실행(선택)

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar --dry-run
```

필요 환경변수는 위 Step B와 동일하다.
