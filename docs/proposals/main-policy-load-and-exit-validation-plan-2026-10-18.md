# Main 정책 로딩 확인 후 종료 보완안 — 2026-10-18

## 1. 결정과 완료 범위

휴장일에도 다음 거래일의 준비 정책으로 **실제 Main과 같은 정책 로더를 별도 프로세스에서 실행하고, 로딩 결과를 대조한 뒤 감시·외부 통신·주문 초기화 전에 종료**할 수 있도록 보완한다. 준비본 생성만 확인하고 거래일 당일까지 로딩 결함 발견을 미루는 공백을 없앤다.

원 작성 시에는 계획 단계였고, 후속 사용자 지시로 **계획 리뷰·보완 및 구현·코드리뷰·수정·재리뷰**를 진행했다. 아래 진입점과 검증 경로는 격리 작업본에 구현했다. §9 기록 시점에는 선택900에 아직 배포하지 않았으며, 운영 Main 기동·정책 활성화·주문을 실행하지 않았다. 해당 구현 결과와 잔여 경계는 §9, 최신 실행 승인과 결과는 §12를 따른다.

검토 기준은 [Plan Rebase](../plan-korStockScanPerformanceOptimization.rebase.md) §1–§8과 [10/18 실행 소유자](../checklists/2026-10-18-stage2-todo-checklist.md)다. 계획 작성 시 조회 기준 workspace는 `7c241ea21619ce3153f1a338f1b846b0313a894f`, 선택 릴리스는 `900234d791b0bf31797cd4e823d0ae40296f790b`이며 selector는 `actual_pid_consumed=false`, 다음 적용일 `2026-10-19`를 기록한다. 이번 예시는 원천일10/16·실행일10/18·정책 대상일10/19를 구분한다. 구현 착수 시 selector·준비본·현재 코드와 source hashes를 다시 고정한다.

기술 구현은 `MainPolicyLoadAndExitValidation1018`이 소유한다. 실제 거래일 PREOPEN 활성화·운영 PID 확인은 [10/19 `DirectFamilyPreopenPolicyHandoff`](../checklists/2026-10-19-stage2-todo-checklist.md)의 기존 Acceptance를 유지한다. 자연 주문·체결·비용 성과를 이번 검증의 종결 조건으로 추가하지 않는다.

## 2. 확인한 현재 경로와 결손

| 현재 producer / consumer | 코드에서 확인한 동작 | 보완할 지점 |
| --- | --- | --- |
| [PREOPEN wrapper](../../deploy/run_threshold_cycle_preopen.sh) | `next_preopen_readiness --verify --require-today` 후 날짜별 publisher/activator·bootstrap·entry/holding env를 기록한다. | 운영 활성화의 당일 계약을 보존하고, 사전 검증을 이 운영 명령의 우회 실행으로 구현하지 않는다. |
| [준비본 owner](../../src/engine/automation/next_preopen_readiness.py) `prepare`, `verify_prepared` | 다음 적용일을 결정하고 격리 `output_dir`의 bootstrap/env/verify 및 원천·선택본 결속 영수증을 만든다. | 기존 준비를 재사용한다. 검증 시작·끝에 읽기 전용으로 재검증한다. |
| [bootstrap 검증](../../src/engine/automation/runtime_policy_bootstrap.py) `verify_bootstrap` | `output_dir`와 `pid` 동시 사용은 `prepared_bootstrap_cannot_claim_pid`로 거부한다. | 이 거부를 해제하지 않는다. 준비본 검증은 `write=False`, PID 인자 없이 수행하고 검증용 child 로딩 증명은 별도 schema로 남긴다. |
| [Main launcher](../../src/run_bot.sh) | 오늘 날짜를 산출하고 당일 PREOPEN 성공·bootstrap을 검증한 뒤 env를 읽고 실제 child PID를 기록한다. 종료 후 재시작 loop가 있다. | 날짜·env 구성의 공통 부분만 재사용한다. 로딩 검증은 운영 loop·PID 등록·자동 재기동으로 들어가지 않는다. |
| [Main entrypoint](../../src/bot_main.py) | DB 초기화·보고서·Telegram·휴장일 확인 뒤, 영업일에만 `kiwoom_sniper_v2`를 import/시작한다. | 검증 분기를 부작용 있는 import와 main body보다 앞에 둔다. 휴장일 일반 기동 성공만으로 로딩 검증을 통과시키지 않는다. |
| [엔진 시작](../../src/engine/kiwoom_sniper_v2.py) `run_sniper` | 지연 정책 준비와 sink 설정·`recover_pending=True`가 먼저 있고, 이후 token·계좌/SELL 복구·WS·구독 초기화가 이어진다. 모듈 전역에도 DB/executor 생성이 있다. | 함수를 실행한 뒤 중간에 멈추는 방식 대신, 정책 로딩을 부작용 없는 공통 함수로 추출한다. |
| [지연 로더](../../src/engine/scalping/pre_submit_delay_tuning.py) `prepare_runtime_policy` | `now`에서 정책 날짜를 정하고 모듈 cache를 준비한다. 실패가 `preparation_invalid` 반환으로 끝날 수 있다. | 대상 정책일과 실제 시각을 분리하고, 명시 실패를 상위 PASS로 삼키지 않는다. |
| [손절 로더](../../src/engine/scalping/main_stop_policy.py) `preload`, `record_loaded_policy` | 메모리 로딩과 운영 PID 영수증 쓰기가 분리돼 있다. | 같은 `preload` 결과를 검증하되 운영 `record_loaded_policy` 경로에는 기록하지 않는다. |
| [trailing 로더](../../src/engine/scalping/trailing_situation_policy.py) `prepare_runtime` | env·parent SHA·target date로 실제 prepared object를 만든다. | 동일 object의 policy/parent/적용 scope를 대조한다. 단순 env 문자열 일치로 대체하지 않는다. |

`is_test_mode=True`, 가짜 영업일, 운영 날짜 변경, pause.flag만으로 실행을 제한하는 방식은 사용하지 않는다. pause는 SELL·계좌 대사·재시도를 모두 차단하는 정책 로딩 전용 경계가 아니다.

## 3. 목표 흐름과 실제 확인 범위

```text
선택본·준비본·원천·operator 설정 신원 고정
  -> 격리 입력/출력·외부 통신 차단 확인
  -> 다음 거래일 PREOPEN 결과와 같은 env/정책 view 구성
  -> 선택본 또는 code-handoff 검증 후보의 Main entrypoint를 검증 인자로 한 번 실행
  -> 공통 정책 로더 호출·필수 consumer별 실제 로딩 결과 기록
  -> parent가 child PID/start ticks·결과·종료·보호 파일 불변 대조
  -> 검증 전용 최종 영수증 발행, 종료
```

성공이 증명하는 것은 **정확한 준비 세대가 선택된 코드의 정책 로더에서 지정 대상일로 로딩됐고, 검증 child가 종료됐다는 사실**이다. 운영 PID 실행·네트워크 접속·감시·주문·전체 시스템 health 정상은 이 결과로 주장하지 않는다. 상류 source gap은 그대로 남기되, native 계약이 승인한 carry/OFF/not-applicable은 그 사유와 기대값을 대조해 정상 분류한다.

## 4. 최소 구현 구조

### 4.1 공통 로더와 조기 종료 분기

- orchestrator는 기존 역할 패키지 `src/engine/automation`에 둔다. 신설이 필요하면 `main_startup_validation.py`가 parent 실행·격리·영수증을 소유한다.
- 실행/검증 공통 정책 로딩 함수는 `src/engine/infrastructure/main_policy_loading.py`에 둔다. 이는 계획상 경로다. 구현 전 인접 모듈과 import graph를 확인하고 기존 적합한 owner가 있으면 그곳을 확장한다. `src/engine` root에는 새 모듈을 만들지 않는다.
- 정상 Main과 검증 분기는 같은 함수·consumer adapter·env 구성·typed parsing·policy hash·code-handoff 검증을 사용한다. 검증용 정책 해석기를 복제하지 않는다. 정상 기동은 기존 초기 delay·trailing 두 로딩의 시점을 유지하며 나머지10개는 기존 실제 소비 시점까지 `deferred`다. 검증 기동은 동일 native 함수의 adapter를 통해12개를 확인한 뒤 종료한다. 정상 기동을12개 eager 로딩으로 바꾸거나 `deferred`를 로딩 성공으로 표시하지 않는다.
- `src/bot_main.py`의 인자 판정은 DB/Telegram/엔진/관측 sink import 전에 실행한다. 검증 child가 필요한 공통 로더만 import하도록 전역 DB/executor·상태 writer와 의존성을 분리한다.
- `src/run_bot.sh`의 operator/native-custody/retirement/AI-context 적용 순서와 공통 함수의 결과가 동일한지 검증한다. 기존 `entry_setup_live_policy.load_preopen_runtime_env` helper만 보고 launcher와 같다고 가정하지 않는다. env precedence를 먼저 실제 코드로 고정한다.
- 공통 로더에는 정책 대상일·실제 시각·data root·env와 검증 문맥을 전달한다. canonical 원천은 실제 경로에서 읽고 native 경로·custody 검사와 고정 hash로 결속한다. 미래 정책/준비 view는 native adapter에 명시해 옛 `current.json` 소비를 성공으로 오인하지 않는다. 봉인 문서의 절대 경로·해시를 고쳐 쓰지 않는다. env 사본과 출력은 private run directory에 두며 OS 경계는 그 밖의 쓰기를 차단한다. 읽기 전체를 경로 allowlist나 별도 mount로 제한하는 구현은 아니다.
- entry/auxiliary/지연/초기수량·split/holding/stop/trailing 등 실제 bootstrap의 활성 consumer를 전수 분류한다. consumer ID·모듈/함수·입력 변수명·타입·단위·날짜·parent/current pointer·cache key·로딩 결과를 P0 표로 확정한다. 고정 숫자나 옛 family 목록으로 coverage를 대신하지 않는다. 퇴역 위젯/에피소드 consumer는 실행 대상에 넣지 않는다.
- 주문 이후에만 의미가 생기는 position pin·잔량·계좌·quote·추론은 `requires_live_context`로 명시한다. 그 consumer가 정책을 읽는 부분은 공통 로딩으로 검증하고, 실시간 판단을 재현했다고 표시하지 않는다. 필요한 로딩 자체를 하지 못하면 `unverified`이며 전체 로딩 PASS 대상에서 임의 제외하지 않는다.

### 4.2 날짜·future policy·env 해석

`target_date`는 적용할 정책의 거래일이고 `observed_at_kst`는 실제 검증 시각이다. target은 준비본·선택본·공식 거래일 달력과 결속한다. 날짜 인자를 생략해 오늘 날짜로 대체하거나 프로세스 전체 clock을 미래로 바꾸지 않는다. 시세 TTL·source freshness·operator 유효기간 검사에는 실제 시각을 사용한다. 미래 유효 정책은 로딩 가능성만 검증하며 지금 활성화된 것으로 취급하지 않는다. 현재 validator에서 내용 해석과 현재 시각의 활성화 권한 검사가 섞인 부분은 공통 내용 검증과 실행 허용 검사를 분리한다. 검증은 내용·provenance·effective-date 정합성을 모두 확인하고 실행 권한은 false로 둔다. 운영 경로는 두 검사를 계속 모두 통과해야 하며 미래 시각을 `now`로 넘겨 권한 검사를 통과시키지 않는다.

준비본 env와 미래 활성화 이후 env가 항상 같다고 가정하지 않는다. staged Main/auxiliary candidate와 현재 포인터가 다른 경우 native publisher/activator의 동일 변환을 격리 사본에 적용해 expected activation view를 만든다. 이를 위해 계산/검증과 active pointer 쓰기를 분리하고 native source/code/safety 검증은 공유한다. 구현이 현재 포인터를 그대로 읽어 옛 정책으로 성공하면 실패다. 변환 결과와 봉인된 준비본 사이 차이는 항목별 근거를 기록하고, 설명되지 않는 차이가 있으면 검증을 중단한다. live `--require-today`와 실제 활성화 시각 검사는 유지한다.

fresh interpreter에서 cache를 시작하고 key에 target date·정확한 source/policy generation이 포함되는지 확인한다. 같은 프로세스의 전날 cache, 부모의 오염 env 또는 준비본 경로만 바꿔 붙인 정책을 재사용하지 않는다. env는 신뢰된 준비본에서 허용한 assignment만 해석하며 임의 shell command를 실행하지 않는다.

### 4.3 부작용 차단·수명

canonical data·selected source·운영 정책/current·owner journal·수동 설정·PREOPEN/strict/controller·실패 영수증은 읽기 전용으로 둔다. 검증용 env/pointer view·로그·영수증만 run별 별도 경로에 쓴다. 원 준비본도 덮어쓰지 않는다. 운영 selector PID receipt·bootstrap PID verification·stop PID receipt·heartbeat·observer 최신 세대는 갱신하지 않는다.

OS 수준의 파일 쓰기 제한·외부 통신 차단과 Python 부작용 경계 시험을 함께 적용한다. 실제 환경에서 user/mount/network namespace는 uid_map 권한 거부로 사용할 수 없었다. 대체 구현은 비특권 Linux Landlock(현재 ABI8)과 seccomp이며, run directory 밖 쓰기·network/process 생성·운영 lock/metadata/process 제어를 막는다. Python audit와 거부 예외 기록도 함께 확인한다. 격리를 설치할 수 없으면 `isolation_unavailable`로 실패하며 패키지 설치나 일반 Main 실행으로 대체하지 않는다. 이는 검토된 애플리케이션 코드의 부작용 제한이며 임의 적대적 native 코드 실행 환경을 제공하지 않는다.

API token 발급·계좌·REST/WS REG/REMOVE·provider·Telegram·scheduler·DB migration·주문·SELL 복구·관측 sink/recover_pending 진입 시도는 검증 실패다. 외부 통신이 OS에서 거부됐다는 이유로 시도 자체를 성공으로 간주하지 않는다. 상속된 연결 FD와 운영 제어 채널도 child에 넘기지 않는다.

parent는 child PID/start ticks·run ID·기대 execution root/commit과 동일성을 확인한다. 후보 모드에서도 부모의 selected identity는 별도로 고정한다. 별도 검증 process group만 소유하고 제한 시간 초과 시 그 그룹을 정리한다. 운영 Main·tmux·cron·다른 검증 run에는 신호를 보내지 않는다. 종료 후 생존 worker가 없어야 최종 PASS다. 기존 Main supervisor의 재시작 loop는 사용하지 않는다. 제한 시간은 최초 로딩 실측으로 확정하며 원 runtime 주문 deadline·source TTL을 늘리지 않는다.

### 4.4 제안 진입점과 결과

후보 구현의 진입점은 `bash deploy/run_runtime_release.sh validate-startup 2026-10-19`다. 현재 선택900은 이 새 operation을 지원하지 않는다. 선택본으로 배포한 뒤 사용할 명령이며 대상일은 필수다. router는 선택을 한 번 고정하고 검증 orchestrator로 넘기며, `--print-plan`은 실행하지 않는 기존 의미를 유지한다. child는 선택본 `src/bot_main.py --validate-startup ...`의 조기 분기로 실행한다. 세부 내부 인자는 P0에서 확정하고 일반 운영 launcher에는 target-date 우회 옵션을 열지 않는다.

배포 전 후보 검증은 별도 basis인 `reviewed_candidate_handoff`로 기록한다. 아직 기능이 없는 현재 선택900을 새 후보로 바꿔 적거나 검증을 위해 selector를 먼저 발행하지 않는다. 후보 자체 orchestrator가 기존 native candidate/source-code handoff 검증을 통과한 exact root/commit·부모 선택본·준비 세대를 결속한 뒤 후보 Main child를 실행한다. handoff 부재·후보 dirty·준비본과 code 계약 불일치는 실패다. 선택본 검증과 후보 검증 모두 같은 공통 로더·격리·terminal 계약을 사용하되 실제 실행한 code root/commit은 별도 필드로 남긴다.

검증은 수동 1회 호출부터 수용한다. cron 신설이나 장시간 상주 감시기를 추가하지 않는다. 최초 완료 뒤 배포·후속 재기동의 정규 preflight에 연결할지는 별도 구현 변경으로 운영 문서와 함께 검토한다. 이미 승인된 최초 정책에 추가 경제성/자연소비 승인을 요구하지 않는다.

출력은 `data/report/main_startup_validation/<target_date>/<run_id>/`의 request, child receipt, parent final receipt와 원 로그다. 임시 파일 쓰기·flush/fsync·원자적 rename 후 terminal을 발행한다. 과거 시도는 보존하고 exact run의 `final.json`과 원천 hash로 판단한다. `latest` 포인터는 만들지 않는다.

| 필드 집합 | 요구값 / 의미 |
| --- | --- |
| `schema`, `run_id`, `target_date`, `observed_at_kst` | `main_policy_load_exit_validation_v1`, 실행 신원과 실제 시각·정책일 분리 |
| `selected_release_root`, `selected_release_commit` | 시작/종료 시 동일한 선택본. selector hash는 `request.source_hashes`의 실제 selector 경로에 보존 |
| `execution_release_root`, `execution_release_commit`, `release_binding_basis`, `candidate_handoff_sha256` | 실제 child 코드와 `selected` 또는 `reviewed_candidate_handoff`. 후보를 운영 선택본으로 오인하지 않음 |
| `prepared_receipt_sha256`, `input_manifest_sha256`, `expected_env_sha256` | 준비본·원천·operator/retirement·source/code·활성화 view와 결속 |
| `validation_pid`, `validation_start_ticks` | 실제 실행한 검증 child 신원. child 코드 hash는 `request.source_hashes`의 `src/bot_main.py` 경로에 보존하며 일반 `pid_consumed` 영수증과 구별 |
| `consumer_results` | consumer별 expected/actual policy·parent·loaded-object digest, scope, 날짜, native 상태, 실패 사유 |
| `load_check_passed`, `child_exit_code`, `child_terminated`, `protected_sources_unchanged` | 로딩 결과와 종료·보호 경계 모두 확인 |
| `status`, `failure_phase`, `findings` | exact run의 `passed` / `failed`. child receipt 없이 exit0, partial, timeout은 PASS 불가 |
| `runtime_effect`, `allowed_runtime_apply`, `actual_pid_consumed` | 모두 `false`. 검증 child 존재와 운영 Main 소비를 혼동하지 않는다. |

비밀 env/token은 원문 출력하지 않는다. 검증값은 allowlist된 정책 필드·digest만 기록한다. 필수 consumer의 `preparation_invalid`, 누락·scope 미완료·의도하지 않은 fallback을 상위 PASS로 바꾸지 않는다. 기대된 disabled/carry/parent-only는 exact native 사유·policy/env 일치가 확인된 경우에만 허용한다.

## 5. 구현 순서와 각 단계 종결 조건

| 순서 | 구현 사항 | 종결 조건 |
| --- | --- | --- |
| P0 | 선택본 기준 producer→bootstrap→env precedence→실제 loader/cache/recording callsite 목록 작성. 격리 기능 가용성, 날짜·future/current 차이 조사 | 활성 consumer 누락·추정 변수·미검증 부작용 경로0. 불가능한 격리는 blocker로 명시하고 일반 기동으로 대체하지 않음 |
| P1 | 공통 env/정책 로더 추출, live callsite 연결, 날짜 문맥 분리 | 기존 운영 경로와 같은 입력의 object/policy/scope digest 동일. 기존 current-code·operator·retirement·hard safety 의미 불변 |
| P2 | 격리 future activation view 및 Main 조기 검증 분기 | 휴장일/평일 모두 실제 공통 로더까지 실행. DB/Telegram/token/worker 시작 이전 종료, 원본 포인터 불변 |
| P3 | 선택 root를 고정한 parent 1회 실행·child 신원/종료·원자적 terminal | exact PID/start ticks와 child 결과 결속. timeout·크래시·부분 쓰기·동시 변경을 실패로 보존 |
| P4 | consumer coverage·변조/실패·운영 동등성 표적 회귀, 코드리뷰→수정→재리뷰 | 아래 수용 행렬 통과. 정상/실패의 실제 producer 출력부터 parent terminal까지 비어 있지 않은 end-to-end fixture 확보 |
| P5 | 검증된 불변 후보의 실제10/19 준비 세대로 사전 로딩 후 종료 1회 | 실행 권한 확보 후 실제 코드·원천의 child 로딩/종료 receipt, 운영 보호 hash 불변·외부 호출0 확인. 운영 selector를 옮기지 않고 후보임을 표시 |
| P6 | 허용된 배포 시 선택본/세대 결속 확인, 거래일 재확인 계약 인계 | 변경 없으면 사전 결과를 재사용하고 당일 활성화·운영 PID만 확인. 변경 있으면 영향 범위의 사전 검증을 다시 수행하고 원 실패/이력을 보존 |

P5 실행·P6 배포는 이 문서 작성의 실행 범위가 아니다. 사용자 최신 지시에 따라 **P5 불변 후보 검증은 모든 연구작업 종료 뒤에도 별도 실행 지시를 받은 후** 진행한다. 연구 종결을 P5 실행 권한으로 간주하지 않는다. 이후 사용자의 `57a4659f4` 통합 배포본 준비 지시에 따라 코드 통합·오프라인 회귀·후보 디렉터리 구성은 먼저 진행한다. 실제 준비 세대의 P5 child 검증은 모든 연구작업 종료와 사용자의 별도 실행 지시 전까지 실행하지 않으며 기존 P0~P4 코드 검증을 P5 완료로 바꾸지 않는다. 연구 종료 시 실제 통합 코드·원천·정책 세대를 다시 고정한다. 운영 release source/hash에 공통 로더가 새로 들어가면 기존 code-handoff/native parity·family contract 절차로 인계하며, 원천 코드 해시를 검증에서 제외해 통과시키지 않는다.

## 6. 필수 수용 행렬

| 시험 | 기대 결과 |
| --- | --- |
| 휴장일10/18 → 정책10/19, source10/16 | 실제 로더 완료·해당 날짜 정책/세대 일치·정상 종료. 오늘 정책으로 fallback 없음 |
| 평일의 동일 검증 명령 | 동일하게 로딩 후 종료. 장이 열렸다는 이유로 감시/주문 시작 없음 |
| 현재 포인터와 미래 staged 정책이 다름 | 미래 활성화 view에 결속한 expected object와 일치. 옛 current 로딩을 PASS로 오인하지 않음 |
| operator override·dated override·custody·retirement가 함께 존재 | 실제 launcher precedence와 동일. 기존 손절 기준·장기 슬롯·수량·수동관리/퇴역 설정 변경0 |
| cold cache·전날 cache·다른 source generation | fresh child에서는 동일 해석. target/generation 혼동 및 오염 env는 거부 |
| required source/준비본/code-handoff·policy hash 누락/변조 | native 검증 실패와 consumer ID/phase 기록. 날짜·해시를 새로 꾸며 재시도하지 않음 |
| 정상 carry/OFF/parent-only와 로딩 실패 | 기대된 상태는 근거 대조 후 수용. 실패·미분류 fallback·미검증 consumer는 실패 |
| loader가 예외 대신 invalid 상태를 반환 | 전체 실패. import 성공·env 일치·child exit0만으로 PASS 없음 |
| 계좌/WS/provider/Telegram/DB/sink/recovery 진입 시도 | 실행 차단·전체 실패, 운영 파일 불변 |
| child timeout/강제 종료·receipt 부분 쓰기·parent 중단 | run 실패/미완료 보존. 운영 PID/다른 run 불간섭, 정확한 소유 process group만 정리 |
| 실행 중 selector·원천·operator·준비본 변경, 동시 검증 | 변경된 run은 무효. run별 출력·신원 분리, 뒤늦은 old PASS가 새 세대를 덮지 않음 |
| 사전 성공 후 배포/정책 변경, 또는 거래일로 날짜 전환 | 새 selection/target/source에 old PASS 재사용 불가. 당일 freshness는 실제 시각으로 다시 확인 |
| 정상 live 기동 회귀 | 당일 PREOPEN·정책 활성화·운영 PID receipt·native guard는 기존 의미 유지 |

실제 활성 정책의 양성 fixture가 필요하다. 빈 목록·모두 OFF·JSON 파싱만으로 전체 로딩 검증을 종결하지 않는다. 범위가 다른 정책이 정확히 대응했는지 consumer별 exact-set equality로 확인하며 missing/unexpected 목록을 보존한다.

## 7. 당일에 남기는 작업과 재사용 기준

사전 검증 후 코드·선택본·준비본·원천·operator/retirement 및 expected activation view가 같으면 기존 로딩 성공을 같은 target date에 재사용한다. 거래일 당일에 연구/후보 탐색/전체 보고서를 새로 만드는 요구를 추가하지 않는다. native 계약이 요구하는 실제 시각의 freshness·활성화 시각·현재 predecessor 확인은 수행한다. 당일 publisher가 새로 만드는 generation/시각 필드는 사전 기대값과 구분하고, 정책 의미·정확한 부모·scope·규칙값이 같다는 native 검증 없이 hash 차이를 무시하지 않는다.

당일에는 정규 PREOPEN이 활성 포인터/env를 발행하고 실제 Main이 같은 로더를 거쳐 운영 PID 영수증을 남긴다. 검증 child의 성공으로 이를 대체하거나 `actual_pid_consumed=true`로 승격하지 않는다. 준비·로딩·활성화·감시/주문 결과는 각각 기록한다. 실제 외부 수신/체결·경제성은 기존 owner가 필요한 자연 시점에 확인한다.

## 8. 변경·검증 경계와 다음 액션

후속 구현 지시에 따라 공통 loader·launcher env·검증 child·router와 표적 시험을 구현하고, [운영 문서](../runtime-release-routing.md)의 수동 검증 계약을 같은 변경 집합에 갱신했다. Plan Rebase/AGENTS/README·cron·서비스·운영 정책·현재 PID는 수정하지 않는다. 현행 동시 손절·익절 연구 문서와 checklist 내용을 보존한다.

문서는 링크/anchor·source 함수·단일 stable owner·권한/날짜/상태 구분과 print-only parser·diff check로 검증한다. 구현은 실제 native loader·OS 격리 child·실패 주입·운영 동등성 표적 회귀로 검증하며, provider·실제 보고서 재생성·외부 Project/Calendar sync는 실행하지 않는다. P0~P4의 코드 종결과 P5의 실제 준비 세대 실행·P6 운영 적용을 구별한다.

## 9. 구현·리뷰 결과와 남은 운영 경계

구현 작업본은 `/home/ubuntu/KORStockScan-worktrees/main-policy-load-exit-20261018`이다. 공통 로더는 실제 함수·typed object·policy/source hash를 사용하며 필수12개 consumer ID는 `main_policy_loading.CONSUMER_IDS`가 소유한다. bootstrap의 역사적 selected_families17개를 이 coverage로 오인하지 않는다.

| 실제 consumer | native 함수 / 확인 값 |
| --- | --- |
| typed rules | 실제 env로 생성된 `TRADING_RULES` 전체 typed 값 |
| Main machine | `reversal_evaluation_context.prepare_policy_loading` → `N.load`/`verified_evaluation` → 동일 backend configure, policy/scope/source |
| Main auxiliary | `verify_auxiliary_reader`의 registry·overlay·source compatibility |
| pre-submit delay | `prepare_runtime_policy`의 실제 prepared cache·code/source receipt |
| Main stop | `preload`·`load_bundle`·실제 memory cells, 운영 loaded-PID writer 제외 |
| mechanical / situation trailing | `runtime_policy_vector_snapshot` / `prepare_runtime`의 실제 vector·typed cells |
| initial quantity | `load_pinned_initial_quantity_policy` 또는 검증된 기존5단계 fallback |
| entry split | `_load_policy_from_env`, operator future content와 현재 실행 허용 구분 |
| holding path | `runtime_policy_from_env`의 실제 bundle / parent 상태 |
| entry / holding prompt | 같은 native resolver의 각9scope와 exact candidate·operator pin·준비 activation view |

리뷰·실제 격리 시험에서 발견한 delay cache 실패 후 disabled 오인·split 미래 실행 날짜 우회·일부 consumer 부작용 있는 import·불완전 terminal/authority 판정·env shell expansion/ambient hook·코드/원천 동시 변경을 보완했다. 환경은 기존 launcher의 원문 fragment를 공통 shell 함수로 이동하고 실제 Bash 결과를 비교했다. 검증에서는 원 env를 실행하지 않고 허용 assignment를 literal로 재구성하며 `-I` Main child를 사용한다.

선택본과 검증 후보 모두 기존 계약과 실행 코드가 다르면 parent가 native code delta를 검증한다. 기존 선택본의 인증된 준비 code-handoff가 원7f 계보를 보존하면 그 원천을 재사용하며, 최신 준비본의900 commit을 최초 원천으로 덮어쓰지 않는다. 격리 child의 source-bound code context는 parent가 검증한 exact proof를 Python hash로 다시 확인할 뿐 운영 인계·정책을 발행하지 않는다. 이 context는 실제 OS 격리 안에서만 설치할 수 있고 일반 live 경로의 기존 인계·날짜·PID 검사는 유지한다.

실제 selected900의10/19 준비본은 native `current_full_contract` PASS/findings0·source10/16·actual_pid_consumed=false를 읽기 전용으로 확인했다. 실제 원문 파일로 만든 fixture의 Main child는 실제 시각·대상10/19로12개 consumer를 검증해 금지 시도0·정상 종료했고, 원천 변조는 실패했다. 별도 genuine V6 producer→loader→backend→auxiliary 시험은128route를 확인하며 원 current와 PID 기록을 보존했다. 이는 운영 정책 세대의 실제 candidate child 실행이나 운영 PID 소비를 대신하지 않는다.

배포 시에는 새 source와 frozen delay code-handoff의 원 계보를 보존하고, split reader 변경에 따른 quantity monitor/research 코드 세대 영수증을 기존 producer가 현행화해야 한다. 원 정책·과거 영수증을 고쳐 쓰거나 전체 보고서를 무조건 재생성하지 않는다. 실제 운영 준비 세대를 사용한 P5 검증과 P6 배포/운영 PID는 해당 단계 근거를 별도로 남기며 미확인을 PASS로 바꾸지 않는다. 상세 시험·수정 근거는 [구현 검토 기록](../audits/main-policy-load-and-exit-implementation-review-2026-10-18.md)에 정리한다.

## 10. 57a4659f4 통합 배포 후보 준비

사용자 후속 지시에 따라 정책 로딩 검증 `590fccd7002082db3fbd02dd4fe3a47de5a39174`와 보유 연구 `57a4659f471044f8c8a59db53fc01b12d194333a`를 함께 포함한다. 연구 branch의 선행6개 commit을 보존하며 현재 선택900에 누적된 코드·source-control/snapshot 경로 수리를 계승한다. 다른 세션의 미완료 코드나 이후 commit을 자동 포함하지 않는다.

이번 종결은 통합 코드·리뷰·오프라인 회귀와 표준 공유 mount를 갖춘 선택 전 배포 후보 구성이다. 공통 상태 처리 코드가 frozen delay/stop/holding inventory와 교차하므로 원7f 계보와 exact reviewed source pair를 검증한다. 새 진입 연구 도우미도 검토한 코드 closure에 결속하며 원 정책 digest는 보존한다. 세대가 바뀌면 과거 code-handoff를 그대로 재사용하지 않는다.

실제 준비 정책의 child 로딩(P5)은 **다른 세션의 연구작업 종료 및 사용자의 별도 실행 지시 후** 최종 코드·원천·정책·선택본을 다시 고정하고 실행한다. 이번 준비에서는 code-handoff·정책/PREOPEN/strict/controller·quantity monitor 세대 영수증을 발행하거나 selector를 옮기지 않는다. P6 배포·Main 재기동도 수행하지 않는다. 결과와 정확한 후보 commit/root는 [통합 후보 검토](../audits/main-policy-holding-integrated-candidate-review-2026-10-18.md) 및 그 근거 manifest를 따른다.

## 11. 잔여 연구 종결 인계

현재 원천·등록 가설 범위 stop/holding 연구를 종결했다. stop 최종 격리 commit은 `eb8e18cefacad23a298fd237093732e0f0977d70`, holding 엄격 비용 후속은 별도 `3ab6916e28ee3301402c6ac8b64fbc2090f49000`이다. [stop 종결 검토](../audits/main-stop-remaining-research-closure-review-2026-10-18.md)와 [보유 계획 §17](main-all-symbol-all-market-trailing-and-replay-improvement-plan-2026-10-10.md#17-2026-10-18-현재-원천-범위-연구-종결)을 인수 근거로 삼는다. stop 고정 workload 성능 판정 `blocked`와 실제 소비 결과는 수치 정책 승인·경제 개선·운영 적용과 분리한다.

§10의 기존 통합 후보는 이 후속 commit들을 자동 포함하지 않는다. 별도로 승인된 통합 owner는 다음 후보에서 실제 포함 commit·원천·정책·code-handoff를 다시 대사해야 한다. 이번 연구는 코드 통합·실제 준비 세대 child·배포를 실행하지 않았다. **연구가 종료됐어도 P5는 사용자의 별도 실행 지시 전 보류**하며 `MainPolicyLoadAndExitValidation1018`은 해당 실행 owner로 OPEN을 유지한다. 실제10/19 PREOPEN/PID·자연 terminal/손익은 기존 owner가 계속 소유한다.

## 12. 최종 연구 통합과 P5·P6 실행 승인

사용자 최신 지시로 연구 종결 확인 후 `9d2201141aeae409fe960ff7795a1340718a7146`에 최종 stop `eb8e18cefacad23a298fd237093732e0f0977d70`과 holding 비용 `3ab6916e28ee3301402c6ac8b64fbc2090f49000`을 통합하고, 실제10/19 준비 세대의 P5 사전 로딩을 실행한 뒤 통과하면 P6 배포를 이어간다. §5·§10·§11의 별도 지시 대기는 이 승인으로 해제됐다. 이전 연구의 CPU 기준 미충족과 수치 후보 발행 차단은 유지하며 신규 grace0 정책 승인으로 바꾸지 않는다.

실행일10/18·원천10/16·대상10/19를 분리한다. 최종 clean 후보의 원 정책/code 계보·native parity·필수 소비자와 변경된 quantity/capability 세대를 검증한다. P5는 selector 이동 전 격리 child에서 실제12consumer를 로딩하고 종료·외부 부작용 차단·보호 hash를 확인한다. 통과 후 기존 native producer로 다음 정규 기동 준비를 만들고 잠금·CAS 아래 선택을 발행한다. 이전 준비본·원 정책·strict/controller·실패 시도는 별도 원문으로 보존한다.

현재 Main이 없는 비거래일이므로 강제 기동하지 않는다. P6의 선택·준비 완료와 실제10/19 PREOPEN·운영 PID·자연 fill/손익은 별도이며 후자는 기존 `DirectFamilyPreopenPolicyHandoff`가 소유한다. P5의 `actual_pid_consumed=false`와 초기 부모 승계·hard safety·Main/manual custody는 유지한다. 구현·검토·수정·재리뷰·표적 검증 후 각 단계의 실제 영수증으로 결과를 기록한다.


## 13. P5 cold 준비 경로와 전체 선정 검증 근거 전달

실제 P5의 원 실패4회와 보완 이력은 [통합 실행 검토](../audits/main-research-integrated-p5-p6-deployment-review-2026-10-18.md)에 보존한다. 기계·보조 cold import 부작용과 준비 anchor 쓰기는 소비 경로를 수리한다. 추가 소규모 실제 OS 시험에서 진입지연의 sharded 검증은 원천 디렉터리에 scratch를 만들고 SQLite index로 전체 선정 재계산을 수행함을 확인했다. 단순 private scratch 이동 뒤에도 SQLite 차단이 남으므로 이 중간안의 시험 성공을 P5 통과로 취급하지 않는다.

보완 계약은 OS의 SQLite·네트워크·프로세스·운영 잠금 차단을 유지한다. 부모의 **동일 native 준비 검증 호출**에서 원 검증기가 전체 모집단 선정 재계산을 실제 성공한 직후에만 정확한 policy/report 의미 해시·원천 root/ref·선정 코드와 인자를 관측한다. 전체 native CLI 성공, 동일 run/request/선택본·코드·원천 신원을 결속한 근거만 해당 child로 전달한다. 과거 PASS, 관측하지 않은 receipt, 형제 실행 또는 새 원천을 대신 사용하지 않는다.

child는 원 native validator의 header·날짜·code 계약을 실행하고 전체 qualified projection/partition/cell과 중첩 membership 자료의 물리·논리 무결성을 검사한다. 전체 선정 재계산 결과만 그 정확한 부모 근거와 대사하며, active 문맥에서 근거 누락·변조·혼합은 실패한다. 정상 운영·장후 호출은 기존 전체 재계산을 유지한다. 부모에서 재계산한 범위와 child에서 재검증한 범위를 영수증에 구분하고 격리/원천 조건을 완화하지 않는다.

이 보완은 P5 코드 검토·OS 회귀·실제 준비 세대 실행을 닫은 후 P6를 진행하는 기존 순서를 유지한다. source10/16·실행10/18·target10/19, 수치 정책·Main/manual custody·hard safety 및 실제10/19 PREOPEN/PID owner는 §12와 같다.

## 14. 통합 후보 실제 P5와 P6 인계

지정9d·최종 stop eb8·holding3ab·기존 선택900의 계보를 보존한 통합 commit은 `958d35b2b03f0a37462c1c0121fc14c108e709b8`이다. 원 부모의 delay27개와 현재28개 코드 계약을 실제 origin Git 선언에 따라 구분하고 기존 원 정책 digest를 유지한다. [실제 P5](/home/ubuntu/KORStockScan/data/report/main_startup_validation/2026-10-19/ce996f74c04f41269c3605964c3c3f46/final.json)는 필수12개 소비 경로·부작용 시도0·child exit0/종료·부모 종료 후 native/CAS 검사를 통과했다. 원 실패4개와 과거 준비본은 보존한다. 운영 PID 소비나 경제적 개선으로 승격하지 않는다.

P6는 성공한 P5의 exact source/정책/코드 계약을 인수한다. 선택 환경파일의 null은 실제 부재 CAS로 소비하고, private CoW는 봉인된 실제 호스트 namespace와 엄격한 전체 격리 가드를 확인하는 단일 native 호출로 구분한다. 호스트 준비 전후 및 발행 전후의 원 P5 identity 검사는 유지한다. 새 준비/선택 세대 발행 후에는 canonical router로 **해당 최종 세대의 P5를 다시 실행**하고 이전 성공이나 generation-required marker를 덮어쓰지 않는 별도 완료 영수증을 남긴다. 진행과 실제 terminal은 [통합 배포 검토](../audits/main-research-integrated-p5-p6-deployment-review-2026-10-18.md)가 소유한다.

## 15. 최종 배포·사전 로딩 종결

P6는958d35b2b·source10/16·target10/19의54개 파일/선택본을 발행하고 호스트 current_full_contract PASS/findings0으로 종결했다. 표준 canonical 명령으로 실행한 [최종 세대 P5](/home/ubuntu/KORStockScan/data/report/main_startup_validation/2026-10-19/fc98c7d7f0eb42e99515e65b4b6514ba/final.json)도 passed다. 부모와 실행본 모두958이며 원 선언28개·필수12consumer(11 loaded/holding_prompt native parent_only)·금지 부작용0·child exit0/종료 및 부모의 마지막 native/CAS를 확인했다.

원 최초 P5·required marker·이전 준비/정책·실패 영수증은 유지하고 [최종 완료 영수증](/home/ubuntu/KORStockScan/tmp/main-research-policy-deployment-20261018/p5-final-generation-completion-01.json)을 별도 봉인했다. cron8+snapshot3/release-set과 다음 PREOPEN/start의 print-plan을 확인했다. 현재 범위 연구·통합·P5/P6 기술 작업은 종료한다. 정책수치·수탁·hard safety를 유지했고 실제 Main 기동/provider/주문은 수행하지 않았다. actual_pid_consumed=false이며 실제10/19 PREOPEN/PID·자연 수용은 기존 owner와 Acceptance를 유지한다.

## 16. PREOPEN 코드 인계의 첫 장중 전환 승계

당일 PREOPEN이 이미 검증된 prepared code handoff를 소비했다면 최초 Main 기동 commit과 정책 원 code commit은 다를 수 있다. ordered 배포의 delay 사전검사는 원 코드 digest 불일치에 한해 현재 선택본의 정식 prepared 영수증과 전체 frozen source·policy·날짜·scope를 검증하고, 그 검증된 원 commit에서 후보까지의 기존 코드 차이 검사를 수행한다. 다른 실패는 그대로 중단하며 incumbent는 계속 실행한다.

기존 release-set/detector/selector lock 아래 native 사전검증과 drain이 끝난 뒤, selector 게시 전에 기존 prepared publisher가 원 영수증을 새 후보로 승계한다. publisher의 Main/supervisor 부재·원문 snapshot·source CAS·immutable receipt 검사는 유지한다. 정책·PREOPEN·controller 원문을 재발행하지 않는다. 승계 실패는 새 selector 게시를 중단하고 그 단계의 원 실패와 startup hold를 보존한다. 이후 prepare→start→PID 확인은 기존 ordered 경로를 따른다. [10/19 실행 검토](../audits/preopen-alert-repair-2026-10-19.md).

## 17. 2026-10-19 부분 체결 취소와 장중 역사 연구 원천 검증

부분 체결은 원 매도 주문의 종료가 아니다. 잔여 주문이 살아 있는 동안 원 제출 세대·문맥·취소 저널을 보존하고, durable receipt successor가 재기동 복원을 소유한다. 신규 주문 pending 상태를 만들지 않고 정확한 기존 주문에만 취소 저장을 허용한다. 기존 문맥 유실 복구는 원 이벤트/registry/DB/receipt 대조와 승인된 ordered drain 후 native writer를 사용한다. 실제 취소·잔여 체결·terminal은 새 PID의 자연 영수증으로 따로 수용한다.

역사 연구는 동일 source-date의 원 bytes와 정책을 유지한다. 공용 owner registry가 다음 날짜의 별도 owner 주문으로 증가한 경우 원 prefix SHA 및 전체 hash chain을 검증해 구분한다. 과거 owner/날짜, prefix 변조, chain 결손은 검증 실패다. 잠금 파일은 연구 입력이 아니며 실제 vote jsonl/gzip은 계속 inventory에 포함한다. 동기 AI 관측은 exact request와 native PID/observation을 사용하고 비동기 식별자를 만들어 채우지 않는다. 상세 검토는 [복구 감사](../audits/preopen-alert-repair-2026-10-19.md)에 기록한다.

PREOPEN 이후 현재 체크리스트에 다른 실행 owner가 추가돼도 그 편집본을 보존한다. 원 strict receipt의 SHA와 정확히 일치하는 원문만 native 역사 snapshot으로 보존·재사용하며, 원 prepared/controller/strict 결속과 실제 predecessor 검증은 유지한다. snapshot 부재·변조·symlink 또는 잘못된 원문은 전환을 차단한다. 현재 문서를 과거 내용으로 교체하거나 새 문서로 원 strict를 다시 봉인하지 않는다.
