# Snapshot cron 선택본 결속 및 Source Control 통합 — 2026-10-18

사용자 "다음액션 실행하라" 승인에 따라 snapshot 실행 경로 수리·리뷰·검증·적용을 수행하고 기존 Source Control 변경을 보존해 통합한다. 원 선택 `900234d791b0bf31797cd4e823d0ae40296f790b`와10/19 정책/PREOPEN·원 실패 및 비용/custody 원천은 보존한다.

## 구현·리뷰·보완

bootstrap 커밋 `9afd16cdc1d7a10e5c58cab3218a16823dcd15cc`는 canonical router의 `monitor-snapshot` operation을 추가한다. 실제 selected incremental wrapper를 날짜와 함께 직접 실행하며 cwd/PROJECT_DIR/PYTHONPATH/VENV_PY를 선택본에 고정한다. 기존900 safe wrapper·Python·`$0` 비동기 자식은 그대로 사용하고 불변 릴리스 내부를 편집하지 않았다. Main 기동/재기동·정책값·provider/주문 권한은 바꾸지 않는다.

기존 로그 owner·경로·예약·정오 jitter와8필수 route는 유지하며 snapshot3개 tag만 별도로 검증한다. 실제 운영 CLI는 전체 누락도 기동 전에 거부하고, 과거8개만 다루는 순수 변환 API만 호환성을 유지한다. 누락/부분/중복·echo/다른owner/추가인자·복구selector/오염env·동시cron변경을 거부한다. broad installer를 실행하지 않고 기존 lock·backup·CAS/readback의 `--install-cron`으로 정확3행을 적용했다. 향후 설치기도 같은3개 라우트를 발행한다.

리뷰에서 운영 CLI의 전체 snapshot 누락을 통과시키던 호환성 경계를 강화했고, 운영 문서의 기존8행 표현을8필수+3snapshot으로 수정했다. 독립 재리뷰에서 구현 finding0을 확인했다. atomic dump/replace 실패 시 원 bytes·임시파일 정리와8세대×16회 동시 읽기의 완전 JSON을 검증했다.

## 검증 및 실제 적용

- router203개 + snapshot73개, 합계276 passed. 실패worker의 실제 exit·성공 cooldown·완료파일 동시 읽기 포함.
- Python compile, shell syntax, diff check 및 print-only parser PASS.
- 실제 crontab 변경3행, 일정/로그/정오 env·나머지행 보존. readback은8필수+3snapshot, 재변환 동일.
- 실제 선택900을 이용한10/18 수동 완료대기 호출: worker1059464, terminal `success`, `intraday_light`, 보고서3개,3.916초. 선택본 safe wrapper 경로와 새 완료 영수증을 확인했다. 비영업일 운영 경로 검증이며 자연 장중 관측·경제성 증거는 아니다.
- 첫 dispatch-only 수동 호출은 worker1059293의 종결을 확인하지 못했다. `dispatched` 원 영수증을 보존하고 성공으로 바꾸지 않았다. 이후 실제 완료대기 호출과 구분한다. 첫 worker 종료 원인은 확정하지 않았다.
- 기본 async(wait=0)도 별도 유지형 확인 프로세스에서 재검증했다. 부모가 먼저 반환한 뒤 worker1059923의 실제 `/proc` cwd·절대 safe wrapper argv·PROJECT_DIR/PYTHONPATH/commit이 모두 선택900을 가리켰고, 새 terminal success·보고서3개가 발행됐다. 이는 합성 producer가 아닌 실제 selected report 경로의 수동 검증이다. `default-async-verification.json`과 원 worker output을 보존한다.
- 보호11개 파일은 호출 전후 해시가 같다. 실제 Main 기동/재기동·provider/주문·외부 sync는0이며 actual_pid_consumed=false를 유지한다.

Evidence: `/home/ubuntu/KORStockScan/tmp/snapshot-routing-repair-20261018/`. `pytest-routing-final.txt`, `cron-plan-diff.json`, `cron-install.json`, `cron-check.json`, `cron-before.txt`, `cron-after.txt`, `bootstrap-publication.json`, `manual-dispatched-receipt.json`, `manual-snapshot-waited.log`, `actual-snapshot-completion.json`, `actual-snapshot-worker-output.log`, `protected-runtime-after-snapshot.json`이 코드/설치/실제 terminal/미종결 시도를 구분한다.

## Source Control 보존 경계

원102개 파일7,008,025바이트·mode/SHA/Git blob·index·HEAD·selector·cron을 먼저 백업했다. 원문 tar와 `refs/archive/source-control-reconciliation-20261018/original-workspace`의 commit `1223bec80d106ab1f9b5aea0f3612210f44af844`로 원 workspace를 복원할 수 있다. 원 `c938ace06`과 선택900 사이 누적200개 commit의 검증된 소스를 사용하며, 기존8개 불일치 파일만 선택해 옛 코드를 남기지 않는다.

기존 모든 문서·AGENTS·수동관리 설정 bytes와 선택본에서 제거됐던 역사 문서12개를 보존한다. 소스는 선택본과 이번 bootstrap 수리의 검증된 전체 tree를 사용하고, 퇴역 소스2개는 Git 원본을 보존한 채 선택본과 같은 제거 상태를 따른다. requirements 파일의 검증된 상태를 가져오더라도 공유 .venv 패키지를 설치·변경하지 않는다. 전후 선택/정책/준비·동시문서 변경은 CAS로 확인한다.

통합은 별도 index/tree에서 검증 후 수행하고 실제 변경 파일의 원본 hash를 재확인한다. 문서와 운영 원천을 checkout/reset으로 덮어쓰지 않는다. SourceControlReconciliation1018의 실제 main 전진·최종 clean 확인 결과는 후속 완료 기록으로 남긴다. 10/19 PREOPEN/PID·자연 생산/경제성은 원 owner를 유지한다.
