# `build_next_stage2_checklist` direct-family 인계 개선 계획

작성일: 2026-09-19 KST

범위: 지금까지 개편된 장후 family evaluator/publisher, `runtime_approval_summary` v3, `runtime_policy_bootstrap`, strict verifier를 다음 영업일 Stage2 checklist에 정확히 인계하는 제어면 개선

권한: 이 문서는 구현 계획이다. 코드·wrapper·checklist·정책·런타임·주문을 변경하거나 장후/PREOPEN을 실행하지 않는다.

관련 기준: [Plan Rebase](../plan-korStockScanPerformanceOptimization.rebase.md), [현행 장후 작업목록](../audit-reports/2026-09-05-postclose-work-inventory.md), [Daily 튜닝 퇴역 계획](./daily-threshold-cycle-tuning-retirement-and-runtime-owner-separation-plan-2026-09-19.md), [runtime approval direct handoff 계획](./runtime-approval-summary-direct-evidence-handoff-optimization-plan-2026-09-19.md)

## 1. 결정

`build_next_stage2_checklist`는 더 이상 퇴역한 공통 Daily/EV 후보를 설명하거나 generic threshold 작업을 만드는 owner가 아니다. 현행 역할은 다음 세 가지로 제한한다.

1. `runtime_approval_summary` v3의 exact-date direct-family 상태를 검증한다.
2. 구조 수리, 자연 성숙, PREOPEN 정책 소비, 실제 적용 성과 확인 중 실제로 다음 영업일에 해야 할 일만 stable task로 투영한다.
3. `measured_no_edge`, `identical_policy`, retired/OFF/not-applicable처럼 실행할 일이 없는 terminal 상태는 설명으로만 남기고 OPEN task를 만들지 않는다.

후보를 고르거나 EV를 다시 계산하지 않는다. family producer의 경제 판정, 정책 publisher, bootstrap과 장중 consumer의 권한을 그대로 보존한다.

## 2. 현재 구현의 정확한 상태

배포 기준선은 immutable release `runtime-approval-summary-handoff-rereviewed-20260919-4de565801`이다. 현재 direct 경로는 `runtime_approval_summary` schema v3를 발견하면 퇴역 Daily/EV 기반 `_build_tasks()`를 우회한다. 이 전환 자체는 올바르다.

그러나 `_build_direct_family_checklist()`에는 다음 결함이 남아 있다.

| 결함 | 현재 동작 | 영향 |
| --- | --- | --- |
| invalid/missing summary fail-open | 2026-09-19 이후에는 summary가 비어 있어도 direct 경로로 들어가 `신규 공통 튜닝 작업 없음`을 기록할 수 있음 | 장후 producer 실패를 정상 empty로 오인 |
| 과거 stable ID 하드코딩 | 모든 구조 결손을 `[CodeImprovementWorkorderReview0918]`로 인계 | 현재 owner가 아니며 family·원인·완료조건이 소실됨 |
| 실행 항목 부재 | blocker가 있어도 checkbox를 만들지 않고 `task_count=0` 반환 | parser/Project/Calendar에 실행 owner가 없음 |
| 상태 축약 | `source_gap`, `unsupported_scope`, `mixed`만 한 묶음으로 출력 | producer repair, 지원범위 결정, 자연 성숙, 정책 handoff를 구분하지 못함 |
| PREOPEN·PID 인계 누락 | `preopen_consumption_state=pending`, `natural_acceptance_state=not_due`를 task로 만들지 않음 | 정책 파일 생성과 실제 소비·성과 확인이 끊김 |
| future receipt hash 혼합 | postclose checklist marker에 아직 생성 전인 apply-date bootstrap/verify의 `null` hash를 포함 | 정상 PREOPEN 산출물 생성 후 marker가 의도적으로 stale해짐 |
| 반환값과 문서 불일치 | 문서에는 결손이 있으나 반환 `tasks=[]` | controller·검증기가 실제 후속 유무를 판단할 수 없음 |
| legacy 잔존 혼선 | direct 경로 아래에 Daily/EV·swing·runtime-gap·machine approval 기반 구형 builder가 큼 | 신규 수정이 잘못된 경로에 추가될 가능성 |

2026-09-17 실제 summary 기준 direct source는 10/10이지만 경제 상태는 한 가지가 아니다.

- `entry_cancel_wait`, `entry_split`: `source_gap` / producer repair
- `low_price_two_leg`: `mixed` / 실제 표본 floor 결손
- `scale_in_split`: `insufficient_sample` / 자연 성숙
- `rising_missed`: `measured_no_edge` / incumbent 유지
- source-quality, machine, WS, AI outcome: 현재 direct 경제 승격 대상이 아니거나 report-only
- validated edge와 신규 정책 후보: 0
- 2026-09-21 PREOPEN 소비: pending

이 상태를 하나의 과거 workorder 문장으로 합치는 것이 현재 가장 큰 결함이다.

## 3. 보존·제거 경계

### 보존

- checklist 파일의 manual 영역과 사용자가 작성한 OPEN task
- atomic write, file lock, 다음 KRX 영업일 계산, auto block 경계
- exact source date와 apply date 분리
- `runtime_approval_summary`의 family owner, blocker, closure test, policy receipt, 경제 상태
- incumbent, operator lock, 명시 OFF, broker/order/quantity/cap/custody/provider/bot/hard-safety 경계
- print-only parser와 외부 동기화 분리

### active 경로에서 제거

- `threshold_cycle_ev`, `threshold_cycle_preopen_apply`, generic selected-family를 새 direct checklist의 source 또는 표현으로 사용
- Swing OFF, retired lifecycle/pattern-lab/limit-down/PYRAMID/AVG_DOWN/RISING_MISSED_ONE_SHARE_ENTRY를 새 owner로 복원
- runtime-gap·generic code-workorder 문장을 모든 family 결손의 기본 owner로 사용
- `live_auto_apply_ready`, `sim_auto_approved` 같은 퇴역 공통 분류를 active direct-family 상태처럼 출력

### 금지

- checklist builder에서 EV·후보·threshold를 재계산하거나 정책을 선택
- missing/null을 0, valid-empty, no-edge로 변환
- 합성 fixture 성공을 자연 PREOPEN/PID/비용 후 성과로 표시
- source gap을 표본 대기로, 표본 대기를 구현 결함으로 바꿈
- 같은 blocker를 날짜 suffix만 바꾼 새 stable ID로 매일 복제

## 4. 목표 흐름

```text
family producer/evaluator/publisher
              |
              v
runtime_approval_summary v3
  - direct source completeness
  - economic disposition
  - policy receipt validity
  - apply date
  - PREOPEN / natural acceptance state
              |
              v
build_next_stage2_checklist
  - strict summary admission
  - disposition -> stable task projection
  - terminal/no-action summary
  - immutable postclose generation marker
              |
              v
strict verifier -> parser print-only
              |
       next normal PREOPEN
              |
              v
runtime_policy_bootstrap -> PID -> natural behavior -> completed PnL
```

`tuning_performance_control_tower`는 사람이 보는 compact view로 유지할 수 있지만 checklist 생성의 필수 선행 source로 만들지 않는다. 현재 wrapper 순서는 summary 뒤 checklist이므로 builder는 summary만으로 결정 가능해야 한다.

## 5. BC0 — strict summary admission

direct 경로용 `_load_direct_summary()`를 기존 모듈 안에 둔다. 새 module이나 service를 만들지 않는다.

필수 검증:

- `schema_version == 3`
- `report_type == runtime_approval_summary`
- `date == source_date`
- `decision_authority == family_owned_direct_evidence_summary_only`
- `daily_threshold_cycle_retired == true`
- `threshold_cycle_ev_retired == true`
- summary 자체의 `runtime_effect == false`, `allowed_runtime_apply == false`, `actual_order_submitted == false`
- `required_source_count`, `available_required_source_count`, `sources`, `blocking_reasons`, `economic_blockers` 형식
- 각 required source의 target-date·error·applicability·economic evidence 형식
- `preopen_consumption_receipt.apply_date`가 source date 뒤의 KRX 영업일이며 effective dates와 충돌하지 않음

missing, parse error, 잘못된 schema/date/authority는 checklist에 “작업 없음”을 쓰지 않는다. 기존 checklist를 변경하지 않고 명시적 예외로 wrapper를 실패시킨다. 복구 owner는 `runtime_approval_summary` 재생성 및 strict verifier이며 과거 Daily/EV fallback은 사용하지 않는다.

## 6. BC1 — 상태를 실행 의미로 정규화

builder는 summary의 판정을 바꾸지 않고 다음 projection만 만든다.

| summary 상태 | checklist 분류 | task 생성 | 종료 조건 |
| --- | --- | --- | --- |
| required source missing/error/date mismatch | `producer_contract_repair` | 예 | exact-date source와 summary hash 재검증 |
| `source_gap` + `producer_repair` | `producer_contract_repair` | 예 | `closure_owner`의 `closure_test` 통과 |
| `unsupported_scope` | `scope_contract_decision` | 예 | 기존 owner가 지원/제외 범위를 명시하고 consumer 회귀 통과 |
| `mixed` | 구성 상태로 분해 | 조건부 | 최초 actionable blocker만 task, 나머지는 진단 |
| `pending_maturity` / `insufficient_sample` + 미래 생성 계약 유효 | `natural_evidence_wait` | 예, 기존 family acceptance owner 재사용 | 표본/일수/holdout floor 또는 명시 terminal |
| `identical_policy` | `terminal_incumbent` | 아니오 | incumbent 유지 |
| `measured_no_edge` | `terminal_incumbent` | 아니오 | incumbent 유지, 탐색 자동 확장 금지 |
| `validated_edge` + policy receipt valid | `preopen_policy_handoff` | 예 | bootstrap hash/date/scope/guard PASS |
| `validated_edge` + policy missing/invalid | `policy_handoff_repair` | 예 | publisher→policy→bootstrap 동일 hash |
| `not_applicable` / disabled / retired | `terminal_not_applicable` | 아니오 | 복원 task 금지 |
| PREOPEN verified, 자연 미확인 | `post_apply_acceptance` | 예 | 실제 PID·자연 decision/fill·COMPLETED 비용 성과 |

`closure_test`가 null이면 builder가 임의 수치나 기준을 만들지 않는다. task에는 `closure_test=missing`과 해당 `closure_owner`의 계약 보완을 첫 완료 조건으로 기록한다.

## 7. BC2 — stable task 계약

날짜별 새 ID를 만들지 않고 family와 상태 역할로 고정한 ID를 사용한다.

예시:

- `DirectFamilySourceRepairEntrySplit`
- `DirectFamilyScopeDecisionEntryCancelWait`
- `DirectFamilyNaturalEvidenceScaleInSplit`
- `DirectFamilyPolicyHandoffRisingMissed`
- `DirectFamilyPostApplyAcceptanceRisingMissed`

ID 규칙은 `owner + task_role`의 allowlist 기반 PascalCase이며 raw blocker 문자열을 그대로 ID에 넣지 않는다. 동일 target checklist 재생성 시 같은 task를 갱신하고 중복 생성하지 않는다. 다음 거래일에도 같은 결손이면 같은 stable ID를 이관한다.

각 task에는 다음 필드를 사람이 읽을 수 있는 고정 순서로 포함한다.

- Source artifact와 summary SHA
- family owner와 closure owner
- comparison status와 resolution mode
- first blocker
- closure test
- policy receipt valid 여부와 effective date
- 허용된 다음 행동
- 금지된 권한

기존 manual OPEN task는 보존한다. 동일 stable ID가 manual 영역에 있으면 auto block에 복제하지 않는다. 과거 `[CodeImprovementWorkorderReview0918]` 같은 다른 목적의 task를 family 결손 owner로 하드코딩하지 않는다.

## 8. BC3 — PREOPEN·장중·성과 task 분리

### PREOPEN

`preopen_consumption_state=pending`이고 apply date가 target date이면 공통 task 하나에 due family를 나열한다. validated edge뿐 아니라 dated incumbent receipt도 hash/date 검증 대상이지만, incumbent는 runtime mutation 0이어야 한다.

완료 기준:

- policy source date·effective date·schema·semantic hash
- bootstrap accepted/rejected family receipt
- operator lock·retired OFF·same-stage conflict
- manifest/env self hash
- incumbent policy의 override 0 또는 validated 단일축 정책의 allowlist 범위

### 장중

실제 runtime effect가 있는 validated policy만 PID·자연 decision 확인 task를 만든다. incumbent 유지나 measured no-edge를 장중 성과 task로 부풀리지 않는다.

### 적용 후 성과

정책 version이 실제 PID에서 소비된 뒤에만 post-apply task를 활성화한다.

- episode 중복 제거
- rolling/cumulative 비용 차감 EV·순익
- tail·노출/reserve·fill participation
- 모델 delta와 실제 완료 이익 분리
- `COMPLETED + valid profit_rate`만 actual PnL

정책 파일 생성이나 bootstrap PASS만으로 이 task를 완료 처리하지 않는다.

## 9. BC4 — phase-aware generation receipt

현재 `POSTCLOSE_SUMMARY_SOURCES` marker에 미래 bootstrap 파일의 null hash를 넣는 계약을 분리한다.

### postclose generation marker

생성 시점에 존재하고 불변이어야 하는 다음 source만 hash로 결속한다.

- `runtime_approval_summary_<source_date>.json`
- 필요하면 summary가 직접 참조하는 compact terminal companion

### future handoff expectation

아직 생성 전인 bootstrap/verify는 hash source가 아니라 다음 필드로 기록한다.

- expected apply date
- expected path
- expected state: `future_due`
- expected family/policy hashes

PREOPEN 이후에는 별도 consumer receipt가 실제 manifest/verify hash를 소유한다. 정상 미래 파일 생성이 postclose marker 변조로 해석되지 않아야 한다.

이를 위해 `postclose_summary_handoff.source_paths(..., consumer="checklist")`, checklist marker, strict verifier의 direct-family 분기를 함께 수정한다. 구형 schema 경로는 historical source date에서만 유지한다.

## 10. BC5 — active 출력 형태

auto block은 세 부분만 생성한다.

1. `Family 직접 증거 상태`: source 10/10, 경제 상태 count, 후보/validated edge 수
2. `다음 적용일 정책 인계`: apply date, pending/verified/rejected, incumbent와 active policy 수
3. 실제 checkbox task: 구조 수리·자연 성숙·PREOPEN·post-apply 중 현재 필요한 항목

terminal 상태는 compact 표로 남긴다.

| family | economic state | policy handoff | checklist action |
| --- | --- | --- | --- |
| rising-missed | measured no-edge | incumbent preserved | 없음 |
| scale-in split | insufficient sample | incumbent preserved | 자연 표본 owner 유지 |
| entry split | source gap | blocked | producer repair |

raw Python list/dict 전체를 Markdown 한 줄에 출력하지 않는다. family별 최대 한 행으로 제한해 checklist가 audit dump가 되지 않게 한다.

## 11. BC6 — 파일별 최소 변경

| 파일 | 변경 |
| --- | --- |
| `src/engine/build_next_stage2_checklist.py` | strict direct-summary loader, 상태 projection, stable task 생성, terminal 표, 반환 task count 수리 |
| `src/engine/automation/postclose_summary_handoff.py` | postclose immutable source와 future PREOPEN expectation 분리 |
| `src/engine/verify_threshold_cycle_postclose_chain.py` | direct checklist marker·task projection·future_due 계약 검증 |
| `src/engine/automation/postclose_done_controller.py` | builder 실패 시 summary/checklist만 정확히 재생성하고 Daily/EV 복구 action 금지 확인 |
| `src/tests/test_build_next_stage2_checklist.py` | direct-family 상태별 회귀를 중심으로 보완하고 legacy 구현 미러 테스트 축소 |
| 기존 handoff/verifier/controller tests | phase-aware hash와 실행 task conservation 검증 |

새 module, DB, collector, service를 만들지 않는다. `runtime_approval_summary`에 checklist 전용 판단 로직을 추가하지 않고 현재 projection 필드를 사용한다. summary 필드 간 모순이 발견되면 summary producer를 최소 수리하고 builder에서 추정하지 않는다.

## 12. BC7 — 필수 회귀 시나리오

1. summary missing/malformed/wrong schema/date/authority → 기존 checklist 불변, 명시 실패
2. direct source 10/10 + 후보0 + 모두 no-edge/not-applicable → checkbox 0, 정상 terminal summary
3. source gap 2개 → family별 stable repair task 2개, `task_count=2`
4. 같은 source gap 재생성 → 같은 ID 갱신, 중복 0
5. closure test null → 임의 완료 기준 생성 없이 contract 보완 표시
6. insufficient sample + 미래 producer 계약 유효 → natural evidence task, 구현 repair task 아님
7. 미래 producer 계약 없음 → source gap task, maturity로 표시 금지
8. measured no-edge/identical policy → incumbent 표기, task 0
9. validated edge + valid policy → PREOPEN handoff task
10. validated edge + invalid policy hash/date/scope → policy repair task, runtime apply 금지
11. incumbent dated policy → PREOPEN hash 확인은 하되 장중 mutation task 0
12. bootstrap future_due가 실제 생성됨 → postclose generation marker는 stale이 되지 않음
13. bootstrap rejected → PREOPEN task 미완료와 blocker 보존
14. actual PID 미소비 → 배포/선택과 분리된 natural acceptance OPEN
15. manual task와 동일 stable ID → auto duplicate 0, manual 본문 보존
16. retired/OFF family artifact missing → 복원 task 0
17. legacy source date → 명시 legacy branch만 사용, active direct path와 혼합 0
18. atomic write 전 source hash 변경 → checklist 쓰기 실패, 기존 파일 보존

## 13. 검증 범위

구현 후 다음 순서로 닫는다.

1. `test_build_next_stage2_checklist.py`
2. `test_postclose_summary_handoff.py`
3. `test_verify_threshold_cycle_postclose_chain.py`
4. `test_postclose_done_controller.py`
5. `test_runtime_approval_summary.py`
6. wrapper contract test와 `bash -n deploy/run_threshold_cycle_postclose.sh`
7. Python compile, ruff, `git diff --check`
8. `PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500`

실제 provider 호출, 주문, bot restart, 조기 PREOPEN, 전체 raw 재스캔, 대형 경제 보고서 재생성은 이 검증에 포함하지 않는다.

## 14. 단계별 구현 순서

| 단계 | 작업 | 완료 증거 |
| --- | --- | --- |
| BC0 | 배포 release와 exact source summary 동결 | commit/path/hash, schema와 현재 결과 |
| BC1 | strict summary admission | missing/invalid false-green 회귀 |
| BC2 | 상태 projection과 stable ID | 상태별 task conservation 회귀 |
| BC3 | PREOPEN/PID/post-apply 분리 | incumbent/validated/rejected 회귀 |
| BC4 | phase-aware marker 수리 | future bootstrap 생성 전후 hash 회귀 |
| BC5 | direct auto block 간결화 | parser가 실제 task 수와 동일하게 인식 |
| BC6 | wrapper/controller/verifier 영향 검증 | Daily/EV 복구 action 0, strict PASS |
| BC7 | self review→수정→재리뷰 | in-scope finding 0 |
| BC8 | 승인된 경우 commit/push/immutable successor | source test와 release test 분리 |
| BC9 | 다음 정상 장후 자연 생성 | exact generation과 checklist task 확인 |
| BC10 | 다음 정상 PREOPEN·장중 | bootstrap/PID/자연 성과 별도 acceptance |

## 15. 현재 2026-09-17 → 2026-09-21 기대 결과

현행 자연 결과를 새 계약으로 투영하면 다음과 같아야 한다.

- direct source 상태: 10/10 complete
- validated edge: 0
- 신규 runtime mutation 후보: 0
- `rising_missed`: `measured_no_edge`, incumbent 유지, 신규 구현 task 없음
- `scale_in_split`: 실제 미래 생성 계약이 검증돼 있다면 natural evidence owner 유지
- `entry_cancel_wait`, `entry_split`: 각각의 closure owner로 producer repair task
- `low_price_two_leg`: `mixed`를 최초 actionable blocker로 분해하고 actual sample floor가 단순 시간 대기인지 producer/custody 결손인지 owner 계약대로 표시
- 2026-09-21 dated incumbent 정책: PREOPEN에서 hash·fallback·override 0 확인
- 실제 PID 소비·자연 decision/fill·완료 손익: 확인 전까지 별도 OPEN

현재의 `CodeImprovementWorkorderReview0918` 단일 문장과 `task_count=0`은 이 기대 결과를 충족하지 못한다.

## 16. 완료 기준

다음을 모두 만족해야 구현 완료다.

1. 잘못되거나 없는 summary가 정상 empty checklist를 만들 수 없다.
2. 구조 결손, 지원범위 결손, 자연 성숙, no-edge, validated edge가 서로 다른 실행 상태로 남는다.
3. actionable blocker 수와 생성된 parser-visible stable task 수가 일치한다.
4. 같은 blocker를 날짜별 새 ID로 복제하지 않는다.
5. retired/OFF/diagnostic family를 active owner로 복원하지 않는다.
6. 정책 생성, PREOPEN 소비, PID 소비, 자연 행동, 실제 비용 후 성과가 분리된다.
7. 미래 bootstrap의 정상 생성이 postclose marker를 stale하게 만들지 않는다.
8. 전체 native chain이 없거나 경제 후보가 0이어도 구현 가능한 checklist 계약은 완성된다.
9. 자연 표본·실제 PID·완료 손익만 OPEN으로 남고 실행 가능한 코드 결손은 남지 않는다.

양수 후보나 EV 개선은 완료 조건이 아니다. builder의 성공은 경제성 개선이 아니라 다음 행동을 정확한 owner와 상태로 전달했다는 뜻이다.
