# Institutional / Microstructure Context 구현·최종 리뷰 — 2026-09-06

현재 판정은 아래 §7 구현 후 재리뷰와 병합 전 gate 보완을 따른다. §1~5의 925 PASS·0 finding 및 §6의 R1~R5 OPEN은 이전 단계의 기록이다. 변경 범위 코드 검증, 중간 회귀의 종결, 실제 PID 확인을 분리한다.

## 1. 판정

- `institutional_flow_context`: **scheduled/current chain 폐기**. sole consumer인 scalping ADM/LDM이 폐기됐으므로 별도 REST aggregate를 매일 다시 만들 이유가 없다. 기존 exact AI snapshot의 `investor_flow`/`program_flow`는 유지한다.
- `microstructure_reaction_context`: **진단/source-quality owner로 유지**. 신규 튜닝축이나 direct entry modifier로 승격하지 않는다. holding의 명시적 소비는 fail-closed source-quality 평가로 한정한다.
- 런타임 적용: threshold/PREOPEN env 자동 적용을 추가하지 않았다. 기존 runtime feature-packet 계산은 자동이고, 실제 전달/소비 여부를 delivery telemetry v2로 검증 가능하게 했다.

## 2. 구현 근거

### Institutional flow

- 2026-09-04 전용 report는 120/120 `OK`였지만 `source_mix=ka10059+ka10061`뿐이었고, `join_rate_pct`는 consumer join이 아니라 source status 성공률이었다.
- 같은 날짜 exact AI `analyze_target` payload에는 `program_flow` 117건, `investor_flow` 47건이 이미 존재했다.
- wrapper를 inherited override와 무관한 permanent OFF로 고정하고 producer command를 제거했다.
- current threshold EV/runtime approval은 historical artifact를 읽지 않고 명시적 `retired`를 반환한다.
- 명시적 offline CLI는 schema v2, `scheduled_producer=false`, `archive_offline_source_only`, `source_success_rate_pct` 계약으로만 남겼다. legacy `join_rate_pct`는 deprecated alias임을 표시했다.

### Microstructure reaction

- 2026-09-04 report는 26,554행 중 `ok=61`(0.23%), missing/unusable 26,493행이었다. clean-baseline cumulative는 unique opportunity 790, source-quality-pass outcome 39, coverage 4.962%, 비용차감 EV -0.636615%였다. 현 evidence로 derived entry modifier 승격 근거는 없다.
- 기존 hard-coded quote stale 1,200 ms를 canonical feature packet과 같은 event-specific `ai_quote_stale_max_ms`로 통합했고 default는 3,000 ms다. broker submit stale guard는 변경하지 않았다.
- feature packet 존재만으로 `sent=true`를 기록하던 오류를 제거했다. 최종 직렬화 provider payload를 기준으로 `computed`, `sent`, `consumed`, consumer, delivery state를 분리한다.
- telemetry v2 이전 행은 과거 `sent` 값을 신뢰해 재분류하지 않고 `legacy_unverifiable`로 집계한다.
- 누적 판정은 한 날짜의 rollup 누락/stale 때문에 전체 clean-baseline history를 막지 않는다. 결손 날짜와 source-quality-blocked 날짜를 제외하고 valid row/window만 집계한다. 결손은 `source_quality_exclusion_warnings`, 실제 후보 차단은 usable window 없음, source-quality-pass outcome 20건 미만, 비용차감 EV 비양수로 분리했다.
- derived context는 standalone BUY/threshold/runtime apply 권한이 없다. entry exact payload에 직렬화되지 않으면 `computed_not_sent`, holding source-quality에서 사용되면 explicit internal consumer receipt를 남긴다.

## 3. 코드리뷰 결함 및 보완

1. 1차 리뷰에서 holding compact payload 안의 pre-final `microstructure_reaction_context_sent=false`가 실제 direct field 포함 여부와 모순될 수 있음을 발견했다.
   - payload 내부 표시는 `computed`로 바꾸고, `sent`는 최종 serialization 뒤의 runtime receipt에서만 결정하도록 수정했다.
2. historical delivery 행의 기존 `sent=true`를 새 의미로 잘못 집계할 위험을 발견했다.
   - `microstructure_reaction_delivery_telemetry_version=v2`가 있는 행만 computed/sent/consumed 집계에 포함하고 나머지는 legacy-unverifiable로 분리했다.
3. 누적 exact-outcome 미결합을 missing rollup과 같은 hard blocker로 두면 valid row/window exclusion 원칙과 충돌했다.
   - exact/outcome 결손은 exclusion warning으로 이동하고, 유효 표본·양의 EV에 기반한 bounded review 판정과 분리했다.

## 4. 검증

- Python compile: 변경 Python producer/consumer/report/logger 전체 PASS.
- Targeted regression 1차: 262개 중 257 PASS, 변경된 계약의 구 기대값 5건 FAIL을 확인했다.
- 테스트를 새 retirement/freshness/delivery/excluded-date 계약으로 보완한 뒤 targeted regression: **268 PASS**.
- 최종 확장 회귀(생산자·entry/holding transport·logger·daily/EV/runtime summary·retirement verifier·wrapper): **925 PASS**.
- 변경 Python compile, Black check, postclose wrapper `bash -n`, `git diff --check`: **PASS**.
- 문서 backlog parser `--print-backlog-only --limit 500`: **PASS**, 2026-09-07 자연 실행 확인 1건이 정상 OPEN으로 파싱됐다.
- 최종 self-review: unresolved finding **0건**. threshold/order/quantity/provider/bot/PREOPEN live env 권한 변경은 없다.

## 5. 남은 자연 실행 확인

- 2026-09-07 정상 PID와 장후 report에서 delivery telemetry v2를 확인해야 한다. 코드 테스트는 실제 provider payload/로그 발생이나 기대수익 개선의 증거가 아니다.
- dedicated institutional report가 새로 생성되지 않고 current summaries가 `retired`인 것이 정상이다.
- 자연 favorable/match가 0건이어도 계측 정상성과 경제성은 분리한다. threshold 완화, 새 축 추가, 실주문 또는 provider/bot 변경으로 표본을 만들지 않는다.

## 6. 목적·자동화·조건 달성 가능성 재리뷰

### 현재 판정과 기대효과

- Institutional: 전용 aggregate 폐기는 목적에 부합한다. 유일한 ADM/LDM consumer가 폐기됐고, wrapper permanent OFF와 current summary의 retired 처리가 연결됐다. 기대효과는 중복 REST 수집·보고 비용과 폐기 경로 복구 작업의 제거다. 기존 exact AI investor/program 원천은 유지된다. 별도 수익 개선이나 PREOPEN 승격 조건은 이 폐기 작업의 성공 기준이 아니다.
- Microstructure: feature-packet 계산, entry/holding 입력 구성, pipeline/report 집계와 일부 source-quality workorder 전달은 자동이다. 기존 holding source-quality consumer도 존재한다. 반면 derived entry modifier의 독립 후보→PREOPEN→실행→성과 귀속 경로는 없다. 진단 목적에는 자동 apply가 필요하지 않지만, 현재 후보/소비 표시는 실제 권한과 효과를 과장할 수 있다.
- 재리뷰 미해결 finding은 **5건(R1~R5)**이다. 자동화 연결 전체 PASS 또는 기대수익 개선 완료로 판정하지 않는다. 이번 요청은 재점검이므로 실행 코드와 운영 상태는 변경하지 않고 결함·보완/제거안과 수용시험을 기록한다.

### 실제 산출물과 읽기 전용 재평가

- 2026-09-04 기존 일일 artifact는 schema 3으로 delivery v2 이전 자료다. 총 26,554행, ok 61, stale 472, partial 13, not_evaluated 1,423, missing 24,585이며 favorable entry opportunity는 0건이다.
- 2026-09-06 현재 코드의 `_clean_baseline_cumulative_opportunity_exploration('2026-09-04')`를 읽기 전용으로 호출했다. available dates 67, fresh rollups 58, source-quality-allowed dates 54, outcome pass 39, EV-evaluable 39, 비용차감 반사실 평균 -0.636615%, 상태 `non_positive_ev_keep_observe`였다. 과거 저장 report의 included 55와 다르며, 현재 source signatures로 stale rollup을 다시 제외한 결과다.
- 20건 표본 조건은 과거 누적 자료에서 이미 충족했다. 음의 EV를 양의 효과로 판정하기 위해 숫자를 완화할 근거는 없다. 다만 39건은 v2/수정 후 동일 조건의 성과 증거가 아니다. favorable/no-entry 표본의 미래 수익률 평균은 context 추가에 따른 순이익 증가나 실제 소액·고빈도 청산 성과를 입증하지 않는다.
- 과거 저장 누적 report의 unsubmitted 786건 중 no_matching_watch_cycle 584, reference_time_mismatch 152, time_exact 50이다. 결합 결손은 736/786으로, 조건 달성 가능성의 주요 문제는 원천 결합이다. 5초 허용차 확대보다 동일 attempt의 원천/결과 연결을 우선 검토한다.

### R1 — 신선도 결손이 favorable로 승격되고 공통 threshold 정규화도 불일치 (P1)

- 코드: [reaction freshness](../../src/engine/scalping/microstructure_reaction_context.py:853), [canonical packet freshness](../../src/engine/scalping_feature_packet.py:614).
- 재현: 기존 trusted-tick fixture에서 quote age를 제거하거나 tick time을 제거해도 `context_status=ok`, `entry_reaction_quality=favorable_reaction`이 반환됐다. 현재 비교는 age가 None이면 stale 검사를 건너뛴다.
- 재현: `ai_quote_stale_max_ms=0`, quote age 200 ms에서 packet threshold는 3000 ms, reaction threshold는 1 ms가 되어 같은 입력이 서로 다른 판정을 받았다.
- 영향: 부족한 freshness 증거를 favorable/EV 모집단으로 오인하고, 일부 입력은 반대로 불필요한 stale/partial 상태가 된다. broker guard 우회가 확인된 것은 아니다.
- 권고: 동일 정규화 함수로 effective threshold를 결정하고, missing/invalid/future age는 명시적 품질 결손으로 처리한다. submit safety 기준을 조정하는 작업으로 확장하지 않는다.
- 수용시험: None/빈 값/0/음수/NaN/미래 timestamp/정상값의 packet·reaction 일치; age 결손의 favorable 진입 0건.

### R2 — 실제 전송·소비 receipt가 아직 정확하지 않고 logger 전달도 일부 누락 (P2)

- 코드: [delivery finalizer](../../src/engine/scalping_feature_packet.py:1125), [cache annotation](../../src/engine/ai_engine_openai.py:1836), [holding 호출 순서](../../src/engine/ai_engine_openai.py:10051), [AI ops logger](../../src/engine/sniper_state_handlers.py:50139), [tick quality logger](../../src/engine/sniper_state_handlers.py:50589).
- 재현: 실제 key 없이 설명 문자열에 `microstructure_reaction_context_status`만 들어 있어도 `sent=true/consumed=true/provider_model`이 반환됐다. 문자열 substring 검사와 JSON key 검사가 섞여 있다.
- 재현: cache-hit annotation은 이전 receipt의 `computed/sent/consumed=true`를 유지했다. 새 계산이나 provider 호출 횟수로 그대로 집계하면 중복이다. finalizer 자체도 transport 전에 실행되며 `sent`이면 곧바로 provider 소비로 간주한다.
- 재현: `_build_ai_ops_log_fields`는 reaction threshold를 누락했고 `_build_tick_source_quality_log_fields`는 threshold와 delivery v2 필드를 모두 누락했다. upstream holding preflight의 내부 품질 소비도 해당 delivery receipt에 포함되지 않는다.
- 권고: payload 포함, 실제 요청 시도/응답, 내부 소비, cache reuse를 구분하고 call/parent trace로 중복 제거한다. provider payload 포함은 모델의 판단 사용 증명이 아니다. 공통 logger 경로에 threshold와 해당 경로에서 실제 발생한 receipt를 보존한다.
- 수용시험: 이름만 포함한 문자열·field omission·cache·provider 미호출/실패·정상 응답·내부 preflight 각각의 정확한 계측; AI result→logger→일일 report에서 필드와 호출 분모 일치.

### R3 — 후보 표본 floor가 유효 EV 표본과 다르고 version/귀속 계약도 불완전 (P2)

- 코드: [daily rollup](../../src/engine/scalping/microstructure_reaction_context.py:2051), [누적 판정](../../src/engine/scalping/microstructure_reaction_context.py:2276), [report source gate 선언](../../src/engine/scalping/microstructure_reaction_context.py:2899).
- 재현: quality pass 20, EV-evaluable 1, 유일한 수익률 +0.1%인 rollup에 대해 `sample_floor_met=true`, `bounded_candidate_review_only`가 반환됐다. 현재 floor는 finite cost-adjusted return 수를 확인하지 않는다.
- report는 EV에 explicit delivery v2를 선언하지만 funnel/rollup은 이를 확인하지 않으며 기존 v1 rollup에 freshness/feature version, delivery cohort, 내부 소비 여부도 보존하지 않는다. 기존 39개 EV를 새 계측·조건의 적용효과로 사용할 수 없다.
- 권고: 기존 자료는 명시적 historical diagnostic으로 유지하고, 후보 검토가 필요하면 유효 수익률·동일 feature/정규화 version·동일 시점/venue/owner의 근거를 구분한다. 계산된 feature의 source-only 경제성 분석과 실제 전달/적용효과 분석에는 서로 다른 모집단 계약이 필요하다. 목적이 진단이면 runtime 승격을 암시하는 floor/status는 제거 또는 진단 상태로 변경한다.
- 수용시험: pass20/finite1, NaN/Infinity, 결합 실패, version 변경, legacy delivery 사례의 허위 후보 0건; 실제 효과는 기존 owner의 동일 입력 비교·비용차감 성과로 검증.

### R4 — 누적 후보 판정은 소비되지 않고 별도 신규 family 제안은 무관한 조건으로 생성 (P2)

- 코드: [runtime reflection status](../../src/engine/scalping/microstructure_reaction_context.py:2285), [signed-tape workorder](../../src/engine/scalping/microstructure_reaction_context.py:1368), [workorder consumer](../../src/engine/build_code_improvement_workorder.py:6893).
- `bounded_candidate_review_only`는 누적 결과 표시이며 이 namespace의 PREOPEN selector/actuator가 없다. downstream workorder builder는 `code_improvement_orders`만 소비한다.
- 재현: row 1건, REST signed tick 1건, sample floor 미달, EV -1%에서도 `auto_family_candidate`로 `microstructure_signed_tape_runtime_candidate`가 생성됐다. `runtime_effect=false/allowed_runtime_apply=false`이므로 실주문 권한 누수는 아니지만, 신규 축을 만들지 않는 현재 목적과 ‘20건/양의 EV 전 후보 없음’ 설명에 어긋난다.
- 권고: 소비자가 없는 runtime 후보 상태/required PREOPEN action과 독립 signed-tape family 제안은 제거를 우선 검토한다. 필요한 진단 결손은 기존 source-quality 또는 main AI quality owner의 구체적 코드 개선 workorder로 연결한다. 진단 자동화의 완료 기준을 PREOPEN 승격으로 두지 않는다.
- 수용시험: 단순 REST source 발생으로 신규 family 제안 없음; source gap은 기존 owner의 수용시험 있는 workorder로 자동 전달; 정상 진단에 불필요한 apply 대기 없음.

### R5 — 품질 coverage 분모가 과도하게 넓고 실제 개선 handoff가 없음 (P2)

- 코드: [coverage 집계](../../src/engine/scalping/microstructure_reaction_context.py:2600), [5% 경고](../../src/engine/scalping/microstructure_reaction_context.py:2923), [workorder 생성 조건](../../src/engine/scalping/microstructure_reaction_context.py:1200).
- report 행에는 scanner·미평가·다른 시장자료 진단만 있는 행도 포함된다. 61/26,554=0.23%는 전체 event coverage이며 정상 계산 요청의 성공률이 아니다. 상태상 실제 계산된 것으로 보이는 ok/partial/stale 546행만의 비율은 11.17%지만, 이 역시 legacy 자료여서 정확한 call 분모로 확정하지 않는다.
- 재현: row1000/ok1/coverage0.1%/v2 computed1000/sent0/consumed0만 입력하면 관련 개선 workorder는 0개다. 품질 결손·미소비 경고가 지속되어도 자동 수리 handoff가 보장되지 않는다. 기존 5%는 경고일 뿐 runtime 적용 gate가 아니다.
- 권고: applicable/computed/usable/sent/internal-consumed를 stage와 call 기준으로 분리하고, 원천 결손과 의도적 payload omission을 다른 사유로 집계한다. 일률적인 5% 경고는 정당한 분모로 재설계하거나 제거한다. 실제 결손만 source-quality workorder로 전달하며 report-only 경로의 의도적 sent0은 결함으로 만들지 않는다.
- 수용시험: 미평가 scanner 행을 10배 추가해도 정상 요청 품질 비율 불변; 의도적 entry omission 경고 없음; source/delivery 결함 발생 시 동일 owner로 workorder 1건 전달.

### 재리뷰 검증과 실행 owner

- 관련 기존 회귀 7개 파일: **189 PASS**. 이 테스트들은 위 반례를 차단하지 않으므로 PASS를 결함 없음으로 해석하지 않는다.
- 추가 검증은 기존 fixture와 mock을 사용한 읽기 전용 함수 호출로 수행했다. provider/broker API 호출, bot 재기동, 보고서 재생성, PREOPEN 적용은 실행하지 않았다.
- 구현/제거 검토 owner: 다음 영업일 체크리스트 `ContextObjectiveRepairReview0907`. 자연 PID 확인은 기존 `ContextDeliveryNaturalEvidence0907`에서 이어가되 R1~R5가 닫히기 전 현재 receipt로 적용효과/확대를 승인하지 않는다.
- 상세 보완안(2026-09-06): [A~D 구현계획](../proposals/institutional-microstructure-context-remediation-plan-2026-09-06.md)에 수정 위치, 제거 대상, delivery v3/rollup version, 정확한 attempt 결과 연결, 단계별 수용시험과 자연 적용 순서를 정의했다. 계획 수립 완료이며 R1~R5 구현 상태는 OPEN이다.

## 7. A~D 구현 후 재리뷰

### 판정

- 사용자 구현 지시에 따라 [계획 A~D](../proposals/institutional-microstructure-context-remediation-plan-2026-09-06.md#9-구현-결과)를 구현하고 `korstockscan-review-gate`의 구현→리뷰→수정→재리뷰→검증을 반복했다. **R1~R5의 이번 보완 범위에서 남은 확인된 코드 결함은 0건**이다. 아래 중간 회귀 이력과 실제 실행 미확인을 분리한 판정이다.
- 상태는 `implemented_runtime_not_observed_yet`다. 신규 family·별도 PREOPEN 승격 경로 없이 기존 feature/내부 source-quality 소비와 장후 진단→개선 workorder 전달을 보완했다. code-improvement workorder 자동 생성은 자동 저장소 수정이나 실주문 허가가 아니다.
- Institutional 전용 aggregate OFF/current retired 및 ADM/LDM 폐기는 유지한다. 기존 exact AI investor/program context와 broker/account/order/quantity/cooldown·hard safety는 변경하지 않았다. 전략 threshold·provider route·cap·runtime env·cron·bot 상태도 변경하지 않았다.

### 구현과 반례 종결

| 단계 / finding | 보완 결과 | 주된 구현 위치 |
| --- | --- | --- |
| A / R1 | 공통 quote threshold 정규화, 결손·비유한·음수/미래 age의 품질 배제, feature v2·순수 feature hash; 정상 점수 수식 유지 | `scalping/microstructure_reaction_context.py`, `scalping_feature_packet.py` |
| B / R2 | v3 context/evaluation/parent identity, 실제 구조화 payload 포함과 확인된 전송·미확인 시도·내부 소비·cache reuse 분리, nullable receipt의 logger/trace 보존 | `ai_engine_openai.py`, `scalping_feature_packet.py`, `sniper_state_handlers.py`, `scalping/ai_decision_trace.py`, `utils/pipeline_event_logger.py` |
| C / R3 | 기존에 읽은 동일 venue 가격을 원래 context ID·평가시각·가격에 연결하는 attempt outcome 생산; finite 비용차감 결과만 EV 분모, legacy 별도, report schema5/rollup schema2 | `sniper_missed_entry_counterfactual.py`, `scalping/microstructure_reaction_context.py` |
| D / R4~R5 | 독립 signed-tape 후보/PREOPEN 대기 및 전체 event 5% 경고 제거, unique applicable coverage, 실제 계약 결손 workorder와 downstream order ID 대사 | `build_code_improvement_workorder.py`, daily/EV/runtime summary, `verify_threshold_cycle_postclose_chain.py` |

재리뷰 중 발견하여 추가 수정한 경계 사례:

- timeout/formatting 예외에도 이미 계산·내부 소비한 receipt를 보존한다. HTTP 최소 입력 재시도 및 Bedrock 대체 요청은 실제 사용한 payload 기준으로 포함 여부를 갱신한다. 응답 수신과 JSON 해석 성공은 별개이며, 응답 없는 timeout을 전송 성공으로 추정하지 않는다.
- cache-hit은 과거 전달을 새로운 계산·전송·소비로 집계하지 않는다. 새 evaluation ID와 parent context를 남기고 계산 성공률 분모에서도 재사용을 제외한다.
- 필수 holding payload가 빠진 시도도 provider delivery 분모에 남긴다. 의도적 entry omission은 실패로 만들지 않으며, 모순된 sent receipt는 확인된 전달 건수에 포함하지 않는다.
- 문자열로 저장되는 pipeline bool/null/identity를 report가 복원하고, 설명 문자열의 key 이름이나 version-only metadata는 payload 전달로 인정하지 않는다.
- pass20/finite1·NaN/Infinity·구 feature 자료의 허위 sample-floor 충족을 차단한다. 동일 cycle 내 복수 평가도 각각 자신의 동일 venue·정확한 시각 outcome에만 결합한다.
- optional verifier의 source 로딩 순서 오류를 수정했다. 실제 v3 결손에 producer workorder가 없거나 workorder/daily/EV/runtime 전달이 끊기면 해당 diagnostic 분기의 `automation_handoff_gap`을 드러낸다. unrelated 전략 전체의 apply gate로 승격하지 않는다.

### 검증 결과와 중간 회귀 종결

- 중간 17개 관련 모듈 확장 회귀는 **1,248 PASS / 기존 회귀 1 FAIL**이었다. 실패는 `src/tests/test_adm_ldm_retirement.py::test_wrapper_has_no_retired_producer_commands`의 Entry AI gate backtest 호출 존재 assertion이었다.
- 이후 전송 메타데이터 보완 및 Bedrock provider 회귀를 포함한 중간 18개 모듈은 **1,259 PASS / 1 deselected** (23.96초)였다. 제외한 1건은 당시 위 실패였고 나머지 retirement/institutional 회귀는 실행했다.
- 변경 Python 12개 모듈 compile, 변경 범위 Python 19개 파일 Black check, wrapper `bash -n`, `git diff --check`: **PASS**. 실제 wrapper의 Institutional permanent OFF·override/producer 부재를 별도 읽기 전용 assertion으로 확인했다. 문서 backlog parser `--print-backlog-only --limit 500`: **PASS**; 구현·wrapper 정합화 owner는 OPEN 목록에서 제외되고 자연 확인 owner만 OPEN으로 파싱됐다.
- 중간 단계에서 wrapper에는 `-m src.engine.scalping.entry_ai_gate_backtest` 호출이 없고 diagnostic skipped marker가 있었지만, retirement 테스트는 호출 존재를 요구했다. 이 불일치는 아래 병합 전 gate에서 current owner 계약으로 정합화했다.
- 검증은 로컬 fixture/mock 기반이다. 실제 provider/broker 호출, bot 재기동, 운영 report 재생성·전체 장후 실행·수동 PREOPEN 적용을 하지 않았다.
- 병합 전 gate에서 Plan Rebase §7과 현재 checklist의 `일일 controller ON + 누적 backtest on-demand only`를 source of truth로 재대조했다. 위 기존 회귀 assertion을 wrapper의 누적 backtest 미호출, `ENTRY_AI_GATE_BACKTEST_SCHEDULE=on_demand`, `RUN_ENTRY_AI_GATE_BACKTEST=false`, skip marker와 일일 `entry_recheck_drought_controller` 호출을 함께 요구하도록 정합화했다. 예약 producer를 복구하지 않았으며 `ContextAdjacentWrapperRegression0907`은 종결했다. 최종 전체 수치는 병합 증거 보완에서 기록한다.
- wrapper 정합화 후 18개 관련 모듈 최종 회귀는 **1,260 PASS** (22.98초)다. 실제 PID/장후 자연 실행 확인은 이 수치와 별도다.

### 목적·자동화·조건 달성 가능성 최종점검

- 기대효과는 freshness 오판·전송/소비 과장·중복 표본·불필요 승격 대기를 줄이고 실제 계약 결손을 기존 owner의 개선 작업으로 전달하는 것이다. 작은 수익을 자주 확보하는 실매매 성과 자체를 이번 진단 수정만으로 입증하지 않는다.
- 기존 runtime 호출과 장후 producer/consumer 경로에 연결되어 별도 승인용 family를 추가하지 않는다. 실제 실행 중 PID가 변경 코드를 읽었다는 증거는 아직 없다. `ContextDeliveryNaturalEvidence0907`에서 다음 정상 기동의 v3 receipt와 장후 handoff를 대사한다.
- **20건·양의 EV는 코드 기동/계측 적용 조건이 아니다.** 유한하고 같은 계약을 통과한 20개 결과는 누적 진단 해석의 표본 기준일 뿐이며, sample-floor 미달이나 자연 favorable 0건으로 진단 실행을 막지 않는다. arrival/forecast를 보고하고 신규 최소 수익률·기간·종목수 조건은 추가하지 않았다.
- 20분 미래가격 비용차감 진단은 실제 청산 PnL이나 context 추가의 인과적 수익 개선이 아니다. 구 39건/-0.636615%도 수정 후 feature v2 적용효과로 재사용하지 않는다. 이 작업에는 별도 threshold 완화·실주문 trial이 필요하지 않다.
- 기존 full snapshot 생성 시각(15:45) 뒤의 NXT 평가에는 outcome 원천이 없을 수 있다. 이를 pending 또는 historical/source coverage gap으로 남기며 legacy cycle 값·다른 venue·미래 가격 추정으로 채우지 않는다. 현재 구현이 모든 장후 평가의 outcome coverage를 보장한다는 뜻은 아니다.
- 자연 실행과 별도 wrapper 정합화는 [2026-09-07 체크리스트](../checklists/2026-09-07-stage2-todo-checklist.md)에 OPEN으로 유지한다. 테스트 PASS로 운영 확인을 완료 처리하지 않는다.
