# Entry split 주문 재현 검증·분할 경제성 튜닝 상세개선계획

작성: 2026-09-18 KST. 최초 요청은 계획 수립이었다. 이후 사용자가 구현·반복 리뷰/수정/검증·commit/push·배포 및 제한 장후 재생성을 승인했다. 다음9/21 정책 준비와 실제 PREOPEN/env/PID/자연 성과는 구분한다. 구현 package ES0–ES7은 작업 분해이며 신규 일정·주문·guard 우회 권한이 아니다.

## 1. 결정·목적·소유 경계

**기능은 유지하되, 실제 제출 주문으로 기존 방식의 재현 정확도를 먼저 검증하고, 총수량을 고정한 분할 형태의 독립 비용 차감 우위가 확인될 때만 기존 런타임에 전달한다. 동일 입력의 장후 반복 계산은 재사용한다.** 모델 검증 실패나 원천 결손 상태에서 작은 child 평균 수익률로 자동 승격하지 않는다.

목표는 매수 판단이 끝난 주문의 실행 방식 최적화다. 평균 매입가 감소만이 아니라 미체결·부분체결·취소·자금점유·tail과 순익을 함께 개선한다. 미진입 기회비용의 기계 BLOCK/RECHECK/AI VETO 평가와 분리한다. 다만 기존 전수 기회/quantity×leg 합동 계약을 체결 성공 모집단으로 대체하지 않는다.

소유 문서: [Plan Rebase §1–§8](../plan-korStockScanPerformanceOptimization.rebase.md), [당일 checklist](../checklists/2026-09-18-stage2-todo-checklist.md), [전수 기회비용 통합계획 U9–U10](entry-opportunity-cost-full-population-tuning-implementation-plan-2026-09-17.md), [기존 결과 분석](../audit-reports/2026-09-18-scanner-fact-final-review-and-entry-split-analysis.md). 이 문서는 U9–U10의 execution model/leg 평가 보완이며 별도 전수 replay 사업이 아니다. 기존 executable owner `KiwoomCommonHealthOpportunityCostAcceptance0917`의 Acceptance/History를 유지한다. 다음9/21 PREOPEN은 전체 장후 단위 보완 이후의 사용자 예정 경계다. 다른 세션의 AVG_DOWN `scale_in_split_order_plan`은 해당 owner의 검증을 유지한다.

| 역할 | 이번 계획의 경계 |
| --- | --- |
| 기계판정기·보조 AI | 진입 판정/보조 평가 그대로; 가상 AI 또는 새 진입 canary 없음 |
| mechanistic entry price | owner 발급 기준 가격/허용 가격 메뉴 그대로; AI 숫자 가격/직접 추격 가격 도입 없음 |
| position sizing | 초기 총수량 owner 그대로; 첫 탐색은 quantity fixed |
| entry split | 초기 주문의 leg 수·수량 배분·owner 허용 가격 간격과 실행 결과 비교 |
| atomic sizing binder | action/price/quantity/split receipt 결속·수량 보존; 새 진입 판정기로 변경 없음 |
| scale-in/holding/exit | 기존 AVG_DOWN·청산·손절·custody owner 그대로; 최초 진입 튜닝으로 변경 없음 |

clean baseline은2026-06-05T00:00:00+09:00 이후다. real/sim/probe/CF·main/widget/episode/manual·full/partial·KRX/NXT/SOR/session·정책/모델 버전을 분리한다. 퇴역 PYRAMID·Opening Rotation·RISING_MISSED 전용 기능은 복원하지 않는다.

## 2. 현행 근거와 먼저 확인할 문제

확인 source는 selected `53b0264c3` 계열이다. 작업본 wrapper에는 옛 호출이 남을 수 있으므로 후속 구현 시작 시 selector/HEAD/actual consumer를 다시 확인한다. 실행 중 managed root는 편집하지 않는다.

- `sniper_state_handlers` 매수 제출에서 `apply_entry_split_order_policy()`→`compose_entry_execution_sizing_plan()`→leg별 기존 검증/제출 경로가 이미 존재한다. 정책 loader/PREOPEN mapping도 구현돼 있다. 새 executor를 만들지 않는다.
- 9/17 native entry split exit0, generated9/18 00:14:34. 원자 계획 observed3/invalid3/valid0, 최종 policy0/applyfalse. 구조결손과 sample 부족을 구분한다. invalid3의 상세 사유는 기존 bounded 결과만으로 미확정이며 ES0에서 확인한다.
- exact passive child3건 평균+0.7853%는 작은 관찰 seed다. parent 평균/다른 child/전체 주문 대비 인과 ΔEV가 아니며 최종 발행은 차단됐다. sim429,200건은 real 품질 근거가 아니다.
- native executable replay raw_plan_rows0·complete0·four-arm0·holdout0. atomic observed3과 replay0은 같은 분모가 아니므로 숫자 차이만으로 decoder bug라고 단정하지 않는다.
- 기존 `strategy_owner_replay`는180초/TP+0.5%/SL−0.5%, 왕복비용0.23%·stress0.28%, common reservation180초의 연구 모델이다. `actual_fill_evidence=false`다. 운영 청산·실제 비용·자금 경로를 재현했다고 인정할 수 없다.

## 3. 두 모집단과 원천 계약

### 3.1 모델 검증 모집단

**실제 제출 시도 parent 전체**를 기준으로 child orders·취소/거부·full/partial/no-fill/late-fill을 결속한다. 성공적으로 체결된 주문만 추출하지 않는다. 모델 체결 오차는 실제 fill/terminal 원장으로 검증한다. PnL 검증은COMPLETED+유효 비용/손익만 사용하며 아직 보유/미청산은별도 censored/pending이다.

실제 체결 가격은 정답 label이다. replay 시작 가격·분할 메뉴를 실제 체결가/후행 최저가로 맞추지 않는다. 평가 단위는 parent execution attempt다. retry/replace/child fill은 parent의 lifecycle이며 독립 표본으로 중복 집계하지 않는다. Broker가 거부한 시도는 실패 진단에 포함하고 근거 없이 candidate의 정상 체결로 바꾸지 않는다.

### 3.2 분할 후보 평가 모집단

원래 신호·수량·가격·안전 판정이 고정된 **실행 경계의 frozen opportunity/attempt union**을 사용한다. 실제 제출·미체결·부분체결뿐 아니라 leg/binder/dispatcher 문제로 미제출된 eligible attempt도 분모에 남긴다. 기계 BLOCK·AI VETO는 기존 기회비용 owner가 담당하며 이 연구에 가상 주문으로 추가하지 않는다. 기존 U9–U10의 전체 quantity×leg population/최신 source-day holdout은 그대로 보존한다.

실제 제출 주문의 모델 적합성 통과가 미제출 기회의 모델 적합성까지 증명하지는 않는다. 미제출/미관측 영역은 source_gap·unvalidated_scope로 남긴다. 최종 publisher는 검증된 scope와 기존 합동 gate를 모두 확인해야 하며 submitted cohort 양수만으로 전체 최초 진입을 활성화하지 않는다.

### 3.3 최소 결속 필드

| 묶음 | 필요한 원천·판정 |
| --- | --- |
| identity | source/effective date, owner, parent/attempt/action receipt ID, broker order/child/retry/replace ID, episode/custody, stock·venue/session·route |
| frozen intent | submitted 이전 timestamp, signal/action receipt SHA, 원래 총수량·기준 가격·order type·leg 계획, quantity/price/split policy 버전·SHA, 당시 guard 결과 |
| 실행 관측 | submit/send/ack/cancel/replace/terminal 시각·수량, fill ID·price·qty·시각, late fill 및 미체결 잔여; cumulative fill delta 중복 방지 |
| 시장 경로 | causal BBO/depth·잔량·체결 흐름·quote clock·지연·연속성·venue/session·출처·원본 hash |
| 청산·비용 | entry fill 기반 보유량, 실제 exit owner/version·이벤트, exit fill·terminal, 수수료/세금·비용 근거·reconciliation 상태 |
| 자본 | 당시 허용 budget/reservation, 미체결 주문 reserve, 실제 사용/해제, holding capital time; quantity 증가 금지 |

기존 pipeline compact projection·order bundle/owner registry·fills·terminal facts·source-quality audit·DB fact를 먼저 재사용한다. 이번 계획은 새 DB/service/collector/timer/cron/production module/운영 CLI를 요구하지 않는다. 누락 필드는 기존 event emitter/decoder/projection/receipt에서 최소 보완한다. 공식 Kiwoom request/parser/FID를 실제 수정할 경우에만 upstream reference gate를 먼저 수행한다. 문서 수립 단계에서 API를 호출하지 않는다.

## 4. 첫 단계: 기존 주문 모델의 재현 판정

### 4.1 주문별 결과와 보존식

기존 report에 `execution_model_validation` section을 추가한다. 별도 독립 report producer는 만들지 않는다. 각 frozen attempt에 다음 상태를 하나 부여하고 최초 blocker·owner·closure를 기록한다.

- `source_gap`: identity/계획/시장 경로/actual terminal 계약이 없거나 손상됨.
- `terminal_pending`: 유효 원천이 있고 주문 종료 또는 실제 청산/비용을 기다림.
- `ready_for_validation`: 원천과 실제 결과가 연결돼 비교 가능.
- `validation_failed`: 비교했으나 허용 오차/실행 semantics가 맞지 않음.
- `validated_scope`: 고정된 모델을 미사용 기간에서 확인함. 주문1건 통과를 전체 모델 통과로 승계하지 않음.

두 모집단의 census·원천 준비·비교·제외를 따로 보존한다. 원천 준비 상태의 각 건수 합은 해당 parent/attempt census와 같아야 한다. 중복/충돌/irrecoverable은 별도 disposition이며 누락 원천을 valid no-fill로 바꾸지 않는다. 체결 모델 검증 가능 건수와 실제 청산 PnL 검증 가능 건수도 분리한다.

### 4.2 비교 지표와 판정 계약

| 지표 | 산출 방식·실패 의미 |
| --- | --- |
| 허위 체결/누락 체결 | actual full/partial/no-fill vs modeled confusion counts; false fill은 낙관 편향, missed fill은 참여 기회 왜곡 |
| 수량 | modeled vs actual aggregate filled qty·fill ratio; parent/child 수량 및 terminal conservation 검사 |
| 가격 | signed/absolute VWAP 오차(tick·bps), 실제 총수량별 비용 오차; 낮은 modeled 매입가 편향 별도 |
| 시간 | 최초/최종 체결 및 취소/late-fill 시각 차이; observation clock/ack latency 구분 |
| 손익 | 동일 실행·청산 계약의 modeled net vs actual completed net 차이; cost reconciliation 수준 함께 표기 |
| 자본 | 주문 reserve와 실제 노출 시간/금액 오차; 불명확하면 capital metric null |
| 안정성 | 날짜·scope·정책/모델 버전별 rolling/cumulative와 독립 검증 오차; sim와 real 분리 |

허용 오차를 validation 결과를 본 뒤 조정해서 통과시키지 않는다. ES1에서 기존 tick size/quote clock·연속성·실제 ack/cancel latency·기존 replay stress 계약을 근거로 model version별 허용 범위를 고정한다. 범위가 정해지지 않으면 `tolerance_contract_missing`이며 통과하지 않는다. 모든 시장에 임의의 공통1tick/1초/허위체결1% 등을 새 기준으로 박지 않는다.

고정 계약에는 적어도 price/qty/time/false-fill의 허용 범위, 비용 오차의 순익 환산 방법, 지원 market/order type/scope, rolling/holdout 창, sample/coverage owner가 포함돼야 한다. 기존 real outcome20·four-arm complete30/coverage80% 등 소유 기준은 유지한다. 모델 validation의 지원 판단과 경제성 promotion floor를 하나의 sample 숫자로 합치지 않는다. 거래마다 반복된 tick/child/retry를 표본 수로 늘리지 않는다.

**후보 채택 시 비용 오차까지 우위를 잠식하지 않는지 검사한다.** 고정 holdout의 낙관적 체결·순익 잔차와 기존 stress 범위로 paired ΔEV의 보수적 범위를 산출하고 그 하한이 양수인지를 확인한다. Candidate에 actual counterpart가 없으므로 incumbent 오차를 candidate 오차의 완전한 증명으로 쓰지 않는다. 새 leg/주문유형/잔량 영역이 model 지원 범위 밖이면 추가 uncertainty/source_gap으로 차단한다. 새 대규모 Monte Carlo/queue 학습을 기본 요구로 만들지 않는다.

### 4.3 무엇을 언제 판정하는가

| 단계 | 판정 가능 조건 | 지금의 결론 |
| --- | --- | --- |
| 원천 attainability | 작은 manifest/projection·order ledger로 identity/plan/결과 결속 확인 | 즉시 조사 가능; invalid3 이유 및 replay census0 첫 경계 확인이 우선 |
| 단일 주문 실행 오차 | submit/취소/late-fill reconciliation 후 terminal 확정 | 연결되는 기존 주문이 있으면 현재 자료로 가능; 날짜가 지난 것만으로 준비되지 않음 |
| 청산/손익 오차 | 실제 completed exit·유효 비용 확보 | holding/cost pending은 별도 대기; 결손 과거를0으로 대체하지 않음 |
| scope 모델 적합성 | calibration에서 모델 고정 후 독립 미래/미사용 날짜 검증 | 9/17 현재 결과로는 미입증; 지원 scope별 판정 |
| 후보 경제성 | 모델 gate+paired sample+독립 candidate holdout 통과 | 첫 단계 통과와 별개 |

고정된 모델의 holdout을 재보정에 사용하면 그 날짜는 calibration으로 이동시키고 다음 미사용 날짜를 기다린다. 모델 정확도 검증에서 사용한 미래 경로가 후보 선정에 노출됐다면 candidate 경제성의 fresh holdout으로 중복 주장하지 않는다. 필요한 창은 기존 chronological split 하나의 소유 계약으로 관리하며 새 중복 스케줄을 만들지 않는다. 재현 가능 기존자료 수를 ES0에서 산출하기 전 확정 완료일을 약속하지 않는다. 휴장/미적재는 비대상이고 ETA=null이다.

## 5. 후보 튜닝: quantity fixed, leg만 먼저 개선

### 5.1 비교 arm과 모델 수정 범위

첫 후보 비교는 같은 frozen total quantity·entry signal·기준 price receipt·exit/cost/terminal·budget 조건에서 incumbent leg vs candidate leg다. 현재 owner가 발급하는 메뉴·grid를 사용하고 조합을 무작정 늘리지 않는다. 후보가 분할되어도 총수량은 증가하지 않으며 작은 수량의 leg clipping과 실제 적용된 weight를 identity에 포함한다. 요청량≤1·multi-order 미지원·stale/DANGER는 기존 동작/guard를 유지한다.

기존 four-arm은 유지한다. 첫 탐색의 candidate quantity는 incumbent와 동일함을 명시하되 price/quantity owner의 기존 비교를 삭제하지 않는다. U9–U10 합동 후보는 기존 4군에서 quantity 효과·leg 효과·combined 효과를 별도 산출하고 단일 atomic policy로 검증한다. Leg-only 검증 결과가 별도 quantity 후보의 자동 승인 근거가 되지 않는다.

기존180초·고정±0.5% 연구 결과는 supporting research로 보존한다. 운영 성과 재현에는 당시 exit owner 계약/입력 경로를 기존 replay helper로 재사용하고 모델 terminal·비용 provenance를 별도 명시한다. 정확히 재현할 수 없는 AI/비결정적 청산·미확보 미래 feature/custody 전환은 지원 불가로 남긴다. CF fill 시점/보유량이 달라졌는데 실제 매도 체결을 무조건 붙이지 않는다. 공통 timestamp liquidate 평가가 필요한 경우 supporting comparison이며 실제 청산 재현으로 부르지 않는다. Holding/exit live 정책은 변경하지 않는다.

Passive 체결은 trade-through·queue/잔량·latency·partial/late-fill·취소 체계를 기존 conservative helper에서 확인한다. 시장가/지정가·venue/session semantics를 섞거나 touch=fill을 사용하지 않는다. Source-quality exclusion을 양측 같은 원천에 적용하고 exclusion/census를 남긴다. missing execution/cost/capital을 supported no-fill의0값으로 대체하지 않는다.

### 5.2 경제성 지표·선정

주문별 `paired_net_pnl_delta = candidate modeled net − incumbent modeled net`를 계산한다. 같은 frozen budget 기준의 portfolio return Δ, attempt 기준 평균 순익, 체결 참여율, positive terminal 빈도, p10/ES/worst tail, reserve+holding capital time·효율, 모델 오차/stress를 함께 산출한다. 체결된 후보만의 평균 profit_rate는 보조 진단이다. 매입가 개선과 actual completed PnL도 별도 표시한다.

실제로 supported no-fill/no-exposure가 확인된 시나리오만 해당 attempt modeled PnL0을 허용한다. Return 분모/actual PnL이 미확보인 경우 null이다. 후보 미체결 손실은 같은 attempt의 incumbent profit과 paired 비교에 나타나며, missed-entry 보고서와 순익을 중복 합산하지 않는다.

승격은 existing exact shared contract·four-arm complete30/coverage80%·chronological source-date/holdout·candidate cost-adjusted EV≥0.10%·fill participation 감소≤5%와 기존 non-degradation/cost/terminal gates를 유지한다. 기존 허들은 이 계획에서 임의 완화하지 않는다. 새로 산출한 모델 오차를 반영한 보수적 paired 우위와 scope 검증도 필요하다. 이 문서에서 universal ΔEV1%/1.5% 등 추가 허들을 만들지 않는다.

정확 child3건 양수는 후보 발굴/관찰값으로 보존하되 **challenger 자동 활성화의 model/paired/holdout 대체 경로는 막는다.** 기존 사용자 승인된 behavior-equivalent baseline/operator override는 challenger와 분리해 expiry/custody를 보존한다. 자료 부족으로 승인된 baseline을 임의 OFF/ON하지 않는다. 무효 source·음수 edge·catastrophic safety rollback은 서로 다른 disposition으로 전달한다.

## 6. 필요한 경우만 계산하는 장후 경계

기존 entry split producer 내부에 actual census→원천/terminal 준비→모델 검증→새 후보 evaluation의 cheap precheck를 둔다. 새 독립 wrapper stage는 추가하지 않는다.

- fingerprint 입력: parent/attempt·주문 lifecycle/fill/terminal revision, frozen plan/정책/모델/exit/cost/budget hash, 시장 partition/source audit generation, tolerance/holdout identity와 clean baseline. Raw file 경로/mtime만으로 경제성 revision을 판정하지 않는다.
- 준비 원천/새 terminal/모델·비용 계약 revision이 없으면 이전 동일 SHA 결과 재사용. `no_new_ready_source`는 fresh evaluation 완료나 valid no-edge가 아니다.
- terminal/실제 비용 revision이 늦게 들어오면 해당 parent와 영향받는 aggregates만 갱신. 손상·충돌 source는 격리하고 양측 동일 revision을 사용한다. immutable holdout 사용 이력은 바꾸지 않는다.
- 새 지원 scope 또는 모델 revision은 해당 검증을 다시 열고 과거 PASS를 새 버전에 승계하지 않는다. 실행 중/미완료 source는 immutable 읽기 경계/lock·manifest로 보호한다.
- source manifest/projection·기존 compact state/cache를 먼저 사용. 64MiB 초과/growing JSONL은stat 후 summary/manifest/bounded streaming만 허용. 장후 매번 전체 clean baseline raw를 다시 읽지 않는다. Full population을 임의로 축소해 빨라졌다고 주장하지 않는다.
- model/ready preflight 실패면 expensive grid를 건너뛰고 owner·첫 blocker·closure test·ETA=null을 기존 section에 남긴다. 분석 실패/예외를 hold_no_edge나 PASS로 삼키지 않는다.

## 7. 정책·PREOPEN·장중·실제 성과 인계

경로는 기존 entry split/economic section→Daily/calibration→단일 execution sizing/기존 split policy→PREOPEN→dated loader→`apply_entry_split_order_policy`→atomic binder→leg별 safety/submit→actual receipt/fill/exit다. 호환 legacy field와 current contract는 기존 caller 때문에 필요한 범위만 유지한다. 두 publisher/같은 stage 독립 정책 승격을 만들지 않는다.

검증되지 않은 모델/unsupported scope/미확보 holdout은 runtime_apply_allowed=false와 구체 reason으로 전달한다. Source gap이면 missing metrics null, valid no-edge면 실제 paired 결과와 hold 사유를 남긴다. 날짜별 policy/evaluation/model/tolerance/holdout SHA와 market/session/order scope를 묶어 구 report/legacy positive child를 현행 ready로 읽지 못하게 한다. 지원 검증 정보는 existing policy schema validation의 의미 변화로 처리하고 producer/consumer/fixtures를 같이 갱신한다.

정책 없거나 부적격일 때 기존 원래 주문 계획을 유지한다. 그 뒤 atomic binder가 invalid면 현행 fail-closed submit block을 유지한다. 원자 계약 결손을 해결하려고 guard를 우회하거나 stale action snapshot을 신뢰하지 않는다. 초기 원천 수리·진단 통과는 live 활성화 승인이 아니다.

자연 소비는 report 생성/선택 release·PREOPEN artifact/actual PID consumption/정책 적용/실제 주문/완료 손익을 각각 receipt로 남긴다. 실제 적용 version별 parent/episode·fill ID 중복을 제거하고 full/partial·venue/session·custody별 rolling/cumulative net/EV/tail/exposure/model error를 기존 post-apply section에서 산출한다. Actual counterfactual가 없으므로 실제 candidate PnL 전체를 causal uplift로 표현하지 않는다. Model ΔEV·실제 손익·실제 모델 잔차·새 정책 적용 여부를 분리한다. 비용 미확정이면 actual net null이며 비교 비용 모델은 명시적으로 별도다.

## 8. 구현 package·파일·완료 기준

| package | 기존 파일 중심의 작업 | 검증·closure |
| --- | --- | --- |
| ES0 source inventory | entry split/atomic plan·sniper field emitter·native decoder·기존 ledger/projection 조사; invalid3의 최초 사유 및3 vs replay0 분모 확인 | parent별 재현 가능/원천 결손/terminal 대기 목록·원본 provenance·보존식. Raw 전체 재스캔 없이 known/unknown 명시 |
| ES1 validation contract | `scalping/entry_split_order_plan.py`, `strategy_owner_replay.py`, 기존 execution math에 model validation section·tolerance/version/scope 결속 | 기존 실제 주문 fixture의 fill/qty/VWAP/time/cancel 비교; unsupported/비용 미확보는 실패/null. 모델 gate와 경제성 gate 분리 |
| ES2 source repairs | `scalping/entry_execution_sizing_plan.py`, `sniper_state_handlers.py`, native decoder의 확인된 누락만 수리 | 진짜 producer→compact representation→decoder→signed receipt 회귀; private cache 주입/guard bypass 없이 natural attainability |
| ES3 replay calibration | 기존 replay helper에서 incumbent actual 대비 오차 검증; exact exit/cost/budget 지원 여부 명시 | 허위체결·partial/no-fill·cancel late-fill·clock·scope/stress; actual PnL로 후보를 선택한 뒤 모델 재보정하는 leakage 차단 |
| ES4 paired leg selection | 기존 entry split grid·four-arm helper·quantity fixed 첫 비교, original eligible population 유지 | paired Δnet/자본/tail/fill·모델 오차·독립 holdout; child3/sim/failed source 우회 승격 거부 |
| ES5 incremental evaluation | 기존 entry split input/cache/state/producer cheap readiness·fingerprint 재사용 | 동일 revision 계산 재사용, late terminal/cost revision만 재평가, conflicting source quarantine, stale PASS 재유입 거부 |
| ES6 consumer closure | Daily·PREOPEN·dated loader·strict/summary 및 기존 runtime receipt에 model/scope/hash 계약 연결 | publication/source/effective date·schema/hash·inactive fallback·unsupported positive policy 거부·단일 stage authority·quantity guard 보존 |
| ES7 natural acceptance | 기존 post-apply section/DB fact/receipts에 실제 version별 성과 연결; 승인된 제한 regeneration | 실제 PID/자연 적용/COMPLETED 비용/중복 제거·rolling/cumulative·model vs actual 분리; 증거 없는 경제성 완료 거부 |

Source/tests는 기존 role package/파일을 확장한다. `src/engine` root에 새 module을 만들지 않는다. Production module/test/CLI 추가가 불가피하면 location gate·caller/ownership 이유부터 제시한다. 기본 산출물은 기존 report section/정책/receipt이고 새 독립 과거 report series는 생성하지 않는다.

## 9. 비례 검증·정리·운영 전환

필요한 기존 tests: `test_entry_split_order_plan.py`, `test_entry_execution_sizing_plan.py`, `test_strategy_owner_replay.py`, `test_split_execution_math.py`, 변경된 Daily/PREOPEN/wrapper/strict 계약 tests. 회귀 fixture는 full/partial/no-fill/cancel-replace/late-fill/duplicate/conflicting identity·없는 seed·stale quote/venue mismatch·future data·비용 누락·동일 fingerprint/late revision·child clipping·quantity conservation·모델 PASS와 경제성 FAIL을 검증한다. 구현을 그대로 복사한 tests/전체 provider·trading suites 반복/큰 synthetic performance sweep은 하지 않는다.

각 package는 implementation→self review→fix→re-review→targeted pytest/compile/diff를 완료한다. Wrapper 변경 시bash-n/영향 계약 tests와 운영 문서·checklist를 함께 갱신한다. 문서만 변경할 때는 link/owner/authority와 print-only parser만 실행한다. 후속 사용자 승인 범위에서만 commit/push·immutable successor release·bounded result regeneration을 수행한다. 진행 중 bot/worker source를 편집하지 않는다.

불필요한 과거 outputs는 source-consumer/reference/active FD/lock·policy/current/rollback/holdout 증거를 확인하고 compact 원분모·비용·결과·hash/provenance와 deletion manifest를 보존한 뒤 정리한다. 현행 cumulative input·generation policies·실제 주문/손익 원장·PREOPEN·model holdout은 삭제하지 않는다. 정리 자체를 신규 EV 개선으로 계산하지 않는다.

## 10. 유지·중단 판단과 최종 완료

| 결과 상태 | 다음 동작 |
| --- | --- |
| source_gap/unsupported_model | 원천/contract owner closure만 진행; unchanged grid 재계산하지 않음; 기존 실행/override guards 보존 |
| terminal_pending | native 종료/비용 revision 때 재개; 단순 나이로 완료 처리하지 않음 |
| model_validation_failed | 원인별 기존 helper 보완 또는 unsupported scope로 제한; candidate auto-promotion 차단 |
| validated model, insufficient independent sample | 유효 원천 자연 누적; 종료일 추측 없음 |
| valid holdout no-edge | 기존 주문 유지·새 source revision 시 제한 탐색; 기준을 낮춰 positive 만들지 않음 |
| positive robust paired candidate | 기존 bounded policy/단일 stage mapping으로 PREOPEN 인계; 실제 PID/완료 성과는 별도 OPEN |
| post-apply negative economics/model drift | 해당 owner의 기존 freeze/disable/rollback disposition; ordinary no-edge와 hard safety 구분 |

계획의 구현 완료는 ES0–ES6 계약/회귀/소비 증거로 판정한다. ES7 자연 수집·PID 소비·실제 비용 손익까지 확인된 범위만 성과 완료다. 모델이 지원하지 않는 청산/자금/미제출 영역은 미완료 범위를 명시하고 전체 전수 최적화 완료로 발표하지 않는다.9/21까지 positive 정책이 생겨야 한다는 이유로 source/model/holdout gates를 우회하지 않는다. 적격 후보0이면 기존 주문 보존 또는 이미 승인된 OFF/override disposition을 정확히 준비하는 것도 정상 결과다.


## 11. 구현 및 잔여 계약

[경제성 완결 리뷰](../audit-reports/2026-09-18-entry-split-economic-completion-review.md)와 `tmp/entry-split-economic-completion-20260918/`가 ES0–ES6 실행 계약/회귀/배포/제한 재생성 증거를 소유한다. 운영 청산 interpreter·당시 비용 provenance·reserve/holding capital·모델 calibration 및 chronological holdout·동일 qty/budget paired 경제성·stress/error 하한·독립 candidate holdout·Daily/PREOPEN/장중 소비를 구현했다. 지원 입력은 활성 정책까지 계산하며 source gap/unsupported/pending/insufficient/valid-no-edge는 별도 null/blocker/owner/closure로 반환한다.

지원 범위는 정확 frozen Main initial full fill 및 독립 full SELL 경로다. partial/no-fill CF cancel/late fill·후속 ADD/partial SELL·누락 AI/시장 입력은 재현 근거 부족으로 unsupported이며 지원 전체를 차단하지 않는다. ES7 실제 버전별 평가 경로는 구현했지만 미래 자연 PREOPEN/PID/적용/완료 비용 성과는 OPEN이다. 기존 invalid3 상세/전체 historical Main census는 미확정이다. 자연 후보0일 때 prepared9/21 inactive keep-original도 정상 정책 준비이며 합성 활성 회귀를 자연 성과로 주장하지 않는다.
