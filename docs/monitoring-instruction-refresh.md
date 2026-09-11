# 모니터링 작업지시문 서버 자동 현행화

사용자가 승인한 문서 전용 자동화다. 구현 owner는 `src/engine/automation/monitoring_instruction_refresh.py`, 실행은 `deploy/run_monitoring_instruction_refresh.sh`, 설치는 `deploy/install_monitoring_instruction_refresh_cron.sh`다.

| 실행 조건 (Asia/Seoul) | 갱신 대상 |
| --- | --- |
| 매일 19:30 시작, 휴일 포함. 19:59까지 매분 미완료/남은 시도 확인 | [장후 작업지시문](./postclose-tuning-result-review-task-instructions.md) |
| 매분 읽기 전용 완료 확인 후 source-date당 한 번 | [장중 작업지시문](./intraday-monitoring-task-instructions.md) |

장후 종료는 `postclose_finalization_cron.log`의 해당 source-date 최신 terminal이 `postclose_final_detector ... finalization=done detector=done`이고, 같은 날짜 strict verifier의 summary handoff PASS, 실제 controller DONE 및 현재 source/tower/checklist hash 검증이 모두 성립해야 한다. 중간 finalization DONE·이전 PASS·dry-run은 종료가 아니다. 재시작/실패 marker가 뒤따르면 기다린다. 자정 이후에도 전일 source-date를 유지하며 오늘/전일만 확인한다. 설치 전 source-date는 자동 소급 실행하지 않는다.

## API와 문서 게시 계약

- OpenAI Responses API, `gpt-5.6-sol`, reasoning `medium`, structured JSON을 사용한다. 작성과 독립 리뷰를 각각 호출하고, findings가 있으면 한 번 보완한다. 시도당 최대 4회, 날짜·문서별 최대 2시도이며 완료 후 중복 호출하지 않는다. 19:30 작업은 lock 충돌이나 실패 후에도 19:59까지 남은 시도로 재확인한다. 성공 후에는 추가 API를 호출하지 않는다. 장중 문서 작업은 다음 분부터 남은 시도를 사용한다.
- credential 우선순위는 `MONITORING_DOC_OPENAI_API_KEY`, `OPENAI_API_KEY`, `data/config_prod.json`(없으면 `config_dev.json`)의 숫자 suffix 순 첫 유효 OpenAI key다. 키를 문서·receipt·로그에 기록하지 않는다. 모델 실패 시 다른 모델/provider로 자동 우회하지 않는다. 이 설정은 거래 AI provider와 별개다.
- 입력은 AGENTS, Plan Rebase §1–§8, 현재/source-date 체크리스트 목적·강제 규칙, 대상 문서, release routing, 제한된 committed 코드와 선택 release 메타데이터다. 최근 12 commit 및 직전 성공 이후 변경 경로를 참고하며 전체 source text는 140,000자로 제한한다. 코드의 literal credential은 전송 전에 가리고, 누락 경로는 manifest에 남기고 부족한 근거로 사실을 추정하지 않는다. 미커밋 코드 경로와 live PID 소비는 committed 코드와 구분한다.
- 최대 8개의 정확한 문자열 치환만 받는다. 실제 source quote, 겹치지 않는 위치, 문서 크기(-15%~+5%), 제목·보호 문단·로컬 링크·Markdown 기본 형식을 검사한다. 권한·승인·안전·퇴역·수량·PID 등 보호 문단 변경은 자동 게시하지 않는다. 날짜별 완료 이력이나 새 체크박스를 추가하지 않는다.
- 독립 API 리뷰와 print-only parser 검증을 통과하고, 장후 완료 재검증을 마친 뒤 게시 직전까지 HEAD·참조 문서 hash·완료 receipt가 바뀌지 않았을 때만 대상 파일을 원자 교체한다. 실패 시 원본을 보존한다. 교체 전 `publishing` journal을 저장한다. 중단 후 원문이 승인 후보 hash와 일치하면 API/문서 재교체 없이 완료 receipt만 복구하고, 불일치하면 `blocked_publication`으로 중단해 원문을 보존한다. 리뷰에서 수정 필요가 없으면 `unchanged`로 완료한다. 파서는 두 작업지시문을 backlog 입력으로 소비하지 않으며, 해당 문서의 게시 전 검사는 별도 구조/링크 검증이 담당한다.
- 모델에는 실행 도구를 제공하지 않는다. 게시 allowlist는 위 두 문서뿐이다. 주문·env·threshold·provider 설정·봇 재시작·장후 producer 재실행·Project/Calendar sync·자동 commit/push는 수행하지 않는다. 보호 계약 변경이 필요하면 별도 코드/문서 리뷰로 처리한다.

## 설치·상태·복구

```bash
bash deploy/install_monitoring_instruction_refresh_cron.sh --print-plan
bash deploy/install_monitoring_instruction_refresh_cron.sh --install
bash deploy/run_monitoring_instruction_refresh.sh --mode postclose --preview --date YYYY-MM-DD
bash deploy/install_monitoring_instruction_refresh_cron.sh --remove
```

설치는 현재 사용자 crontab의 전용 marker 두 줄만 관리하며 기존 항목을 보존한다. 설치는 시스템 timezone이 Asia/Seoul이 아니면 중단하며, 제거는 timezone 변경 후에도 가능하다. 설정은 `data/config/monitoring_instruction_refresh.json`, 설치 증거는 `data/report/monitoring_instruction_refresh/installed_trigger.json`이다. 매매 release selector와 별개로 설치된 workspace의 wrapper/module을 호출한다. 변경 배포 시 해당 파일 hash와 cron을 다시 확인한다.

실행 증거는 `data/report/monitoring_instruction_refresh/YYYY-MM-DD/{postclose,intraday}/`의 최신 `status.json`과 `attempt_N/`별 `context_manifest.json`, `before.md`, `candidate.md`, `change.diff`, draft/review JSON이다. `api_calls`에는 response ID·실제 모델·사용량이 남는다. preview는 별도 `_preview` 경로를 사용하며 원문과 예약 실행 횟수를 바꾸지 않는다. 공통 로그는 `logs/monitoring_instruction_refresh.log`다.

`failed`는 원본 유지, `blocked_publication`은 교체 여부 불명확으로 자동 재시도 없이 원문·후보·journal 대사가 필요한 상태다. `running`이 15분 이상 남으면 wrapper timeout/중단 여부를 확인한다. 공통 파일 lock으로 중복 writer를 막고 wrapper는 900초 후 종료한다. API 오류·리뷰 결함·동시 수정 원인을 해결한 뒤에만 남은 시도로 wrapper를 재호출한다. 횟수를 자동 초기화하거나 같은 실패를 무한 반복하지 않는다. 설정은 writer lock을 획득한 후 읽어 제거 직전의 enabled 값을 재사용하지 않는다. `--remove`는 전용 cron을 제거하고 설정을 disabled로 저장한다. 설치·preview 성공과 19:30/장후 종료 후 자연 실행 성공은 별도 acceptance다.
