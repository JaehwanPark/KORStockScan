# Main 반복 원천 검증 I/O 구현·리뷰 — 2026-10-14

## 1. 판단·기준

사용자 요청에 따라 [보완 계획](../proposals/main-io-residual-validation-and-monitor-read-amplification-remediation-plan-2026-10-14.md)을 최종 선택 릴리스 `5fb4c0a33a9df2b26e5fab4740576ce746a8cc93`에 맞춰 재검토하고 격리 구현했다. 작업본은 `/home/ubuntu/KORStockScan-worktrees/main-io-residual-20261014`, branch는 `fix/main-io-residual-20261014`다. 원 작업공간의 다른 변경을 합치거나 덮어쓰지 않았다.

09:29 및09:50 KST 확인에서 selected root는 `main-market-weakness-20261014-5fb4c0a33`, selector는 `main_stopped_no_start_requested`/`actual_pid_consumed=false`, 실제 Main PID는 관측되지 않았다. [재확인 기록](/home/ubuntu/KORStockScan/tmp/main-io-residual-implementation-20261014/latest-release-recheck.json)을 기준으로 삼는다. 08:44 경보 당시 PID3854164/01d9fefa4는 역사이며 지금 실행 중인 PID로 보고하지 않는다.

**코드 구현·표적 회귀 완료, 배포·기동·정규3슬롯 자연 성능은 미수행**이다. 검증을 위해 정책·threshold·provider·계좌·주문·custody·퇴역 경계를 변경하지 않았다.

## 2. 최종 설계와 변경

| 소유 경로 | 구현 | 보존한 계약 |
|---|---|---|
| [digest session](../../src/engine/infrastructure/validation_digest_session.py) | 명시적 ContextVar 범위에서1MiB 이상 local data 파일 SHA만 재사용. observer6시간/transition120초, 역할별32세대·각512KiB, private mode, bounded flock, atomic write, warm write0 | semantic PASS/selection/incident를 저장하지 않는다. 파일 세대·경로/권한/alias 변경을 검사하고 모든 native 기대 SHA 비교를 다시 실행한다. |
| [machine loader](../../src/engine/scalping/mechanistic_entry_runtime_policy.py), [reversal hash](../../src/engine/scalping/continuous_reversal_postclose.py), [delay raw generation](../../src/engine/lifecycle/holding_window_generation.py) | 현재/과거 family와 code handoff 원천뿐 아니라 delay ledger의 historical raw 해시도 같은 explicit session에 연결 | default context 없음은 원 full 경로. 누적 compact hash·작은 JSON/정책 선택·부재/목록/PID 검사는 그대로 실행한다. 구형 origin subprocess full 비용은 남는다. |
| [monitor](../../src/engine/monitoring/submission_bottleneck_monitor.py), [budget](../../src/engine/monitoring/observation_budget.py) | source gap 먼저 계산, 큰 검증에만 digest lock, 상태 잠금2초, 단일120초 예산과 마지막15초 저장/알림 여유, run_id/실행/관측/알림/개별 publication 표시 | deferred가 pending을 지우거나 active를 해소하지 않는다. 기존 cursor/first_seen/notified 이력 유지. source-only는 machine cache lock을 기다리지 않는다. |
| [wrapper](../../deploy/run_buy_funnel_sentinel_intraday.sh), [freshness](../../src/engine/error_detectors/artifact_freshness.py) | 모든 자식에 동일 priority, 전체180초와 자식 회수5초, monitor 실패75/1 전파와 성공 cooldown 제한, 신규 execution/semantic 상태 소비 | Sentinel 실패 뒤 source-only 성공으로 원 실패를 지우지 않는다. 기존 cron DONE/FAIL parser를 재사용하고 regression으로 검증한다. valid-empty·관측된 issue·알림 실패와 실행 실패를 구분한다. |
| [bootstrap](../../src/engine/automation/runtime_policy_bootstrap.py), [handoff](../../src/engine/automation/intraday_release_handoff.py), [driver](../../src/engine/automation/ordered_intraday_deploy.py), [launcher](../../src/run_bot.sh) | explicit CLI session, candidate/launcher namespace 전달, 새 PID/start/cwd 분리, independent driver verify 유지, exact reviewed consumer hash pair 추가 | standalone CLI/PREOPEN/live 기본 full. native prepare/consume/verify와 원 출력 발행을 수행한다. launcher는 namespace env를 Main에 남기지 않는다. 새 정책 승인·Main 기동 권한이 아니다. |

위치 gate: 공유 검증 비용 계층은 `infrastructure`, observer deadline은 `monitoring`, 새 회귀는 `src/tests`다. engine root 새 모듈/중복 wrapper는 없다. 운영 변경은 [릴리스 계약](../runtime-release-routing.md), [시간별 runbook](../time-based-operations-runbook.md), 격리 [당일 checklist](../checklists/2026-10-14-stage2-todo-checklist.md)에 같이 반영했다. 공유 operational checklist는 변경하지 않았다.

metadata 재사용은 같은 OS/local writer와 ctime 세대 검출을 신뢰한다. 파일 내용의 매회 암호학적 재해시나 관리자 변조 방어와 같지 않다. 비지원 filesystem·다른 mount·cache 저장 장애는 full fallback이며 timeout/lock 경합은 명시적 실패다. store가 semantic 성공을 발행하지 않으므로 native 실패를 cached PASS로 바꾸지 않는다.

## 3. 반복 리뷰·수정

1. 검증 결과 전체를 cache하는 초안을 파일 digest만 공유하는 설계로 고쳤다. 부재/새 후보/env·PID 조건을 빠짐없이 cache key로 복제해야 하는 부담을 제거하고 native 검사를 매회 유지했다.
2. machine 경로 외 delay ledger의 `byte_generation` 원천 재해시를 연결했다. 작은 파일·누적 compact 계산과 기존 source inventory 오류는 유지했다.
3. deferred/partial이 incident를 초기화하는 경로, blocking state lock, monitor exit0와 freshness 정상 판정 혼동을 수정했다. 실제 source gap을 확인했더라도 다른 source가 미관측이면 partial로 남긴다.
4. independent source-only에 불필요한 machine cache lock을 걸지 않게 수정했다. 새 phase context와 실제 tmux child 전달을 확인했고, launcher 명령에 세션 namespace를 전달했다. 후속 실제 router 연동에서 hold 해제 순서 오류를 발견해 아래 재리뷰로 보완했다.
5. synthetic 측정에서 warm cache에도 fsync가 발생하는 결함을 찾아 제거했다. TTL은 hit로 연장하지 않으며 storage/partial publication 실패는 정상 완료로 바꾸지 않는다.
6. 이전 테스트의 mock launcher 명령과 생성자 우회 fixture를 새 계약에 맞췄다. 실제 standalone/default opt-out, cross-process reuse, PID 검사 재실행·실패 전달, native policy/monitor parity, source rewrite/alias/expiry/corruption/permission/ENOSPC/lock·deadline·notification 이력·wrapper failure propagation을 재검증했다.

현재 리뷰 범위의 미수정 코드 결함은0이다. 배포 전 native compatibility 발행과 자연 성능은 코드리뷰 완료와 구별한다.

## 4. 검증 결과

- [통합 회귀 로그](/home/ubuntu/KORStockScan/tmp/main-io-residual-implementation-20261014/pytest-final.log): **1,450 passed /17.19초**. 실제 provider/Telegram/주문은 호출하지 않았다.
- 변경 Python compile, `bash -n` 두 wrapper, `git diff --check`, print-only parser·로컬 링크·current stable owner 확인은 [최종 검증 기록](/home/ubuntu/KORStockScan/tmp/main-io-residual-implementation-20261014/validation.json)에 남긴다.
- [8MiB synthetic 실험](/home/ubuntu/KORStockScan/tmp/main-io-residual-implementation-20261014/digest-benchmark-final.json): 독립 Python 프로세스의 native `byte_generation` 결과가 모두 같았다. full 논리 읽기8,388,706 bytes, cold session8,393,838 bytes, warm7,184 bytes로 **해당 구간99.91% 감소**. full5.79~5.80ms, cold12.92ms, warm1.64~1.65ms. cold cache 저장4KiB·warm write0. page cache를 지우지 않았다.
- 위 실험은 파일 검증 구간이다. 전체 monitor90% 감소·wrapper60초·host iowait p95<20%·Main local 지연 개선을 입증하지 않는다. 실제6.89GiB 원천 full 재생은 이번 시험에 사용하지 않았다.

## 5. 남은 수용·프로세스·배포 경계

- 선택 릴리스/PID/정책/원천을 다시 고정한 뒤 허용된 배포 절차가 active-policy code handoff, 필요 시 동일 정책 future refresh·source reseal과 checklist publication을 수행해야 한다. 원 PREOPEN commit `bd40c7f12a8c3913e638809cc8aa3cb04f29fa70`에서 현재 reviewed bootstrap/monitor까지 exact hash pair만 허용했다. 이 pair는 별도 발행/소비 증거를 대체하지 않는다.
- `NonfixedDispatchReadinessReview1012`: 실제 정상3슬롯의 scope/분모·source age·full/reused 파일 bytes·worker wall/RSS·host10초 표본 및 active 구간을 확인한다. 구형 origin full 비용/부적격 cache 비중을 공개한다.
- `DirectFamilyPreopenPolicyHandoff`: 다음 허용된 적용·기동의 원 정책 불변과 실제 successor PID 소비를 확인한다. 현재 Main 정지 선택을 이번 구현으로 해제하지 않는다.
- `AuxiliaryCircuitRecoveryRepair1012`: 실제 정상 attempt가 생긴 뒤 원5초 deadline과 offered/timeout/censored·guard를 비교한다. 현재 자연 표본 미관측은 pending이다.
- RIO4 재확인에서 별도 Gunicorn과 ModemManager/multipathd는 관측됐으나 제거 가능한 불필요 프로세스로 확정하지 않았다. PID/서비스 종료, swapoff, cache drop, EBS/cron/경보 임계치 변경은 하지 않았다.
- 롤백은 native full/default CLI와 검증된 Main-only recovery release를 사용한다. incident/cursor 삭제로 정상화하지 않으며, 퇴역 owner를 복원하지 않는다. shared workspace의 다른 변경·선택 릴리스·실제 데이터는 보존한다.

## 6. 후속 배포 승인·재리뷰

10/14 사용자가 반복 코드리뷰·수정보완 후 배포 및 Main 기동을 명시적으로 승인했다. 10:04 재확인에서 selected5fb4c0a33/Main 없음, operator startup hold/restart 요청 없음이다. 일반 ordered driver는 실행 중인 predecessor를 요구하므로 이번 정지 배치는 기존 native `--previous-stopped` 인계를 사용한다. 현재 미기동 selector와 마지막 실제 소비01d9fefa4/PID3854164/ticks18431371을 각각 보존하고, 이전 소비·원 PREOPEN/manifest/env/prepared·정책 byte와 code delta를 검증한 뒤 release/detector 잠금 아래 publication·prepare·ordinary launcher·실제 PID 검증을 수행한다. 정지 상태에서 실제 소비 영수증을 새로 합성하지 않는다.

재리뷰에서 candidate checklist가 이후 추가된 약세 연구 배포 승인 이력을 누락하는 것을 발견하여 원문을 보존하도록 보완했다. monitor budget/부분 관측/incident·파일 SHA 재사용/native semantic 반복·wrapper 실패 전파·launcher PID 분리 범위에 추가 미수정 코드 결함은 확인되지 않았다. 검증·배포 phase·새 PID 결과는 `/home/ubuntu/KORStockScan/tmp/main-io-residual-deploy-20261014/`와 deployment result가 소유한다.

### 기동 전 holding 계약 결함과 보완

첫 candidate `b98559625`의 native prepare가10:10 KST에 `holding_path_vote_policy_receipt_mismatch,holding_path_vote_policy_stale_env`로 차단됐다. 변경한 `holding_window_generation.py`가 보유 vote 수치 연구의 code pin에도 포함되지만 reviewed pair와 선택 전 holding code 검증이 빠진 것이 원인이다. Main은 기동되지 않았고 원 정책/PREOPEN/env/manifest/prepared byte는 보존됐다. 실패 phase·자기 hold·선택을 보존한 뒤 release/detector 잠금과 byte CAS로 기존5fb4c0a33 정지 선택·공유 문서를 복원했다. [실패 복구 기록](../../tmp/main-io-residual-deploy-20261014/failed-attempt-recovery.json)을 성공으로 덮어쓰지 않는다.

원 PREOPEN code pin에서 실제 리뷰한 holding generation 파일까지 exact SHA pair를 추가했다. 새 `verify_candidate_holding_vote_code`는 native bundle 구조/receipt/date/origin/carry를 검사하고 approved source delta를 선택 전 검증한다. 수치 successor는 기존 current code 계약을 유지하고 전체 source/bootstrap 검증도 다시 수행한다. 일반 ordered driver와 이번 정지 배치 preflight 모두 이 검사를 사용한다. 잘못된 origin/date/bundle/path, 미검토 코드, 수치 successor와 원천·verifier 변조를 반례로 추가했다. [표적760개](../../tmp/main-io-residual-deploy-20261014/holding-fix-tests.log) 통과; 보유 native 회귀와 최종 통합 검증은 재배포 기록에 별도 봉인한다.

### Native router의 자기 hold 순서 보완

두 번째 candidate `0aceeec35`는 delay/stop/holding preflight와 native prepare/bootstrap/auxiliary 준비를 통과했다. 이어 `make_plan`이 자기 startup hold를 일반 operator hold로 차단하여 Main launch 전에 정지했다. 실제 router를 mock한 기존 테스트가 이 연동을 검증하지 못했다. 기존 성공·실패 기록을 보존하고 같은 CAS 절차로 정지 선택을 복원했다.

release-set lock을 계속 유지한 채 소유 byte·phase·selector·Main 부재를 검증하고 **자기 hold 제거 → 원 router 계획/명령 검증 → launcher → PID** 순서로 고쳤다. 계획/launch 실패는 기존 failure handler가 자기 hold를 exclusive 생성하며 다른 operator hold를 덮어쓰지 않는다. 실제 router 호출과 계획 실패/hold 복원 반례를 추가했다. 정책 검증을 생략하거나 router hold guard를 완화하지 않았다. 최종 후보는 이 보완을 포함해 재배포한다.

두 번째 준비의 bootstrap은 `full_reads=0`, `reused_reads=2`, `reused_bytes=10438031954`로 native PASS였다(2.04초, 전체 logical read251,291,057 bytes). 이는 해당 재검증 단계의 실측이며 전체 서버·정규3슬롯 성능 PASS는 아니다.
