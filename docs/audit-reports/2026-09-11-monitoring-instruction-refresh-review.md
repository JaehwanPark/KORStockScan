# 모니터링 작업지시문 자동 현행화 구현·설치 검증

판정: 문서 전용 서버 cron/API 후속 리뷰 finding 0, 대상 테스트 48개 PASS, 재설치·장후/장중 실제 API preview PASS. 자연 예약 실행은 `MonitoringInstructionRefreshNaturalAcceptance0911`의 후속 확인이며 아직 완료로 판정하지 않는다.

- 범위: `src/engine/automation/monitoring_instruction_refresh.py`, 전용 wrapper/cron installer, 운영 문서·runbook·workorder 확인 계약, 체크리스트. 매일 19:30 KST 장후 지시문, source-date 최종 detector DONE + strict summary/current hash + 실제 controller DONE 후 장중 지시문을 갱신한다. 자정 이후에도 원 source-date를 유지한다.
- 검토: 최신 START/FAIL 뒤 오래된 DONE 재사용 차단, 보호 문단·근거 quote·크기·링크·제목 검증, 독립 리뷰, 동시 문서/HEAD 수정 검출, 원자 게시, 단일 writer, 최대 2시도·시도당 4 API 호출, 원본/시도별 증거 보존, 기존 cron 보존/실패 복구를 확인했다. API는 도구 없이 두 문서만 편집하며 거래·장후 producer·외부 sync·자동 commit/push 권한이 없다.
- 실제 검증 보완: 첫 preview에서 리뷰 모델의 긍정 설명이 findings에 들어와 보수적으로 차단됐다. findings는 actionable defect만 허용하고 승인 시 빈 배열을 반환하도록 계약을 명확히 했다. 인증정보는 기존 설정에서 직접 읽어 거래 모듈 import를 제거했다. 코드의 literal credential은 전송 전 가리며, private cron 백업/API context는 Git 제외 경로에 보관한다.
- 검증 명령: `.venv/bin/python -m pytest -q src/tests/test_monitoring_instruction_refresh.py src/tests/test_build_codex_daily_workorder.py` → 42 PASS. 변경 Python compile, 두 shell `bash -n`, `git diff --check`, print-only backlog parser PASS. 신규 자연 확인 ID는 파싱 결과 한 개다.
- 설치: 2026-09-11 12:13:38 KST 최종 receipt, 시스템 timezone Asia/Seoul, cron active. 전용 marker 두 줄을 제외한 crontab은 최초 백업과 동일하다. module SHA256 `00fcd1d1f2bd6cabaa1c88f8df901766845fb0f865f1da5f72525678fe3f0ea9`, wrapper SHA256 `1c45932ed055739640b616e96d38490039579854eae7e0a709f403af5c495efe`. 설정/실제 설치 증거는 `data/report/monitoring_instruction_refresh/installed_trigger.json`이 소유한다.
- 실제 API: 12:11:51~12:12:19 KST, `gpt-5.6-sol` / reasoning medium. 작성 `resp_03561651cc200fc3016aa37179409c87d0bad3681527a5c4bf`, 리뷰 `resp_0d4884c018e77f68016aa371869a7087d08ec54836d6bf44ab`. 최종 preview 입력 103,168 / 출력 1,313 tokens, review findings `[]`, parser PASS, `preview_validated`. 이 수치는 최종 성공 preview 두 호출의 합이며 최초 계약 보완 전 호출 비용을 포함하지 않는다.
- preview 결과는 수정 없음이다. 원문/후보 SHA256 모두 `e58c9f93533da024cd1a5ee3cf965e8fb6a621981223e568aa2f99fd1133825d`; 원문 게시 및 예약 실행 횟수 소모 없음. 최종 보완 중 receipt 보존 부분은 대상 테스트로 재검증했으며 동일 API 요청을 추가 반복하지 않았다.

운영 계약과 중지·복구 명령은 [자동 현행화 운영 문서](../monitoring-instruction-refresh.md)를 따른다. 설치/preview는 실제 19:30·장후 완료 후 자연 실행, 거래 PID 소비 또는 경제성 증거가 아니다.


## 후속 리뷰·수정 반복

- 재현 후 수정: 기존 구현에서 장후 완료 hash 재검사 중 사용자 수정이 덮어써졌고, 문서 교체 전/후 프로세스 중단 뒤 API가 재호출됐다. 세 재현 케이스를 먼저 실패시킨 뒤 수정해 통과시켰다.
- 19:30 한 번의 cron tick이 writer lock과 충돌하면 그날 실행이 사라지는 문제는 `30-59 19 * * *` 재확인으로 수정했다. 시작은 19:30이며 기존 날짜·문서별 최대 2시도와 완료 후 중복 방지는 유지한다.
- 교체 전에 `publishing` journal을 내구성 있게 저장한다. 재시작 시 승인 후보 hash와 실제 문서가 일치하면 API/문서 재교체 없이 완료 receipt만 복구한다. 불일치·이후 사용자 수정은 `blocked_publication`으로 보존하고 자동 재시도를 중단한다. 두 번째 시도에서 끊겨도 횟수 제한 전에 journal을 복구한다.
- 장후 완료 재검증과 journal 저장 후 게시 직전에 문서/HEAD hash를 다시 확인한다. 설정은 writer lock 획득 후 읽어 remove와의 stale-enabled 경합을 없앴다. timezone 변경 후에도 제거는 가능하며 cron 백업은 생성 시점부터 0600이다.
- 재리뷰 범위: completion producer/consumer, publisher 중단/동시 수정, 반복 cron/중지, 보존·횟수 계약. 대상 48 tests PASS, compile·shell syntax·diff·print-only parser PASS. 신규 자연 확인 owner는 기존 ID 하나를 유지한다.
- 서버 재설치: `20260911T122110464658` KST, module SHA256 `3c6e5f80e59350a306fed9048d00ef61c405a630a82a0791af7811a9ec63996f`. 전용 두 cron과 module hash 일치, 전용 marker 외 기존 cron 보존 확인.
- 후속 postclose 실제 API: `2026-09-11T12:21:35.355715+09:00`, `data/report/monitoring_instruction_refresh/2026-09-11/postclose_preview/attempt_3`. 작성/리뷰 2회, 입력 101,750 / 출력 1,013 tokens, findings 0, preview_validated. 원문/후보 hash 동일, 예약 상태 파일 생성·횟수 소모 없음.
- 후속 intraday 실제 API: `2026-09-11T12:22:15.873460+09:00`, `data/report/monitoring_instruction_refresh/2026-09-11/intraday_preview/attempt_1`. 작성/리뷰 2회, 입력 101,997 / 출력 955 tokens, findings 0, preview_validated. 원문/후보 hash 동일, 예약 상태 파일 생성·횟수 소모 없음.
- 마지막 판단: 검토한 자동화 범위의 미해결 코드 결함 0. 실제 19:30·장후 완료 시점의 자연 실행은 기존 체크리스트 owner로 남기며, 거래 프로세스·전략 설정·외부 sync는 변경/실행하지 않았다.
