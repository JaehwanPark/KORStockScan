# Latency recommendation 폐기·진단 통합 최종 리뷰 — 2026-09-06

현재 판정은 §7 보완 구현·재검증을 따른다. §1~5의 1,248 PASS는 최초 구현 기록, §6의 R1~R3 OPEN은 병합본 재점검 당시 기록이다. 이번 보완으로 R1~R3를 닫았으며, 구현 종결과 실제 자동화/성과 확인은 구분한다.

## 1. 최종 판정

- 독립 `latency_classifier_recommendation`은 목적을 달성하지 못하는 중복 장후 작업이므로 `latency_recommendation_retirement_20260906`으로 폐기했다. scheduled producer, PREOPEN loader/candidate, AI review 예외와 current approval 승격 경로가 모두 제거됐다.
- 실제 runtime `LatencyMonitor`와 `EntryPolicy`, `latency_block`/`latency_pass`, quote freshness와 DANGER/stale/broker 차단은 유지한다. `SAFE`와 `CAUTION`은 기존처럼 slippage 검사 뒤 normal submit으로 진행한다.
- latency/freshness의 사후 기회 분석은 BUY Funnel, performance tuning, daily threshold report의 `diagnostic_only`로 통합했다. 표본 수와 양의 사후 수익이 커져도 독립 threshold 후보나 code-improvement candidate로 승격하지 않는다.
- 별도 `latency_spread_relief_real_operator_override`는 이번 폐기 대상이 아니다. 현재 exact-date PREOPEN 환경의 fresh spread-only operator lock과 기존 rollback/safety 계약을 그대로 유지했으며 값·주문·provider·bot을 변경하지 않았다.

## 2. 목적·기대효과·기존 조건 재평가

- 구 목적은 관측된 latency 분포와 counterfactual을 이용해 다음 PREOPEN의 latency 경계값을 추천하는 것이었다. 그러나 runtime은 이미 단순화돼 CAUTION과 SAFE가 같은 submit 의미를 가졌고 report 자체도 `eligible=false`를 영구 출력해 실제 자동 적용 가능성이 없었다.
- 2026-09-04 artifact는 270행/63 unique attempt였으나 recovery와 유효 counterfactual이 0건이고 RTT 재현도 없었다. 선택된 CAUTION age가 59 ms로 SAFE age 250 ms보다 엄격해 의미가 역전됐으며, counterfactual은 비용 차감 순이익이 아닌 gross 관측이었다.
- clean baseline 이후 64개 historical artifact에서 apply 허용·bounded candidate·recovery evidence가 모두 0건이었다. 따라서 표본·EV 조건을 완화해 경로를 살리는 것보다 중복 권한을 제거하고 실제 safety/submit funnel 계측을 보존하는 편이 목적과 기대효과에 부합한다.
- 기대효과는 죽은 후보 대기·AI 예외·PREOPEN 재활성화 위험과 중복 장후 비용의 제거, 그리고 submit drought 원인을 latency/freshness/hard safety와 실제 경제성으로 일관되게 분리하는 것이다. 이 작업 자체를 수익 개선 증거로 해석하지 않는다.

## 3. 구현 및 재활성화 방지

1. 공통 retirement 계약에 report와 calibration family를 등록했다. runtime telemetry family는 broad retired family로 넣지 않아 안전 계측을 보존했다.
2. postclose wrapper에서 producer 명령을 제거하고 상태 marker를 영구 `false`로 고정했다. producer 모듈과 전용 테스트는 삭제했고 engine-root allowlist도 정리했다.
3. PREOPEN에서 report loader를 제거하고 historical primary/separate artifact에 악성 `allowed_runtime_apply=true` candidate가 남아도 selection/env override가 생성되지 않게 했다. 동일 폐기 family의 오래된 operator lock도 합성 candidate로 복원되지 않는다.
4. threshold EV, daily report, runtime approval summary는 historical recommendation을 읽지 않는다. 실제 latency pass/block 성과만 diagnostic owner로 표시하며 recommendation/runtime apply는 `retired`, `false`로 고정한다.
5. verifier의 AI exemption을 제거했다. stale historical selected family도 current runtime selection 수에 포함하지 않는다.
6. one-share의 `latency_or_freshness`를 BUY Funnel hard-safety attribution으로 통합하고 diagnostic-only 그룹으로 고정했다. 3건 이상의 양의 결과가 있어도 threshold opportunity/workorder로 승격되지 않는 반례 테스트를 추가했다.

## 4. 코드리뷰와 검증

- 1차 리뷰 finding: one-share first-blocker 경로가 latency/freshness를 기존-family 개선 후보로 다시 만들 수 있었다. diagnostic-only allowlist와 workorder 이중 방어를 추가하고 양의 표본 floor 반례로 닫았다.
- 2차 리뷰 finding: report candidate는 제거됐지만 동일 family의 stale operator lock이 합성 candidate를 만들 수 있었다. retired calibration family를 lock 보존보다 먼저 거부하고 force-emit 대상에서도 제거했으며 악성 lock 반례로 닫았다.
- historical report의 primary calibration list, 별도 report와 stale operator lock이 동시에 악성 candidate를 포함하는 경우를 재현했고 PREOPEN runtime 변경·env key·selected family가 모두 생성되지 않음을 확인했다.
- producer/report/approval/one-share/location 회귀: **318 PASS**.
- PREOPEN/verifier/wrapper 회귀: **510 PASS**.
- `LatencyMonitor`, entry latency, pipeline event, source-quality와 backfill 회귀: **420 PASS**, 외부 `pandas_ta` deprecation warning 1건만 존재한다.
- 합계 **1,248 PASS**. 변경 Python Black/Ruff, compile, wrapper `bash -n`, 문서 parser와 `git diff --check`를 최종 gate에서 확인했다.
- 최종 self-review의 이 범위 미해결 finding은 **0건**이다. bot restart, report 대량 재생성, 실주문, threshold/operator-lock 값, provider, quantity/cap과 hard safety 변경은 수행하지 않았다.

## 5. 런타임 적용 가능성과 남은 자연 확인

- 폐기 적용은 코드와 예약 wrapper에 자동 반영된다. 다음 postclose에서 사용자가 개입하지 않아도 독립 producer가 실행되지 않으며, 다음 PREOPEN은 과거 artifact를 candidate로 읽지 않는다.
- 현재 `threshold_runtime_env_2026-09-07.json`을 읽기 전용으로 대조한 결과 selected family에는 `latency_classifier_runtime_profile`이 없고 `latency_spread_relief_real_operator_override`만 별도 owner로 존재했다. 이는 새 코드의 실제 PID 소비 증거가 아니라 장전 파일의 권한 분리 확인이다.
- 실제 정상 기동 PID에서 DANGER/stale/broker 차단과 `latency_block/pass`가 계속 기록되는지, 다음 postclose marker가 recommendation `false`인지, PREOPEN selected family에 폐기 family가 없는지는 2026-09-07 자연 실행에서 확인한다.
- 현재 exact-date env의 `latency_spread_relief_real_operator_override`는 별도 owner다. 이를 폐기 family로 오인해 제거하거나 recommendation 폐기를 근거로 spread/safety 경계를 완화하지 않는다.
- 자연 latency 대상 0건은 `not_observed`이며 성공·실패 또는 threshold 변경 근거가 아니다. 자연 증거가 생길 때까지 기존 안전 계측과 BUY Funnel 진단만 계속한다.

## 6. 병합본 목적·자동화·조건 달성 가능성 재점검

검토 기준: `main` 병합 커밋 `4110e95d`, 2026-09-06. 이번 요청은 재점검이므로 실행 코드·운영 env를 수정하지 않았고, 메모리에서 반례를 주입해 읽기 전용으로 검증했다. 보고서와 체크리스트만 현행화한다.

### 판정과 자동화

- 독립 추천 폐기는 목적에 부합한다. producer 명령과 PREOPEN loader는 제거됐고, 기존 candidate/동일 family operator lock 차단 테스트도 통과한다. 죽은 후보 생성과 중복 report 비용은 다음 예약 실행부터 제거되는 구조다. 순이익·매매빈도 개선은 아직 입증되지 않았다.
- 설치된 crontab은 평일 07:35 `auto_bounded_live` PREOPEN와 20:10 postclose wrapper를 현재 작업 디렉터리에서 호출한다. 폐기 반영에 추가 수동 승격은 필요하지 않다. 점검 시 해당 bot/postclose 프로세스는 확인되지 않았으며 다음 정상 PID 소비는 미확인이다.
- 현재 2026-09-07 runtime manifest에는 폐기 family가 없고 별도 `latency_spread_relief_real_operator_override`가 선택돼 있다. 현재 파일의 정상 상태와 잘못된 이전 파일을 거부하는 verifier의 완전성은 별개의 검증이다.
- 폐기된 추천에는 표본·EV·AI 승인 조건이 적용되지 않는다. 기존 안전 판정은 매 요청마다 자동 실행된다. 실제 기준은 CAUTION age 700 ms, jitter 300 ms, 기본 spread 0.5%이며 별도 spread relief는 단일 spread 원인·fresh quote·slippage/stability 등 기존 guard를 통과해야 한다.
- spread relief의 장전 설정 score 60은 effective floor 80과 `max()`로 결합되므로 실제 최저치는 80이다. floor80 자체가 달성 불가능하다는 근거는 없으며, 표본을 만들기 위해 완화할 근거도 확인되지 않았다. effective 기준과 탈락 이유를 같은 attempt별로 노출해 판단해야 한다.
- 9/4 19:20 BUY Funnel의 quote-refresh 귀속은 KRX latency-pass 복구 14건/submit 1건, NXT 복구 2건/submit 0건이었다. 복구 후 AI authority revalidation이 KRX 8건/NXT 2건을 차단했다. 이는 quote-refresh 전체 경로의 관측이며 spread-only lock 단독 효과나 비용차감 수익 증거가 아니다. 남은 병목을 latency threshold 하나로 설명할 수 없다.

### R1 — 폐기 family가 남은 runtime manifest를 verifier가 정상으로 승인 (P1)

- 코드: [PREOPEN verifier](../../src/engine/threshold_cycle_preopen_apply.py:5778), [env writer](../../src/engine/threshold_cycle_preopen_apply.py:6668), [runtime config 소비](../../src/engine/sniper_entry_latency.py:32).
- 재현: 현재 9/7 manifest를 메모리에서 복제해 selected family에 `latency_classifier_runtime_profile`, override에 `KORSTOCKSCAN_SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION=1200`을 추가했다. `verify_runtime_env_handoff` 결과는 `status=pass`, `passed=true`, `findings=[]`이고 family는 `removed_selected_families_ignored`에만 들어갔다.
- runtime 소비 반례: 격리된 Python 프로세스 안에서 같은 env key를 임시 주입해 `constants._build_trading_rules()` → `sniper_entry_latency._build_entry_config()`를 호출하면 실제 config의 CAUTION age가 1200 ms로 바뀐다. 운영 파일과 실행 PID 환경은 변경하지 않았다.
- 원인: selected family를 제거한 뒤 retired-family FAIL 목록을 만들어 해당 family가 검사를 건너뛴다. CAUTION env key는 현행 runtime 설정이기도 하므로 제거 목록에 없고 runtime config가 여전히 소비한다. writer도 제거된 selected family와 그 env 출처를 결속해 거부하지 않는다.
- 영향: 정상 새 candidate 생성 경로는 차단됐지만, 과거/혼합 manifest의 실제 override까지 검증됐다는 잘못된 PASS가 가능하다. 현재 실제 9/7 파일에 이 오염이 있다는 뜻은 아니다.
- 보완: raw selected family에서 폐기 calibration을 먼저 FAIL 처리하고 writer 입력에서도 selected-family/env 출처를 검증한다. 정상 별도 operator owner와 baseline runtime key는 일괄 삭제하지 않는다.
- 수용시험: 폐기 family만 주입, family+CAUTION key 주입, writer 직접 입력을 모두 거부한다. 정상 baseline과 별도 spread-only operator lock은 통과하고 raw `latency_block/pass`는 보존한다.

### R2 — 통합 candidate/decision 잔존으로 폐기 후보·AI 요구가 다시 표시 (P2)

- 코드: [runtime approval candidate reader](../../src/engine/runtime_approval_summary.py:715), [calibration decision rows](../../src/engine/runtime_approval_summary.py:1079), [다음 PREOPEN 상태](../../src/engine/runtime_approval_summary.py:940), [verifier AI 요구](../../src/engine/verify_threshold_cycle_postclose_chain.py:2600).
- 재현: 통합 calibration의 폐기 family를 `adjust_up`, `allowed_runtime_apply=true`로 주입했다. 같은 family가 `adjust_up` 행과 `baseline_hard_safety` 행으로 2번 표시되고 두 행 모두 `next_preopen_candidate_state=eligible_pending_preopen_selection`이었다. 현재 runtime selected는 false여서 실제 새 적용은 차단된다.
- 같은 candidate를 verifier에 넣으면 `_runtime_candidates_requiring_ai`가 폐기 family를 반환한다. AI exemption 삭제가 candidate 제거를 대신하지 못한다.
- 원인: 공통 `current_report_view`는 raw telemetry를 살리기 위해 해당 family를 broad retirement에서 제외했지만, calibration 전용 collection을 걸러내는 소비자 계약이 누락됐다.
- 보완: calibration candidates/decisions/approval requests를 읽는 지점에서 전용 retirement filter를 적용한다. 진단 행의 다음 적용 상태는 `not_applicable_retired`로 고정하고 AI 검토 분모에서도 제외한다. raw telemetry family는 계속 보존한다.
- 수용시험: 악성 통합 candidate+decision+selection을 함께 주입해 진단 행 1개, 다음 적용 후보 0개, 폐기 family AI 요구 0개를 확인한다.

### R3 — 새 진단 owner에도 달성 불가능한 결합 결손과 서로 다른 분모가 잔존 (P2)

- 코드: [performance latency section](../../src/engine/sniper_performance_tuning_report.py:2349), [performance metrics 생성](../../src/engine/sniper_performance_tuning_report.py:3041), [daily latency 진단](../../src/engine/daily_threshold_cycle_report.py:2731).
- 재현: 9/4 performance는 latency block **227 events**, 61 stocks이며 `latency_guard_counterfactual_joined`를 생산하지 않는다. 현재 helper는 결손 key를 0으로 대체해 `counterfactual_join_gap_count=227`을 출력한다. 별도 missed-entry report에는 latency terminal 사후 관측 **147 candidates**가 실제 존재한다.
- daily 소비자는 위 gap227을 그대로 복사하면서 별도로 `227 events - 147 candidates = 80`을 `events_without_counterfactual`로 표시한다. event와 attempt 분모·coverage window를 결합하지 않은 차감이므로 80을 실제 누락 수로 확정할 수 없다. block이 있는 한 미생산 joined key 때문에 performance의 결손은 계속 남는다.
- 같은 section의 owner는 여전히 `pre_submit_price_guard`, top reason은 `latency_state_danger` 100%이다. 상세 원인 143 `spread_above_caution_below_guard_cap`, 66 `spread_too_wide`, 29 `ws_age_too_high`, 1 `quote_stale`는 별도 breakdown에만 있다. 원인은 중복 가능하므로 합을 event 분모로 쓰지 않는다.
- 보완/제거 권고: 실제 same-attempt·동일 source-window 결합을 구현할 필요가 없다면 미생산 metric에 의존하는 `counterfactual_join_gap_count`와 단순 차감 gap을 제거하고 `not_evaluated`로 명시한다. 보존할 경우 eligible unique attempt → joined → unjoined/not-applicable를 직접 계산한다. owner는 기존 BUY Funnel 진단으로 일치시키고 상세 원인을 전달한다.
- 수용시험: 한 attempt의 block event를 반복해도 unique 결합 coverage가 변하지 않아야 한다. joined key 결손은 0건이 아니며, 실제 원천 147 candidates를 전부 누락으로 표시하지 않는다. source/window가 다르면 산술 차감으로 결손을 만들지 않는다.

### 검증 및 다음 작업

- 이번 targeted 회귀 **38 PASS**: 기존 폐기 candidate/lock 차단, stale selection 숨김, one-share diagnostic-only, `EntryPolicy`/`LatencyMonitor`, performance report.
- 기존 테스트가 통과해도 위 새 반례의 verifier PASS, 중복/eligible 행, AI 요구, gap227/80은 재현됐다. 이번 최종 판정은 **R1~R3 OPEN**이다. 최초 1,248 PASS를 새 반례까지 검증한 것으로 소급 해석하지 않는다.
- 코드 보완 순서는 R1 → R2 → R3이며, runtime threshold 조정이나 독립 추천 부활은 권고하지 않는다. 실행 owner는 현재 체크리스트 `LatencyRetirementFinalReviewRepair0907`, 이후 자연 확인은 `LatencyDiagnosticNaturalEvidence0907`이다.
- 문서 변경은 source/lineage와 수용시험을 재리뷰했고 backlog parser와 `git diff --check`가 PASS다. parser에서 R1~R3 수리 항목과 기존 자연 확인 항목이 각각 OPEN으로 확인됐다. 이번 재점검에 따른 코드·env 수정, report 재생성, bot 재기동, commit/push는 없다.

## 7. R1~R3 보완 구현 및 최종 재검증

판정: 2026-09-06 사용자 보완 요청에 따라 R1~R3를 구현하고 review → fix → re-review를 반복했다. 변경 범위의 미해결 finding은 0건이다. 독립 추천은 계속 RETIRED이고, 신규 튜닝축이나 실주문 권한은 추가하지 않았다.

### 수정 내용과 수용시험

| 항목 | 구현 | 최종 확인 |
| --- | --- | --- |
| R1 장전 검증·저장 | verifier는 display filter 전 raw selection을 검사한다. writer는 폐기 calibration owner가 selected collection에 있으면 env/manifest 쓰기 전에 ValueError로 거부한다. 공용 CAUTION 설정키 자체는 삭제하지 않는다. | 폐기 family만, family+age/jitter/spread key, writer 직접 입력을 거부. 기존 파일 보존/새 경로 미생성 확인. 과거 ignored audit record와 정상 baseline은 허용. |
| R2 후보·AI 분모 | 공통 calibration 전용 filter를 candidates/decisions/approval requests에 적용하고 EV·summary·verifier의 직접 소비자도 방어한다. raw telemetry family는 보존한다. | stale candidate+decision+selection을 함께 넣어도 diagnostic 행 1개, 다음 상태 `not_applicable_retired`, 추천값 없음, 해당 family AI 요구 0개. 정상 타 family와 raw `latency_block` 유지. |
| R3 진단 분모·owner | performance schema9/latency contract2에서 event와 unique stock을 구분한다. 미생산 joined key 차감과 event-candidate 차감을 제거하고 nullable legacy 필드를 `not_evaluated`로 명시한다. 상세 DANGER 원인은 중복 가능한 event reason으로 전달한다. | 후보 수 0/147/227/300 모두 gap을 산술 추정하지 않음. 실제 source contract 결손은 계속 경고/수리 경로로 전달. gross 사후 관측은 realized net EV나 승격 근거가 아님. |

- R3 연결 리뷰에서 추가로 확인한 latency → `dynamic_entry_price_resolver` source fallback을 제거했다. 가격해결기의 자체 exact counterfactual 지표는 그대로 보존하며 latency 집계가 대신 채워지지 않는다.
- 기존 `order_latency_guard_miss_ev_recovery`는 BUY Funnel diagnostic owner에 통합한다. 가격해결기 계측 완료를 latency 완료 근거로 쓰거나 독립 join/sample 작업을 재개하지 않는다. `runtime_effect=true` 작업지시는 계속 거부한다.
- 원천 결손과 의미 없는 join gate를 구별했다. legacy v1의 fabricated join gap만 무효화하며 다른 source-quality gap은 보존한다. 공통 filter는 집계 숫자/다른 schema 형태를 임의의 빈 list로 바꾸지 않는다.

### 검증 근거

- PREOPEN, runtime approval, retirement, postclose verifier, performance, daily threshold, threshold EV, workorder, engine location gate: **863 PASS**.
- entry latency, `EntryPolicy`/`LatencyMonitor`, one-share, BUY Funnel, wrapper, pipeline logger, observation source-quality, hard gate/clean baseline: **627 PASS**. 외부 `pandas_ta`의 pandas deprecation warning 1건 외 실패 없음.
- 합계 **1,490 PASS**. 초기 회귀의 예전 fallback/작업지시 기대값과 과도한 빈-dict 단정은 수정했다. 최종 회귀는 가격해결기의 정상 자체 지표 보존까지 검증했다.
- 수정 Python Black/Ruff·compile, 문서 backlog parser, `git diff --check`를 최종 gate에서 검증했다. 프로젝트 전체 테스트나 실제 주문 시험은 수행하지 않았다.
- 9/4 저장 artifact를 읽어 helper만 메모리에서 실행: performance **227 block events / 61 stocks**, missed-entry **147 evaluated candidates / gross avg close10m 0.05%** 보존. 잘못된 gap227/80은 모두 null이고 `counterfactual_join_status=not_evaluated`; 상세 최상위 이유는 `spread_above_caution_below_guard_cap`이다. 운영 report 파일은 재생성하지 않았다.
- 현재 9/7 runtime manifest 읽기 전용 검증: `status=pass`, `retired_selected_families_blocked=[]`, `missing_family_count=0`. latency selected family는 별도 `latency_spread_relief_real_operator_override`뿐이다.

### 목적 부합성·자동화·잔여 확인

- 목적 부합: 달성 불가능한 독립 후보/결손 대기를 없애고 submit drought의 실제 원인·안전 계측을 기존 BUY Funnel로 모았다. 조건을 느슨하게 하여 BUY를 늘리거나 수익 개선을 확정한 작업이 아니다.
- 자동화: 기존 예약 POSTCLOSE → daily/EV/summary 및 PREOPEN writer/verifier가 수정된 경로를 자동 소비한다. 별도 신규 producer나 사용자 승인 단계는 없다. 실제 PID 소비와 자연 장후 결과는 아직 미래 증거다.
- 다음 자연 검증 owner는 `LatencyDiagnosticNaturalEvidence0907`만 OPEN으로 유지한다. 대상 0건은 `not_observed`; producer 미실행 marker·폐기 family 비선택·latency 안전 이벤트·진단 집계를 확인한다.
- 이번 작업에서 runtime env, threshold/score80 floor/spread lock, provider/bot, broker/order/quantity/cap/hard safety는 변경하지 않았다. 병행 중인 market/panic 변경은 보존했으며 이번 latency 결함 종결 판정에 포함하지 않는다. commit/push는 수행하지 않았다.
