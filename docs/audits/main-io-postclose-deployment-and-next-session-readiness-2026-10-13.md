# I/O 개선 장후 배포와 다음 정규 기동 검증

## 승인과 실행 순서

사용자는 I/O 개선계획의 보완·구현·반복 리뷰·배포·재기동을 승인한 뒤, 현재 장후 작업이 완료되면 배포하고 다음 영업일 정상 기동을 재점검하도록 지시했다. 원 장후 source/publication은 `2026-10-13`, 다음 적용일은 `2026-10-14`로 유지한다. 기존 Main은 20:00 자연 종료했다. 다음 실제 Main 소비는 정규 기동의 별도 수용이다.

장후 Main 성공, whole-chain strict/controller DONE, tuning 성공 및 이전 실행본의 프로세스 종료를 먼저 확인한다. 이후 완료된 장후 수리 릴리스를 부모로 I/O 개선을 추가하고, 변경된 계약의 producer와 summary/checklist/strict/controller 및 다음 PREOPEN 준비를 검증한다. 활성 wrapper를 중단하거나 실행 중 selector를 전환하지 않는다.

## 배포 후보 검토

- 원 I/O 변경의 코드·안전·전체 보고서 의미 및 성능 검증은 [구현 리뷰](main-io-contention-and-repeated-validation-implementation-review-2026-10-13.md)가 소유한다. 기존 1,226개 표적 시험과 최종 Sentinel 209개 시험은 중복 합산하지 않는다.
- 23:45 후보 `bfa7eb02718559b82b7f8288de9a24dd75bb8f3f`는 최종 장후 인계 수리 `8e0bd25f704271b1a890061f9099d9149f55060d`를 부모로 검토된 I/O 13개 파일만 추가했다. 정책 계약 33개는 부모와 byte 동일하다. 이전 `53371593` 후보는 장후 수리를 포함하지 않으므로 배포 대상으로 사용하지 않는다.
- postclose stage·입장 대기·wrapper·observer·bootstrap/readiness 결합 시험 176개 PASS, 보조 정책 128개 범위 검증 PASS다. 별도 confirmation 검증은 128 scopes·76,800 ticks·614 hits이며 signal SHA가 동일하다. 새 provider 호출·실주문은 없다.
- 증빙은 `tmp/io-postclose-deployment-20261013/{release-build,preflight,native-parity,context}.json` 및 `integration-tests.log`다. 배포 직전 selector가 바뀌면 최신 수리를 보존해 후보를 다시 구성한다.
- 10/14 00:10 추가 수리 `375f2ae28c2077bd94c667d23e638a3a8d1d0f30`가 선택됨에 따라 후보를 `783806f8785bc5ab670ce62f2af55e40934bac1e`로 다시 구성했다. 결합 시험 179 PASS(4.93초), 정책 계약 33개 동일, auxiliary 128개 범위 PASS다. 앞선 후보 증거는 `v3-*`로 보존했으며 이 후보도 장후 완료 전에는 선택하지 않는다.
- 최종 checklist 수리 `5cffbc22a61995d8d0233ca95bb2c95915610ba7`를 부모로 후보 `373d5f10f3aecf2c31e5a6b8864080e6760c2263`를 구성했다. 결합 시험 202 PASS(5.69초), 실제 커밋과 시험 source SHA 일치, 정책 33개 동일성 및 auxiliary 128 scopes PASS다. 앞선 후보는 `v4-*`로 보존했다.

## 장후 선행 상태

23:48:42 관측에서 native Main run `f343c03991b742f590431a3291bff03f`는 최종 검증에서 exit 2로 실패했다. 이전 cancel-wait custody 문제는 수리됐으며, 이번 첫 source 결함은 `entry_split:semantic_unverified_large_source`다. 보고서 539,058,129 bytes가 native reader의 bounded predecessor 계약에서 거부됐다. 이 결함을 검증 성공이나 원천 부재로 바꾸지 않는다. 현재 선택은 `8e0bd25f`, controller/tuning은 해당 실행본에서 선행 완료 대기 중이다.

이 시점의 후보 시험 PASS는 장후 완료·I/O 배포·다음 PREOPEN 준비 PASS가 아니다. 배포와 다음 기동 준비 결과는 실제 완료 증거를 확인한 후 아래에 기록한다. [장후 수리 리뷰](postclose-failed-stage-recovery-implementation-review-2026-10-13.md)의 진행 중 변경은 보존한다.

10/14 자정 이후에는 code handoff를 실제 현재 날짜로 발행하고, 원 10/13 source/publication의 봉인된 machine/auxiliary를 native publisher로 10/14 미활성 후보에 결속한다. 시각을 과거로 전달하거나 failed-PREOPEN 권한을 합성하지 않는다. 07:30 이전, Main/이전 wrapper 부재, 당일 PREOPEN 미실행·정책 미활성, current pointer·selector·선행 terminal CAS를 요구한다. Native reader의 선택 경계에 맞춰 두 deployment lock 아래 selector와 후보를 게시하며 실패 시 소유한 bytes만 CAS 복원한다. 보고서 값·멤버십·threshold·후보의 behavioral family 동일성을 확인한다.

정규 cron 경로 8개 검증은 PASS다. 설치 일정은 05:35 장후 최종화, 07:35 PREOPEN, 07:55 Main 기동이며 미래 실행 성공이나 PID 소비를 뜻하지 않는다.

00:38:00 native Main은 `5cffbc22a`에서 `succeeded`·exit 0으로 종료했고 final strict PASS를 기록했다. 보고서 값/정책 generation을 보존한 서식 압축과 `HoldingProfitExitSourceContractRepair`를 포함하는 실제 생성 task 비교로 앞선 두 결함이 해결됐다. 당시 controller와 tuning은 하류 작업 중이므로 전체 DONE이나 I/O 배포로 기록하지 않았다. 배포 script의 실제 거부 시험은 이전 worker 존재 시 selector/current/future bytes 모두 불변임을 확인했다. 프로세스 gate는 직전 릴리스 외에 모든 과거 release root의 잔류 owner도 확인한다.

## 남은 수용

기존 `DirectFamilyPreopenPolicyHandoff`는 정확 적용일 정책·release binding·prepared 검증과 다음 실제 PID/start/cwd 소비를 맡는다. `NonfixedDispatchReadinessReview1012`는 Sentinel 정규 3회 DONE/freshness·전체 분모·RSS/I/O를, `AuxiliaryCircuitRecoveryRepair1012`는 같은 정상 attempt의 지연·원 5초·필수 저장과 guard를 맡는다. 미래 일정과 원 Acceptance/History를 실제 다음 checklist로 인계하며, 준비 결과를 주문 성공이나 비용 후 수익 개선으로 표시하지 않는다.

## 실제 배포

- 선행 Main은 00:38:00 성공, tuning은 00:42:11 성공, controller는 00:48:28 whole-chain DONE·strict PASS다. 기존 `5cffbc22a`의 wrapper와 PREOPEN 준비 프로세스 종료 및 `prepared_verified`를 확인했다. 배포 직전 native whole-chain 재검증도 issues 0이다.
- 10/14 00:56:15 선택 기록의 실제 I/O 릴리스는 `373d5f10f3aecf2c31e5a6b8864080e6760c2263`, root는 `/home/ubuntu/KORStockScan-runtime-releases/main-io-postclose-20261013-373d5f10f`다. 부모의 장후 수리와 원 I/O 13개 파일을 함께 보존했다.
- 현재 활성 pointer는 byte 불변이다. 원 10/13 machine/auxiliary를 native publisher로 10/14 후보 `316f76178f645174b14f571164a1832eed454dcd694850c9b6b4ed35c00ce001`에 결속했고, 전체 behavioral family 동일성 및 auxiliary 128 scopes PASS를 확인했다. 당일 PREOPEN 미실행·미활성 상태에서 실제 10/14 code handoff를 사용했다. 새 Main은 시작하지 않았으며 `actual_pid_consumed=false`다.
- `selection-published.json`, `predecessor-native-closure.json`, `active-code-handoff.json`, `future-auxiliary-readiness.json`이 실제 전환 증거다. 앞선 정상 controller/checklist/summary/prepared index는 `predeployment-snapshots/`에 보존했다.
- 프로세스 inventory에서 독립 `korstockscan-gunicorn.service`의 기존 10/10 실행본을 확인했다. kernel cgroup·launcher·unit WorkingDirectory를 확인하고 해당 웹 owner를 유지했다. 이 배포는 Main과 선택된 장후/정규 cron 코드의 전환이며 웹 unit 재배포나 재시작을 포함하지 않는다. 전체 서비스의 동일 release 적용을 주장하지 않는다.
- 00:58:00 변경된 delay 코드 계약의 native 재발행을 원 source/publication 10/13으로 시작했다. 새 release의 summary/consumer/controller/prepared가 끝나기 전에는 기존 준비 receipt를 새 코드의 PASS로 사용하지 않는다.
- [10/14 체크리스트](../checklists/2026-10-14-stage2-todo-checklist.md)에 원 Acceptance·History와 두 자연 수용 owner를 이전했다. 기존 AUTO bytes를 보존했으며 print-only parser는 24개, 연결된 세 stable ID는 대상일 owner 각각 1개다. 외부 Project/Calendar sync는 실행하지 않았다.

## 잔여 비용과 증거 경계

기존 native controller PID 3639584의 00:47경 누적 관측은 논리 읽기 70,105,178,312 bytes·물리 읽기 55,475,720,192 bytes였다. 이는 현재 계약을 전체 검증하는 장후 프로세스의 누적 값이며 개별 함수 비용, Main 비용 또는 새 I/O 코드의 성능으로 환산하지 않는다. 이번 observer 재사용은 준비·최종화·PREOPEN의 full 검증을 단축하지 않는다. Native full 검증의 잔여 비용과 다음 정규 Main/Sentinel의 자연 성능은 분리한다.

## 배포 후 최종 기동 준비 검증

- 새 릴리스의 native `pre_submit_delay`는 01:04:06 `succeeded`·exit 0·issues 0, Main AI consumer 갱신은 exit 0이다. 기존과 새 delay 정책의 실제 값·셀 참조·원천·적용일은 동일하다. 바뀐 필드는 `code_contract_sha256`, `policy_sha256`, `report_sha256`뿐이며 `delay-policy-preservation.json`에 기록했다.
- `summary_handoff`는 01:08:46 성공했고 whole-chain controller는 01:14:16 `done`·strict `pass`·blocked reasons 0이다. Main 원 장후 계산은 부모 `5cffbc22a`에서 성공했으며, 배포 후 필요한 delay와 하류 인계만 `373d5f10f`에서 갱신했다. 전체 wrapper 재계산은 하지 않았다.
- 10/14용 새 prepared receipt는 01:16:47 생성됐으며 controller wrapper의 최종 `[DONE]`을 확인했다. 이후 선택된 릴리스와 native custody 환경에서 `verify_prepared('2026-10-14', require_today=True)` 기본 full 검증을 실행했다. **113.319초, `status=pass`, `validation_scope=current_full_contract`, findings 0**이다. Receipt·controller·selector hash와 commit 결속도 재확인했다. 증거는 [최종 검증](../../tmp/io-postclose-deployment-20261013/final-readiness.json)과 [완료 기록](../../tmp/io-postclose-deployment-20261013/completion.json)이다.
- 정규 cron 8개와 10/14 finalize/PREOPEN/start의 선택 root·날짜·cwd를 확인했다. 01:21:39 재점검에서 활성 정책 pointer는 배포 전과 동일하며 Main/tmux bot, `restart.flag`, operator startup hold는 없다. 실행 코드 경로 `src/deploy/config/.github`의 변경 잔여도 없다. 공유 data/docs/logs/tmp mount의 Git 표시는 코드 변경으로 해석하지 않는다.
- **배포와 현재 시점 기동 준비 검증은 완료**다. 05:35 최종화, 07:35 PREOPEN 활성화, 07:55 Main 정규 기동과 실제 PID 소비는 아직 미래 실행이다. `actual_pid_consumed=false`를 유지하며 세 기존 owner가 해당 실행·정규 Sentinel 3회·같은 Main attempt의 자연 수용을 확인한다. 준비 봉인 뒤 체크리스트는 변경하지 않았다. 비용 후 수익·실주문 성공·자연 I/O 개선은 미관측이다.
