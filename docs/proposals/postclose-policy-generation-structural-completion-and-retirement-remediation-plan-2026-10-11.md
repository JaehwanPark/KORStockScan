# 장후 정책 생성 구조 완성·퇴역 잔재 정리 상세 보완계획

작성일: 2026-10-11 KST. 상태: **구현·반복 리뷰/보완·영향 검증·승인 배포·10/12 기동 준비 PASS; 전체 숫자 실험 성능·실제 PID/자연 수용 OPEN**. 구현 근거와 변경된 원천/시장 축, 후속 승인 배포 결과는 [구현 검토 §7–§8](../audits/postclose-structural-policy-completion-implementation-review-2026-10-11.md)에 기록한다. 아래 계획 작성 시점의 선택본·무실행 영수증은 역사 문서 검증 기록이다.

## 1. 목표와 근거

목표는 유효한 원천과 후보가 주어졌을 때 **생성→평가→선정→발행→소비로 도달할 수 있는 경로**를 만들고, 과거 결손·기능 미구현·표본 부족·의도된 미적용을 구분하는 것이다. 개선 후보가 없는데 변경 정책을 강제로 만들거나, 퇴역 작업을 복원하여 완료율을 높이지 않는다.

구현 중 시장 축 대사: NXT-only는 프리마켓 원천/주문 경로 및 실제 체결시장 진단으로 구분한다. 정규장·애프터장의 정책 분석은 통합시장 `decision_market_scope`를 유지하며 같은 판단을 KRX/NXT 양쪽 표본으로 중복 계산하지 않는다. 기존 진단 field만으로 통합 원천을 추측하지 않는다.

- 직접 근거: [10/11 전수 감사 F1–F5/R1–R5](../audits/postclose-structural-policy-and-retired-code-audit-2026-10-11.md), [고정한 source/code 스냅샷](../../data/report/postclose_structural_audit/2026-10-11/audit-snapshot.json).
- 원칙: [Plan Rebase §1–§8](../plan-korStockScanPerformanceOptimization.rebase.md), [현행 10/11 체크리스트](../checklists/2026-10-11-stage2-todo-checklist.md). [봉인된 10/12 체크리스트](../checklists/2026-10-12-stage2-todo-checklist.md)는 이 문서 작업에서 수정하지 않는다.
- 기준 코드: workspace `38f66369c74f7773822fa8b8b03c4d645eba83d3`, selected `main-stop-semantic-20261011-v1` / `91edc62844180be6a279e761f32996c3c76ce72e`. 이전 검사에서 Python/shell 1,112개가 같았으며 구현 착수 때 다시 고정한다.
- 현재 운영 증거: source10/8→target10/12 PREOPEN 전체 계약 PASS, 필수 cron8 연결 PASS, `actual_pid_consumed=false`. 준비 성공을 새 경제 정책이나 실제 PID 소비로 해석하지 않는다.
- 완료된 trailing/delay/수량/stop 기본 발행과 semantic 수리를 다시 구현하지 않는다. 새 결함과 아래 잔여 경로만 이행한다.

### 1.1 상세 대조에서 바로잡은 범위

1. **보조 PASS 분모 0은 명시된 비교 불가 규칙**이다. [보조 연구계획 §7](main-auxiliary-prompt-research-and-intraday-adoption-plan-2026-10-08.md)의 `null` 유지·자동 교체 금지를 지킨다. 이를 0%로 바꾸거나 다른 승률을 대체 기준으로 쓰는 수리는 포함하지 않는다.
2. **holding vote의 초기 baseline 발행은 정상 기능**이다. 미완성은 이후 경제 후보 선택 경로다. 초기 정책에 경제 우월성 gate를 소급 추가하지 않는다.
3. **새 보호선은 별도 매도 전략을 만드는 허가가 아니다.** 기존 Main trailing이 유일한 일반 익절 owner다. 퇴역 PYRAMID/MFE protect의 생성자를 되살리지 않고 현재 유효 보호선의 출처/소비와 실제 필요한 producer를 먼저 분류한다.
4. **rising-missed NULL 차단은 안전 장치**다. [기존 RM 계획 §21](rising-missed-direct-paired-economic-tuning-and-runtime-consumer-plan-2026-09-19.md)은 가상 고정 100만원을 제거하고 수량·자본 미구현 시 차단하도록 의도했다. 이를 유지하면서 모델 입력·계산의 빠진 연결을 구현한다.
5. **정기 보조 예산과 별도 연구 예산을 분리한다.** 정기 원천일 100회와 별도 연구 key의 승인 이력은 다르다. 로컬 연구 원장에는 200→400→600→800 top-up이 남아 있다. 과거 초기 200회 메모나 최종 보고의 잔여 숫자를 현재 가용량으로 사용하지 않는다. 이 계획 작성 중 호출은 0회다.

## 2. 작업 소유와 우선순위

| 단계 | 감사 항목 / 수정 소유 | 기존 또는 신규 실행 owner | 우선순위·완료 산출물 |
| --- | --- | --- | --- |
| P0 | 코드·source·선택 정책 기준 고정, 도달성 반례 | 각 family owner; 공통 대사 `PostcloseStructuralPolicyCompletion1011` | 최우선; 입력 manifest·변경 범위·기능/성능 기준 |
| P1 | cancel-wait 과거 결손과 미래 비교 분리 | `DirectFamilySourceRepairEntryCancelWait` | 높음; 분리된 대사/학습·실제 후보 선정 시험 |
| P2 | rising-missed 수량·자본 paired 계산 | `PostcloseStructuralPolicyCompletion1011` | 높음; 원천 schema·제약 재생·선정/소비 연결 |
| P3 | 보조 campaign 종결·유효 비교·예산 | `DirectFamilySourceRepairCompactAuxiliary` | 높음; 불변 campaign의 resolution revision·완결 상태 |
| P4 | holding vote 수치 후보 선정·versioned 발행 | `MainStopLossRetirementRuntimeTuning1010` SL-F11 | 기존 OPEN 잔여; 후보 재생→v2 정책→reader |
| P5 | 보호선 출처·조건부 적용·퇴역 생성 경로 | `MainStopLossRetirementRuntimeTuning1010` SL-F8 | 기존 OPEN 잔여; origin 대사·Main 동작 동등성 |
| P6 | entry-split/WS/legacy label 미래 원천 지원 | entry-split은 `DirectFamilySourceRepairEntrySplit`; WS·공통 지원은 통합 owner | 높음; 필드별 producer→consumer와 지원 scope 증거 |
| P7 | 의미적 감시·summary·권고 intake | `SemanticMonitorLatestReleaseRepair1010` | P0부터 병행 가능한 수리; 구조 상태·복구·단일 owner |
| P8 | 고립 파일·CLI·퇴역 대형 모듈/helper 정리 | `PostcloseStructuralPolicyCompletion1011`; stop 내부는 기존 stop owner | 독립 제거/의존 이전 구분; source/consumer 회귀 |
| P9 | 영향 통합 검증·성능·정식 인계 | 각 native producer 및 기존 `DirectFamilyPreopenPolicyHandoff` | 단계별 release 수용과 자연 소비 별도 증거 |

P0–P9는 코드 소유를 나누기 위한 내부 단계이며 각 단계마다 새 checklist ID를 만들지 않는다. 공통 owner는 P2/P6 공통/P8/교차 검증만 맡고 기존 cancel/auxiliary/entry-split/stop/semantic 수용을 중복 인수하지 않는다. 일자·실행 슬롯은 체크리스트가 소유한다.

작업 순서는 `P0 → P1/P2/P3/P6의 독립 수리 → P4/P5 → 영향 P7/P8 → P9`다. P7의 퇴역 산출물 경고와 P8의 고립 entrypoint 정리는 독립적으로 먼저 닫을 수 있다. 전체 vote 연구가 끝날 때까지 detector 경고 수리를 보류하지 않는다. 각 묶음의 운영 수용은 의존하는 P7/P9만 닫고 진행할 수 있으며 무관한 후속 연구 완료를 추가 선행조건으로 만들지 않는다.

| 독립 변경 묶음 | 포함 | 다른 묶음과의 의존 |
| --- | --- | --- |
| A 감시·고립 잔재 | P7 phantom 요구/표시, P8 고립 wrapper/import·낡은 테스트 | baseline source 동등성만 필요; 신규 경제 모델과 독립 |
| B cancel | P1 + 해당 native reader/감시/회귀 | A 전체가 아닌 해당 schema reader가 먼저 준비 |
| C auxiliary | P3 + resolution consumer/감시 | 기존 durable store/budget·현재 wire 계약 |
| D rising | P2 + source capture/paired 모델/기존 TP1 소비 | 공유 순수 수량/자본 adapter와 해당 성능 gate |
| E vote·보호선 | P4/P5 + 기존 stop owner의 영향 수용 | path별 모델 adapter/reader와 runtime 성능 |
| F 공통 helper·나머지 원천 | P6/P8의 caller migration | 실제 영향받는 B–E 회귀를 포함; 파일 수로 배포 범위를 결정하지 않음 |

## 3. 공통 계약: 발행, 비교, 실제 소비를 각각 표현

새 중앙 서비스나 중복 상태 DB를 만들지 않는다. 각 **기존 native 보고서/세대 manifest**에 아래 정보를 추가하고 summary·strict·semantic reader가 같은 projection을 읽는다. 아래 필드는 계획상의 계약이며 현재 구현되어 있다는 뜻이 아니다.

| 필드 묶음 | 필수 의미 |
| --- | --- |
| identity | family, source date, publication/apply date, scope, source/schema/code hash, incumbent hash, native generation |
| generation capability | 활성 조건, 생성/선정/발행/reader 지원 여부, 누락 단계, 마지막 소비자, 확인 코드/fixture receipt |
| source state | complete, bounded-wait, recoverable-gap, irrecoverable-history, unsupported-scope, valid-empty; scope별 분모/제외 원장 |
| comparison state | not-run, incomplete, unrankable, hold-sample, hold-no-edge, selected; 적용한 원 family metric/검증 계약 |
| handoff state | no-candidate, incumbent-carried, initial-published, successor-published, prepared, PID-consumed |
| repair ownership | 현행 owner ID/파일, blocker, 허용 다음 동작, closure test, retry 가능 조건 |

`artifact_complete`와 `generation capability`를 합치지 않는다. 예를 들어 rising-missed는 당일 valid-empty여도 수량 모델 미구현을 별도로 표시한다. 의도적으로 report-only/retired인 family에는 신규 정책 생산을 요구하지 않는다. 오래된 보고서에 capability가 없으면 `unverified`로 읽으며 실패나 성공을 추정하지 않는다.

성숙 대기는 원 producer가 선언한 horizon과 계속 도착 가능한 원천을 가진 경우에만 사용한다. 재시도 키는 `(family, source_generation, code_contract, unresolved_reason)`로 고정하고 **변화 없는 회복 불가 입력의 자동 재실행은 하지 않는다**. 코드나 정확 원천 revision이 바뀌면 영향 범위만 재검증한다.

새 연구 지표는 metric role·primary metric·window·floor·authority·forbidden uses를 선언한다. 가격 시점 연구에 실제 체결/청산을 추가 요구하지 않으며, 실제 실행 품질이나 순이익을 주장할 때는 해당 계약의 비용/종결 증거를 별도로 요구한다.

## 4. P0 — 기준 고정과 도달성 시험

1. 선택 release, workspace dirty files, active writer/PID/cwd, 원 source date, incumbent/override, 10/12 sealed checklist/PREOPEN/pointer를 해시로 고정한다. 구현 중 원 파일과 정책을 실험 입력으로 덮어쓰지 않는다.
2. 감사의 5 구조 항목과 5 퇴역 항목을 **현재 코드 반례**로 만든다. 단순 report exists/PASS 대신 `eligible source → selected candidate → native publisher → strict reader`의 도달성을 검사한다. 의도적 carry에는 반대 시험을 둔다.
3. 기존 퇴역 회귀의 165 pass/1 fail은 기준 상태로 남긴다. 삼성 전용 명령 복원으로 실패를 없애지 않고 P8에서 테스트 기대값을 현행 Main-only 계약으로 고친다.
4. full/partial/no-fill, 실제/CF, Main/manual/retired, KRX/NXT/SOR와 세션, 비용 revision·원천 시계·holdout을 fixture에서 분리한다. exact identity가 없는 행의 임의 symbol/time join을 금지한다.
5. 기존 기능 기준 B0, 기능 수리 기준 B1, 최적화본 B2를 구분한다. B0→B1의 의도한 결과 변화 목록을 고정하고 B1↔B2는 동일 전체 입력·분모·후보·정책 의미를 비교한다.

산출물은 작은 감사 manifest와 fixture/benchmark 계약이다. source 파일/테스트 신설 전 위치 gate를 적용한다. Python 신규 구현은 기존 `automation`, `scalping`, `monitoring`, `ai`, `risk` 역할 안에 두며 `src/engine` 루트 신설은 하지 않는다.

## 5. P1 — cancel-wait의 대사와 학습 결합 해소

대상: [entry_cancel_wait_tuning.py](../../src/engine/automation/entry_cancel_wait_tuning.py)의 `_history_dates`, `_hydrate_missing_history`, `_reconcile_history`, `_unresolved_prior_custody`, 평가 후 선정 veto; [entry_cancel_wait_runtime.py](../../src/engine/scalping/entry_cancel_wait_runtime.py), native policy/summary/semantic reader.

### 입력과 알고리즘

1. 같은 보고서에서 **historical submission audit**, **현재 Main custody**, **economic eligible population**의 상태/해시를 분리한다. 옛 9/29·9/30·10/1 gap과 `unresolved_prior_custody_count=null`은 그대로 보존한다.
2. 학습 경계는 refresh 시작일 9/29를 보존하되, 계약 유효성으로 제외된 날짜/행을 제외 원장으로 고정한다. valid-empty 날짜, 회복 불가 날짜, 원천 아직 도착 중인 날짜를 구분한다. 단순 최신 N일로 잘라 과거 결손을 지우지 않는다.
3. 경제 비교는 같은 scope/모델/정책 세대에서 적격 원천을 가진 표본으로 수행한다. calibration/holdout 분리, 취소 확인·늦은 체결·partial/no-fill 모델, 기존 최소 표본·변경 폭은 유지한다. 과거 전체 날짜 coverage를 경제 비교의 단일 boolean으로 사용하지 않는다.
4. 현재 Main custody는 native management disposition 및 verified registry/journal로 별도 판정한다. 단순 로컬 registry의 open0은 독립 증명이 아니다. 이미 정상 경로에서 생산된 position/open-order/intent 대사의 완전성·시각·owner·원천 hash를 가진 custody checkpoint를 사용하고, 그 이후 모든 Main dispatch/partial/late/terminal 연속성을 확인한다. checkpoint가 없거나 local/broker 증거가 충돌하면 현재 custody는 계속 unknown이다. 실제 미종결 주문·현행 식별 불능 custody는 기존 안전 조건을 유지한다. retired owner 잔여는 Main 차단 조건에 넣지 않는다.
5. 학습 후보가 생겨도 현재 custody/적용 계약이 불명확하면 research candidate와 `apply_blocked`를 함께 남기고 incumbent를 승계한다. 대사 결손을 숨기기 위해 후보 자체를 삭제하지 않는다. 제출 0은 실제 원천 대사가 검증된 날짜에만 표시한다.
6. 후속 정확 원천이 도착하면 해당 날짜의 immutable correction revision을 추가하고 관련 모델/holdout/후보를 무효화·재평가한다. 단일 과거 `predecessor_source_gap=true`를 새 세대에 무조건 전파하는 sticky veto를 없애되, 원 gap 기록은 삭제하지 않는다. correction generation·reader code·비용 revision을 cache key에 포함하고 재검증이 끝나기 전 기존 선정의 유효성을 재사용하지 않는다.

### 종료 시험 CW1–CW6

- CW1: 과거 결손 + 미래 완전 표본에서 경제 비교가 진행되고 과거 gap 원장이 남는다.
- CW2: 같은 조건의 현재 known-open/unknown Main custody는 적용을 막고 후보 진단은 보존한다.
- CW3: retired owner 잔여가 Main 후보/준비를 차단하지 않고 역사 owner가 유지된다.
- CW4: 당일 실제 0/단순 missing/부분 projection이 서로 다른 상태다.
- CW5: late fill/비용 정정/원천 정정은 관련 세대를 무효화하고 동일 날짜 successor를 한 번만 발행한다.
- CW6: source-only 연구/현재값 carry는 가능한 반면, 미검증 비용이나 terminal을 0으로 바꾼 경제 승격은 실패한다.

## 6. P2 — rising-missed 수량·자본 모델 구현

대상: [rising_missed_intraday_feedback.py](../../src/engine/monitoring/rising_missed_intraday_feedback.py), [rising_missed_classifier_prior.py](../../src/engine/monitoring/rising_missed_classifier_prior.py)의 join/metrics/evaluate/publish, [rising_missed_candidate.py](../../src/engine/scalping/rising_missed_candidate.py), 기존 최초수량·실행 모델과 bootstrap/strict reader.

### RM 입력 v2

원 `evaluation_id`, 원 decision 시각, owner/symbol/venue/session, policy/version, executable BBO/depth/clock/route/epoch와 함께 **그 시점에 알 수 있었던** sizing policy, 가용 예산·예약/사용 자본·동시 position·상한, 기존 guard 결과를 결속한다. 현재 feedback에 quantity/budget 계열 필드가 존재하더라도 특정 TP1 evaluation과 결속되지 않으면 join하지 않는다.

기존 최초수량의 순수 계산/원천 adapter를 재사용한다. **TP1에서 차단된 opportunity도 제출 이전의 원 평가 지점에서 입력을 보존해야 한다.** 수량 source를 submit/fill 성공 후에만 수집하면 연구 대상 차단 표본은 영원히 적격이 되지 않는다. `_log_rising_missed_tp1_counterfactual_submit_safety`와 원 TP1 평가 시점의 동일 identity에 이미 확보된 공통 account/capital/sizing snapshot을 결속한다. 늦게 생긴 다른 attempt의 budget으로 보충하지 않는다.

평가용 수량 계산을 실제 intent 예약·주문·REST 호출 함수와 분리한다. 당시 shared snapshot이 없으면 구체적 producer gap을 기록하고 그 snapshot의 정상 생산 경로를 먼저 보완한다. 없는 예산을 현재 계좌 잔액으로 소급 보충하거나 고정 100만원 notional을 넣지 않는다. live API/프로토콜 변경이 필요하면 구현 전에 AGENTS의 Kiwoom official reference gate를 거친다.

### RM paired 계산

1. 기존 후보 목록은 baseline + 최대6개, source-day 상한20, calibration30건/3일·holdout20건/2일을 보존한다. 다만 현재 `_candidate_selected`가 식별하는 변경은 **`positive_support_min 2→1` 하나**다. 첫 경제 수리는 이 축을 대상으로 한다. support 강화는 허용 population의 정확 원천이 없으면 unsupported, spread/chase는 실제 selector 결정에 영향을 주는지 확인하여 diagnostic-only/unsupported로 분류한다. 단순 false를 `identical_policy`의 인과적 증거로 사용하거나 diagnostic 수치를 새 매매 gate로 만들지 않는다. 이 floor를 다른 family에 전파하지 않는다.
2. 같은 동결 기회·자본 시작 상태·사전 우선순위에서 두 arm을 각각 시간순 재생한다. 동시 주문의 예약·해제·수량 cap·세션 및 다른 기존 position의 자본 점유를 반영한다. 기회별 독립 가정으로 같은 현금을 중복 사용하지 않는다.
3. 양쪽 arm 모두 동일 cost/model 계약으로 평가한다. 실제 baseline PnL과 가상 candidate PnL을 무표시로 섞지 않는다. 관측된 실제 종결은 모델 검증과 별도 actual 지표로 사용한다. no-trade 0은 해당 arm의 명시적 미거래·자본 중립을 증명한 경우에만 허용한다.
4. 비용 후 모델 손익은 `sell_proceeds - buy_notional - buy_cost - sell_cost`로 계산하고, 원화 일별 합계·일별 차이·worst-day·자본 점유를 함께 만든다. 수익률 평균과 원화 합계는 별개다. 재생용 가격/비용 가정은 decision 당시 알려진 계약을 사용하고, 이후 정산 실제 비용은 검증/actual 원장 및 명시 correction으로 분리한다. 수량/자본/유동성/비용/종결 모델 결손은 NULL/censored로 남긴다. 미해결 점유의 해제 시점을 만들어 후속 기회를 허용하지 않는다.
5. candidate 선택은 train에서 한 번 확정하고 독립 holdout에서 검증한다. 모델 오차·partial/no-fill 지원과 기존 guard를 통과한 범위만 bounded 기존 TP1 selector로 전달한다. calibration과 holdout을 가로질러 자본 점유/가격 경로가 겹치는 opportunity는 한쪽에서 제외하고 원 identity를 남긴다. 선택한 후보가 holdout에서 실패하면 다른 후보를 같은 holdout으로 재선정하지 않는다. CF 우위는 actual order quality/수익 실현의 증거가 아니다.
6. legacy reader는 v1의 NULL을 유지하고 v2 완전 원천만 새 계산에 사용한다. schema만 v2로 바꿔 과거 행을 적격으로 만들지 않는다. 모델 검증 원천은 기존 비용 검증된 실제 실행 모집단에서 오며 **각 가상 challenger의 실제 체결**을 선행조건으로 요구하지 않는다. 기존 family의 모델/승격 조건은 유지한다.

### 종료 시험 RM1–RM6

양수 EV·충분한 표본·유효 자본 모델이면 실제 선정/dated publisher/기존 reader에 도달해야 한다. 반대로 원천 수량이 없으면 기존 structurally-blocked를 유지한다. **실제 제출0인 blocked TP1 fixture에서도 완전 snapshot으로 CF 계산까지 도달**해야 한다. 동시2기회의 자본 중복, no-trade 미확인, 거래순서/시간 역전, 비용 revision, partial/late fill 미지원, 미래 예산 join, 손실 후보의 incumbent carry를 각각 검사한다. `valid_empty`여도 capability 미구현은 독립 표시한다.

## 7. P3 — 보조 캠페인 영구 planned 해소

대상: [reversal_auxiliary_tuning.py](../../src/engine/scalping/reversal_auxiliary_tuning.py)의 prepare/calls/evaluate/improves, campaign/store/budget reader, continuous-reversal auxiliary 발행과 summary/semantic consumer.

### 불변 캠페인과 resolution

1. 원 50 pair/100 request의 manifest·identity·응답·예산 원장은 수정하지 않는다. `(campaign_sha, pair_key, source_revision, request_revision)`에 결속한 resolution revision을 둔다. 별도 중복 원장이 아니라 기존 campaign output 아래 작은 참조 산출물이다.
2. pair를 `awaiting_source`, `ready`, `excluded_irrecoverable`, `invalid_response_terminal`, `budget_exhausted`, `transport_uncertain` 등 원인별로 대사한다. source horizon 도달 가능성과 canonical path/label completeness를 판단한다. 단순 시각 경과로 `path_end_before_horizon`을 resolved로 바꾸지 않는다. WIN/STOP이 원 계약의 first-hit으로 이미 확정된 행에는 불필요한 전체 horizon을 새로 요구하지 않는다.
3. **요청 정산 완료**, **유효 공통 pair 비교 완료**, **정책 개선 선정**을 별도 필드로 표현한다. 29개 source-gap이 terminal exclusion으로 대사돼도 전체 paired 비교가 완료됐다고 표시하지 않는다. 기존 `comparison_complete`의 의미를 몰래 바꾸지 않는다. unresolved transport가 있으면 원 budget 차감은 유지하고 `accounting_pending`이다. 호출 중지의 종료 상태와 전달 결과의 정산 완료를 혼동하지 않는다. store/calls/evaluate/summary가 동일 resolution generation을 읽도록 한다.
4. 정확 원천 복구/정정은 원 parent와 source revision을 가진 successor에서 평가한다. 대체 표집은 제외 행만 원하는 결과로 채우지 않고 scope·시각·사전 hash 순서·개발/holdout 분리를 고정한다. 제외율과 미표집 전체 census를 보존한다.
5. invalid response 재시도는 같은 identity의 오류 원인·지원 codec·원 응답을 보존한다. 미응답/불확실 전송은 실패 여부를 확인하기 전에 중복 호출하지 않으며 원 예약을 유지한다. 유효 cache는 exact input/model/prompt/encoder/schema/decoder/provenance 일치 때만 재사용한다.

### 예산과 선정 경계

- 정기 원천일100회와 연구 key별 durable allowance/사용량을 그대로 읽는다. 새 날짜/세대/후보/재시도로 초기화하지 않는다. 기존 연구 top-up이 있더라도 그 범위의 successor인지 확인하며 다른 정기 작업이 잔여를 자동 사용하지 않는다.
- provider 호출을 하려면 해당 기존 승인 scope·남은 원장 budget·전송 계약이 모두 유효해야 한다. 문서의 800이라는 숫자가 새 허용량이 되지 않는다. 이 계획에는 새 provider 호출이나 증액 실행이 없다.
- `PASS 승률=TP/(TP+FP)`와 동률 TP 비교를 유지한다. 어느 한쪽 PASS 분모0이면 `unrankable_no_pass_denominator`, 수치는 NULL, incumbent carry다. 후보의 추가/제거 PASS W/F는 진단으로 공개한다. 기계 원 승률이나 0%를 대체 comparator로 사용하지 않는다.
- `paired_metrics_ready=true`는 유효 일부 pair가 있다는 뜻이다. 같은 문구를 full census 완료, prompt 효과 입증, PID 채택으로 사용하지 않는다.

### 종료 시험 AX1–AX7

현재 17 valid/29 unresolved/3 extra planned/1 invalid의 원장을 frozen fixture로 대사한다. 영구 결손·미래 성숙·원천 정정·부분 transport 성공·양쪽 budget 경합/잔여1회·0-PASS·current wire 변경을 검사한다. 원 rows 수/identity/기존 사용량이 바뀌지 않고, terminal accounting 후 unchanged campaign에 provider 재호출이 없어야 한다. late valid 응답은 revision으로 한 번만 반영한다.

## 8. P4 — holding vote 후보 선택을 실제 발행기까지 연결

대상: [holding_exit_vote.py](../../src/engine/ai/holding_exit_vote.py), [holding_path_vote_replay.py](../../src/engine/scalping/holding_path_vote_replay.py), [holding_path_vote_policy.py](../../src/engine/scalping/holding_path_vote_policy.py), holding report/source assembler, 기존 Main stop/trailing replay·runtime lookup.

### 수치 정책과 프롬프트 연구를 분리

1. 첫 구현은 **현재 prompt의 실제 원 vote로 평가할 수 있는 기존 수치 후보**다. 원 position·fill·policy pin·market/session·signal time·route/epoch·snapshot·requested/received time을 고정한다. 미래에 도착한 vote로 과거 crossing을 판정하지 않는다. 원 `_candidate_policies`의 window/quorum/firmness/freshness/gap/duration/defer 후보와 허용 compound만 fingerprint로 고정하며 후보를 임의 증식하지 않는다. safety freshness의 상한과 일반 vote freshness는 별도다.
2. 대안 정책이 요구하는 시점에 실제 vote 입력이 없거나 미래에 달라질 holding 상태/후속 AI 답을 알 수 없으면 그 arm은 censored다. recorded vote를 다른 snapshot의 응답처럼 재사용하지 않는다. 원 runtime ring의 eviction/누락과 raw ledger 보존 범위를 함께 검증해 필요한 window가 사라진 행을 complete로 세지 않는다. 새 prompt 비교는 별도 원천/예산이 필요하며 수치 후보 수용의 필수 선행 작업으로 만들지 않는다.
3. 같은 원 입력에서 baseline/candidate의 signal·defer·보호 우선순위를 기존 순수 결정 함수로 재생한다. full depth/실제 entry basis/비용/exit model 지원 범위는 기존 stop/trailing 모델을 재사용한다. **12 cell 중 `ADD_REBOUND` 3개는 기존 별도 ADD owner의 parent를 유지하며 이번 청산 selector의 변경 대상에서 제외한다.** `EXIT_TRAILING_TP`는 trailing 재생, `EXIT_SOFT_STOP`은 stop 재생에 연결한다. `EXIT_POST_ADD_FAIL`은 검증된 실제 ADD 체결 후 aggregate basis/수량/비용의 새 position generation부터 시작하는 adapter를 추가한다. 공통 stop 모델이 ADD를 지원한다고 가정하지 않는다. 그 이후 추가 ADD·partial SELL·manual 전환·다른 exit 개입은 해당 arm에서 censored다.
4. `modeled_delta_net`, tail·exposure·censoring·source coverage를 산출한다. 실제 completed PnL과 CF를 분리하고 train 선택 후 holdout으로 검증한다. vote 전용 실험 계약에 parent/cell/path/허용 수치 키·후보 해시, freeze/split/embargo, train/holdout 최소 표본, censor 상한, paired EV·daily-net·tail/exposure 조건, 모델 오차·성능 receipt를 **평가 전에** 고정한다. 기존 stop의 튜닝 키/계약을 그대로 가져오지 않는다. 수치 한도가 정의되지 않으면 baseline carry이며 기능 미구현과 다른 `experiment_not_armed` 상태다.
5. v2 bundle은 `initial_baseline`, `incumbent_carry`, `validated_successor`를 구분한다. 초기 v1 정책을 읽는 호환 경로를 먼저 배포 가능하게 설계하고, successor에서는 baseline 동일성 대신 정확 parent·허용 키/범위·비교 receipt·reader version을 검증한다. 검증을 느슨하게 해 임의 정책을 허용하지 않는다.
6. 12 cell의 완전한 bundle을 유지하면서 선정된 적격 EXIT cell만 변경한다. 나머지는 실제 선택된 parent policy와 이유를 승계한다. code default를 현재 incumbent로 가정하지 않는다. source-gap cell을 누락하거나 임의 공통 기본값으로 덮지 않는다. normal/fast pin과 operator override 우선순위를 보존한다.

### 종료 시험 HV1–HV6

비기본 유효 EXIT 후보의 replay→selection→v2 publisher→strict→bootstrap→position lookup 양성 경로, v1 현재 baseline 호환, late/missing vote, 다른 snapshot 재사용, 부적격 cell/ADD cell carry, 수동/하드 안전 우선권을 시험한다. POST_ADD는 정당한 재기준 설정과 이후 상태 변경 검열을 각각 검증한다. 금지된 hard/protect/emergency 완화 후보는 source가 완전해도 거부한다. synthetic fixture의 선정 성공을 자연 경제 우위로 보고하지 않는다.

## 9. P5 — 보호선 생성 요구의 의미와 출처 정리

대상: [sniper_execution_receipts.py](../../src/engine/sniper_execution_receipts.py)의 `_apply_scale_in_protection`, Main handler의 line 소비, [main_stop_postclose.py](../../src/engine/automation/main_stop_postclose.py)의 generator status, 기존 trailing owner/stop source ledger.

1. 원 position의 line을 `active_main`, `operator_manual`, `legacy_retired`, `unverified`로 분류하고 원 가격/수익률·생성 시각·policy/source·position generation을 함께 보존한다. 출처가 없는 기존 line을 새 Main 생성선으로 소급 인증하지 않는다.
2. PYRAMID branch의 `avg_price * 1.003/1.01` 생성 코드는 영구 퇴역 경계에 맞춰 제거한다. AVG_DOWN의 soft-stop reset와 기존 historical receipt/DB parser·수동관리 값은 보존한다. 과거 owner나 거래 수량을 Main으로 이전하지 않는다.
3. 일반 Main 익절은 기존 `scalp_trailing_take_profit` owner의 유효 결정과 source lineage를 생성/기록한다. 필요하면 기존 결정의 **같은 의미를 표현하는 관측 projection**을 내보내되 별도 protect 주문·더 이른 exit·새 arm 비율을 만들지 않는다. 비율/가격 환산이 비용·tick/rounding 때문에 동일함을 입증할 수 없으면 raw 결정값과 단위를 그대로 기록한다.
4. 현재 전략에 신규 line producer가 없는 branch는 조건부 미적용으로 선언하고 보호선 없는 position에 영구 생성 대기를 만들지 않는다. 실제 유효 line을 사용하는 position의 source/consumer 결손은 계속 오류다. 이 분류를 기존 Main stop 확인 파라미터의 튜닝 완료로 대신하지 않는다.
5. 독립 신규 보호선 알고리즘·매도 기준 변경이 필요하면 기존 stop owner에서 별도 family/후보/권한/경제 계약을 확정해야 한다. 이번 공통 정리가 자동으로 새 매도 권한을 만들지 않는다.

종료 시험 PL1–PL5: line 없음은 조건부 미적용, Main 유효 line은 provenance 일치, manual/legacy line은 귀속 보존, PYRAMID 신규 line 생성 불가, normal/fast에서 기존 원천/임계치/우선순위/자연 submit 의사결정 동등성을 확인한다. 보호선 없음 자체를 허위 정상값으로 채우지 않는다.

## 10. P6 — 나머지 family의 미래 원천 지원 확인

| 대상 | 필요한 보완 | 완료 기준 |
| --- | --- | --- |
| entry-split | `apply_entry_split_order_policy`의 operating context→원 decision identity/양 arm→`strategy_owner_replay`→평가 field를 한 행씩 추적. 누락 필드를 기존 shared snapshot에서 바인딩하고 경제 적격 원천과 진단을 분리 | 완전 native fixture는 모델/후보 평가까지 도달. queue/unknown partial/cancel/후속 ADD 등 unsupported는 여전히 별도 제외 |
| WS/lookup attention | 전체 scanner partition의 promoted/pruned identity·원 자원예산·선택 변화·후속 관측/모델 입력과 source-quality/master 세대를 결속 | complete partition 양성 경로, missing member/중복/다른 generation/종목 master mismatch 음성 경로; 내부 source-gap을 summary not-applicable로 숨기지 않음 |
| legacy outcome label | exact input bundle/canonical bars/context와 실제 현재 producer 버전을 확인. 과거 19개는 원 데이터가 있는 항목만 immutable correction, 회복 불가는 제외 | 새 source-ready row의 label 도달과 과거 원천 결손 분리. 미래 벽시계만으로 과거 label을 수리했다고 표시하지 않음 |
| pre-submit delay·초기수량·Main trailing·기계판정 | 이미 구현된 source/selector/reader와 공통 변경의 영향만 회귀 | 기존 가격 연구 범위·수량 parent·전수 scope/분모·기계 등록 정책·target-date 인계 보존 |
| 시장약세 연구·OFF/retired | 기존 advisory/retired 계약의 기대 산출물 목록을 명시 | 미생성 live 정책을 장애로 만들지 않고 별도 연구 결과/원천 gap만 보고 |

새 장중 REST/WS/provider 수집으로 원천 결손을 일괄 해결하지 않는다. 우선 기존 공통 원천·bounded queue의 immutable 참조를 재사용하며 누락/overflow/drop을 소비자가 감지하도록 한다. 지원하지 않는 체결 모델을 같은 날 즉시 전부 구현한 것처럼 표기하지 않는다.

## 11. P7 — 의미적 감시·요약·권고 intake

대상: [family_policy_semantics.py](../../src/engine/monitoring/family_policy_semantics.py), [semantic_incident_contract.py](../../src/engine/monitoring/semantic_incident_contract.py), [artifact_freshness.py](../../src/engine/error_detectors/artifact_freshness.py), [runtime_approval_summary.py](../../src/engine/runtime_approval_summary.py), notifier/coverage, [postclose_recommendation_intake.py](../../src/engine/automation/postclose_recommendation_intake.py).

1. §3의 native capability/source/comparison/handoff를 같은 `as_of`/generation으로 읽는다. capability는 함수 이름/등록 개수로 PASS시키지 않고 실제 생산·선정·발행·reader의 코드/검증 receipt와 결속한다. stale 증거는 unverified다.
2. rising-missed의 valid-empty 뒤에 있는 모델 결손, vote의 초기 발행 뒤에 있는 selector 결손, cancel의 역사/현재 custody 차이, auxiliary의 정산/비교 차이를 표시한다. 미래 due와 native cutover를 존중한다.
3. incident identity에 family/scope/source-generation/blocker를 포함한다. 변화 없는 구조적 결손은 동일 건으로 보존하고 새 source/code revision일 때만 복구를 판단한다. 파일이 사라지거나 관심 window 밖으로 나갔다고 자동 해결하지 않는다.
4. `code_improvement_workorder`의 현행 freshness 요구를 제거하고 active source→native recommendation/disposition로 intake를 이행한다. owner별 allowlist/adapter는 실제 code-improvement 권고를 가진 source만 포함하며 모든 정책·보고서 행을 workorder로 바꾸지 않는다. 원 native ID/location/hash를 보존하고 canonical/projection을 두 건으로 세지 않는다. 모르는 schema/권한은 `unobservable`/명시 gap이며 자동 실행 지시로 번역하지 않는다. 퇴역으로 더 이상 기대하지 않는 과거 incident는 retirement 날짜/계약·선택 코드 증거를 가진 `retired_no_longer_expected`로 처분하고 원 missing 이력을 복구 성공으로 바꾸지 않는다.
5. current owner는 현재/이미 예약된 exact-date OPEN 항목에서 하나만 해석한다. 과거 owner 문자열로 fallback하거나 하나의 공통 owner가 모든 향후 source-gap을 영구 인수하지 않는다. owner 불명은 별도 finding으로 보고한다.
6. notifier는 기존 제한/128건 상태 계약과 전송 영수증을 보존한다. 구조 repair와 runtime incident의 severity를 구별한다. 미구현 경제 연구만으로 새 전역 startup 차단을 추가하지 않으며 유효 정책 binding/안전 실패는 기존대로 차단한다.

SM1–SM7: 단독 구조 gap→detector→notifier fixture, valid-empty+capability gap, retired missing 비경고, partial native source, 동일 incident 중복/부분 전송, 정확 successor 복구, 미래 owner/cutover를 검사한다. 테스트 transport를 사용하며 실제 Telegram을 보내지 않는다.

## 12. P8 — 퇴역 코드 정리의 구체 순서

### 12.1 바로 분리 가능한 고립 표면

- `src/trading/order/target_amend.py`: 삭제된 adaptive-exit import를 복원하지 않는다. 정적/dynamic registry/문서·배포·외부 CLI caller를 마지막 확인하고 제거한다. 10/11 구현에서 삭제했으며 [구현 검토](../audits/postclose-structural-policy-completion-implementation-review-2026-10-11.md)에 기록한다.
- `deploy/run_shadow_canary_check.sh`: 현행 caller가 없으면 wrapper/설치 참조를 제거한다. 실제 외부 호환 caller가 발견되면 명시적 retired 응답과 종료 계약을 먼저 제공하고 삭제일/소유를 둔다. 없는 모듈의 실패를 exit0 성공으로 감추지 않는다. 10/11 구현에서 launcher를 삭제했으며 기존 installer는 cron 제거 도구로만 남긴다.
- `test_adm_ldm_retirement.py`의 삼성 전용 producer 기대값을 Main-only 퇴역 계약으로 수정한다. 해당 명령 부재와 `RUN_SAMSUNG_MACHINE_ENTRY_TUNING=false`를 검증한다.

### 12.2 현재 caller가 있는 18모듈

파일별 caller는 [감사 census](../../data/report/postclose_structural_audit/2026-10-11/static-source-census.json)를 기준으로 착수 시 재생성한다. 46,050행 전체를 즉시 삭제 가능한 것으로 보지 않는다.

| 현재 본체/의존 | 이전·제거 순서 |
| --- | --- |
| `scalp_entry_action_decision_matrix`→`entry_observation_source` | raw row/event/backfill helper를 기존 source owner 안으로 이전, 분모/row-byte 의미 동등 검증, matrix 본체 제거 |
| `scalping_avg_down_recovery_calibration`→`strategy_owner_replay` | event path/reader를 현행 replay source 계층으로 이전. AVG_DOWN 공통 수학과 실제 수탁은 유지 |
| `build_code_improvement_workorder`→`pattern_lab_propagation_audit` | 필요한 순수 helper만 이전, P7의 retired freshness/intake 의존 제거 후 구 producer 삭제 |
| `lifecycle_ai_context`, `lifecycle_decision_matrix`, `lifecycle_bucket_discovery`, `lifecycle_decision_matrix_runtime` | active 상수/reader와 neutral 결과 계약을 분리. AI/handler/AVG_DOWN caller를 새 역할 owner로 이전한 뒤 퇴역 본체·불필요 facade 제거 |
| `institutional_flow_context`, `runtime_apply_bridge` | archive reader/runtime-apply audit의 필요한 참조만 남기고 신규 정책/승격 경로 제거 |
| `scalping_pyramid_intraday_feedback`, `scalping_pyramid_quality_calibration` | 퇴역 entrypoint·succession branch와 P5의 신규 보호선 branch 제거. historical attribution은 보존 |
| `ldm_hypothesis_parent_refinement`, `ldm_hypothesis_discovery` | 외부 caller/문서 사용 대사 후 퇴역 연구 본체와 그 내부 참조 제거 |
| `opening_rotation`, `opening_rotation_backtest`, `opening_rotation_tuning` | Main의 receipt/표시 호환과 현재 호출 guard를 보존하면서 직접 CLI의 evaluate/publish/apply 권한까지 제거 |
| `scalp_sim_ev_midcheck`, `scale_in_incremental_counterfactual` | 필요한 공통 수학/과거 receipt reader를 역할 패키지로 이전하고 퇴역 정책 생산 본체 제거 |

신규 helper 파일이 필요하면 역할/사용 caller/기존 모듈로 수용할 수 없는 이유를 변경 근거에 기록한다. root compatibility wrapper는 실제 caller가 있을 때만 임시 유지하고 제거 조건을 둔다. 삭제/이전과 함께 engine-root allowlist·imports·`-m` 명령·registry string·package exports·관련 테스트/문서의 참조를 갱신한다. `owner_retirement.py`, Main/manual veto·journal·historical custody, 오프라인 가격 구간 연구의 episode 명칭은 삭제 대상과 구분한다.

### 12.3 배포 사본과 문서

selected/rollback/worktree/process/prepared/source hash가 참조하는 release를 파일 단위로 고쳐 쓰거나 삭제하지 않는다. 현재 source 정리→새 불변 release 검증→정식 선택 순서로 이행한다. 옛 release 저장공간 정리는 이번 코드 계획과 별도 retention 작업이다.

wrapper/자동화가 실제 변경되는 구현 묶음에는 관련 운영 문서와 checklist 변경을 포함한다. 현재 inventory의 Main stop cutover/야간 연구 누락, retired flags/DONE fields/parser 기대값을 같이 이행한다. README/runbook/Rebase/prompt/AGENTS는 이번 문서 작업에서 수정하지 않으며 실제 수정 필요 시 해당 문서의 명시 요청 범위를 대사한다.

RT1–RT6: 전체 내부 import·literal/dynamic entrypoint census, retired CLI 직접 호출, 현행 source row 동등성, Main/manual/retired custody 경계, 설치 cron/unit, historical schema reader 회귀를 검사한다. 퇴역 기능을 되살리는 rollback은 허용하지 않는다.

## 13. P9 — 검증·성능·정식 인계

### 13.1 기능·실패 주입

| 묶음 | 기본 검증 | 반드시 포함할 실패 |
| --- | --- | --- |
| cancel | `test_entry_cancel_wait_tuning.py`, runtime/attribution, native summary/strict | 과거 missing·현재 open·retired residual·정정·동일날 successor |
| rising | `test_rising_missed_classifier_prior.py`, feedback, TP1 consumer | 수량/자본 결손·동시 점유·미래 join·cost correction·holdout 누출 |
| auxiliary | `test_reversal_auxiliary_tuning.py`, 연구 budget/wire, native publisher | 영구 censor·partial transport·budget race·0-PASS·cache/wire mismatch |
| vote/보호선 | `test_holding_path_vote_replay.py`, policy reader, `test_main_stop_policy.py`, normal/fast handlers | missing/late vote·unsupported arm·v1/v2·manual/retired line·안전 우선권 |
| source/감시 | family semantics/coverage, intake, summary/strict/controller | partial report·native/source hash mismatch·미래 cutover·owner 없음·정산/비교 혼동 |
| 퇴역 | 기존 Main-only/widget/ADM-LDM suite 및 영향 caller | 직접 CLI 부활·import 파손·호환 reader 누락·rollback 퇴역 부활 |

새로운 유의미한 회귀는 각 역할의 `src/tests` 기존 모듈에 우선 추가한다. Python compile/import, shell 변경 시 `bash -n` 및 wrapper contract, `git diff --check`를 수행한다. 코드 변경이 없는 이 계획 작성에서는 관련 거래 suite·provider·보고서 재생성을 실행하지 않는다.

### 13.2 성능과 자원 계약

- 장중: 새 network/provider/file scan, 동기 fsync/hash/decode, 중복 sampler를 추가하지 않는다. 기존 공유 snapshot 참조/queue를 사용한다. normal/burst/slow-writer에서 decision·submit·cancel/fast-stop 지연, queue drop/overflow·원천 complete, CPU/RSS/I/O를 함께 측정한다. 빠른 누락이 최적화가 되지 않게 한다.
- 장후: manifest 기반 touched-shard 재계산, source/code/schema/parent/비용 세대 cache key, 원천 1회 decode/hash, 날짜별 대사 인덱스를 사용한다. 원천 정정은 영향 shard와 전역 통계/선정/발행을 함께 무효화한다. 전체 scope/분모/후보를 줄여 속도를 맞추지 않는다.
- 실측: 동결 입력의 cold/warm/증분/비용 정정/중단 후 재개를 B1↔B2 교대로 각3회 이상 측정한다. 단독과 실제 함께 실행될 heavy-job 조합을 구분한다. 기존 shared admission/CPU/RSS/read-byte/file-count/deadline 한도를 보존한다.
- gate: 해당 owner의 이미 고정된 성능 한도를 우선 적용한다. 신규 측정 항목은 P0에서 데이터 크기·반복수·절대 예산·허용 오차를 먼저 봉인하며 결과를 본 뒤 완화하지 않는다. 기존 stop/semantic의 15% 허용 오차를 모든 장후 작업에 자동 전파하지 않는다.
- 원천 없음/0건의 빠른 실행은 기능·전체 성능 PASS 근거가 아니다. 결합 부하가 확인되지 않으면 해당 런타임 변경의 수용을 완료 처리하지 않는다. 독립 detector-only 수리는 무관한 전체 연구 성능을 기다리지 않는다.

### 13.3 운영 인계와 rollback

1. 각 독립 묶음은 구현→자기리뷰→보완→재리뷰→표적 기능/성능 검증으로 닫는다. 미해결 코드 finding과 자연 미관측을 분리한다. 유효 complete-source 양성 경로가 없으면 구조 완성으로 표시하지 않는다.
2. 기존 승인 범위/체크리스트가 허용하는 운영 후속만 실행한다. 승인 이력을 무시해 다시 요구하지 않지만, 이 계획 문서 자체로 새 임계치·provider·주문·봇 권한을 만들지 않는다.
3. 실제 인계는 선택 release·active writer와 정책 parent를 다시 확인하고 native immutable generation/CAS를 사용한다. shared workspace의 관련/무관 변경을 분리해 검토한 commit 목록과 최종 release 파일 해시를 대사한다. 새 schema는 호환 reader→producer/successor 순서로 이행하며 실행 중인 writer의 코드를 바꾸지 않는다. source 날짜는 원래 10/8 등 작업 대상을 유지하며 publication/apply 날짜와 분리한다. 현재 selector·10/12 sealed preparation을 임의 직접 수정하지 않는다.
4. 영향 producer→summary/tower→checklist→strict `--require-summary-handoff`→controller/finalization→PREOPEN 준비를 닫는다. 검증 실패 후 예전 PASS를 재사용하지 않는다. final verifier/controller의 자기 hash를 source 입력에 넣어 순환을 만들지 않는다.
5. 실패 시 해당 candidate/세대의 적용을 막고 검증된 incumbent를 유지한다. 이미 선택 pointer를 바꾼 정식 transaction이 실패하면 native CAS rollback과 그 parent의 full-contract 재검증을 수행한다. 원천/실험 원장을 지우지 않는다.
6. 실제 예약 PREOPEN→PID loader/pin→자연 결정/주문·종결→경제성은 기존 natural acceptance owner가 별도로 확인한다. fixture, 준비 영수증, provider 응답, 실제 체결을 서로 대신 사용하지 않는다.

## 14. 완료 판정

| 층위 | 종료 조건 | 종료가 아닌 것 |
| --- | --- | --- |
| 계획 | 범위·코드 owner·원천/수식/상태·이행 순서·반례·성능·rollback 정의, 반복 문서 리뷰/검증 | 코드 구현 완료 |
| 구조/코드 | 모든 활성 supported scope에 양성 도달성 + 결손/권한 음성 회귀, 미해결 in-scope code finding0 | 표본0 보고서 생성, retired 요구 삭제만으로 전체 완료 |
| 정책/운영 | 정확 source/code/parent로 발행/선정/승계·strict·정식 준비 각각 입증 | 실제 PID가 아직 없는 prepared PASS |
| 자연 증거 | 해당 PID/policy의 실제 소비 및 가족별 자연 원천·종결 | 다른 PID/과거 회복 표본 |
| 성과 | 원 family 기준의 비교/holdout·실제 비용 결과, 표본 부족/무우위는 그대로 보고 | 시뮬레이션을 실현 순익으로 표시 |

## 15. 반복 리뷰 기록

### 1차: 실제 producer·권한·경제 계산 대조

| ID | 발견한 계획상 빈틈 | 반영한 보완 |
| --- | --- | --- |
| PR1 | 과거 대사와 현재 custody를 분리하면서 local open0을 독립 증명으로 오인할 수 있음 | native custody checkpoint·이후 dispatch 연속성, 미확보 시 unknown 유지 |
| PR2 | rising 후보 목록6개를 모두 인과적 변경으로 해석할 수 있음 | 실제 `_candidate_selected`의 support완화1개를 첫 대상, 나머지 diagnostic/unsupported 분리 |
| PR3 | 수량/자본 계산에 미래 비용·점유 해제·holdout 겹침이 섞일 수 있음 | 사전 계약과 정산 비용 분리, 점유 미확정 보존, 양 구간 겹침·재선정 금지 |
| PR4 | 12 cell 전체 수정이 `ADD_REBOUND` 권한까지 바꾸고 POST_ADD를 지원 없는 공통 모델에 넣을 수 있음 | ADD3 cell parent 보존, EXIT별 adapter, POST_ADD 재기준과 후속 검열 |
| PR5 | vote의 경제 계약을 stop 계약에서 가져오면 다른 키/권한을 수입함 | 별도 frozen vote experiment, 미정의는 experiment-not-armed, parent는 실제 선택값 |
| PR6 | terminal source 제외와 미응답 정산을 혼동하거나 first-hit에 불필요한 horizon 추가 | accounting-pending 별도, 원 first-hit 계약·공통 resolution 세대 보존 |

### 2차: 생성 불능의 재발·퇴역 이행·운영 순서 반례

| ID | 재리뷰 finding | 반영한 보완 |
| --- | --- | --- |
| PR7 | 차단된 rising 표본의 수량을 제출/체결 이후에만 얻으면 여전히 생성 불능 | blocked 평가 시점의 shared snapshot, 실제 제출0 양성 fixture, 가상 challenger 실제 체결 선행조건 금지 |
| PR8 | vote window를 늘려도 원 ring/ledger 입력이 사라지면 허위 complete | 원 후보 집합 고정, eviction/원천 보존 coverage 검사 |
| PR9 | intake 정리가 모든 정책 행을 workorder로 만들거나 퇴역을 복구로 기록할 수 있음 | 실제 native 권고 adapter만 등록, retired disposition과 역사 missing 보존 |
| PR10 | 작은 감시 수리가 전체 vote 경제 연구를 기다리거나 producer가 reader보다 먼저 배포될 수 있음 | A–F 독립 묶음, 영향 gate만 적용, 호환 reader 선행/native successor 순서 |
| PR11 | 파일 삭제 후 engine-root allowlist·dynamic registry·외부 entrypoint 잔존 | 마지막 caller census, 참조/테스트/문서 이행을 같은 묶음에 포함 |
| PR12 | 옛 owner/예산 메모·코드 default가 현재 실행 owner/잔여/parent를 대신할 수 있음 | 현행 checklist 단일 owner, durable top-up/사용량 및 실제 선택 parent 재고정 |

두 차례 보완 후 P0–P9, family별 반례와 A–F 의존을 다시 대사한다. 미정의 실험 수치·미관측 자연 표본은 그 상태로 남으며 문서 리뷰 PASS로 채택 권한을 만들지 않는다.

### 최종 문서 수용

- 계획·현행 checklist의 로컬 링크, 공백, `git diff --check`, print-only parser를 검증했다. parser는23개 항목을 반환하며 통합/semantic/stop/기존3개 source-repair/자연수용의7개 owner는 각각1개다.
- 새 통합 owner만 현행 10/11 checklist에 추가했다. 봉인된 10/12 checklist·PREOPEN index/receipt, selector, 수량 pointer, 지연 committed manifest, Plan Rebase, AGENTS의 기준 해시는 보존했다.
- 이번 검사에서 발견한 문서 범위의 PR1–PR12는 보완했다. 구현 결함·미관측 source/정책·후속 실험 한도·자연 성과는 각 실행 단계의 잔여 수용이며 완료로 바꾸지 않았다.
- 계획 작업이므로 Python/거래 회귀·성능 실측·provider·장후 재생성·배포·재기동·삭제·외부 동기화는 실행하지 않았다. [최종 검증 기록](../../data/report/postclose_structural_plan/2026-10-11/document-validation.json)에 링크/owner/보호 해시와 범위를 기록했다.

구현 결과는 향후 별도 audit에 기록하며 이 계획의 완료 문구로 대체하지 않는다.
