# BUY Funnel Sentinel → submit drought handoff 상세검토

검토 기준: `2026-09-07` R1~R5 보완 구현·반례 회귀·연결 계약 재검증. 자연 상태 수치는 `12:00:04 KST` 관찰 시점이며 새 코드의 실적용 증거가 아니다. clean tuning baseline 이후 원천, Plan Rebase §1~§8 및 당일 checklist 기준.

현행 판정: **유지 필요 / R1~R5 구현 보완 / 자연 적용·성과 확인 별도**. §1~§9는 최초 구현, §10은 결함 재발견 기록이며 현행 보완은 [§11](#11-r1r5-보완-구현과-최종-재리뷰)에 기록한다. Sentinel 자체에는 직접 runtime 권한이 없지만 별도 `entry_recheck_drought_controller`를 통한 조건부 PREOPEN 자동 경로는 있다. 운영 env·PID·보고서를 이번 작업으로 수동 변경하지 않았으며 실제 submit·순이익 개선은 아직 입증되지 않았다.

## 1. 최초 검토·구현 당시 결론 (현행 판정은 §11)

| 질문 | 판정 | 근거 |
| --- | --- | --- |
| 목적·목표에 필요한 작업인가 | **유지 필요** | BUY 후보가 실주문에 이르지 않는 원인을 넓은 threshold 완화가 아니라 attempt별 단계에서 분리하는 source-quality 선행 입력이다. |
| `SUBMIT_DROUGHT_CRITICAL` 탐지 | **작동** | 11:00 KRX 정규장 기준 AI 45, budget pass 31, latency pass 15, submitted 0으로 critical 조건을 실제 충족했다. |
| 장중→장후 자동 handoff | **작동, 당일 종결은 장후 대기** | 장중 5분 producer가 source-only followup을 만들며, 과거 2026-09-04 postclose verifier에서 workorder·EV·runtime summary handoff가 PASS했다. 9월 7일 장후 산출물은 아직 생성 시각 전이다. |
| 5개 핵심 축 분리 | **구현·검증 완료** | schema v4에서 다섯 core axis와 supporting diagnostic을 분리하고, 분모·축을 exact `record_id` terminal partition으로 계산한다. missing/`0` identity와 stage-order 위반은 fallback 없이 source-quality로 제외한다. |
| runtime 자동 적용 | **의도적으로 없음, 정상** | 이 보고서는 `runtime_effect=false`, `allowed_runtime_apply=false`, `broker_order_submit_allowed=false`인 진단·workorder 입력이다. `runtime_approval_summary` 노출은 runtime env 적용을 뜻하지 않는다. |
| 판정 조건 과도 여부 | **과도하지 않음; 일부는 오히려 비정확·민감** | AI 20건 또는 budget pass 3건의 이중 조건은 현재 자연 원천에서 도달했다. source-only 경보라 민감도는 수용 가능하지만, price/AI 축의 raw event 3건 조건과 fallback identity는 중복 이벤트로 허위 인과를 만들 수 있다. |
| 최종 목적 부합성 | **부합** | drought 탐지·자동 전달·exact attempt별 terminal causal 원인·downstream verifier가 닫혔다. 결손 계약은 root cause를 닫지 않고 source-quality-blocked 또는 FAIL로 남긴다. |

## 2. 목적·목표와 기대효과

목적은 BUY 후보가 `ai_confirmed` 또는 `budget_pass`까지 도달했는데도 `order_bundle_submitted`로 이어지지 않는 submit drought를 조기에 발견하고, 아래 다섯 경계의 원인을 서로 섞지 않는 것이다.

1. `UPSTREAM_GATE`: AI action/score/overbought/liquidity 등 submit 이전 gate에서 끝난 attempt
2. `LATENCY_PRE_SUBMIT`: budget pass 뒤 latency hard-safety에서 차단된 attempt
3. `ENTRY_AI_AUTHORITY_REVALIDATION`: submit 직전 AI 결과의 freshness·trust·authority 재검증에서 차단된 attempt
4. `PRICE_REVALIDATION`: submit 직전 가격·호가 freshness/유효성 재검증에서 차단된 attempt
5. `BROKER_RECEIPT`: 실제 broker submit 시도 또는 명시적 submit failure 뒤 receipt가 닫히지 않은 attempt

목표는 같은 exact attempt의 순서와 terminal을 보존하고, 실제 증거가 있는 축만 `causal_bottleneck_axes`로 넘기며, 증거가 없는 축은 `no_current_signal`로 유지하는 것이다. 기대효과는 broad BUY threshold나 hard-safety를 완화하지 않고 실제 병목 owner만 수리해 submit 기회 손실을 줄이고, 이후 실제 fill·terminal·비용 차감 EV를 측정할 분모를 회복하는 데 있다. Sentinel 자체의 report 건수나 workorder 생성은 수익 개선 증거가 아니다.

## 3. 자동화 연결 판정

```text
장중 KRX/NXT 5분 producer
  → buy_funnel_sentinel exact-date report/cache
  → SUBMIT_DROUGHT_CRITICAL source-only followup
  → 장후 code_improvement_workorder
  → threshold_cycle_ev / runtime_approval_summary 가시화
  → postclose verifier
  → causal axis만 conversion/workorder blocker로 전달
```

- producer: KRX `09:05~15:20`, NXT `16:00~19:20`에 자동 실행되고 시장·세션 분모를 합치지 않는다.
- handoff: `entry_submit_drought_auto_workorder`, owner=`postclose_threshold_cycle`, `operator_action_required=false`로 생성된다.
- downstream: `code_improvement_workorder`, `threshold_cycle_ev_report`, `runtime_approval_summary`, postclose verifier가 계약상 필수다.
- 권한 경계: threshold·provider·bot·broker/order guard·수량·hard safety를 변경하지 않으며 실주문 또는 sim 정책 적용 권한도 없다.
- 과거 폐기 owner: ADM/LDM은 2026-09-06 폐기됐으므로 현행 필수 소비자가 아니다. 과거 LDM submit attribution은 archive evidence이며 현재 handoff 성공 조건으로 요구하면 안 된다.

따라서 “자동화되어 있는가”에 대한 답은 **탐지와 장후 작업지시 전달은 자동, 실제 runtime mutation은 자동이 아니며 그렇게 유지하는 것이 타당**이다.

## 4. 2026-09-07 보완 전 자연 원천 확인

11:00:04 KST `KRX|KRX_REGULAR` 선택 scope의 현재 보고서는 다음과 같다.

| 항목 | 값 |
| --- | ---: |
| AI confirmed unique | 45 |
| budget pass unique | 31 |
| latency pass unique | 15 |
| order bundle submitted unique | 0 |
| submitted / AI | 0.0% |
| submitted / budget | 0.0% |

현재 보고서의 causal 표시는 `UPSTREAM_GATE=76`, `LATENCY_PRE_SUBMIT=27`, `PRICE_REVALIDATION=3`, `ENTRY_AI_AUTHORITY_REVALIDATION=14`이고 `BROKER_RECEIPT=0/no_current_signal`이다. 같은 raw scope를 strict `record_id`로 재집계하면 upstream blocker는 100 event, 43 exact attempt다. 보고서의 upstream 76은 `_ai_trace_key` 수이며 exact attempt 수가 아니다. Price 3, Entry AI 14는 이번 자연 표본에서는 모두 유효 record ID를 가져 strict 값과 우연히 일치했지만 구현은 missing record ID에서 code/name fallback을 허용한다. Broker submit/failure 원천은 0이므로 broker 축을 causal로 올리지 않은 판정은 맞다.

이는 현재 submit drought가 실제이고 threshold가 도달 불가능하지 않다는 증거인 동시에, “어느 축이 몇 attempt를 막았는가”라는 핵심 수치는 아직 contract-complete가 아니라는 증거다.

## 5. 조건 달성 가능성·과도성 검토

현재 critical 조건은 다음 OR 계약이다.

- `ai_confirmed unique >= 20`이고 `submitted / ai < 20%`
- `budget_pass unique >= 3`이고 `submitted / budget <= 10%`

현재 45/31/0 자연 표본에서 두 조건 모두 충족되므로 달성 불가능하거나 지나치게 높은 허들이 아니다. budget 3건·submit 0건만으로도 이른 시간에 critical이 될 수 있어 detection은 민감하지만, 결과가 source-only workorder이고 intraday runtime mutation을 금지하므로 안전 측면에서 수용 가능하다. 이 조건을 향후 live mutation 승인 조건으로 재사용하는 것은 금지한다.

반대로 축별 match 조건에는 다음 비합리성이 있다.

- `PRICE_REVALIDATION`과 `ENTRY_AI_AUTHORITY_REVALIDATION`은 exact attempt unique가 아니라 raw event 3건으로 match될 수 있어 한 attempt의 반복 event가 3건 조건을 채울 수 있다.
- funnel 분모도 `_stage_unique_key`의 record ID → stock code → stock name fallback을 사용하므로 record ID 결손이 source-quality gap으로 차단되지 않는다.
- `UPSTREAM_GATE` observed count는 attempt가 아닌 AI trace 수가 될 수 있고 같은 attempt의 여러 trace를 중복한다.
- verifier의 root-cause closed 판정은 unknown latency와 산출물 존재를 중심으로 하며, 다섯 축의 exact identity 결손을 검사하지 않는다.

따라서 조건의 문제는 “너무 엄격함”이 아니라 **핵심 분모와 축 상태가 exact-attempt 요구보다 느슨함**이다.

## 6. 최초 발견 결함 목록 — 당시 해소 기록

### F1 — HIGH: critical 분모 exact identity 미강제

`ai_confirmed`, `budget_pass`, `latency_pass`, `order_bundle_submitted` unique가 `_stage_unique_key` fallback을 허용한다. invalid/missing record ID가 있어도 critical 판정에 들어갈 수 있다.

### F2 — HIGH: upstream count가 attempt count가 아님

`upstream_block_unique`는 `_ai_trace_key`를 사용한다. 9월 7일 현재 보고서 76과 strict attempt 43의 차이가 자연 원천에서 확인됐다.

### F3 — HIGH: price·Entry AI·broker 축 fallback identity

세 축의 unique가 `_attempt_key`를 사용해 record ID가 없으면 code/name으로 대체한다. 동일 종목의 서로 다른 attempt가 합쳐지거나, identity 결손 row가 causal evidence로 승격될 수 있다.

### F4 — MEDIUM: raw-event floor와 attempt floor 불일치

price·Entry AI drought match가 `events >= 3`을 사용한다. 중복 event를 dedupe하지 않으므로 `sample_floor=one_explicit_attempt_per_axis` 및 same-session unique-attempt 설명과 일치하지 않는다.

### F5 — HIGH: verifier가 exact-attempt 결손을 닫지 못함

workorder·EV·runtime summary 존재와 latency unknown 위주로 closure를 판단한다. exact key missing, 축 순서 위반, 같은 종목의 다중 attempt 병합을 FAIL시키지 않아 `root_cause_closure_status=closed`가 과대 판정될 수 있다.

### F6 — DOC: 현행 traceability의 폐기 LDM 필수 소비자 잔재

ADM/LDM 폐기 후에도 문서가 submit drought handoff에 LDM attribution을 필수로 기술했다. 현행 필수 계약은 Sentinel contract→workorder→EV/runtime summary→verifier이며 LDM은 archive evidence다. 본 검토와 함께 문구를 현행화한다.

## 7. 보완 계약 — 구현 완료

`BuyFunnelSubmitDroughtExactAttemptRepair0907`에서 다음 순서로 닫았다.

1. 다섯 핵심 축을 별도 `core_handoff_axes`로 고정하고 budget/economic/sim-real/taxonomy는 supporting diagnostic으로 유지한다.
2. critical의 AI/budget/submitted 분모와 다섯 축 `observed_count`를 valid exact `record_id`만으로 계산한다. 결손은 code/name으로 보간하지 않고 축별 `missing_exact_attempt_key_events`와 source-quality gap으로 보낸다.
3. attempt state machine으로 순서를 검증한다: upstream terminal→budget, budget→latency, pre-submit AI authority, price revalidation, broker submit/failure→receipt. 이후 성공 stage가 있으면 앞선 blocker를 terminal causal로 남기지 않는다.
4. raw event floor를 exact unique attempt floor로 교체한다. 같은 record의 반복 event는 1건, 같은 종목의 서로 다른 record는 각각 1건이어야 한다.
5. conversion/workorder는 다섯 core axis 중 `observed + exact_join_valid`만 소비한다. broker submit/failure가 없으면 `BROKER_RECEIPT=no_current_signal`을 유지한다.
6. verifier가 exact denominator coverage, missing identity, stage order, causal/no-signal 분리를 검사하고 결손 시 closure를 FAIL 또는 source-quality-blocked로 남기게 한다.
7. 회귀 테스트에 missing/`0` record ID, same-code multi-attempt, duplicate events, later recovery, broker no-submit/no-receipt 구분, current retirement owner를 추가한다.

수정은 attribution·source-quality에 한정한다. submit을 만들기 위해 AI/score/latency/price/broker guard threshold를 낮추거나 runtime env·provider·bot·수량을 변경하지 않는다.

## 8. 최종 검증

- 관련 현행 회귀: BUY Funnel, cache parity, workorder, EV, runtime summary, conversion lane, verifier 7개 모듈 **498 PASS**.
- 새 회귀는 missing/`0` record ID, 분모·축 stage order, duplicate event, later recovery, same-code multi-attempt, broker failure/no-signal, malformed v4 contract와 source-quality-blocked propagation을 검증한다.
- Black/Ruff/compile/diff 및 checklist parser 검증을 통과했다.
- 운영 report·runtime env·PID·주문·bot 상태는 변경하지 않았다.

최종 판정은 **기능 유지, 자동 handoff 유지, runtime 비적용 유지, exact-attempt 집계·consumer·verifier 보완 완료**다.

## 9. 보완 결과와 자연 원천 재대사

- producer schema를 v4로 올리고 `ai_confirmed`, `budget_pass`, `latency_pass`, `order_bundle_submitted` 분모를 valid exact `record_id`로 고정했다. `latency_pass`는 선행 budget, submit/failure는 선행 budget+latency를 요구하며 위반 행은 집계에서 제외한다.
- terminal state machine은 동일 attempt의 뒤이은 성공 stage가 앞선 blocker를 causal로 남기지 않으며, 다른 blocker로 대체된 경우와 실제 downstream progress를 별도 계수한다.
- conversion lane은 다섯 core axis 중 `observed + exact_join_valid`만 blocker로 만들고 불완전한 v4 계약이나 빈 causal partition을 split complete로 판정하지 않는다. supporting budget/economic/sim-real/taxonomy은 causal 승격 대상이 아니다.
- workorder는 v4 exact 계약 누락·구조 불일치를 `artifact_regeneration_required`, 자연 identity/order 결손을 `source_quality_blocked`로 전파한다. verifier는 분모 census, 두 종류의 stage-order census, 축별 exact/event/terminal count, 계약 복사, causal/no-signal partition과 runtime authority false를 대사한다.
- 11:40 KST의 기존 sentinel lossless cache를 덮어쓰지 않고 읽기 전용으로 재집계한 KRX 결과는 AI 49, budget 36, latency 16, submitted 0, exact contract `pass`였다. terminal causal은 `UPSTREAM_GATE=41`, `LATENCY_PRE_SUBMIT=17`, `ENTRY_AI_AUTHORITY_REVALIDATION=4`, `PRICE_REVALIDATION=1`, `BROKER_RECEIPT=0`이며, 따라서 current drought 탐지는 유지되고 broker 축은 자연 증거 부재로 `no_current_signal`을 유지한다.

## 10. 최종 재점검 — 완료 판정 재개방

이 절의 당시 요청은 리뷰였다. 당시 생산 코드·report·runtime env·PID·주문은 수정하지 않았고, 반례와 다음 보완 owner를 기록했다. 이후 사용자 구현 지시로 수행한 보완은 §11이다. 기존 테스트 PASS는 아래 새 반례의 무결성을 보증하지 않는다.

### 10.1 판정·자연 증거

- 목적은 기존 진입/submit 병목의 정확한 식별과 담당 수리 경로 연결이다. 신규 튜닝축·threshold 완화·강제 매수는 목적이 아니다. 기능은 유지하되 현 상태를 결함 없는 구현 또는 수익 개선 완료로 인정하지 않는다.
- `buy_funnel_sentinel_2026-09-07.json`의 `as_of=12:00:04`, schema v4, KRX 분모는 AI **50**, budget **36**, latency **16**, submitted **0**이다. terminal 표시는 upstream **43**, latency **16**, Entry AI **3**, price **1**, broker **0**, exact contract `pass`다. 이 값은 현행 보고값이며 아래 결함 때문에 정확한 인과 분할을 입증하지 않는다.
- 당일 lossless cache(최신 event `12:00:02.299773`)에는 KRX `blocked_liquidity` 64 event와 `blocked_overbought` 139 event가 있다. 이들은 새 core upstream 계산 대상이 아니다. event 수는 unique attempt 수가 아니다.
- `record_id=40475`: `09:51:52 latency_block → 09:53:27 budget_pass → 10:21:54 blocked_strength_momentum`; `40589`: `11:14:14 latency_block → 11:16:19 budget_pass → 11:41~11:42 blocked_strength_momentum`. 두 record 모두 이후 latency pass/submit이 없지만 다섯 core terminal이 모두 0이다. 실제 병목 해소가 아니라 재시도 경계·미지원 terminal 누락이 결합된 사례다.
- 최근 3거래일(9/3, 9/4, 9/7) 기존 보고서에는 같은 KRX scope의 critical 및 addressable 표시가 있다. 9/3·9/4는 구 schema 집계이므로 새 exact 계약 충족 증거로 재사용할 수 없지만, 경보 floor의 관찰 가능성은 확인된다. 당일 source-quality preflight는 점검 시 `missing`이며 장후 생성 전 대기다.

### 10.2 자동화와 실제 적용은 별도 판정

| 경로 | 구현·자동화 | 현재 증거/제한 |
| --- | --- | --- |
| 장중 Sentinel → 장후 workorder → EV/runtime summary → verifier | 자동 연결 있음 | 5분 source-only producer와 장후 소비자 존재. 9/7 장후 종결은 아직 미확인 |
| workorder → 실제 코드 수리 | 무인 수리 완료를 뜻하지 않음 | 당일 checklist 규칙은 사용자 Codex 구현 지시 후 실행. `operator_action_required=false`는 작업지시 생성에 대한 값 |
| Sentinel → 일일 drought controller → 다음 PREOPEN → 기존 recheck family | 별도 조건부 자동 경로 있음 | Sentinel의 `runtime_effect=false`는 이 간접 경로가 없다는 뜻이 아님 |
| 오늘 recheck 실제 반영 | PREOPEN 미선택 확인 | manifest의 `drought_policy_version_invalid`, runtime env의 `disabled_or_removed`에 `entry_opportunity_recheck_runtime` 존재. 현행 PID 소비·실제 submit/fill/EV 증거는 별도 |

연결 소스: [controller 입력](../../src/engine/scalping/entry_ai_gate_backtest.py:174), [고정 profile·조건](../../src/engine/scalping/entry_recheck_policy.py:29), [장후 호출](../../deploy/run_threshold_cycle_postclose.sh:1603), [PREOPEN 재검증](../../src/engine/threshold_cycle_preopen_apply.py:1850), [당일 선택 결과](../../data/threshold_cycle/runtime_env/threshold_runtime_env_2026-09-07.json:689).

### 10.3 재현된 결함과 보완 순서

#### R1 — P1: runtime 소비자가 Sentinel exact 계약을 검증하지 않음

`_drought_day_summary`는 날짜와 일별 preflight만 검사한 뒤 `scope_summary`에 분모/causal 목록을 넘긴다. Sentinel의 `exact_attempt_contract`, 축별 exclusion·terminal 증거는 검사하거나 history에 보존하지 않는다. PREOPEN 재계산도 이 축약 history를 재사용한다. recheck 자체의 post-apply exact 계약은 검증하지만, 선행 Sentinel exact 계약을 대체하지 못한다.

반례: 자연 보고서의 top-level/모든 scope/복사본 `exact_attempt_contract`를 메모리에서 제거하고 일별 preflight만 PASS로 고정해 `_drought_day_summary`를 호출하면 `source_quality_pass=true`, `addressable_critical=true`가 그대로 남는다. 실제 runtime을 켠 실험은 아니다. 오늘 PREOPEN은 구 controller version 때문에 미선택됐고, 9/7 장후 후보에는 당일 preflight missing이라는 별도 대기 조건이 있으므로 이 반례를 현재 오적용 실적으로 해석하지 않는다.

보완: Sentinel→workorder/conversion→controller→PREOPEN에 하나의 공통 exact 검증 결과·source binding을 전달한다. 손상된 row/scope만 분리할 수 있으면 제외하고, 판정 분모를 재구성할 수 없는 scope만 적용 차단한다. 현행 날짜의 schema downgrade는 legacy 허용으로 우회하지 못해야 한다. 정상 scope의 유효 분모·causal 증거까지 이유 없이 전부 차단하지 않는다.

#### R2 — P1: 실제 producer와 core 축 stage 목록이 어긋남

[core 목록](../../src/engine/buy_funnel_sentinel.py:42)은 upstream을 AI 관련 네 stage로 제한한다. liquidity/overbought/strength terminal은 표시 목적에 포함되지만 exact partition에는 없다. Broker 축은 `broker_submit_failed|buy_order_failed|submit_order_failed`를 기다리는 반면, 현재 일반 주문 실패 producer는 [order_bundle_failed](../../src/engine/sniper_state_handlers.py:71783)를 낸다. 그 이벤트에는 `broker_submit_attempt_count`, `broker_submit_success_response_count`, `order_bundle_failure_mode`가 이미 있다.

반례: `budget_pass → latency_pass → order_bundle_failed(attempt=1, success_response=0)`가 broker terminal **0**, source quality **pass**로 끝난다. `ai_confirmed → blocked_liquidity`도 upstream **0/pass**다. 현재 broker 0건을 단순 표본 부족으로만 설명할 수 없는 구조적 사각지대다.

보완: 기존 producer stage/원인 계약을 inventory로 대사해 exact-cache·raw·summary의 소비를 맞춘다. `pre_broker_blocked`와 실제 broker 호출 후 실패/응답 신원 결손을 구분하고, 전자는 broker 실패로 올리지 않는다. 최종 차단/진행 중/결손을 구별해 미분류를 조용한 `no_current_signal`로 닫지 않는다. broker API나 guard를 바꿀 필요는 없다.

#### R3 — P1: 재평가를 통과·해소로 오인하고 이전 pass를 재사용함

[state machine](../../src/engine/buy_funnel_sentinel.py:847)은 `ai_confirmed|budget_pass|latency_pass|order_bundle_submitted` 중 아무 progress event에나 terminal을 지운다. 동일 record의 `seen_budget_pass/seen_latency_pass`는 재시도 시 초기화하지 않는다. `record_id`는 lineage root가 될 수 있지만 그 record의 하루 전체를 한 execution attempt로 취급하면 재평가 경계가 사라진다.

반례: `budget_pass → latency_block → budget_pass`가 latency terminal **0/pass**, `budget_pass → latency_pass → price_block → budget_pass → submit`도 과거 latency pass를 빌려 순서 위반 **0/pass**가 된다. 후자에 앞 세 event의 `main_lifecycle_attempt_id=A`, 뒤 두 event의 `main_lifecycle_attempt_id=B`를 명시해도 record가 같으면 결과는 같다. 첫 반례는 해당 gate 통과 증거가 없으며 새 attempt가 진행 중인 경우에도 `recovered`와 분리해야 한다.

보완: 가능한 producer-owned attempt/trace/bundle identity와 실행 순서로 재시도를 분리한다. 이른 stage의 재실행은 뒤쪽 gate 통과가 아니다. 연결 불가능한 경계는 pending/unknown/source-quality로 남기고 이전 attempt의 차단 이력은 보존한다. 실통과, 다른 blocker로 대체, 새 평가 시작, 주문 접수를 서로 다른 상태로 검증한다.

#### R4 — P2: 비차단 price fallback을 terminal 가격 차단으로 계산

`ENTRY_PRICE_GUARD_STAGES`는 `entry_ai_price_canary_fallback`을 포함한다. 실제 [fallback](../../src/engine/sniper_state_handlers.py:45576)은 `ai_engine_unavailable`, `above_best_ask` 등에서 기존 `planned_orders, False`를 반환하므로 새 AI 가격 적용 실패이지 주문 차단 자체가 아니다.

반례: `budget_pass → latency_pass → entry_ai_price_canary_fallback(ai_engine_unavailable)`만 있어도 price terminal **1/pass**다. 이후 submit이 생기면 지워질 수 있지만, 그 전이나 다른 미지원 blocker에서 종료되면 허위 causal이 된다.

보완: fallback은 보조 진단으로 남기고 실제 skip/최종 pre-submit guard 차단만 core causal로 사용한다. 회복 증거 부족을 가격 차단으로 추정하지 않는다. 오늘 관찰된 fallback 3 event는 `skip_low_confidence` 2, `above_best_ask` 1이며 이 raw 수로 price 차단을 판정하지 않는다.

#### R5 — P2: verifier의 분모 대사·현행 schema 강제가 불완전

[exact verifier](../../src/engine/verify_threshold_cycle_postclose_chain.py:3261)는 census key/합계와 복사 필드를 검사하지만 실제 분모 `contract.stage_unique`와 `denominator_exact_attempt_counts`의 동일성은 검사하지 않는다. schema <4는 대상 날짜와 무관하게 `legacy_not_required`다.

반례: 12:00 자연 계약의 `stage_unique.budget_pass`만 **36→999**로 바꾸고 exact census는 36으로 두어도 verifier **pass**다. 날짜를 오늘로 둔 schema3·빈 exact 계약은 **legacy_not_required**다.

보완: 분모·ratio·critical·축 terminal을 같은 입력으로 재산출하고 current report의 source date/schema/census/selected scope를 대사한다. 과거 artifact는 archive 읽기만 허용하고 current runtime/closure 증거는 별도 migration 기준을 통과해야 한다. 후속 EV/runtime summary는 primary 문자열 존재뿐 아니라 같은 source generation을 소비했는지도 검증한다.

### 10.4 조건의 유지·보완·제거 판단

| 조건 | 판정 | 이유/수정 방향 |
| --- | --- | --- |
| AI ≥20 & submit/AI <20%, 또는 budget ≥3 & submit/budget ≤10% | 유지 | 자연 원천에서 도달. source-only 경보이며 수익·실주문 승인 조건이 아님 |
| 같은 scope 최신 critical + 최근 3거래일 중 2일 critical | 유지, exact 입력 보완 | 경보 반복성은 관찰됨. 오늘 PREOPEN 미선택은 구 controller version 때문이며, 9/7 preflight 미생성은 오늘 장후 후보의 별도 대기 조건 |
| recheck exact armed20의 전환율 중단, paired10의 비용 차감 EV/순손익 검증 | 기본 진입조건과 분리해 유지 | paired10은 초기 controller ON의 선행조건이 아니라 성과 중단·추가 escalation 조건. 아직 자연 달성 확률을 입증하지 못했으므로 불가능하다고 단정해 삭제하지 않음 |
| 20거래일 안 scope·체결 cohort별 유효 pair10 | 달성률 계측·재검토 | 기존 `EntryRecheckNaturalAttribution0907`가 발생률·version/episode 누적 창 검토를 소유. 부족 표본을 zero EV로 보간하거나 hard safety를 낮추지 않음 |
| 진단 결함 수리에 BBO + 모든 1/3/5/10/20/30/60분 MFE/MAE + 양수 EV | repair 완료 조건에서 분리 권고 | [conversion acceptance 문구](../../src/engine/automation/conversion_lane.py:682)에 경제성 연구·one-share 후보와 계측 수리가 섞여 있다. 문구가 실제 실행 hard gate라는 증거는 없으나, 무제출/late-session 표본에서 수리까지 경제성 완성을 기다리게 하면 부당함 |
| 해당 axis의 실제 producer 증거 | 유지하되 stage 계약 수리 | 존재하지 않는 alias를 기다리는 broker 조건을 제거/매핑하되 receipt 증거 요구 자체를 제거하지 않음 |

진단 수리 acceptance는 identity·순서·terminal·exclusion·consumer 대사로 닫고, 실제 경제성 변화의 acceptance는 기존 owner의 비용 차감 EV·bounded 권한·rollback으로 별도 닫는다. 새로운 튜닝축을 추가하거나 Sentinel에 직접 runtime 권한을 부여하지 않는다.

### 10.5 검증·다음 owner

- 이번 재실행: Sentinel/cache/workorder/EV/runtime summary/conversion/verifier **498 PASS**; recheck policy/controller/backtest/PREOPEN **297 PASS**. 두 실행은 서로 다른 test file 집합이며 전체 저장소 검증은 아니다.
- 문서 재리뷰에서 당일 PREOPEN의 구 version 차단과 9/7 장후 preflight 미생성 대기를 분리하고 반례 조건을 보강했다. checklist print-only parser는 **46개 OPEN**, 신규 repair owner **1개**를 인식했고 `git diff --check`를 통과했다. Project/Calendar sync는 실행하지 않았다.
- 별도의 메모리 반례 8건으로 stage 누락, 재시도/회복 오인, fallback 오귀속, census mismatch, current legacy 우회, controller exact 입력 누락을 재현했다. 메모리 반례는 아직 checked-in regression test가 아니며 다음 구현에서 고정해야 한다.
- 자연 JSON/cache와 PREOPEN manifest/env를 읽기 전용으로 대조했다. bot/PID·생산 report/env·broker 호출·threshold/provider 변경은 실행하지 않았다.
- 당시 구현 owner: `BuyFunnelFinalContractReviewRepair0907` (현재 §11에서 코드 보완 완료). 순서는 R1/R5 공통 계약 → R2/R4 producer/consumer taxonomy → R3 attempt state → acceptance 분리 → 통합 재리뷰였다. runtime 실적용은 기존 별도 guard를 따른다.
- 자연 장후/다음 PREOPEN/PID/submit/fill/terminal·EV owner는 기존 OPEN `EntryRecheckNaturalAttribution0907`을 재사용한다. 오늘 장후 검증과 다음 PREOPEN의 신규 계약 소비가 확인되기 전에는 자동 적용 완료·수익 개선 완료로 종결하지 않는다.

## 11. R1~R5 보완 구현과 최종 재리뷰

사용자 `결함보완하고 코드리뷰 후 수정보완` 지시에 따라 기존 진단·recheck 입력 계약을 보완했다. 새 튜닝축이나 Sentinel 직접 주문 권한은 추가하지 않았다. 공통 검증기는 새 engine-root 모듈 대신 `src/engine/automation/submit_drought_contract.py`에 두었다. 소유 경계는 순수 source 계약 검증이며 broker/런타임 I/O가 없다.

| 결함 | 구현·보완 결과 | 검증 경계 |
| --- | --- | --- |
| R1 runtime 입력 미검증 | controller는 scope별 Sentinel schema5/exact2 계약·날짜·as_of·digest를 history에 보존한다. PREOPEN은 같은 공통 검증기로 원 계약과 축약 scope row를 재계산한다. | 손상 scope는 제외, 정상 scope는 유지. preflight가 없거나 scope를 특정할 수 없는 원천 손실은 승인 차단. |
| R2 실제 stage 누락 | liquidity/overbought/strength/VPW/gap/수량/expiry terminal을 upstream에 포함한다. `order_bundle_failed`의 실제 시도·응답 수와 failure mode로 pre-broker 차단과 broker 실패를 분리한다. | 미지원 terminal/불일치 provenance는 unknown/source-quality gap이며 `no_current_signal/pass`로 숨기지 않는다. API/주문 guard 변경 없음. |
| R3 재평가·회복 혼합 | record 안 explicit attempt와 순서 기반 cycle을 분리한다. A/B/A interleaving, 동일 promotion ID 재사용, retry와 실제 gate 통과를 구별하며 이전 cycle pass를 새 submit에 재사용하지 않는다. | 이전 blocker·pending·submitted·unknown 상태와 exact denominator/terminal census 보존. |
| R4 비차단 fallback 오귀속 | `entry_ai_price_canary_fallback`은 보조 가격 진단으로 유지하고 core terminal에서는 제외한다. | 실제 skip/최종 price guard만 price causal로 인정. |
| R5 느슨한 verifier | 분모·ratio·critical·ledger record binding/순서·terminal 합계 및 runtime authority false를 공통 검증한다. 현행 날짜의 schema downgrade를 금지한다. EV/runtime summary의 계약 복사가 원 Sentinel과 다르면 generation mismatch FAIL/재생성 필요로 남긴다. | workorder 생성·구현 완료와 source-quality/root-cause 종결을 분리한다. |

재리뷰 중 추가로 확인해 수정한 사항:

- 확장 upstream 진단이 recheck 권한을 넓히지 않도록 addressable 근거를 기존 AI score/WAIT와 Entry-AI authority terminal로 제한했다. liquidity·수량·expiry만 있는 drought는 진단 가능하지만 recheck 활성화 근거는 아니다.
- 원본 terminal이 요약 로그에서 생략되면 exact-cache 보존만으로 복구되지 않는다. `pipeline_event_summary`는 해당 upstream raw를 suppression 대상에서 제외한다. Sentinel cache version은 일반8/lossless10으로 올려 오래된 축약 cache를 새 계약으로 재사용하지 않는다.
- 과거 producer summary만 남은 terminal은 raw-derived summary와 중복 합산하지 않고 원본 차이를 identity gap으로 표시한다. 요약의 종목/시각만으로 누락 attempt·venue를 추정하지 않는다. 이 비격리 손실이 있는 scope 입력은 승인 차단하며, raw-only 모드에서도 동일하게 검증한다. 원본이 남은 정상 scope/행은 불필요하게 전체 차단하지 않는다.
- 진단 수리 acceptance에서 모든 horizon MFE/MAE·양수 EV·one-share 승격 요구를 분리했다. 수리는 exact 원인/계약/consumer 대사로 닫고, 실제 경제성·확대 승인은 기존 recheck owner와 rollback 계약이 계속 소유한다.

### 11.1 조건 달성 가능성과 실제 자동화

탐지 floor `AI≥20 & submit/AI<20% OR budget≥3 & submit/budget≤10%`와 기존 3거래일 반복성 조건은 변경하지 않았다. 자연 원천에서 탐지 조건은 도달했으며, paired10은 초기 ON 조건이 아니라 성과 중단·추가 확대 판정용이다. paired10의 20거래일 내 달성률은 아직 자연 증거가 없어 삭제나 완화 근거로 삼지 않는다.

새 schema5 Sentinel → 일일 controller → PREOPEN → 정상 기동 PID 경로는 코드로 연결되고 조건 충족 시 별도 매회 사용자 선택을 요구하지 않는다. 그러나 **이번 코드 수정이 기존 PID 또는 이미 생성된 env에 소급 적용되는 것은 아니다**. 장기 PID의 raw 보존 변경은 다음 별도 허용된 정상 기동부터 적용된다. 구 schema3/4 보고서는 runtime history의 새 exact 계약을 대체할 수 없다. 정확한 최근 3개 거래일이 새 계약으로 준비되기 전의 미선택은 계약 이행 대기이며, 허위 floor 완화나 구 성과/stop 삭제로 해결하지 않는다.

### 11.2 검증과 자연 후속

- 최종 통합 **1,061 PASS**: Sentinel/공통 계약/cache parity/workorder/conversion/EV/runtime summary/verifier/controller/backtest/recheck/PREOPEN/pipeline logger·summary/wrapper/cron·freshness detector 17개 테스트 파일. 보완 후 재실행도 동일 통과했다.
- 문서·checklist parser·engine location gate **53 PASS**. 합계 **1,114 PASS**이며 전체 저장소 검증은 아니다. Black/Ruff/compileall/`git diff --check` PASS. 체크리스트 print-only parser는 OPEN 45개를 인식하며 구현 owner는 완료, 자연 후속 owner는 1개 OPEN이다. Project/Calendar sync는 실행하지 않았다.
- `korstockscan-review-gate`에 따라 producer→cache/summary→workorder/conversion→controller→PREOPEN→EV/runtime summary→verifier 계약을 재리뷰하고 발견 반례를 회귀 테스트로 고정했다. 이 gate 때문에 봇 재기동·운영 보고서 재생성·광범위 자동화 실행은 보류했다.
- 자연 후속은 기존 OPEN `EntryRecheckNaturalAttribution0907`이 소유한다. 최신 Sentinel schema/원본 terminal 보존, 날짜별 source-quality, controller 생성, PREOPEN 선택·미선택 사유, PID 소비, exact submit/fill/terminal 및 비용 차감 EV를 별도로 확인한다. 코드 PASS만으로 drought 해소·순이익 개선·실적용 완료를 선언하지 않는다.
- 최종 판정: 검토 범위의 미해결 코드 finding **0건**. 목적은 정확한 병목 진단과 기존 조건부 자동화 연결이며 이에 필요한 코드 보완은 종결했다. 운영 report 수동 재생성·실주문·runtime env 변경·bot 재기동·threshold/provider/수량/hard-safety 변경은 수행하지 않았다. 실제 효과와 신규 계약의 자연 소비는 미확인이다.
