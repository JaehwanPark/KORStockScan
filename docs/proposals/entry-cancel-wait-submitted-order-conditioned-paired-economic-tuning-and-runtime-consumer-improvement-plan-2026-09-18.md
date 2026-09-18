# Entry cancel-wait: 실제 제출 주문 조건부 경제성 탐색·런타임 소비 최종 구현계획

2026-09-18 KST. 대상은 `src.engine.automation.entry_cancel_wait_tuning`과 독립 `entry_cancel_wait_runtime` family다. **실제 BUY 제출 실적이 있을 때만 평가하며, 체결 성공 건만으로 모집단을 제한하지 않는다.** 미체결·부분체결·취소·지연 체결을 포함해 대기시간 변경의 비용 후 EV와 동일 자본 일별 순익을 비교한다. 이 문서는 계획이며 구현·재실행·정책 적용·배포를 실행하지 않는다. 아래 단계는 향후 구현 범위이지 새 일정/OPEN owner 또는 주문 권한이 아니다.

## 1. 목표와 현재 진단

우선순위는 제출 원천·실행 모델의 구조 결손 해결 → 유효한 paired 경제성 값 → 후행 정책 소비 → 불필요 실행시간 축소다. 양수 결과를 보장하거나 기존 차단/floor를 완화하는 계획이 아니다. 현재 미평가를 EV0/no-edge로 표현하지 않고, 독립 후보에서 음수·무효·개선 없음도 정상 결과로 종결한다.

현재 근거는 [최종 리뷰 및 cancel-wait 분석](../audit-reports/2026-09-18-daily-final-review-and-entry-cancel-wait-analysis.md)이다. 코드 확인 기준은 선택 release `daily-proof-summary-reviewed-20260918`, commit `a97b4f538ba6b670cf9a41c17ab5e5585370e9fc`이며 실제 PID 소비를 의미하지 않는다.

| 확인된 현황 | 개선에 필요한 변화 |
| --- | --- |
| Native wrapper에서 Daily/AI correction 이후 cancel-wait CLI 실행, inventory #55 | 기존 호출 위치/CLI/독립 family 유지. 선행 원천 준비 여부와 후행 PREOPEN handoff를 명시 |
| 9/17 결과: 약155.25초, exit0, 등록/완료 후보0, `no_observation_hold`, 경제성 입력false | 종료 성공과 경제성 미평가 분리. 등록0을 실제 BUY 제출0으로 간주하지 않음 |
| standard90/breakout120/pullback600/reserve1200초 보존 | incumbent의 실제 유효 정책/override/manifest에서 비교 기준 확정. default standard60과의 차이는 자체 오류가 아님 |
| 현 proxy는 timeout 이후 첫 가격의 touch와 60초 gross mark | 실제 제출→체결/취소 race→재고→운영 청산→full-cost/자본 계약으로 대체. proxy는 진단 전용 |
| 9/17 이후 date guard로 경제성 입력 차단 | 실행 증거 버전·검증 계약을 구현한 새 경로만 허용. 날짜 조건 삭제나 flag true만으로 개방하지 않음 |
| 등록은 취소된 일부 주문, 부분체결 residual 등 제외 | 실제 제출 parent union과 전체 disposition의 완전성 확인 |
| 원 pipeline JSONL 약5.32GiB를 날짜별 순회 | 완전성이 검증된 기존 주문 projection/catalog로 조건 판단. 현재 summary의 등록0은 제출 census가 아님 |
| 재사용 entry 운영 replay는 partial/no-fill의 cancel ACK·late-fill 재고 미입증 | 공통 freeze/cost/검증 도구를 재사용하되 기존 실행 owner의 해당 상태만 최소 보완 |
| PREOPEN은 독립 보고서를 읽으나 현재는 incumbent carry | 모델/holdout/경제성 proof 검증→적용 범위→실제 runtime receipt까지 연결 |

## 2. 평가 조건과 상태 종결

평가 모집단은 clean baseline `2026-06-05T00:00:00+09:00` 이후 main-only/normal-only/post-fallback의 **실제 BUY 제출 시도**다. 성공 ACK/체결 건만 필터링하지 않는다. 실제 제출 후 거절·응답 불명확 건도 census에 포함하고, 경제성 비교 가능 여부를 별도 판정한다. 주문을 제출하지 않은 BLOCK/RECHECK/AI VETO·미진입 opportunity는 이 family의 분모에 넣지 않는다. main/widget/episode/manual, real/sim/probe/CF, venue/session/route는 혼합하지 않는다.

| Admission 조건 | 처리와 다음 조치 |
| --- | --- |
| 완전한 주문 census·재고 조회 증거로 대상 제출0 확인 | `skip_no_submitted_orders`; 후보 replay 생략, incumbent 보존. 무노출/미해결 주문 없음도 확인해야 실제 일별 순익0 사용 가능 |
| census 누락·불완전·generation 충돌 | `source_gap`; 제출0/무거래0로 바꾸지 않음. 기존 주문 원천 owner에서 coverage 수리 |
| 실제 제출 있음, quote/ACK/비용/실행 모델 결손 | `diagnostic_only` 또는 `unsupported_scope`; 필요한 lineage만 진단, 경제성 grid 생략 |
| lineage 유효, 체결/청산/비용 미성숙 | `waiting_outcome`; 성숙 조건과 재평가 fingerprint 명시. 준비된 다른 cohort까지 일괄 차단하지 않음 |
| 성숙한 공통 비교 모집단·검증 모델·독립 holdout 확보 | 후보 동결 후 경제성 평가 |
| 동일 입력/model/policy/cost fingerprint | 기존 결과를 원래 as-of로 재사용. 날짜를 바꿔 새 증거처럼 표시하지 않음 |

시간 경과로 해결 가능한 것은 정상 수집된 주문의 ACK/청산/비용 성숙과 이후 실제 제출 표본의 증가다. 과거 quote/lineage 소실, partial/no-fill 모델 미지원, 소비 계약 누락은 시간이 해결하지 못한다. 구조 차단 ETA는 null로 둔다. 일부 unsupported를 제외할 때 원본/제외 manifest와 coverage를 보존하며, 후보마다 유리한 성공 체결만 남기는 필터를 금지한다.

## 3. 실제 원천과 frozen context

기존 main 주문·lifecycle journal과 entry 실행 projection을 우선 재사용한다. `entry_split_order_plan`의 census가 특정 compact lineage만 검증한 경우 전체 Main 제출 census로 확대 해석하지 않는다. 원본→projection 간 제출/ACK/fill/cancel count, parent/child key, source SHA·generation·시간 coverage가 맞아야 admission에 사용한다.

제출 직전 frozen context에 parent/child/retry 식별자, 종목/owner/profile, 거래일·venue/session/route, 제출 가격·수량·예산·reserve, 유효 timeout과 policy version, 당시 호가/quote clock·거래 clock, guard 결과 및 운영 exit/cost/model identity를 결속한다. profile 판정은 당시 상태에서 고정하고 사후 가격이나 최종 손익으로 재분류하지 않는다.

제출/ACK/거절/취소 요청·ACK/누적 및 개별 체결/잔량/late fill/재고 귀속/최종 청산/비용을 동일 parent로 연결한다. retry·부분체결 누적 이벤트를 중복 합산하지 않는다. 취소 요청은 취소 확정이 아니며, cancelled 응답과 filled 응답의 race를 재고 증거로 판별한다. 프로세스 mutable stock state 제거나 후속 가격 update 부재 때문에 원천이 유실되지 않도록 기존 durable journal에서 terminal disposition을 소비한다.

거래일 경계·세션 종료·시장/guard 중단에도 pending을 임의 no-fill0으로 종결하지 않는다. verified no-fill은 cancel ACK와 잔여 late-fill 구간/재고가 해결된 상태다. 미해결 custody/부분 청산·HELD는 검열 상태이고 경제성 값은 null이다. 프로토콜/API를 수정해야 하는 구현은 그때 공식 Kiwoom reference gate를 통과하며 이 계획은 호출 방식이나 주문 안전장치를 변경하지 않는다.

## 4. 기존 entry 실행 모델 재사용과 최소 보완

[Entry submitted-order replay 계획](entry-split-order-plan-submitted-order-replay-and-economic-tuning-improvement-plan-2026-09-18.md)의 실제 제출 검증·공통 자본·모델 identity 원칙을 재사용한다. 코드 owner는 기존 `src/engine/scalping/strategy_owner_replay.py`의 `freeze_entry_operating_context`, `entry_operating_model_identity`, `replay_operating_entry_arm`이다. 별도 replay engine/queue 학습/Monte Carlo/신규 DB를 만들지 않는다.

**현재 운영 arm의 partial/no-fill은 `unsupported_scope`이며 재사용만으로 cancel-wait 비교가 완성되지 않는다.** research arm의 `supported_no_fill`, 고정 연구 비용/180초 exit 또는 touch/60초 mark를 운영 계약으로 가져오지 않는다. 기존 owner에서 다음 상태를 검증 가능한 범위만 확장한다.

1. 같은 실제 parent의 가격·수량·예산·entry/exit guard를 고정하고 timeout만 바꾼다. 변경 timeout까지의 체결 가능한 수량/가격, 취소 요청→ACK 지연, fill/cancel 순서와 late-fill 재고를 재현한다.
2. 먼저 체결된 수량은 취소되지 않는다. residual 취소·부분 inventory의 exit/stop·reserve 해제를 별도로 재현한다. 더 긴 대기가 세션/guard 종료를 넘을 때 해당 운영 계약을 우선한다.
3. 후보가 새로 체결하거나 수량/시점이 달라지면 해당 arm의 운영 holding/exit/cost 증거를 산출한다. incumbent의 실제 exit/PnL을 그대로 복사하지 않는다. 동일 노출·동일 exit 계약이 입증된 부분만 실제 증거를 공유한다.
4. 실측 full/partial/no-fill/cancel/late-fill 사례로 체결률·수량·가격·cancel ACK clock·재고·비용 오차를 모델 버전별 검증한다. 실제 full-fill에서만 맞는 모델로 pending/cancel 상태를 승격하지 않는다.

모델 허용 오차/지원 route·profile·상태는 후보 순위 전에 동결한다. 실제 tick/quote/clock/cancel/cost 품질에 근거하고 사후 양수 결과에 맞춰 변경하지 않는다. 기존 entry owner의 검증 gate를 같은 상태/route에 한해 재사용하고, 새 cancel 상태는 별도 실측 검증 항목으로 추가한다. 모델 검증용 시간 holdout과 정책 선정용 미사용 holdout을 분리한다. 지원되지 않는 시장/상태는 null/제외 사유로 남기고 지원된 cohort만 독립 평가한다.

## 5. 후보 탐색과 비용 후 paired 경제성

profile별 기존 제한 메뉴와 step cap을 유지한다. standard/breakout 현재±30초, pullback/reserve 현재 기준 기존 제한 범위,5~1200초다. runtime 메뉴와 tuner step 규칙의 차이를 숨기지 않고 **실제 적용할 최종 bounded 값**을 먼저 freeze하여 비교한다. 최상위 후보를 나중에 clamp한 미평가 값에 그 후보의 EV를 붙이지 않는다. 첫 구현은 profile 한 축만 변경하고 주문 가격/수량/분할/exit/AI threshold/cap은 고정한다.

Incumbent는 control로 항상 포함한다. 값/행동이 같은 후보는 `baseline_preserved`/`no_policy_difference`로 분리하고 개선 검증 건수에서 제외한다. training에서 후보를 선택·동결한 뒤 독립 미사용 시간 holdout에서 그 후보와 incumbent만 비교한다. holdout을 보고 다른 후보를 선택하거나 동일 날짜를 반복 검증하여 성공만 남기지 않는다. 후보/모델/holdout 사용 identity를 보존한다.

### 5.1 학습 후보 선정 함수 — 최종 확정

구조/모델 검증을 통과한 동일 scope·profile의 후보를 아래 순서로 선정한다. source/model/cost/coverage·표본·tail·capital gate와 오차 산정 규칙은 training 순위를 보기 전에 동결한다. runtime 성능·승률·체결률·gross mark는 후보 순위 점수가 아니다.

1. **공통 비교 기준:** 각 parent의 제출 직전 가격×요청 수량을 고정 notional `N_i`로 사용한다. arm별 비용 후 최종 현금 손익을 `P_i(a)`라 할 때 `notional_weighted_ev_pct(a) = 100 × ΣP_i(a) / ΣN_i`다. 후보와 incumbent에 동일 parent·notional 분모를 적용하며 실제 체결 notional로 분모를 바꾸지 않는다. ΔEV는 두 arm EV의 차이(%p)다. 정의된 거래 비용만 차감하고 reserve 효과는 별도 portfolio 결과에 반영한다.
2. **일별 목적함수:** 같은 시작 자본/동시 reserve 조건의 `day_delta_d(a) = day_net_d(a) − day_net_d(incumbent)`를 계산한다. 사전 고정한 공통 검증 거래일의 평균 `mean_day_delta_krw`를 사용한다. 제출 날짜만 평균내거나 일별 값을 단순 합산해 EV라고 부르지 않는다.
3. **동시 개선 후보만 선정 대상:** ΔEV>0과 평균 일별 순익 차이>0을 모두 만족하고, 검증 모델/비용 오차를 전파한 두 값의 보수적 하한도>0인 후보만 shortlist에 넣는다. 불확실성은 검증에서 동결한 오차 계약으로 산정하며 사후 임의 할인율·새 통계 gate를 추가하지 않는다. 오차를 산정할 수 없으면 `model_unvalidated`다.
4. **순위:** shortlist에서 평균 일별 순익 개선의 보수적 하한(원/일)이 큰 후보 → ΔEV 보수적 하한(%p)이 큰 후보 → incumbent 대비 절대 timeout 변경량이 작은 후보 → 고정 candidate ID 오름차순으로 하나를 선택한다. 숫자 정밀도/동률 tolerance도 사전에 동결한다. 단위가 다른 값을 임의 가중 합산하지 않는다.
5. **개선 후보 없음:** 유효한 독립 비교를 완료했지만 shortlist가 비면 `no_edge`+incumbent 보존이다. 값/행동이 같으면 `no_policy_difference`, 원천/모델/표본 결손이면 해당 hold 상태로 종결하며 `no_edge`라고 표시하지 않는다. 서로 충돌하는 ΔEV/일별 순익, 음수 결과와 탈락 사유도 그대로 보고한다.
6. **holdout 사용:** 선정된 최종 bounded 값·scope·선정 함수 버전을 freeze한 뒤 정책 holdout을 한 번 평가한다. holdout에서도 기존 §5의 동시 개선·오차·위험/자본 gate를 만족해야 승격한다. 실패하면 incumbent을 보존하며 같은 holdout으로 차순위 후보를 다시 선택하지 않는다. 다음 연구는 새로운 미사용 holdout이 있을 때만 가능하다.

이 함수는 CW3의 필수 구현사항이다. training에서 단순 gross EV 상위1개를 선택하고 나중에 일별 순익을 참고하는 방식을 남기지 않는다. 선정과 검증 결과를 분리해 `training_selected`를 신규 적용 가능 상태로 취급하지 않는다.

### 5.2 비교 coverage와 경제성 검증

비교 지원 여부는 수익 순위 전에 같은 frozen 메뉴의 모든 arm에 적용한다. 한 arm이라도 cancel/exit/cost를 입증하지 못한 parent는 전체 paired 비교에서 제외하고 전체 제출 census에는 남긴다. 제외가 실제 no-fill/부분체결에 집중되면 full-fill subset 결과를 전체 timeout 정책의 개선으로 승격하지 않는다. 상태별 coverage와 해당 범위의 적용 가능성을 model owner의 사전 계약으로 확인하며, 부족하면 `unsupported_scope`/미평가로 종결한다. 동일 parent의 중복 child, 같은 episode의 train/holdout 분할, 반복 검증 회차를 독립 표본으로 세지 않는다.

| 경제성 항목 | 산출 규칙 |
| --- | --- |
| paired EV | §5.1의 동일 지원 parent union·고정 제출 notional로 `notional_weighted_ev_pct` 비교. 분모/단위/coverage를 명시하고 체결 건 평균만 쓰지 않음 |
| ΔEV | 후보−incumbent. 검증된 no-fill arm의 거래 손익0은 가능하나 취소/거래 비용과 reserve 상태를 함께 반영. 누락/미청산 arm은0이 아님 |
| 일별 순익 | 같은 시작 자본·동시 주문·reserve/재고 제약으로 시간순 portfolio replay. 날짜별 후보/기존 원화 net·delta·평균/누계/최악 일자·검증 무거래일을 함께 표시 |
| 비용 | 수수료/세금/체결 가격의 slippage 등 owner 비용 계약. 모델 비용·실측 비용을 구분하고 slippage 이중 차감 금지. 비용 미확정은 null |
| 위험/자본 | tail/worst loss, inventory 미해결, stress cost, 체결 참여·reserve 시간·peak 사용 자본을 별도 비교 |
| 실적 | 실제 PnL은 COMPLETED+유효 profit/cost만. CF paired 결과와 실제 계좌 실적을 합산하지 않음 |

빠른 취소로 해제된 자본을 관측되지 않은 새 주문에 재투자했다고 가정하지 않는다. 같은 실제 제출 union 안의 자본 충돌은 지원되는 portfolio 계약으로 평가하되, 제출하지 않은 기회의 수익은 이 모델의 결과가 아니다. 미지원 재진입/기회비용은 unknown으로 명시한다.

승격은 독립 holdout에서 ΔEV와 같은 자본 일별 net delta가 모두 양수이고, 사전 동결된 모델/비용 오차를 반영한 보수적 하한과 tail·capital·source gate를 통과할 때만 가능하다. 모든 거래/매일 양수를 요구하지 않는다. 기존 `SAMPLE_FLOOR=5`는 진단 기준이며 경제성 승격 증명으로 사용하지 않는다. 표본 gate는 해당 상태/route 검증 오차와 독립 날짜 coverage에 따라 선정 전에 owner 계약으로 확정하고 다른 family의 숫자를 기계적으로 복사하지 않는다.

주문별 평가와 일별 portfolio의 공통 검증 날짜를 각각 기록한다. 조건부 EV의 분모는 실제 제출 parent이고, 일별 순익의 분모는 사전 고정된 검증 거래일 전체다. 완전한 source로 확인한 무제출·무노출 날짜도 일별0으로 포함하여 제출한 날짜/수익 난 날짜만 평균내지 않는다. 날짜별 delta에서 이전 custody나 다른 owner 손익을 후보 효과로 귀속하지 않는다.

## 6. 보고서·증거·carry 계약

기존 JSON/Markdown 경로와 CLI를 유지하고 executable evidence schema를 versioning한다. 보고서에는 source/effective date, generation/as-of, 제출 census와 coverage/exclusions, 실제 effective incumbent/override provenance, 후보 최종 값·scope·identity, model/cost/holdout versions, 공통 parent/date 수, arm별 EV·ΔEV·day net·tail/capital, 검열/지원 실패, 변경 여부/승격 gate 및 proof 참조를 기록한다. `selection_rule_version`, 고정 notional/거래일 분모, 후보별 point estimate·보수적 하한·eligibility/탈락 사유·순위, 최종 tie-break와 training/holdout 각각의 결과를 함께 결속한다. 메트릭 계약은 `primary_ev`/독립 cancel-wait decision authority와 rolling training·독립 holdout window, sample/source gate 및 다른 family·실제 PnL 합산 금지를 선언한다.

상태는 `no_submitted_orders`, `source_gap`, `waiting_outcome`, `model_unvalidated`, `unsupported_scope`, `baseline_preserved`, `no_policy_difference`, `no_edge`, `economic_improvement_validated`를 구분한다. null·verified0·음수·자기 비교를 모두 구별한다. legacy proxy는 진단 필드에만 두며 current schema/경제성 입력으로 자동 변환하지 않는다. `source_quality_status=pass`, exit0, enabled 또는 allowed-runtime-apply는 승격 증거가 아니다.

새 정책이 없으면 실제 검증 가능한 이전 적용 manifest/명시 override를 carry하고 fallback provenance를 남긴다. 과거 JSON의 첫 양수 threshold를 곧바로 incumbent으로 사용하지 않는다. prebaseline·stale/conflict·다른 scope·미검증 추천은 신규 튜닝 근거에서 제외한다. 지속 ON과 명시 OFF lock/override expiry는 현재 owner 계약대로 유지하고, 신규 후보 freshness 만료를 기존 운영 lock의 임의 해제로 해석하지 않는다.

## 7. 후행 소비와 장중 적용 범위

| 연결 | 필요한 계약과 closure 증거 |
| --- | --- |
| 실제 주문 journal→compact projection/census | 원본 coverage·dedup·source generation 검증. 선행 fact-sync가 만드는 입력의 준비 시점 확인 |
| census/frozen context→실행 owner→cancel-wait tuner | 상태별 검증 모델, 동일 population/capital, 후보 freeze/독립 holdout·full-cost proof |
| tuner→standalone PREOPEN selector | exact source/effective date·schema·scope·incumbent/candidate identity·원 proof SHA 및 gate 재검증. self-hash/flag만 신뢰하지 않음 |
| PREOPEN→dated policy/env→timeout resolver | 실제 적용 값과 scope, provenance·rollback incumbent·expiry 결속 |
| resolver→실제 submit/cancel attribution | effective policy/hash/profile/scope/선택 timeout, 실제 취소 요청·ACK clock·fill/inventory receipt |
| 실제 결과→다음 postclose | 실제 COMPLETED+cost와 모델 오차/정책 실적 누적. CF 양수를 실제 개선으로 집계하지 않음 |

현재 selector의 네 timeout env scalar는 profile별 공통 설정이다. **KRX 특정 scope만 검증한 결과를 NXT/SOR 등 전체 호출 범위에 공통 적용하면 안 된다.** 우선 기존 `entry_cancel_wait_runtime.py` helper와 `_resolve_buy_order_timeout_sec`에서 이 family의 dated scope 정책을 읽고 지원 범위에만 override하며, 나머지는 기존 값/guard를 쓰는 최소 확장을 구현 대상으로 정한다. 신규 범용 registry/서비스나 다른 family stage 차용은 하지 않는다. 기존 `strategy_owner_components`가 cancel-wait scope consumer를 제공한다고 가정하지 않는다.

공통 env만 바꾸는 구현을 선택한다면 실제 영향을 받는 모든 활성 scope의 지원/비열화 검증이 필요하다. 그것이 불가능하면 공통 값은 보존한다. 독립 지원 scope의 개선 판단 자체를 미지원 scope 표본 부족으로 덮지 않고, 적용 범위를 분리한다. context/profile fallback, reserve/pullback 특수 경로와 timeout priority를 확인하여 scope override가 hard session·stale/conflict·broker/account/order/quantity/cooldown·operator veto를 우회하지 않게 한다.

Standalone PREOPEN의 기존 `entry_cancel_wait_operational` 권한을 유지한다. ADM/LDM/lifecycle bucket/일반 threshold EV/runtime bridge에 경제성 입력이나 주문 authority를 새로 공급하지 않는다. 요약에 진단을 싣더라도 다른 family의 추천/승격으로 재집계하지 않는다.

Source date는 자정 이후에도 보존하고 effective date는 거래일 calendar로 확정한다. 9/18 source라면 다음 정규 거래일9/21 적용 후보가 될 수 있지만, 평가/승격 통과·정상 PREOPEN·실제 consumer receipt 없이는 적용됐다고 보고하지 않는다. 정책 파일 생성, 선택 release, process-loaded hash/PID, 자연 취소 행동, 실제 비용 후 성과를 각각 분리한다.

Native wrapper는 기존 CLI와 산출물 wait를 유지하되 새로운 schema 상태의 terminal/handoff 계약을 연결한다. 기존 tower→checklist→strict `--require-summary-handoff`→finalization에서 **해당 family의 source generation과 최종 소비 결과**가 일치해야 한다. 전체 strict PASS를 standalone policy 적용 증거로 대체하지 않는다. 현재 checklist의 실행 owner를 구현 intake 때 확인·재사용하고 한 parsed owner에 acceptance를 연결한다. 이 계획 작성만으로 새 OPEN 작업/cron/early PREOPEN을 생성하지 않는다.

## 8. 실행시간 축소: 작은 조건 판단과 변경분 평가

입력 fingerprint는 제출 census/terminal generation, 지원 scope와 rolling window의 source-quality, 실제 incumbent/context, quote/cancel/exit/cost, model/code/schema·후보/holdout identity를 포함한다. 지연 청산/비용·취소 ACK가 도착하면 필요한 parent/cohort와 후행 proof만 무효화한다. 새 거래일이 rolling window·holdout eligibility에 영향을 주면 원 주문 수가 같아도 재검토한다.

완전한 census0이면 거대 raw 순회 없이 skip 보고서를 만든다. 기존 summary stage allowlist가 cancel-wait 제출을 포함하지 않으면 요약0으로 skip하지 않는다. 기존 durable 주문 projection을 보완하는 것을 우선하고 별도 중복 저장소/DB/worker pool/watchdog/performance guard는 추가하지 않는다. catalog 없는 과거 날짜는 source gap으로 남기며, 향후 별도 승인된 bounded bootstrap 외에 자동 전체 raw 재스캔을 반복하지 않는다.

새 성숙 parent가 없거나 모델이 미지원이면 저비용 진단/기존 proof 재사용으로 종결한다. 지원 scope 한 개·기존 작은 메뉴부터 평가하며 전체 날짜/전 family 재생성을 피한다. 실행시간 단축이 어려우면 탐색 profile/지원 범위와 분석 깊이를 줄이고 그 한계를 공개한다. 비용·exit·population·holdout의 유효성을 줄이지 않는다. 성능 목표 숫자를 새 승격 gate로 추가하지 않는다.

## 9. 구현 순서와 파일 소유권

| 순서 | 기존 owner 중심 구현 | 완료 조건 |
| --- | --- | --- |
| CW0 현행 계약 동결 | native wrapper, standalone PREOPEN, actual order journal/projection 및 유효 policy/PID 확인 | 대상 scope·population·baseline·consumer와 미지원 상태를 확정 |
| CW1 제출 census/context | 기존 main producer·entry projection 및 `sniper_state_handlers.py`의 최소 attribution 보완 | 실제 full/partial/no-fill/cancel/rejected/ambiguous union·durable terminal 연결, source0/missing 구분 |
| CW2 실행 모델 | `scalping/strategy_owner_replay.py` 및 기존 entry model 검증 helper | cancel ACK/late-fill 재고·부분 inventory/exit/cost 검증. 미지원 상태는 차단 유지 |
| CW3 경제성 탐색/보고서 | `automation/entry_cancel_wait_tuning.py`, `scalping/entry_cancel_wait_runtime.py` | §5.1 동시 개선 shortlist/원화 일별 개선 순위·tie-break·보존 판단 구현, 최종 bounded 후보·독립 holdout·선정 함수/proof 버전 산출 |
| CW4 소비/범위 적용 | `threshold_cycle_preopen_apply.py`, 기존 timeout resolver/runtime helper | scope/date/proof 엄격 검증, incumbent fallback, 실제 선택/사용 attribution |
| CW5 handoff/변경분 | 기존 wrapper/summary/strict 및 projection catalog | 원천 준비→최종 소비까지 끊김 없음,0/동일 입력 저비용 종결 |
| CW6 리뷰/검증/후행 | 기존 관련 테스트·운영 문서/단일 checklist owner | 수정→리뷰→보완→재리뷰→대상 검증. 이후 승인된 bounded 재생성/배포만 실행 |

새 engine-root Python module은 만들지 않는다. 꼭 필요한 source/test 추가는 repository location gate를 먼저 적용하고 기존 역할 package 안에 둔다. 코드·자동화가 실제로 바뀌는 구현 단계에서 owning 운영 문서/checklist를 함께 갱신한다. 이번 계획에서는 baseline 문서·다른 세션의 entry split/AI 검증·주문 프로토콜을 수정하지 않는다.

## 10. 회귀검증과 종결 기준

테스트는 기존 테스트 파일과 실제 producer→journal/projection→tuner→PREOPEN→resolver 흐름을 활용한다. private fixture에 보고서만 주입해 PASS시키는 검증에 그치지 않는다.

- Admission: 완전 census0에서는 raw scan/replay 없음; catalog missing/등록0/중복 retry는 실제 제출0으로 오인하지 않음. clean baseline·owner/real/route 분리.
- 모델: full/partial/no-fill/residual/late fill, cancel 요청 전후 race, quote clock gap·stock state 제거·세션 종료·HELD/비용 미확정. unsupported는 null이며 gross 연구 arm으로 승격되지 않음.
- 경제성: 자기 비교/행동 동일 제외, 적용할 clipped 후보 실제 평가, 동일 자본 동시 reserve, verified0/negative/null 구분, ΔEV 양수라도 일별 net 음수면 승격 안 함. training/model holdout/policy holdout 중복·재선택 금지.
- 선정 함수: EV가 더 높아도 일별 net이 음수인 후보 제외; 동시 개선 후보끼리는 일별 개선 보수적 하한 우선, 동률은 ΔEV 하한→변경량→ID 순. verified no-fill의 고정 요청 notional·무제출 날짜 분모·오차 미입증·shortlist0·holdout 실패 후 차순위 재선택 금지를 검증한다.
- 소비: legacy/date-guard 우회 flag·변조 self-hash·stale/wrong date/scope/model/cost/후보 proof 거부. 유효 지원 scope만 적용, 나머지 incumbent, 명시 OFF/override·hard guard 유지.
- 변경분/handoff: ACK/late cost/model/scope/window 변경 시 해당 proof 무효화; 동일 fingerprint as-of 보존; family report→summary/strict→dated policy의 같은 generation 확인.

문서 종결은 링크/owner/authority·diff·print-only parser 검증이다. 향후 코드 종결은 관련 pytest/compile 및 wrapper 변경 시 bash/contract 검증 후 in-scope 결함0이다. 정책 종결은 **검증된 개선 후보 또는 정확한 incumbent 보존 정책과 사유가 정상 후행 소비되는 상태**다. 실제 제출0/원천 미지원이면 신규 개선 정책을 억지 생성하지 않는다. 자연 실측/비용 후 성과는 별도 acceptance이며 미래 제출·청산이 필요하면 그 조건을 남긴다.

## 11. 계획 리뷰 결과

자기검토에서 단순 기존 entry 모델 재사용으로 partial/no-fill까지 검증됐다고 볼 위험, post-selection clamp 값의 미평가, 제출 census와 취소 proxy0 혼동, 공통 env의 scope 확장 위험을 확인해 CW1~CW4에 반영했다. 최종 보완에서는 학습 후보 선정의 미정 부분을 §5.1로 확정하고 보고서/CW3/회귀검증에 연결했다. 재검토에서 순익 단일 순위가 EV 음수 후보를 선정하지 못하도록 동시 개선을 선행 eligibility로 두었고, 선정 후 holdout 실패 시 같은 holdout의 차순위 반복을 금지했다. 구조 결손→EV/일별 순익→후행 소비→성능 순서를 유지하며 신규 범용 시스템은 추가하지 않는다. 실제 source0 원인·운영 PID 사용·신규 경제성/승격 결과는 이번 계획에서 확정하거나 생성하지 않았다.

## 12. 구현 종결 및 자연 검증 경계

CW0–CW6 구현·리뷰의 owning evidence는 [구현 리뷰](../audit-reports/2026-09-18-entry-cancel-wait-economic-implementation-review.md)와 `tmp/entry-cancel-wait-economic-20260918/` receipts다. 기존 producer/projection·durable 원장·entry operating replay·standalone PREOPEN·dated scoped helper·summary generation을 연결했다. 실제 제출 census가 불완전하면 `source_gap`, 미해결 주문은 `waiting_outcome`, 검증 모델이 없으면 경제성 null과 incumbent 보존으로 종결한다.

첫 구현은 사전 고정한 지원 scope 한 개를 분석한다. 실제 체결 witness와 연속 native no-touch 구간으로 검증 가능한 취소 terminal만 지원하며, 취소 후 가상 passive 체결/queue와 취소 ACK 이전 partial holding frame은 미지원으로 남긴다. 해당 상태를 모델에서 지원했다고 선언하거나 실제 수익으로 간주하지 않는다. 기존 전체 제출 union·동일 notional·자본·cost·holdout gate를 유지한다. 지연 발행은 source date를 바꾸지 않고 publication date와 다음 거래일을 명시한다. 다음 정책은 검증 후보 또는 정확한 incumbent carry이며 자연 actual model/새 holdout·정규 PREOPEN/PID·실제 비용 후 성과는 별도 acceptance다.
