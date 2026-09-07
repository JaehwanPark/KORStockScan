# 2026-09-07 두 번째 전체 소스 배포 검토

대상일: 2026-09-07 KST. 시작: 16:23 KST. 이 기록은 13:08 재기동 완료 기록을 대체하지 않는다.

## 판정과 범위

사용자 지시: 전체 커밋·푸시·main 병합 후 우아한 재기동. 전체 `src/`, `deploy/`, `docs/`의 기존 변경과 통합 검증 보완을 포함한다. 운영 중 생성되는 `data/cache/`, `data/runtime/`, `data/report/`는 보존하며 소스 커밋에 포함하지 않는다. 수동목록, 당일 policy/env, broker 주문·취소와 owner 원장은 이번 배포 검토에서 변경하지 않았다.

16:35 검토 시점에는 코드·문서 검증 범위의 미해결 finding이 0이었으나 GitHub main PR 승인 1건 때문에 병합·재기동을 보류했다. **16:41 이후 사용자 명시 지시로 PR 필수 규칙을 제거했으며 현재 계약은 아래 추가 실행 기록을 따른다.** 이전 권한에서 승인 규칙을 임의로 우회한 것으로 해석하지 않는다. 이후 확정된 Black CI 실패는 별도 검증 결함으로 보완한다.

## 포함한 변경

- [수동 veto·동일종목 공존 최종 리뷰](2026-09-07-manual-veto-coexistence-final-review.md): 사용자/auto veto 영속과 최종 main 주문 전송 전 재검사, machine scope 분리, quiescent marker migration 및 owner isolation.
- [scanner lookup 최종 리뷰](2026-09-07-scanner-lookup-attention-final-review.md): 완전한 경쟁군과 한계 pair 계산, immutable base, source-quality 국소 제외, 다음 exact-date PREOPEN receipt와 runtime provenance.
- [AI decision/action/outcome 최종 리뷰](2026-09-07-ai-decision-action-outcome-calibration-final-review.md): 부분 성공 학습과 승격 차단 분리, cohort/source/hash·비용·위험 계약, #82→optimizer 및 metadata-only 후속 consumer 결속, wrapper 의존 순서.
- 관련 테스트·checklist·traceability. 신규 계산 모듈은 기존 소유 패키지 `src/engine/scalping/`에 위치하며 engine root 새 모듈은 없다.

## 통합 리뷰에서 추가 수정

1. `test_kiwoom_orders.py`의 전역 빈 `holidays` stub이 다른 테스트의 거래일 달력을 오염시켰다. requirements에 이미 있는 실제 설치 의존성을 사용하도록 stub을 제거했다. 패키지 변경이나 설치는 하지 않았다.
2. scanner pool fixture가 운영 exact-date owner policy/registry를 읽어 host 계좌 설정에 따라 후보를 모두 차단했다. policy와 registry를 tmp 경로로 격리했다. production fail-closed 로직이나 resolver는 완화하지 않았다.
3. `symbol_owner_policy.py`의 과거 docstring에 남은 manual_operator 예외 설명을 수정했다. 공존 정책은 machine scope만 대체하며 explicit/auto veto를 우회하지 않는 현재 계약과 일치시켰다.

수정 전 전체 회귀는 45 failed/2967 passed였다. 위 test isolation 보완 후 해당 영향면 258 PASS를 확인하고 동일 전체 범위를 다시 실행했다. 앞선 component 리뷰의 옛 stub 예외 설명은 당시 검증 기록이며 현재 코드에는 그 stub이 없다.

## 최종 검증

- 30개 테스트 파일 통합 회귀: **3012 passed, 1 warning, 84.49초**. warning은 외부 pandas_ta의 pandas4 deprecation이다. `/tmp/full_merge_restart_0907_final_tests.log`에 실행 출력이 있다.
- 테스트 범위: 이번 변경된 18개 `src/tests/test_*.py` 전부와 `test_scanner_lookup_attention_resource.py`, `test_symbol_owner_policy_apply.py`, 삼성 morning/midday/afternoon 및 각 preflight 6개, `test_sniper_scale_in.py`, `test_restart_flag_race_guard.py`, `test_error_detector_coverage.py`, `test_engine_location_gate.py`.
- 실행은 project `.venv`, `PYTHONPATH=.`, `pytest --override-ini addopts='' -q`를 사용했다. broker/provider 실호출을 위한 시험 주문이나 표본 생성은 하지 않았다.
- 변경 Python 및 신규 모듈 compileall PASS. 변경 wrapper 3개와 `restart.sh`, `run_bot.sh`의 `bash -n` PASS. `git diff --check` PASS.
- 변경 Python Ruff PASS(기존 scanner bootstrap E402 예외). `kiwoom_sniper_v2.py`의 기존 E402/F401 91건은 base와 현 코드의 code/message multiset이 동일함을 확인했다. 기존 lint 부채를 전체 0이라고 주장하지 않는다.
- 문서/checklist parser print-only 검증 PASS(50개 OPEN task, 신규 배포 gate 포함). GitHub Project/Google Calendar sync는 실행하지 않았다.
- 자기 리뷰와 수정 후 재리뷰는 producer→consumer, scanner→state→최종 주문 경계, source-only 권한, 실패 전파 및 다음-session handoff를 포함했다. 이 검증은 live 수익성·broker 체결 품질·새 PID 실제 소비 완료를 뜻하지 않는다.

## Git·운영 근거와 남은 gate

- 시작 main/원격 main: `e7d3886a15deb5ca9bbc953735cccc3140dddbf1`. fetch 후 main divergence 0/0.
- 작업 브랜치: `codex/full-workspace-veto-calibration-20260907`. 소스 commit→branch push→normal PR까지만 진행하고 승인 충족 전에는 병합하지 않는다.
- GitHub branch-protection API 확인: `required_approving_review_count=1`, `enforce_admins=false`, `required_status_checks=null`. 기술적으로 관리자 bypass가 가능하더라도 승인 gate는 유지한다.
- 점검 당시 main PID `356899`, 시작 `13:08:27 KST`, runtime commit `9c712b4c3be0139d0579752faca02d28820a072a`; widget PID `9704`, 시작 `07:57:59 KST`. 이번 검토에서 중단/재기동하지 않았다. 새 소스가 해당 PID 메모리에 반영됐다고 보지 않는다.
- 수동 제외목록은 기존 legacy 기계 표식 18행과 SHA-256 `56efd7881ab1ff04a47fa351e42bc4ca6a93770057715e23d535a094a8c1804d`를 보존한다. 당일 16종목 정책을 확대하지 않는다.
- 병합 뒤에만 최신 process·runtime verify·broker KRX/NXT 미체결/잔고·owner registry를 다시 읽고 기존 graceful restart 계약으로 배포한다. 새 PID commit/env·WS first-data·canary·singleton과 owner별 잔고/미체결 연속성을 확인한다. 옛 broker snapshot을 재기동 직전 근거로 재사용하지 않는다.
- main 승인·병합·재기동 owner는 `FullWorkspaceSecondMergeRestart0907`, 목록 전환은 `ManualVetoCoexistenceDeployment0907`, 다음 exact-date 실제 적용은 `SameSymbolMachineScopePreopenAcceptance0908`이다. 승인 대기나 이 기록은 자동 재기동 예약이 아니다.

## 배포 receipt (16:35 KST)

- 소스 commit: `47b2779ee0455fa2baf0e39e2c55c59e47961338`, 49 files, 7656 insertions/1116 deletions. 기능 브랜치 원격 push를 확인했다.
- [PR #58](https://github.com/JaehwanPark/KORStockScan/pull/58): base `main`, 상태 `OPEN`, `reviewDecision=REVIEW_REQUIRED`, `mergeStateStatus=BLOCKED`. 이 확인 시점의 Black CI는 진행 중이다. 로컬 검증 PASS를 CI 완료로 대신하지 않는다.
- 로컬/원격 main은 모두 `e7d3886a15deb5ca9bbc953735cccc3140dddbf1`로 유지됐다. main 병합·push는 실행하지 않았다.
- 최종 읽기 전용 확인에서 main/widget PID와 시작 시각, 수동 제외목록 hash는 위 기록과 동일하다. source worktree는 clean이며 생성 데이터 10개 status 항목은 그대로 보존됐다.
- 다음 액션: PR 승인 1건과 최신 head의 검증 상태를 확인한 뒤 main 병합 및 허용된 graceful restart를 이어간다. 승인이나 CI 결과를 가정해 미리 재기동하지 않는다. 이 문서 receipt를 추가하는 후속 commit은 문서 전용이다.

## PR 의무 제거와 직접 병합 실행 (16:41 KST 이후)

- 사용자 추가 지시: `PR 원칙을 제거하라. PR 없이 병합하라`. 이는 이전 PR 승인 대기 절차를 대체하는 명시적 권한이다.
- `DELETE /repos/JaehwanPark/KORStockScan/branches/main/protection/required_pull_request_reviews` HTTP204. 전후 전체 protection 응답에서 해당 필드만 제외한 값은 동일했다. 강제 push·브랜치 삭제 금지는 계속 false(불허), 다른 보호 설정도 유지한다. [원본/결과·rollback 근거 JSON](2026-09-07-main-pr-rule-removal.json)을 보존했다.
- 원격 Black26.5.1 CI는 71개 파일 포맷 불일치로 실패했다. 같은 버전의 로컬 cached 검사는 67개만 탐지했으므로 나머지 4개와 최종 전체 검사는 `--no-cache`로 고정한다. 포맷 변경 71개 모두 `ast.dump(..., include_attributes=False)`가 HEAD 전후 완전히 동일하며 API·주문·가격·수량·provider 판단을 변경하지 않는다. 기존 review된 기능 변경과 이 formatting-only 보완은 구분한다.
- 확대 61-file 회귀와 캐시 없는 전체 Black 검사, compile/shell/diff/parser 검증이 완료된 뒤에만 직접 main merge/push 및 별도 승인된 graceful restart를 진행한다. 검증 결과와 실제 merge/PID/broker 연속성은 아래에 추가한다.

### 직접 병합 전 최종 gate (16:57 KST)

- 확대 회귀 첫 실행은 `137 failed, 4496 passed, 18 skipped`였다. 실패는 모두 `test_sniper_scale_in.py`에서 운영 exact-date owner policy/registry를 읽는 test isolation 결손이었다. 과거 시각/가상 종목 시험이 host policy의 날짜·account guard에 차단되는 원인을 분리하고, fixture에 임시 policy/registry 경로만 설정했다. production resolver·manual veto·broker/order guard는 그대로 실행한다.
- 수정한 파일 단독 `1037 passed`, 동일 61-file 통합 재검증 **4633 passed, 18 skipped, 1 warning, 162.99초**. 출력: `/tmp/prless_merge_0907_tests_final.log`. 18 skipped는 검증 완료 표본으로 세지 않으며 warning은 위 외부 pandas deprecation이다.
- `black --no-cache --check --workers 2 .`: **869 files unchanged**. 71개 formatting 파일 AST 동일, 추가 fixture 10행만 test input isolation 변경이다. 72개 Python compile, shell syntax, 문서/parser print-only, `git diff --check` PASS. 변경과 연결된 producer/consumer, fail-closed 유지, fixture env key와 teardown을 재리뷰했으며 이 coverage 내 미해결 코드 finding0이다.
- 읽기 전용 runtime verify: main PID356899 `pass`, findings `[]`. 16:47 KRX/NXT broker snapshot은 `249420=1`, `304100=1`, 미체결0이었다. DB active SCALPING rows40942/40904가 각각 15460/16280원 1주로 일치하여 이 두 종목을 manual/기계 custody로 오인하지 않는다. 실제 재기동 직전에는 새 snapshot을 다시 받는다.
- 위젯 PID9704의 `/proc/9704/environ`은 permission denied로 확인 불가다. unit/state만으로 PID 환경 검증 성공을 주장하지 않으며 위젯 재기동은 보류한다. inactive인 삼성/저가주 episode 서비스를 임의 기동하지 않는다.
- 별도 운영 warning: 16:46:20 observer canary는 0B callback p99 `2.360669ms > 2ms` 3회로 `stop_required`, 이후 snapshot stale이다. 이는 source-only capture/Provider replay readiness blocker로 유지하며 재기동으로 과거 source 결손이 복구됐다고 주장하지 않는다. canary 임계치나 stop 판정은 변경하지 않는다.
