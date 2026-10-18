# Main 정책 로딩 확인 후 종료 — 구현 검토 2026-10-18

사용자 승인 범위는 계획 보완·구현·코드리뷰·수정·재리뷰다. [보완안](../proposals/main-policy-load-and-exit-validation-plan-2026-10-18.md)의 P0~P4를 격리 작업본에 구현했다. 실제 준비 세대를 사용하는 불변 후보 실행(P5), 배포·운영 Main 재기동(P6)은 수행하지 않았다. 선택본900의 준비 검증과 시험 fixture의 실제 loader 실행을 구별한다.

## 코드와 실행 경계

- 작업본: `/home/ubuntu/KORStockScan-worktrees/main-policy-load-exit-20261018`, branch `feat/main-policy-load-exit-20261018`, 부모 `7c241ea21619ce3153f1a338f1b846b0313a894f`.
- 조회한 선택본: `900234d791b0bf31797cd4e823d0ae40296f790b`, `/home/ubuntu/KORStockScan-runtime-releases/quantity-broker-cost-monitor-20261018-900234d79`. 선택·정책·운영 PID를 변경하지 않았다.
- 모듈 위치: 실행 조율은 `src/engine/automation`, 공통 로딩·환경·격리는 `src/engine/infrastructure`에 둔다. `src/engine` root에 새 모듈을 추가하지 않는다.
- 정상 운영은 기존 delay·trailing 준비 시점만 공통 함수로 옮기고 나머지10개 consumer의 기존 지연 로딩을 유지한다. 검증 모드만 같은 native 함수의 adapter로12개를 확인한다. 손절·슬롯·수량·manual/retirement·주문 안전 기준은 변경하지 않는다.
- `bot_main.py --validate-startup`은 DB·Telegram·엔진·휴장일 처리의 부작용 있는 import 전에 분기한다. 선택된 코드에서 `validate-startup YYYY-MM-DD`를 수동1회 실행하며 cron·supervisor loop를 만들지 않는다.

## 리뷰에서 수정한 결함

| 결함 | 수정과 종결 근거 |
| --- | --- |
| 정상 Main의 모든 consumer를 처음부터 로딩하면 기존 lifecycle·실패 시점이 바뀜 | live 초기2개만 유지하고 나머지10개는 `deferred`. 검증 분기는 필수12개 exact-set equality·실제 object/scope/source digest를 요구 |
| delay 실패가 준비 cache에 남으면 다음 요청에서 disabled로 오인 가능 | 성공 마지막에만 cache 발행, receipt 실패 시 cache 해제. root/target/원천 내용의 변경과 재시도 회귀 |
| 미래 split 내용 검증이 현재 실행 허용으로 이어질 수 있음 | 내용 로딩과 실행 권한을 분리하고 검증 결과 `execution_authority=false`. 일반 경로의 실제 날짜·operator 유효기간 검사를 유지 |
| quantity·holding import가 broker/logger 등 초기화를 끌고 옴 | 실제 비용/용량·offline 품질 함수 사용 시점에만 import. 공통 정책 파싱은 외부 통신·운영 mkdir 없이 실행 |
| launcher env와 별도 검증 env의 우선순위 불일치, shell/interpreter hook | 기존 shell fragment를 공통 함수로 이동하고 실제 Bash 결과를 대조. 검증 입력은 허용 namespace의 literal assignment만 수용하고 ambient hook을 제거, child `-I` 실행 |
| exit0·불완전 consumer·잘못된 정책·권한 필드를 PASS로 오인 | parent가 schema·필수 consumer·policy hash·child PID/start ticks·격리 신원·authority false·종료·보호 원천을 독립 대조 |
| 원천·env·코드·selector의 실행 중 변경 | 원문 신원과 hash를 고정하고 env 구성 전후·child·최종 native 검증/HEAD binding 후 다시 대조. 변경 run은 실패로 보존 |
| 최신 준비 manifest의900 SHA와 원 정책7f 코드 출처 혼동 | 기존 발행 selected code-handoff를 native 검증해 원래7f 계보를 보존. 당시 `selected_paths`와 현재 명시 확장을 별도 검증 |
| 새 공통 loader가 frozen delay code inventory에서 누락 | `CONTRACT_PATHS`에 명시 추가하고 원7f/bd576 계약에 exact reviewed 확장 SHA를 등록. 원 digest는 보존하며 미등록 경로·변조 bytes를 거부 |
| 격리 child의 기존 native code guard가 Git subprocess/운영 인계를 요구 | parent가 native origin·exact source delta를 검증하고 child가 요청·원천·정책·실제 OS 격리·Git HEAD를 다시 결속하는 검증 전용 context 사용. 일반 운영 guard는 유지하며 인계 영수증을 발행하지 않음 |

위 수정 후 담당자 교차 리뷰와 별도 독립 리뷰에서 미해결 in-scope finding은0건이다. native prompt·split·날짜·수량 import와 공통 loader lifecycle, parent의 원천/terminal, 최종 code context·origin·확장 inventory를 다시 검토했다.

## 격리의 실제 보장과 제한

실제 호스트에서 user/mount/network namespace는 uid_map 권한 거부로 사용할 수 없었다. 비특권 Linux Landlock ABI8과 seccomp를 사용하며, 사용할 수 없으면 실패한다. run directory 밖 쓰기·network/process 생성·운영 lock·metadata/process 제어를 차단하고 상속 FD를 닫는다. Python audit와 잡힌 PermissionError도 기록해 애플리케이션이 예외를 삼켜도 실패한다. parent는 자신이 만든 child process group만 정리한다.

이는 검토한 애플리케이션 코드의 부작용 제한이다. 임의 적대적 native 코드를 실행하는 보안 환경으로 주장하지 않는다. native syscall을 직접 호출하고 errno를 완전히 숨기는 코드는 Python 시도 기록 범위 밖이지만 실제 쓰기는 커널 경계에서 차단한다. 설계 근거는 [Landlock](https://docs.kernel.org/userspace-api/landlock.html), [seccomp filter](https://docs.kernel.org/userspace-api/seccomp_filter.html)와 호스트 syscall 정의다.

## 검증 증거와 판정 범위

최종 명령·결과는 `/home/ubuntu/KORStockScan/tmp/main-policy-load-exit-implementation-20261018/`에 보존한다. 서로 겹치지 않는 최종 두 실행은 **3,395 passed**다. 이전 실행과 반복 실행 수를 합산하지 않는다.

| 검증 | 최종 결과 / 로그 |
| --- | --- |
| shared/native loader·prompt·delay·split·allocator·launcher/router·prepared/intraday handoff·위치 gate16개 모듈 | 3,302 passed, `final-native-launcher-regression.txt` |
| context·OS 격리·Bash env 동등성·parent transaction4개 모듈 | 93 passed, `final-parent-context-regression.txt` |
| 변경 Python30개 compile·shell3개 `bash -n`·`git diff --check` | 통과 |
| 문서 링크/anchor·print-only parser | 46개 경로/anchor 통과, backlog23개·현재 기술 owner1개 |

두 실행은 프로젝트 `.venv/bin/python -m pytest -q`로 수행했다. 첫 실행은 `test_main_policy_loading`, `test_main_prompt_policy_loading`, `test_main_policy_native_child`, `test_pre_submit_delay_tuning`, `test_entry_split_order_plan`, `test_scalping_position_sizing_allocator`, `test_entry_setup_live_policy`, `test_entry_setup_scalping_rollout`, `test_holding_prompt_live_policy`, `test_runtime_release_router`, `test_threshold_cycle_wrappers`, `test_restart_flag_race_guard`, `test_auxiliary_reader_readiness`, `test_prepared_policy_code_handoff`, `test_intraday_release_handoff`, `test_engine_location_gate`다. 두 번째는 `test_startup_validation_code_context`, `test_startup_validation_isolation`, `test_main_policy_environment`, `test_main_startup_validation`이다. 모든 파일은 `src/tests/` 아래 `.py`다.

- 실제 native producer→Main machine loader/backend→auxiliary 양성 fixture는128route를 확인하고 원 current와 PID 기록을 보존했다.
- 원문 source와 resource를 복사한 Main child가 실제 시각·대상10/19로12consumer를 확인하고 종료했다. 이 child는 loader stub 없이 native 함수를 사용한다. 변조 원천은 실패하며 금지 시도0·보호 파일 불변을 확인했다.
- 별도 parent transaction fixture는 intake/env만 단위 대체하고 실제 Main 조기 진입·OS 격리·PID/start ticks·원자적 terminal·timeout/크래시·금지 시도 실패를 검증한다. 이를 실제 운영 준비본 전체 실행으로 표시하지 않는다.
- code context 양성 시험은 실제 Git source delta와 커널 격리를 적용한 뒤 H를 처음 import하고 실제 `verify_entry_consumer_code`를 호출했다. request/정책/원천/consumer 인자 변경·잘못된 context 설치는 실패한다.
- 실제 selected900의10/19 준비본을 native `current_full_contract`로 읽기 전용 검증했다: `status=pass`, findings0, 원천10/16, `actual_pid_consumed=false`. 원문 결과는 `actual-selected-preparation-check.json`이다. 이 결과는 새 후보 코드의 P5 PASS가 아니다.

## 남은 적용 작업

`MainPolicyLoadAndExitValidation1018`은 P5 실제 준비 세대의 불변 후보 실행을 OPEN으로 유지한다. 먼저 clean candidate와 표준 공유 mount를 구성하고 source/native 계약을 검증해야 한다. 배포 단계에서는 split reader 변경에 따른 quantity monitor/research 코드 세대 영수증을 기존 producer로 현행화하고, frozen delay의 원7f 계보와 명시 확장을 인계한다. 원 정책·과거 실패/strict/controller/인계 bytes를 고쳐 쓰지 않는다.

P6 운영 PREOPEN·실제 PID 소비는 [10/19 `DirectFamilyPreopenPolicyHandoff`](../checklists/2026-10-19-stage2-todo-checklist.md)가 계속 소유한다. 검증 receipt는 항상 `runtime_effect=false`, `allowed_runtime_apply=false`, `actual_pid_consumed=false`이며 운영 health·자연 감시·주문·체결·비용 성과를 대체하지 않는다. 이번에는 선택/정책 발행·provider/API/Telegram·cron/서비스·Main 재기동·외부 문서 sync를 수행하지 않았다.
