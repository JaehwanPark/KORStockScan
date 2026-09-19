# Daily threshold-cycle 공통 튜닝 퇴역 및 런타임 소유권 분리 상세계획

작성: 2026-09-19 KST

## 1. 결정과 목표

`daily_threshold_cycle_report`와 `threshold_cycle_ev_report`를 공통 EV 탐색기로 유지하지 않는다. 현재 두 계층은 active family의 서로 다른 challenger를 만들지 못하고, 2026-09-17 기준 17개 family 중 paired comparable 0개, validated improvement 0개, 신규 apply candidate 0개였다. 동일 입력을 반복해도 `incumbent_preserved_identical_policy`와 구조적 `source_gap`을 다시 집계하는 비중이 크다.

권장 종착점은 다음과 같다.

1. 공통 Daily calibration·EV 집계·generic workorder 경로를 완전히 퇴역한다.
2. 실제 가치가 있는 family는 각 원 생산자·평가기·PREOPEN publisher·장중 owner의 직접 경로를 유지한다.
3. Daily 계층에 섞여 있는 operator lock, 명시적 OFF, carry-forward, rollback, 날짜별 런타임 환경 생성과 검증은 작은 런타임 bootstrap owner로 이전한다.
4. 새 bootstrap은 후보를 탐색하거나 경제성을 보정하지 않고, 이미 승인된 family receipt만 합성한다.
5. 직접 소비와 봇 기동 검증을 완료한 변경에서 기존 Daily/EV/PREOPEN 공통 구현과 파생 산출물을 제거한다.

이 계획은 코드·스케줄·런타임을 변경하지 않는다. 구현 시 current checklist에 단일 stable ID `DailyThresholdCycleRetirement0919`를 등록하고, 기존 완료 항목을 새 OPEN owner로 복제하지 않는다.

## 2. 현재 구조와 제거가 바로 불가능한 이유

현재 이름상 Daily 튜닝 계층은 다음 책임을 함께 가진다.

| 책임 | 현재 owner/경로 | 현재 판단 |
| --- | --- | --- |
| 17개 family calibration·방향 추천 | `daily_threshold_cycle_report.py` | 퇴역 |
| family 경제성 상태 집계 | Daily `economic_evaluation` | 직접 family evaluator로 환원 |
| 전체 EV·workorder source 요약 | `threshold_cycle_ev_report.py` | 퇴역 |
| AI correction 재시도 | postclose wrapper→Daily | 공통 경로 퇴역 |
| PREOPEN 후보 선택 | `threshold_cycle_preopen_apply.py` | Daily 후보 선택부 퇴역 |
| operator lock·carry-forward·OFF 합성 | `threshold_cycle_preopen_apply.py` | 새 bootstrap으로 이전 |
| 날짜별 runtime env/manifest/verify | PREOPEN apply→`threshold_runtime_env_*` | 새 bootstrap으로 이전 |
| 봇 기동 전 env source·검증 | `src/run_bot.sh` | 새 bootstrap 계약으로 전환 |
| strict verifier/controller 완료 조건 | verifier/controller/summary/tower | direct-family 완료 조건으로 축소 |
| checklist/workorder 자동 생성 | checklist/workorder builders | Daily/EV 의존 제거 |

`src/run_bot.sh`는 날짜별 threshold runtime env가 없으면 기동을 대기하거나 중단한다. 따라서 Daily와 PREOPEN 모듈을 먼저 삭제하면 EV 탐색뿐 아니라 기존 승인 정책·OFF 상태·기동 검증까지 끊길 수 있다. 퇴역은 런타임 bootstrap 전환 후에만 수행한다.

## 3. 범위와 비범위

### 3.1 제거 범위

- `src.engine.daily_threshold_cycle_report`의 report/calibration/cumulative/AI correction/apply-candidate 기능과 CLI
- `src.engine.threshold_cycle_ev_report`와 JSON/Markdown producer
- Daily/EV를 다시 읽어 generic 개선 항목을 만드는 workorder 분기
- postclose wrapper의 Daily 최초 실행·재시도·cumulative wait·EV pre/post pass
- PREOPEN의 Daily `calibration_candidates`·`apply_candidate_list` 소비
- strict verifier/controller/tower/summary/checklist의 Daily·EV 필수 완료 조건
- Daily/EV 전용 freshness·cron-completion·monitoring registry
- Daily/EV 및 퇴역 PREOPEN 공통 구현만 검증하는 테스트
- 전환 완료 후 Daily/EV 파생 보고서·AI review·calibration·cumulative·apply-plan 과거 산출물

### 3.2 유지 범위

- EOD와 주문·체결·청산·비용·custody 원장
- clean baseline 및 source-quality 정책
- active family의 직접 원천·평가기·정책 publisher·장중 consumer
- broker/account/order/quantity/cooldown/provider/bot-state/hard/protect/emergency guard
- 명시적으로 승인된 operator lock과 그 rollback 값
- retired/OFF family를 다시 켜지 못하게 하는 startup OFF 계약
- 실제 runtime PID·cwd·policy hash·결정·주문·terminal 결과 증거

### 3.3 이번 퇴역과 별개인 family

다음 family는 공통 Daily/EV를 제거한다는 이유로 삭제하거나 복구하지 않는다. 각각의 활성 상태와 직접 소비 계약만 유지한다.

| family | 유지할 직접 경로 | Daily 제거 시 처리 |
| --- | --- | --- |
| entry cancel wait | `entry_cancel_wait_tuning`→기존 timeout runtime owner | Daily 요약 없이 전용 report/dated receipt를 bootstrap이 소비 |
| entry split | `entry_split_order_plan`→전용 policy/submit owner | submitted·no-submit·no-fill·cost/terminal gate 유지 |
| scale-in split | `scale_in_split_order_plan`→scale-in order owner | base-order 보존과 실제 fill 조건 유지 |
| scanner lookup-attention | WS finalize/tuning→dated scanner policy→scanner | complete partition·policy hash를 직접 검증 |
| machine entry timing | machine evaluator→PREOPEN publisher→timing loader | source/effective date·scope·policy hash 직접 검증 |
| compact auxiliary AI | paired evaluator→dated publisher/plan→mechanistic consumer | Daily 복제 없이 native paired/holdout receipt를 소비 |
| low-price two-leg | research/tuning→candidate→PREOPEN policy→profile/runtime | exploratory·promotion·actual custody 분리 유지 |
| strategy-owner components | owner replay/economics→operator policy succession | active receipt만 bootstrap에 입력 |

family가 source-only, observe-only, OFF 또는 retired이면 bootstrap 입력 자격이 없다. 코드가 남아 있다는 이유로 runtime candidate를 만들지 않는다.

## 4. 목표 구조

```text
intraday producer / terminal / cost ledger
        │
        ├─ family-owned evaluator ── no-edge/source-gap report
        │
        └─ validated family candidate
                │
                ▼
      family-owned dated PREOPEN publisher
                │
                ▼
        runtime policy bootstrap
        - approved receipt inventory
        - operator lock / explicit OFF
        - same-stage conflict
        - rollback / expiry / exact date
        - immutable env + manifest + verify
                │
                ▼
           normal bot startup
                │
                ▼
        family-specific intraday owner
                │
                ▼
       actual decision/fill/exit/cost attribution
```

공통 bootstrap은 EV를 계산하지 않는다. 누락된 경제성을 0으로 만들지 않고, family publisher가 `validated` receipt를 제공하지 않으면 incumbent·명시적 lock·OFF 상태를 보존한다.

## 5. 새 runtime bootstrap 계약

### 5.1 코드 위치

새 파일이 필요하면 `src/engine` root가 아니라 `src/engine/automation/runtime_policy_bootstrap.py` 한 곳만 사용한다. 이 위치는 주문 executor가 아니라 승인된 정책 receipt를 기동 환경으로 합성하는 automation owner이기 때문이다. 별도 daemon, service, DB, provider caller, compatibility Python wrapper는 만들지 않는다.

기존 `threshold_cycle_preopen_apply.py`를 축소해 재사용하는 방법과 새 automation 모듈로 옮기는 방법을 구현 시작 시 비교한다. 최종 상태에는 두 구현을 함께 남기지 않는다. 삭제 규모와 import cycle을 고려해 한 번의 cutover에서 새 owner로 이동하고 이전 모듈을 제거하는 방식을 우선한다.

### 5.2 입력

- exact target trading date
- active family별 immutable apply receipt와 policy artifact hash
- source/publication/effective date
- family·stage·scope·venue/session·owner
- `allowed_runtime_apply=true`와 family-native economic gate 결과
- operator lock ID, persistence/expiry, 허용된 close 사유, rollback env
- explicit OFF/retirement envelope
- 이전 정상 기동 manifest 중 carry가 허용된 active family의 승인 값

Daily/EV report, generic 방향 추천, win rate, simple PnL, sim/probe/CF만 있는 후보는 입력으로 받지 않는다.

### 5.3 출력

경로명은 cutover 시 한 번만 변경한다.

- `data/runtime/policy_bootstrap/runtime_policy_bootstrap_YYYY-MM-DD.env`
- `data/runtime/policy_bootstrap/runtime_policy_bootstrap_YYYY-MM-DD.json`
- `data/runtime/policy_bootstrap/runtime_policy_bootstrap_verify_YYYY-MM-DD.json`

manifest 최소 필드는 다음과 같다.

- schema/report type, target date, generation time
- selected release SHA와 producer code SHA
- selected/retained/disabled/rejected family 목록
- family별 source receipt·policy path·byte hash·stage·scope·effective date
- selection change class: `newly_selected`, `policy_refreshed`, `retained_approved`, `operator_lock_preserved`, `explicit_off`, `rejected`
- env key owner와 충돌 결과
- rollback env와 rollback owner
- removed/retired key scrub 결과
- no-provider/no-broker/no-order assertion
- self hash와 verify result

env에는 적용 값만 둔다. 권한·원천·결정 설명은 manifest에 두고, env 주석이나 문자열을 runtime 판단 근거로 사용하지 않는다.

### 5.4 fail-closed 규칙

- 날짜·scope·hash·effective date가 맞지 않으면 해당 family만 거절한다.
- 전역 manifest 자체가 없거나 malformed, self hash 불일치, env/manifest 불일치이면 봇 기동을 차단한다.
- same-stage owner 충돌은 현재 승인 우선순위와 explicit operator lock 경계를 보존한다.
- 이전 manifest carry는 family가 명시적으로 persistence를 허용하고 정책 파일·rollback 값이 검증될 때만 가능하다.
- report-only/source-only/sim/probe/CF는 실거래 env를 만들 수 없다.
- hard/protect/emergency·broker/account/order/quantity/cooldown guard는 bootstrap이 완화하거나 덮어쓰지 못한다.

## 6. 구현 단계

### R0. 정확한 소비자 census와 퇴역 동결

수정 대상:

- `daily_threshold_cycle_report.py`, `threshold_cycle_ev_report.py`, `threshold_cycle_preopen_apply.py`
- postclose/preopen/finalization/calibration wrappers
- `src/run_bot.sh`
- verifier/controller/summary/tower/workorder/checklist builders
- artifact freshness/cron completion/monitoring registry
- Daily 상수만 import하는 모듈

작업:

1. import, CLI 호출, artifact path, hash 요구, checklist source를 분리해 목록화한다.
2. 각 소비자를 `runtime-critical`, `family-direct`, `report-only`, `retired`, `path-constant-only`로 분류한다.
3. Daily/EV에서 신규 적용 후보를 만들지 않도록 현 상태를 동결하되, 아직 코드를 삭제하지 않는다.
4. 현재 실제 PID가 있으면 그 PID가 읽은 env와 selected family/owner를 snapshot으로 고정한다. PID가 없으면 마지막 exact-date verify를 참고 자료로만 보존하고 현재 소비 성공을 주장하지 않는다.

완료 기준:

- 모든 import/caller/artifact consumer가 단 하나의 분류와 후속 owner를 가진다.
- consumer 미확정 항목이 남으면 R1 이후로 진행하지 않는다.
- 퇴역 대상이 active 주문·custody·hard-safety owner를 겸하지 않음을 확인한다.

### R1. bootstrap의 최소 계약 구현

작업:

1. active family receipt registry를 코드 고정 목록으로 새로 만들지 않고, 현재 family publisher의 명시적 receipt만 읽는다.
2. operator lock·OFF·rollback 합성 기능을 이전한다.
3. env owner 충돌, retired key scrub, date/hash 검증을 이전한다.
4. 기존 `threshold_runtime_env`와 동일 입력 fixture에서 의미상 같은 active env가 생성되는 differential test를 작성한다.
5. 기존 환경에 포함돼 있지만 owner가 retired/source-only인 키는 baseline으로 승계하지 않고 제거 목록에 넣는다.

성공 기준:

- 허용된 active key의 값과 owner가 기존 검증 manifest와 일치한다.
- 새 manifest는 Daily/EV 파일 없이 생성·검증된다.
- malformed receipt 하나가 다른 무관 family를 승인하지 않는다.
- provider, broker, order 모듈 import/call이 없다.

### R2. family별 직접 입력 전환

우선순위는 현재 runtime effect가 있는 family부터다.

1. operator lock/strategy-owner component
2. entry cancel wait
3. machine entry timing·scanner policy
4. entry/scale-in split
5. compact·low-price 등 dated policy family

각 family에서 다음을 검증한다.

- producer→candidate→apply receipt→bootstrap→runtime loader 경로
- source/effective date와 policy/content hash
- incumbent/validated candidate/explicit OFF의 구분
- no-fill, partial, held, custody-censored, source-gap 상태가 apply receipt로 바뀌지 않음
- runtime consumer가 실제 사용하는 key 또는 policy field와 동일한 값

family 자체에 유효한 경제성 evaluator가 없으면 새 generic evaluator를 만들지 않는다. 해당 family는 incumbent/lock/OFF만 유지하고 향후 전용 workorder 대상으로 남긴다.

### R3. PREOPEN·봇 기동 cutover

수정 위치:

- `deploy/run_threshold_cycle_preopen.sh` 또는 후속 이름의 기존 PREOPEN wrapper
- `src/run_bot.sh`
- `entry_setup_live_policy.py`와 family preflight 중 runtime env를 직접 읽는 부분

작업:

1. PREOPEN wrapper가 family publisher 실행 후 bootstrap을 한 번 호출하도록 순서를 바꾼다.
2. `run_bot.sh`의 wait/source/verify 경로를 새 env와 manifest로 바꾼다.
3. entry setup loader의 merge 순서는 bootstrap→operator dated override→owner custody로 고정한다.
4. 실제 실행 중 PID에 hot reload하지 않는다. 다음 정상 기동에서만 새 계약을 소비한다.
5. 기존 `threshold_runtime_env_*` fallback은 두지 않는다. rollback은 이전 immutable release 선택으로 수행한다.

완료 기준:

- print-plan에서 Daily/EV 파일 없이 PREOPEN 순서가 완결된다.
- missing/malformed bootstrap이면 봇이 기동하지 않는다.
- exact-date bootstrap과 selected release가 맞으면 정상 기동 경로가 열린다.
- 실제 PID 검증은 배포 후 별도 receipt이며 코드 테스트 PASS와 구분한다.

### R4. postclose 공통 튜닝 단계 제거

`deploy/run_threshold_cycle_postclose.sh`에서 다음을 제거한다.

- Daily 최초 실행과 AI correction 재시도 loop
- Daily calibration/cumulative artifact wait
- Daily late refresh
- EV pre-workorder/post-workorder pass와 duplicate-refresh 판단
- Daily/EV 전용 resource label·env flag·DONE marker
- generic Daily/EV 입력에만 의존하는 code-improvement workorder 분기

family-native postclose producer는 실행 순서와 직접 consumer가 확인된 것만 남긴다. 단순히 Daily에 포함됐다는 이유로 유지하지 않는다. 반대로 Daily가 사라진다는 이유로 active family producer를 삭제하지 않는다.

완료 기준:

- wrapper 순서가 `원천/terminal→family evaluator/publisher→summary/verifier`로 표현된다.
- Daily/EV artifact를 기다리는 단계가 0개다.
- 같은 family를 공통 wrapper와 family wrapper가 중복 실행하지 않는다.
- 비활성/retired producer를 완료 조건으로 복구하지 않는다.

### R5. verifier·controller·summary·checklist 전환

수정 대상:

- `verify_threshold_cycle_postclose_chain.py`
- `postclose_done_controller.py`
- `postclose_summary_handoff.py`
- `tuning_performance_control_tower.py`
- `runtime_approval_summary.py`
- `build_code_improvement_workorder.py`
- `build_next_stage2_checklist.py`
- artifact freshness/cron completion/monitoring coverage

원칙:

- Daily/EV 전체 PASS 대신 active family의 native terminal과 최종 직접 consumer를 검증한다.
- runtime selection, env publication, PID consumption, natural decision/fill, 비용 후 EV를 별도 축으로 유지한다.
- family가 그날 disabled/retired/valid-empty이면 해당 상태를 terminal로 인정하되, missing을 valid-empty로 바꾸지 않는다.
- checklist는 Daily/EV source link를 자동 생성하지 않는다.
- generic workorder는 source-gap을 반복 복제하지 않고 family owner와 closure test가 있는 항목만 생성한다.

완료 기준:

- strict verifier가 Daily/EV 파일이 없어도 active direct-family chain을 판정한다.
- controller가 Daily/EV 재실행 action을 만들지 않는다.
- summary와 다음 checklist에 퇴역 작업이 active owner로 나타나지 않는다.
- 동일 blocker가 매일 새 stable ID로 복제되지 않는다.

### R6. 코드·테스트·문서 최종 삭제

코드 제거 후보:

- `src/engine/daily_threshold_cycle_report.py`
- `src/engine/threshold_cycle_ev_report.py`
- `src/engine/threshold_cycle_preopen_apply.py`
- `deploy/run_threshold_cycle_calibration.sh`
- Daily/EV 전용 compatibility helper와 refresh logic

`run_threshold_cycle_postclose.sh`와 PREOPEN wrapper는 active family orchestration 역할이 남아 있으면 중립 이름으로 바꿀 수 있다. 이름 변경은 호출자·cron·runbook을 같은 변경에서 갱신하며, 기존 이름의 wrapper를 호환 목적으로 남기지 않는다.

테스트 처리:

- 구현을 그대로 미러링하는 Daily/EV 테스트는 삭제한다.
- bootstrap, launcher, active family direct consumer, strict verifier 계약 테스트로 교체한다.
- source-quality·order/custody·hard-safety·family-native economics 테스트는 보존한다.
- import allowlist와 engine-root location gate를 검증한다.

문서 처리:

- active inventory에서 Daily/EV/PREOPEN generic tuning 단계를 삭제한다.
- 코드가 완전히 제거되면 residual-code 항목도 남기지 않는다.
- Plan Rebase/README/AGENTS는 별도 명시적 문서 유지 요청이 있을 때 owning 문서부터 갱신한다.
- runbook·traceability·postclose instructions·cron 문서는 실제 새 wrapper/owner와 일치시킨다.
- 과거 checklist/audit 기록을 현재 owner로 인용하지 않는다.

### R7. 파생 산출물과 디스크 정리

직접 consumer가 0개이고 현재/rollback runtime에 필요하지 않음을 확인한 뒤 삭제한다.

- `data/report/threshold_cycle_*.json|md`
- `data/report/threshold_cycle_calibration/`
- `data/report/threshold_cycle_cumulative/`
- `data/report/threshold_cycle_ai_review/`
- `data/report/threshold_cycle_ev/`
- old apply plans, old `threshold_runtime_env_*`, old verify artifacts
- Daily/EV 전용 temporary cache·workorder projection

보존 대상:

- raw order/submit/fill/terminal/cost/custody ledger
- family-native immutable candidate·policy·apply receipt
- 현재 selected release와 rollback release에 필요한 manifest
- clean baseline/source-quality 원본
- 법적·운영 감사에 필요한 broker receipt

삭제 전 active process의 cwd/open-file, wrapper lock, selected release, rollback 참조를 확인한다. 삭제는 exact allowlist로 수행하고 report/log/archive 전체를 포괄하는 glob 삭제는 금지한다.

### R8. 리뷰·배포·자연 검증

1. implementation self-review
2. producer/consumer·authority·silent-failure review
3. finding 수정
4. re-review finding 0
5. targeted tests·compile·`bash -n`·`git diff --check`
6. print-only checklist parser
7. immutable release 생성 및 source test 재검증
8. selected release 원자적 전환
9. 다음 정상 PREOPEN의 bootstrap 생성·verify
10. 다음 정상 봇 기동의 PID/cwd/env/policy 소비 확인
11. 자연 장중 decision과 이후 terminal/cost attribution 확인

배포 완료는 8번까지다. PREOPEN/PID/자연 거래/EV는 각각 별도 Acceptance다. 봇 임의 재시작, 주문 생성, provider 변경, threshold 완화는 이 계획의 구현 검증에 포함하지 않는다.

## 7. 파일별 변경 지도

| 파일/영역 | 예정 조치 |
| --- | --- |
| `daily_threshold_cycle_report.py` | 최종 삭제 |
| `threshold_cycle_ev_report.py` | 최종 삭제 |
| `threshold_cycle_preopen_apply.py` | bootstrap 이전 후 최종 삭제 |
| `automation/operator_policy_succession.py` | active lock/승계 receipt 제공자로 유지; 전체 bootstrap을 흡수해 비대화하지 않음 |
| 새 `automation/runtime_policy_bootstrap.py` | 단일 신규 owner가 필요할 때만 생성 |
| `run_threshold_cycle_postclose.sh` | Daily/EV 단계·wait·refresh 제거, active family orchestration만 유지 |
| `run_threshold_cycle_preopen.sh` | direct publisher→bootstrap→family preflight 순서로 전환 |
| `src/run_bot.sh` | 새 bootstrap wait/source/verify로 전환 |
| `entry_setup_live_policy.py` | 새 env provenance 소비 |
| verifier/controller/summary/tower | direct-family terminal 검증으로 축소 |
| workorder/checklist builders | Daily/EV source·generic blocker 생성 제거 |
| monitoring/error detector | old artifact 기대 제거, bootstrap/current family만 감시 |
| active inventory/runbook/traceability | 실제 호출 순서와 owner로 현행화 |

Daily의 `REPORT_DIR` 같은 상수만 가져가던 consumer는 owner-local path나 해당 family 상수를 사용한다. 삭제된 Daily를 import compatibility module로 남기지 않는다.

## 8. 검증 행렬

| 축 | 필수 검증 |
| --- | --- |
| import/caller | old module import·CLI·artifact wait 0개 |
| wrapper | postclose/PREOPEN `bash -n`, print-plan, 순서/중복/lock 테스트 |
| bootstrap | exact date/hash, env/manifest equality, self hash, conflict, OFF, carry, rollback |
| launcher | missing/invalid env fail-closed, valid env source 순서, PID environ verify |
| family | candidate→receipt→bootstrap→runtime loader fixture E2E |
| authority | source-only/sim/probe/CF가 실거래 env를 만들지 않음 |
| safety | broker/account/order/quantity/cooldown/hard/protect/emergency 불변 |
| verifier | direct source·consumer terminal, disabled/retired/valid-empty/missing 구분 |
| docs | 링크·owner·stable ID·권한 검사와 print-only parser |
| repository | compile, 관련 pytest, `git diff --check` |

전체 과거 보고서 재생성이나 실데이터 full replay는 기본 검증이 아니다. 작은 frozen fixture와 기존 exact-date artifact의 read-only differential comparison으로 cutover를 검증한다.

## 9. 중단 조건과 rollback

다음 중 하나면 삭제 단계로 진행하지 않는다.

- 현재 PID가 소비하는 active env key의 owner를 결정하지 못함
- family policy receipt와 runtime loader의 hash/scope가 일치하지 않음
- operator lock persistence/close/rollback 계약 손실
- PREOPEN exact-date bootstrap이 기존 정상 기동 값을 재현하지 못함
- strict verifier의 대체 direct terminal이 정의되지 않음
- 새 계약이 provider/broker/order authority를 추가함
- runtime env가 없을 때 baseline으로 조용히 진행하는 fallback 발생

배포 후 bootstrap 또는 기동 검증이 실패하면 활성 PID를 수동 hot-edit하지 않는다. 이전 immutable release와 그 selector로 rollback하고, 새 release의 실패 receipt를 보존한다. 이미 발행된 family 정책을 임의 삭제하거나 과거 PnL을 새 경제성으로 재분류하지 않는다.

## 10. 완료 판정

다음을 모두 만족해야 공통 threshold-cycle 튜닝 퇴역이 완료된다.

1. Daily/EV/PREOPEN generic 모듈과 CLI가 코드베이스에서 제거됐다.
2. wrapper·cron·controller·verifier·summary·workorder·checklist가 삭제된 artifact를 요구하지 않는다.
3. active family는 native source→evaluator→policy→runtime consumer 경로를 가진다.
4. operator lock·explicit OFF·rollback이 새 bootstrap에서 동일 권한으로 보존된다.
5. 봇은 새 exact-date bootstrap 없이는 기동하지 않고, 유효 bootstrap은 정상적으로 source·검증한다.
6. selected immutable release와 실제 PID/cwd/env 소비가 확인된다.
7. active inventory에 삭제된 작업이나 residual code 이력이 남지 않는다.
8. Daily/EV 파생 산출물은 보호 원장·rollback을 침해하지 않고 제거됐다.

경제성 완료 조건은 별도다. 각 family는 실제 적용 후 COMPLETED+유효 비용 결과로 EV·일별 순익을 검증해야 한다. 공통 Daily/EV 계층을 제거했다는 사실은 family의 경제적 성공이나 실패를 의미하지 않는다.

## 11. 권장 실행 순서

권장 순서는 `R0→R1→R2→R3→R4→R5→R6→R7→R8`이다. R1–R5는 하나의 review branch에서 구현하되, 기존 runtime과 새 runtime을 운영 환경에서 병렬 실행하지 않는다. fixture differential 검증 후 한 변경에서 caller를 전환하고 이전 구현을 삭제한다.

시간이 부족하면 family 전환 범위를 active runtime family로 제한하고 나머지는 incumbent/explicit OFF로 종료한다. 후보 탐색 깊이와 보고서 수를 줄일 수 있지만, 날짜·hash·비용·권한·rollback·hard safety 검증은 줄이지 않는다.
