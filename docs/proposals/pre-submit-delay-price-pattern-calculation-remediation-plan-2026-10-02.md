# 첫 BUY 제출 시점의 가격 패턴 계산 보완구현 계획

작성일: 2026-10-02 KST. 상태: 추가 리뷰·보완·불변 배포·승인 재기동·Main PID 소비 수용 완료. 10/10 후속 점검에서 10/8 자연 가격 분석 `partial` 산출을 확인했으며 초기 자동 정책은 미선정이다(§9).
실행 소유자: [당일 checklist](../checklists/2026-10-02-stage2-todo-checklist.md)의 `PreSubmitDelayPricePatternRemediation1002`.

## 1. 목적과 범위

기계 `ENTER_NOW`와 보조 AI `PASS/CAUTION`으로 진입이 허용된 동일 기회에서, 즉시 매수 가능한 가격과 30/60/120/180초 뒤의 가격을 비교한다. **어떤 판정 당시 조건에서 기다리면 더 낮은 가격에 진입할 수 있었는지, 어떤 조건에서 즉시 진입이 유리했는지**를 계산하고 별도 후행 표본에서 확인한다.

이 가격 경로 시뮬레이션의 계산 완료에는 실제 주문 제출, broker 접수, 체결, 청산, 거래 비용 또는 실제 수익 영수증을 요구하지 않는다. 가격 차이를 실제 체결가격·순이익·비용 후 EV로 표현하지 않는다. 제출 terminal은 별도 운영 진단으로 보존한다.

계획 수립 후 사용자의 구현·반복 코드리뷰 지시에 따라 아래 계산/패턴/consumer 보완을 구현했고, 후속 배포·재기동 승인으로 검증한 릴리스를 Main이 소비하게 했다. [구현 수용 기록](../audits/pre-submit-delay-price-pattern-implementation-review-2026-10-02.md)에 범위와 검증을 기록한다. 현재 정책·cron·provider·주문·수량·가격 상한·hard safety는 이 작업에서 변경하지 않았다. 기존 진입가격 resolver, 초기수량, 분할, 취소대기와 별도인 첫 제출 시점 축만 다룬다.

## 2. 구현 전 확인한 동작과 변경 이유

| owner | 확인된 동작 | 보완 내용 |
| --- | --- | --- |
| [계산 생산자](../../src/engine/scalping/pre_submit_delay_tuning.py) `_source_rows`, `build_report` | 전용 compact 원천을 읽고 intent를 묶지만, horizon별 `mean_observed_ask`만 계산한다. 같은 intent의 0초 호가와 차이를 계산하지 않는다. | 같은 기회의 0초/지연 호가를 직접 짝지어 가격 변화와 분모를 산출한다. |
| 같은 생산자의 `build_report` | 경제성 필드는 모두 null이며, 제출 terminal 결손 또는 미검증 fill/청산/비용 모델이 최종 blocker다. | 가격 분석의 완료·결손 사유와 기존 경제성/정책 상태를 독립적으로 기록한다. terminal 부재 때문에 유효한 가격 비교를 버리지 않는다. |
| 같은 생산자의 `_validated_candidate`, `load_runtime_policy` | v1의 비용 후 EV·holdout·terminal·model 조건과 report/policy hash를 검증한다. | 가격 연구 추천을 이 loader의 선정 정책으로 위장하지 않는다. 기존 적격 정책 승계와 미선정 시 기존 즉시 제출 동작을 보존한다. |
| [장후 dispatcher](../../src/engine/automation/postclose_summary_handoff.py), [직접 family summary](../../src/engine/runtime_approval_summary.py), [의미감시](../../src/engine/monitoring/submission_bottleneck_monitor.py) | v1 schema·generation·policy 결속과 경제성 상태를 소비한다. 감시의 `completed_terminal_count`도 제출 함수 terminal count다. | 가격 분석 결과를 독립 소비하고 `analysis_complete`를 실제 체결 완료나 `validated_edge`로 바꾸지 않는다. 제출 함수 terminal과 거래 완료 명칭을 구분한다. |

현재 [traceability](../report-based-automation-traceability.md)의 `pre_submit_delay` 행과 [운영 runbook](../time-based-operations-runbook.md)의 원천 감시는 비용 EV 정책과 제출 terminal을 별도로 요구한다. 이번 계획은 가격 패턴 분석의 계산/요약 경계를 보완한다. 기존 자동 적용 계약을 가격 진단으로 대체하는 일은 포함하지 않는다. 이 차이를 누락하거나 계획만으로 현행 계약이 바뀌었다고 보고하지 않는다.

## 3. 입력과 분석 모집단

### 3.1 원천과 기준 시각

- 직접 입력은 `data/threshold_cycle/date=YYYY-MM-DD/family=pre_submit_delay/part-execution-*.jsonl`의 `pre_submit_delay_committed`와 `pre_submit_delay_quote_observed`다. 제출 terminal 이벤트는 운영 부록으로 읽는다.
- 정규 stage의 `pre_submit_delay_source_ledger_YYYY-MM-DD.json`에 봉인된 당일 raw/compact 공통 ID를 재사용한다. producer summary의 집계 수만으로 event 동일성을 대신하지 않는다. 같은 원천을 계산 단계마다 raw 전체에서 다시 찾지 않는다.
- 정책 갱신 원천은 2026-09-29 이후 적격 날짜부터 대상일까지다. 6~8월이나 9/28 이전 자료를 새 후보 학습에 넣지 않는다. 기존 과거 보고서·정책 bytes/hash는 보존한다.
- 기준 `t0`는 기존 `decision_committed_at_epoch`, 즉 주문가·계획수량 준비 뒤 첫 제출 intent를 고정한 시각이다. 실제 broker 제출 시각과 동일하다고 가정하지 않는다. 실제 제출 시각이 있으면 별도 운영 latency로 표시하고 가격 분석의 기준점을 사후 이동하지 않는다.
- 기준 가격 `P0`는 같은 intent의 유효한 **0초 최우선 매도호가**다. 미래 가격, 최저가격, 실제 체결가 또는 다른 record의 호가로 대신하지 않는다. `Pd`는 같은 intent의 지연 d초 유효 최우선 매도호가다.

### 3.2 짝짓기와 결손 처리

1. `owner=main_scalping`, `entry_action=ENTER_NOW`, `auxiliary_effective_action=PASS|CAUTION`, `planned_qty>0`인 commit을 모집단으로 고정한다. VETO/BLOCK/RECHECK·widget/episode/manual/scale-in을 섞지 않는다. 주문 발생 여부나 사후 가격 방향으로 모집단을 골라내지 않는다.
2. event key는 기존 `(source_date, record_id, stock_code, delay_intent_id)`와 decision/source hash다. 동일 이벤트 재발행은 한 번만 집계한다. 같은 기계 관측의 재시도 intent가 있으면 보존된 원 machine observation/attempt identity로 연결하고 최초 적격 commit 한 번만 학습한다. 서로 다른 판정·부모 세대는 합치지 않는다. 이를 판별할 원천이 없으면 retry linkage unknown을 공개하고 강한 패턴 검증에서 제외한다.
3. 같은 intent·route·WS transport epoch·원천 hash·시각을 유지한다. 기존 목표 offset ±3초, 정확 route 0D 수신 age 0.7초 이내의 유효 호가 기준을 보존한다. route/epoch 변경·상충·잘못된 가격·future clock은 해당 pair를 제외하고 사유를 남긴다. REST backfill·추정 경로·재접속 전후 호가 혼합을 하지 않는다.
4. **각 지연 d의 짝 `P0/Pd`만 있으면 계산한다.** 180초 호가가 없다고 유효한 30초 비교까지 버리지 않는다. 0초가 없으면 상대 비교는 null이며 후행 호가만 별도 관측으로 남긴다. terminal/실제 체결/청산이 없어도 pair는 유효할 수 있다.
5. `ask_qty>0`은 기존 호가 원천 검증으로 유지하되, 계획수량 전체를 채울 잔량·체결 모델을 가격 비교의 필수 조건으로 추가하지 않는다. 최우선 호가 수준의 비교임을 명시하며 전량 체결가능성을 주장하지 않는다.
6. pair별 missing/conflict/exclusion과 eligible·paired count를 보존한다. 다른 horizon·날짜·종목을 평균 가격끼리 비교하지 않는다. 전체 source 계약 불명·raw 격리 불능만 전역 차단하며 식별 가능한 결손은 pair 단위로 제외한다.

## 4. 계산 계약과 패턴 검증

### 4.1 핵심 계산

각 유효 pair에 아래 값을 계산한다. 1bp는 0.01%다.

```text
price_change_bp(d)      = (Pd - P0) / P0 * 10000
price_improvement_bp(d) = (P0 - Pd) / P0 * 10000
```

`price_improvement_bp>0`이면 기다렸을 때 낮은 가격, `<0`이면 즉시 진입이 유리한 가격 경로, `=0`이면 가격 차이 없음이다. 예: P0=10,000, P30=9,950이면 +50bp, P60=10,050이면 -50bp다. 실제 수익·실제 missed winner로 해석하지 않는다.

지연별 paired count, coverage(`paired/eligible`), 개선/악화/동일 건수·비율, improvement의 평균·중앙값·p10/p90을 산출한다. `paired=개선+악화+동일`, 가격 비교 비율의 분모는 paired, coverage의 분모는 eligible이다. 평균은 **기회별 비율의 평균**이며 종목별 평균 호가의 비율이나 서로 다른 pair 집합의 평균 차이가 아니다. 결측값을 0bp로 채우지 않는다. 0초 control의 0bp는 유효 P0가 있을 때만 계산한다. p10/p90은 정렬된 값의 `(n-1)*q` 위치 선형보간으로 고정하고 n=1이면 해당 값, n=0이면 null이다. 가격 방향은 반올림 전 값으로 분류한다.

가격 상한을 넘은 `Pd`는 가격 상승 기회 손실 진단에 포함하고 `price_cap_exceeded`를 표시한다. 그 가격으로 실제 주문이 가능했다고 주장하지 않는다. cap 결손은 별도 unknown이며 가격 상대 비교를 자동 폐기하지 않는다. d초 전 경로가 없으면 그동안의 최대 상승·낙폭을 만들어내지 않는다.

### 4.2 가벼운 패턴 분석

- 첫 구현은 기존 commit의 `delay_decision_type`에 고정된 venue/session/price-tick type과 spread를 사용한다. 새로운 ML 모델·외부 특징 수집·provider 호출을 추가하지 않는다. UNKNOWN 특징은 UNKNOWN으로 남기며 미래 변동성·시총·사후 최저가로 보충하지 않는다.
- 우선 전체와 기존 venue/session/type별 0 대비 30/60/120/180초 pair 통계를 제공한다. 표본 1개도 계산을 막지 않는다. count/coverage와 검증 상태를 함께 보여주며 소표본 결과를 확정 패턴으로 표현하지 않는다. spread는 첫 회차 설명 변수로 표시하고 데이터로 임의의 수십 개 경계값을 탐색하지 않는다.
- 기본 시간순 split은 고유 기회의 앞 70% learning, 뒤 30% validation이다. n≥2이면 learning 수는 `min(n-1, max(1, floor(n*0.7)))`, n=1이면 계산만 남기고 독립 검증은 부족으로 둔다. split은 intent 시각과 deterministic identity 정렬로 먼저 고정한다. learning 기회의 최대 관측 종료시각이 validation 시작과 겹치는 행은 learning에서 purge한다. 같은 원 기회/재시도는 양쪽에 걸치지 않게 한다. 한 날짜도 독립 분할이 가능하면 사용하고 고정 다일 대기를 추가하지 않는다.
- 여러 지연을 순위화할 때는 learning에서 해당 후보들이 모두 가진 공통 pair 집합으로 비교한다. learning의 적격 pair가 0인 지연은 unsupported candidate로 명시하며 다른 지연의 기초 통계를 막지 않는다. 남은 후보의 공통 집합이 비면 `insufficient_comparable_pairs`로 추천을 유보하고 horizon별 계산은 보존한다. 후보 집합·공통 count/coverage를 봉인해 후보마다 유리한 모집단을 고르지 않는다. 후보 집합과 cutoff를 validation 결손 여부로 바꾸지 않는다.
- learning 평균 improvement가 가장 큰 지연 하나를 비교 후보로 고정한다. 지연 간 동률이면 더 짧은 지연이다. 평균이 양수이면 해당 지연을 추천하고, 0 이하이면 즉시 제출(0초)을 추천한다. 추천이 즉시 제출이어도 고정한 지연 대비 가격 차이를 validation에서 확인한다. learning/validation 모두 양수이면 지연 방향, 둘 다 0 이하이면 즉시 방향이 재현된 `pattern_supported`다. 둘 다 0이면 `no_price_difference`로 남긴다. 방향이 바뀌거나 learning 양수/validation 0이면 `pattern_not_confirmed`, 독립 표본이 없으면 `insufficient_sample`이다. 이 판정은 고정 비교 후보에 대한 결과이며 모든 지연에 대한 최적성을 주장하지 않는다. validation을 보고 차순위 지연을 다시 고르지 않는다.
- 검증 수치는 candidate/control의 같은 pair에서 구한다. validation 수와 coverage·tail을 함께 공개한다. `pattern_supported`는 시간순 분할에서 방향이 재현됐다는 뜻이며 소표본의 통계적 확증이나 실거래 승인으로 표현하지 않는다. 매 기회의 사후 최저가격을 골라 평균내는 oracle은 학습/검증/추천값에 쓰지 않는다. 가격 경로 일부만 보이는 기회를 무기회 또는 개선 0으로 바꾸지 않는다.
- 패턴 추천은 보고서의 `recommended_delay_sec`다. 실제 정책의 `selected_delay_sec`와 구분하고 price 연구에 기존 경제성용 10 terminal·체결·비용·model 조건을 추가하지 않는다. 독립 검증 부족은 추천 강도의 상태이며 유효한 가격 계산의 실패가 아니다.

## 5. 결과와 직접 소비 계약

기존 보고서에 버전이 있는 `price_pattern_analysis` section을 추가한다. 외부 v1 report/policy envelope와 hash 결속은 유지하고, 새 section도 report hash에 포함한다. historical v1에 section이 없으면 `not_evaluated_legacy`로 표시하며 과거 가격 원천을 재검증했다고 주장하지 않는다.

| 필드 | 계획 계약 |
| --- | --- |
| `schema` | `pre_submit_delay_price_pattern_v1` |
| `metric_role` | `diagnostic_entry_price_timing`; 이 section의 명시 역할이며 소비자/시험에 등록한다. |
| `decision_authority` | `report_only` |
| `window_policy` | `forward_from_20260929_same_intent_zero_vs_fixed_delay` |
| `sample_floor` | 가격 계산은 유효 pair 1개; 패턴 검증은 분리된 learning/validation의 유효 pair 필요. 추가 실체결/일수 floor 없음. |
| `primary_decision_metric` | `mean_paired_price_improvement_bp` |
| `source_quality_gate` | `exact_intent_zero_and_delayed_route_epoch_hash_clock_quote_pair` |
| `forbidden_uses` | `realized_pnl`, `net_ev`, `execution_fill_claim`, `runtime_apply`, `entry_action_override`, `price_quantity_or_safety_override` |

section에는 source/algorithm hash, 원천 날짜·기회·pair 분모, pair exclusions, horizon/type 통계, split·purge·추천/검증 근거를 기록한다. 대형 event 전체를 보고서에 복사하지 않고 bounded 예시와 원 source identity를 보존한다.

가격 분석 상태는 `computed`, `partial`, `valid_empty`, `source_gap`으로 구분한다. `computed`는 모집단 전체에서 모든 요구 horizon의 pair가 유효한 경우, `partial`은 유효 pair가 있지만 일부가 결손인 경우다. 적격 기회가 검증된 원천에 없을 때만 `valid_empty`, 적격 기회는 있는데 유효 pair가 없거나 원천 계약을 검증하지 못하면 `source_gap`이다. 기대값의 실제 0bp와 결손 null을 구분한다.

`runtime_approval_summary`와 의미감시는 section의 계산 상태·추천·검증 분모를 별도 projection으로 보여준다. 기존 경제성 `comparison_status`, 정책 선정/승계, 실제 PID 소비를 별도 유지한다. 운영 terminal 경보는 보존하되 이를 가격 section의 blocker로 복사하지 않는다. `computed/partial`에서 유효한 분석 산출물을 확인한 상태를 `analysis_complete`로 보고할 수 있지만 전체 native DONE이나 정책/경제성 성공으로 바꾸지 않는다. stage hash/date 검증과 strict/controller의 기존 mandatory handoff는 유지한다.

`_validated_candidate`, PREOPEN/bootstrap와 runtime loader는 가격 추천만으로 positive-delay env를 발행하거나 기존 적격 정책을 지우지 않는다. 기존 적격 policy가 있으면 원 계약으로 승계하며 없으면 기존 즉시 제출 동작을 유지한다. 비용 후 EV 필드는 null로 남아도 가격 분석 수용을 닫을 수 있다. 향후 실제 자동 적용으로 범위를 확장할 때는 별도 owner 계약을 의도적으로 변경해야 하며, 본 계획에서 그 권한을 만들지 않는다.

## 6. 구현 순서와 위치

| 단계 | 기존 수정 위치 | 완료 기준 |
| --- | --- | --- |
| P0 원천·pair | `src/engine/scalping/pre_submit_delay_tuning.py` | 유효 P0/Pd, 기회 중복·route/epoch/hash, terminal 독립성을 확인하고 pair별 exclusion을 보존한다. |
| P1 계산 | 같은 파일 | 부호·bp 단위·같은 기회 평균·horizon별 분모·부분 결손·cap 진단을 정확히 계산한다. |
| P2 패턴 검증 | 같은 파일 | 기존 frozen type의 시간순 split/purge, learning 단일 후보 동결과 독립 validation을 구현한다. |
| P3 report/consumer | 같은 파일, `runtime_approval_summary.py`, `monitoring/submission_bottleneck_monitor.py`; 필요 시 `automation/postclose_summary_handoff.py`, `verify_threshold_cycle_postclose_chain.py`, `build_next_stage2_checklist.py` | 가격 section의 직접 소비와 legacy 호환/hash·stage generation·정책 승계가 함께 닫힌다. |
| P4 표적 검증·성능 | 기존 `src/tests/test_pre_submit_delay_tuning.py`와 영향 consumer tests | 아래 반례·손계산·권한 불변·bounded 성능 수용을 통과하고 리뷰를 닫는다. |

분석 owner는 기존 `src/engine/scalping`, stage owner는 `src/engine/automation`, 감시는 `src/engine/monitoring`, 시험은 기존 `src/tests`다. 새 engine-root module·새 CLI·서비스·cron·수집기를 만들지 않는다. runtime observer/logger는 기존 입력으로 pair 계산이 불가능한 **신규 원천 결함**이 확인된 경우에만 별도로 범위를 식별한다. 실제 Kiwoom request/parser/FID/REG/REMOVE/recovery 수정이 필요하면 그 변경 전에 [Official Kiwoom Reference Gate](../kiwoom-api-data-contract.md#official-kiwoom-reference-gate)를 수행한다. 계획 작성 중 공식 프로토콜 검증이나 wire 수정은 수행하지 않았다.

owning traceability의 가격 분석 section/경제성·정책 경계와 운영 runbook의 계산 상태·terminal 의미를 구현과 함께 일치시켰다. wrapper/자동화 변경이 필요하면 같은 변경 집합에서 운영 문서·checklist·shell 계약을 검증한다. 이번 구현에서는 wrapper·cron을 변경하지 않았다.

## 7. 표적 검증과 유한 종결 기준

| 반례/샘플 | 통과 조건 |
| --- | --- |
| P0=10,000; P30=9,950; P60=10,050; P120=10,000 | +50/-50/0bp, 개선/악화/동일 분류와 pair 평균·단위가 손계산과 일치한다. |
| 실제 주문/terminal/fill/청산/비용 없음, 유효 P0/P30 있음 | 30초 pair 계산과 가격 분석 수용 가능; EV null·runtime 미선정·운영 terminal 결손은 별도 유지한다. |
| 0초 없음, 180초만 없음, 30초 stale/상충/다른 epoch | P0 없음은 pair null; 180초 결손은 30초 정상 계산을 보존; 잘못된 30초 pair만 격리한다. |
| 서로 다른 가격대 종목, horizon마다 다른 누락 집합 | 기회별 bp 평균을 사용하며 후보 순위는 동일 learning 집합으로 비교한다. 평균 호가 차이·결손 0 채움·선택 분모 이동은 0건이다. |
| replay/retry·동일 이벤트 중복·다른 부모/날짜·원천 변경 | 고유 기회 count 보존, 충돌 격리·hash invalid 검출, stale cache 재사용 0건. |
| learning 1위 validation 실패, 2위 validation 성공 | 1위 검증 실패로 `pattern_not_confirmed`; validation에서 2위 재선정 0건. 미래 특징/최저가 누출 0건. |
| 모든 지연이 악화, 전부 동일, learning/validation 방향 반전 | 악화 재현은 즉시 방향, 전부 동일은 `no_price_difference`, 방향 반전은 `pattern_not_confirmed`; 0초를 양수 지연처럼 검증하거나 지연 후보를 재선정하지 않는다. |
| 한 날짜·분할 불가 소표본·서로 겹치는 180초 구간 | 가능하면 same-day 독립 split; 불가능하면 계산은 남기고 검증만 부족. 원 기회 겹침·learning 관측의 validation 누출 0건. |
| 작은 최우선 잔량, cap 초과·cap 결손 | 유효 호가 가격 비교 보존; 전량체결·cap 초과 주문 가능성·실제 기회 손익 주장 0건. |
| legacy v1, 새 section 있는 report, report/policy/date 변조 | 구 보고서 호환·새 section hash 결속·summary/monitor projection 확인; runtime 추천 혼입 0건, 기존 적격 정책 승계 유지. |

pair 계산은 intent를 한 번 index하고 고정 5개 horizon을 비교하는 O(events + intents×5)로 구현한다. 시간순 split·quantile 통계의 정렬 비용은 별도 포함해 측정한다. 기존 64MiB compact decode 상한을 유지하며 추가 API/AI/계좌 조회·raw 전체 재스캔을 넣지 않는다. 캐시를 쓰면 source inventory/hash와 계산 버전·split 설정을 key에 포함하고 변경 시 무효화한다. 첫 구현에는 별도 캐시 저장 체계를 추가하지 않는다.

고정 입력으로 baseline/candidate를 각 3회 측정한다. 기존 원천 count/hash·quote coverage를 대조하고 새 pair 결과는 독립 손계산 fixture로 검증한다. wall/CPU 중앙값 baseline×1.20 이내, RSS baseline×1.10+64MiB 이내를 기존 Main/compact 계획과 동일한 엔지니어링 수용 기준으로 사용한다. 기존 절대 자원 상한이 우선이다. 입력 날짜/기회를 줄여 성능을 통과시키지 않는다.

구현 → self review → 보완 → 재리뷰 → 영향 pytest/compile·diff와 consumer/정책 권한 검증으로 닫는다. 기존 pre-submit delay, runtime summary, submission monitor, stage handoff, bootstrap, strict/checklist 시험 중 영향 selector만 실행한다. wrapper 변경 시에만 `bash -n`과 해당 계약 시험을 추가한다.

코드 완료는 위 계산·반례·consumer 계약으로 판정하며 실제 거래 성숙을 기다리지 않는다. 자연 원천이 없으면 자연 분석 수용은 `not_observed`; 필수 source 계약 결손은 owner/artifact/closure test와 함께 `blocked`다. 동일 결손 입력을 반복 재생하거나 실제 주문을 만들어 표본을 채우지 않는다. 실제 release 소비·정책/PID·실현 순익은 별도 상태이며 배포/재기동은 이 계획의 실행 범위가 아니다.

## 8. 계획 리뷰와 구현 수용 상태

현행 계산 생산자·WS 관측 생산자·raw/compact writer·stage/report hash·summary·감시·PREOPEN loader와 기존 시험을 대조했다. 초기 검토에서 horizon 평균 호가의 서로 다른 모집단 비교, P0 없는 상대 계산, terminal 결손의 가격 분석 전파, 사후 최저가·validation 재선정, 가격 추천의 runtime 혼입을 보완 대상으로 확인했다. 위 설계는 pair별 계산·독립 검증·별도 소비로 이를 다룬다.

문서 self review에서 후보의 공통 모집단이 비는 경우, 즉시 제출 추천의 검증, 1개 표본의 분할/quantile 및 baseline에 존재하지 않는 새 계산값의 검증 기준을 추가 보완했다. 재리뷰는 가격 계산의 실체결 전제 제거와 현행 policy 소비의 권한 보존을 각각 확인한다.

계획 수립 당시 `PreSubmitDelayPricePatternRemediation1002`는 이 가격 계산/패턴/consumer 보완의 단일 OPEN owner였다. 계좌 원천 조회 계획 및 기존 `MainEntryEconomicLineageRepair1002`의 자연 capacity/guard/residual 수용을 대체하지 않는다. 기계·compact 선정 계획의 source/정책 권한도 유지한다. 후속 초기정책 계획 기록은 §9의 10/10 owner를 따른다.

구현·self review·보완·재리뷰·표적 회귀를 완료했다. 가격 계산·검증의 최종 7개 영향 suite 423 PASS와 summary Markdown 추가 회귀 32 PASS, 수정 Python 7파일 compile PASS, 신규 F/E9 lint finding 0건이다. 마지막 계획 대조에서 고정 후보의 validation coverage/tail과 전체 기회 수 대비 검증 count 결속을 보완했다. 512기회/3,072 events 고정 입력의 baseline/candidate 각 3회 측정에서 wall/CPU ×1.07011/×1.08033, RSS +864 KiB로 수용 기준을 통과했다. 구현 범위의 미해결 결함은 0건이며 상세 근거와 기존 lint 한계는 [구현 수용 기록](../audits/pre-submit-delay-price-pattern-implementation-review-2026-10-02.md)에 남긴다.

가격 계산의 코드 수용은 완료했다. 후속 사용자 승인으로 추가 의미 계약을 보완하고 `c61fefcf` 부모의 불변 `820c7c42`를 배포했다. 9개 영향 suite 작업본/격리 후보/불변 root 모두 523 PASS·F/E9 finding 0건과 최신 동일 입력 성능 수용을 확인했다. 기존 graceful restart 후 ubuntu Main PID 2957878의 source clean·당일 runtime env/native consumed·process health·WS 수신과 정책 5파일·독립 pin 416개·cron 보존을 확인했다. 상세 상태는 구현 수용 기록이 소유한다. 10/2 당시 단일 owner는 후속 자연 가격 산출물 수용 때문에 OPEN이었고 자연 분석은 `not_observed`였다. 당시 보고서의 비싼 자연 원천 재생성·external sync·실제 거래/순익 수용은 실행하지 않았다. 실제 체결·청산을 가격 계산 완료의 전제로 다시 추가하지 않는다.

## 9. 10/10 현재 결과 점검과 초기정책 후속 계획

[10/8 가격 분석](../../data/report/pre_submit_delay_tuning/pre_submit_delay_tuning_2026-10-08.json)은 누적 commit 31건·적격 29건·유효 P0 6기회에서 30초 6쌍 및 60/120/180초 각 5쌍을 계산했다. `analysis_complete=true`, 상태는 `partial`이며 21쌍은 21개의 독립 기회를 뜻하지 않는다. 10/8 당일 ledger의 `valid_empty`와 누적 계산을 구분한다. report/policy/summary 결속과 기존 영향 회귀 56 PASS를 확인했지만 현재 선택 지연은 null이고 runtime 적용은 허용되지 않았다.

현 생산자는 가격 연구 뒤 초기정책을 선택하는 경로가 없고 v1 정책은 기존 비용모형 계약만 지원한다. source-invalid P0가 시간순 split에 참여하는 문제, 전체 PASS 이전의 관측 공백과 상황 특징 확장은 [상황별 초기정책·장후 재생성 상세 계획](pre-submit-delay-situation-initial-policy-and-postclose-regeneration-plan-2026-10-10.md)으로 구체화했다. 10/10 `PreSubmitDelayInitialPolicyPlan1010`은 그 문서 수립·검증 기록이며 후속 구현·정책 발행 완료를 뜻하지 않는다. 기존 report-only 추천은 새 v2 생산자·검증·runtime 계약이 구현되기 전까지 실행 정책으로 승격하지 않는다.
