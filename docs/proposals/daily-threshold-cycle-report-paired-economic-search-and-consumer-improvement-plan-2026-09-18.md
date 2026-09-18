# Daily threshold cycle report EV·일별 순익 탐색 및 소비 연결 상세개선계획

작성: 2026-09-18 KST. 대상은 `src.engine.daily_threshold_cycle_report`다. 후속 사용자 지시로 D0–D6 구현·반복 리뷰/보완·commit/push·선택 배포와 제한 장후 재생성을 승인받았다. 자연 PREOPEN/PID/주문·실제 경제성은 별도 Acceptance이며 수동 선행 실행하지 않는다. 실행 owner는 당일 `ThresholdDailyEVReport0918`을 재사용한다.

## 1. 결정과 목표

**일일 통합 평가 기능은 유지하되, 경제성 비교가 성립한 활성 family만 제한 탐색하고 기존 정책 대비 비용 후 EV·동일 자본의 일별 순익 우위를 독립 검증한 결과만 기존 소비 경로에 전달한다.** 결손 상태의 전체 재실행이나 후보 확대보다 비교 계약·원천·후행 소비를 먼저 보완한다.

우선순위는 구조적 결손 해소→유효 경제성 값 도출→후행 소비 closure→필요한 계산시간 단축이다. 양수 결과를 만들기 위한 기준 완화·결손0 대체·대량 후보 생성은 하지 않는다. 검증된 음수/no-edge도 유의미한 결과이며 결과가 null인 비교 불가와 구분한다.

기준 문서: [Plan Rebase §1–§8](../plan-korStockScanPerformanceOptimization.rebase.md), [당일 checklist](../checklists/2026-09-18-stage2-todo-checklist.md), [장후 결과 리뷰 규칙](../postclose-tuning-result-review-task-instructions.md). 원칙/active·OFF/rollback 소유권은 Rebase, 실행 owner·Acceptance·일정은 current checklist다. 문서 작성이나 조회만으로 장후 절차를 실행하지 않는다.

## 2. 현행 근거와 소유 경계

현행 snapshot 근거는 [step1023 요청](../../tmp/postclose_stepwise_2026-09-17/request_1023.json), [실행 결과](../../tmp/postclose_stepwise_2026-09-17/result_1023.json), [Daily](../../data/report/threshold_cycle_2026-09-17.json), [compact 경제성](../../data/report/ai_entry_setup_paired_replay_batch/compact_auxiliary_paired_economic_2026-09-17.json)다. 이 경로의 후속 projection은 원 ledger와 구분하며 후속 구현에서 as-of/hash를 재확인한다.

계획 수립 시 선택 source는 `e1d3cfab31b42fc53c57fd16b3562e4cb3295155` (`ai-quality-source-attainability-final-reviewed-20260918`)다. 후속 구현 시 selector/HEAD·actual caller를 다시 확인하고 실행 중 managed release를 편집하지 않는다. unrelated workspace와 다른 세션의 원천/평가기 구현은 보존한다.

- 9/17 step1023은 9/18 00:19:25~00:24:31, 305.35초/exit0. 생성 시점의 calibration19개, apply candidate0, runtime_change=false. AI 검토 대상0으로 신규 provider 호출 없음. exit0은 경제성 완료가 아니다.
- `adjust_up/down` 공통 분기에는 추천값/현재값 비교가 포함된다. 추천 방향은 검증된 ΔEV가 아니다. soft-stop 표본810/방향상향이 있어도 outcome/exposure/EV readiness와 적용 권한은 별도다.
- 가격 관측16,292건은 exact real execution economic pair 분모가 아니다. 현행 가격 선택의 전용 paired proof 소비도 존재하므로 과거 관측 집계만 보며 전용 평가기를 중복 구현하지 않는다.
- 수량 후보의 exact terminal·비용 후 EV 비교/선택, smoothing의 rolling5/10/20일 및 guarded downside 판단은 재사용한다. 모든 family가 동일한 탐색·holdout·일별 순익 계약을 구현했다는 뜻은 아니다.
- 9/17 compact 관측21건은 stop 결손11/자연 계약9/경로1로 전부 제외. paired0, EV/일별 순익 null. 9/18 publication→9/21 incumbent compact v3 보존은 source/consumer 연결이고 신규 개선 증거는 아니다.
- 9/17 historical Daily/EV에는 현재 퇴역 family와 당시 적용 manifest가 남는다. immutable 원본을 보존하고 현재 판단 projection에서 archive-only로 분리한다. 과거 selected 목록을 새 장후 개선 후보로 집계하지 않는다.

| 역할 | 소유·재사용 경계 |
| --- | --- |
| Daily | family 입력·비교 가능성·판정·적용 readiness 통합. 공용 새 replay engine이나 주문 executor가 아님 |
| family 평가기 | causal replay/모델/비용·자본·holdout·후보 평가의 원 owner. Daily는 유효 증거를 소비 |
| entry split/수량·가격 | 기존 execution model·exact plan·원천 및 합동 gate 사용. 다른 세션의 검증을 중복하지 않음 |
| compact AI | 기존 paired→calibration→dated publisher→optimizer plan→consumer 경로 유지. 고정 provider/model 및 현행 승인 경계 유지 |
| holding/exit | 기존 실제 owner·source-only/권한 경계 유지. report-only를 sample 증가만으로 live로 변경하지 않음 |
| PREOPEN·runtime | 기존 selector/loader·mapping·guard·rollback·custody 소유. Daily가 env/provider/수량/주문을 직접 변경하지 않음 |

퇴역 ADM/LDM/PYRAMID/RISING_MISSED/current-axis/R0–R3 등을 신규 평가·복구 owner로 만들지 않는다. `main_ai_prompt_optimizer`의 폐기 standalone CLI를 실행하거나 복원하지 않는다. 현행 compact finalizer의 순수 helper와 plan refresh만 소비한다.

## 3. 먼저 확정할 family별 비교 가능성

D0에서 기존 registry/metadata·실제 wrapper/cron·publisher/loader를 대조한다. 새 registry/service/DB를 만들지 않는다. 각 family에 active bounded/active observe·report-only/OFF/retired, stage·조작 지점·cohort·기존 정책 버전, 실제 입력/평가기/소비자/최초 blocker/closure를 기록한다. 실제 활성 상태와 코드 존재 여부를 구분한다.

| family/유형 | 첫 보완 | 탐색 조건·처리 |
| --- | --- | --- |
| position sizing | exact parent·수량·체결/청산·비용·자본 결속 및 current/rollback 후보의 paired 모집단 확인 | 실제 분모와 기존 floor 통과 후 기존 grid만 평가. 비율 EV 상위가 원화 순익을 줄이면 승격하지 않음 |
| dynamic entry price | 기존 exact price selection proof/model·운영 scope와 Daily binding 확인 | 관측 proxy와 operating paired EV 분리. projection gap이면 cheap 진단만 발행 |
| entry/scale-in split | 원 owner의 execution/atomic/fill/cost 모델 gate와 합동 selection proof 소비 | entry는 기존 submitted/전체 기회 계약, scale-in은 기존 실제 체결 조건 유지. 서로 모집단을 대체하지 않음 |
| soft-stop/holding smoothing | 기존 path journal의 causal delta·cost·downside·지연 및 report-only 범위 확인 | 표본만 준비된 상태와 경제성/권한 준비를 분리. source-only delta를 실제 순익으로 사용하지 않음 |
| protect/trailing | evaluated/qualifying·GOOD_EXIT 위험·paired exit outcome 의미 확인 | qualifying0과 결손/미검증을 구분. freeze/report-only guard 유지 |
| market regime | label/context 통계와 실제 조작 가능한 기존 축 구분 | label별 평균 EV를 threshold 정책의 causal 개선으로 사용하지 않음 |
| compact | 기존 실행 모델·정확 입력/stop·비용/portfolio·forward holdout 결과 소비 | 다른 세션의 source-label/evaluator 개선을 재구현하지 않음 |
| OFF/retired | 현재 projection의 terminal disposition 확인 | 신규 후보·source gap 복원 업무·필수 wait에서 제외. raw/주문/비용/rollback 원장은 보존 |

유효 source가 존재하고 새 terminal만 기다리는 경우 `pending_maturity`다. 원천 유입0은 active producer와 수집 경계 확인 전까지 단순 waiting으로 처리하지 않는다. immutable 과거 payload/stop/계획 손실은 시간으로 복원되지 않으며 제외·원 owner의 향후 원천 보완 대상으로 남긴다. 구조 결손/불명확 ETA는 null이다.

## 4. 경제성 판정 계약: 기존 보고서의 section 보완

기존 Daily/calibration의 family row 또는 기존 `candidate_readiness`에 경제성 증거 section을 추가/확장한다. 별도 독립 report producer를 만들지 않는다. 필드 이름은 후속 구현에서 현행 schema와 중복되지 않게 확정하고 producer/consumer를 함께 수정한다.

필수 정보는 family/stage/cohort·owner·source/effective date, incumbent/candidate 정책·평가기/모델 버전·SHA, frozen opportunity census·기간·source hash, cost/exit/capital·holdout 계약 SHA, 조작 축, 최초 제외 사유·owner·closure, 계산 as-of/최종 소비 generation이다.

추천 방향(`adjust_up/down/hold`)과 다음 증거 상태를 서로 독립적으로 표시한다. 기존 `calibration_state` enum을 전면 교체하지 않는다.

| 증거 상태의 의미 | 경제성 값·후행 처리 |
| --- | --- |
| retired / disabled / observe_only | 상태별 terminal 또는 source-only. 새 적용 authority 없음 |
| source_gap / unsupported_scope | 비용/결과 null, 평가 불가·원 owner/closure 표시 |
| pending_maturity / insufficient_sample | 유효 비교 준비/표본 정도 표시, incumbent 유지 |
| incumbent_preserved_identical_policy | 동일 정책 자기 비교. Δ0 진단 가능하나 독립 후보 검증/개선 집계 제외 |
| valid_no_effect | 서로 다른 정책이나 행동/노출 효과 없음. valid pair 수·Δ0 명시 |
| valid_no_edge | source/model/비교 계약이 유효하나 보수적 개선 기준 미달. 측정값 보존 |
| validated_improvement | family별 기존 경제성·holdout·위험 gate 통과. 별도로 적용 권한/동일 stage/rollback 확인 |
| evaluation_failed | 예외·불완전 결과. 성공/hold_no_edge/valid empty로 삼키지 않음 |

이 상태는 판정 의미이며 이 문서가 특정 enum 신규 구현을 강제하지 않는다. 기존 동등 상태가 있으면 재사용한다. 새 증거 section을 쓰는 family에만 계약 버전을 올리고 strict 소비자가 이를 요구하도록 전환한다. 미전환/과거 호환 row의 generic 방향 추천은 경제성 통과가 아니며 새 challenger 적용을 허용하지 않는다. 기존 separately approved baseline/operator override 및 behavior-equivalent 초기 정책은 challenger와 분리하여 기존 시작 조건·expiry/custody를 보존한다. 예를 들어 현행 가격 P1 초기 baseline에 challenger 경제성 gate를 새로 부과하지 않는다.

## 5. 동일 기회·동일 자본의 EV·순익 평가

### 5.1 모집단·실행·비용

- family owner가 정의한 frozen opportunity/attempt/episode union에서 incumbent/candidate를 평가한다. 체결 성공 행만 추출하거나 양측의 source exclusion을 다르게 하지 않는다. source census는 평가 가능/결손/미성숙/unsupported/중복 disposition 합계로 보존한다.
- main/widget/episode/manual·real/sim/probe/CF·full/partial/no-fill·venue/session/route·입력/정책 버전을 분리한다. parent/episode의 retry/child/fill을 독립 표본으로 중복 세지 않는다.
- actual PnL은 COMPLETED+유효 비용/손익만 사용한다. model/CF 경제성은 검증된 scope에서만 별도로 표시한다. 행동이 바뀌면 체결/청산·보유량·reserve도 달라지므로 실제 incumbent fill/exit를 candidate에 무조건 붙이지 않는다.
- 당시에 알 수 있는 가격/시장/AI 입력·clock만 사용한다. 미진입 기계 BLOCK/AI VETO 평가와 실제 체결 이후 split/ADD timing 평가를 해당 원 owner의 정의대로 분리한다.
- 지원된 no-exposure/no-fill만 modeled PnL0이 가능하다. 누락된 비용·보유 미청산·미지원 execution을0으로 만들지 않는다. 실제 무거래와 미청산 실현0을 구분한다.
- 동일 초기 budget·주문 reserve·동시 보유 제약을 사용한다. 각각의 후보를 무제한 자본으로 평가하거나 수량 증가를 독립 split/price 우위로 섞지 않는다.

### 5.2 목적함수·지표

paired 원화 순익 차이는 `candidate modeled net pnl − incumbent modeled net pnl`이다. 기존 family의 primary EV 정의를 유지하고 ΔEV의 분모·표본·notional weighting을 명시한다. 공통 supporting 지표로 frozen budget 기반 portfolio return Δ와 거래일별 modeled net delta, attempt 기준 평균 순익, 참여/미체결·부분체결, reserve/holding capital time, p10/ES/worst tail·stress·모델 오차를 전달한다. 실제 net PnL과 모델 비교는 별도 field다.

비율 EV와 일별 원화 순익을 하나의 임의 가중 점수로 합치지 않는다. bounded 적용 후보는 기존 family gate와 함께 **기존 정책 대비 ΔEV·공통 자본의 합의된 기간 일별 순익 집계가 모두 개선되고 tail/stress 기준을 통과하는 경우**만 선정한다. 일별 각 값·평균·누적·worst day를 표시하며 모든 날짜 양수라는 신규 보편 허들을 만들지 않는다. 표본/비용/holdout floor는 기존 family 계약을 유지한다.

실행/AI 비용은 actual 또는 reviewed cost model·환산 revision을 결속한다. 평가 provider 비용과 장중 증분 추론 비용을 분리한다. Δ값0·null·음수·양수를 명확히 구분하며 positive 값만 남기지 않는다. 자본/PnL이 없으면 EV가 양수여도 경제성 전체 검증은 미완료다. Source-quality 결손에 임의 할인계수를 곱한 EV나 label/cohort별 단순 평균을 causal ΔEV로 사용하지 않는다. 기존 지표는 diagnostic으로 보존하되 결손 격리 후 정확한 양측 분모와 비용 계약을 확인해야 경제성 판정에 사용한다.

## 6. 제한 탐색·독립 검증·선정

기존 grid·사전 허용 parameter 범위·daily step/canary 제한을 먼저 사용한다. 조작 축은 하나씩 고정하고 incumbent를 항상 control로 포함한다. 동일 정책은 보존 판단으로 분리한다. price×quantity×split 등 기존 합동 owner가 있는 경우 그 gate를 재사용하고 Daily가 별도 결합 탐색/정책을 발행하지 않는다.

1. cheap admission: active scope·원천/비용/실행 모델 준비·새 ready revision 확인. 실패면 expensive grid를 건너뛰고 결손/owner를 발행한다.
2. learning evaluation: 지원 scope·동일 모집단에서 기존 candidate 메뉴의 경제성·tail·모델 오차를 평가한다. 학습 상위가 incumbent이면 보존이지 독립 후보 검증 성공이 아니다.
3. candidate freeze: family/조작 축·candidate 및 source/모델/비용/계획 SHA를 고정한다. Holdout에서 후보/기준을 재선택하지 않는다.
4. independent validation: existing chronological/forward holdout을 한 번 사용한다. 모델 validation holdout과 정책 learning/holdout을 분리한다. 같은 날짜/episode/입력을 train/test 또는 별도 성공 표본으로 재사용하지 않는다.
5. selection: 개선 기준 미달/no-effect/결손이면 구체 disposition과 incumbent를 전달한다. validated improvement도 적용 권한·operator lock·same-stage·rollback gate와 별도다.

유효 비교가 없으면 후보 메뉴를 확대하기 전에 최초 blocker를 수리한다. holdout이 얇으면 분석 결론을 잠정 상태로 남기고 자연 표본을 기다린다. 실패한 후보를 같은 holdout에서 계속 바꾸며 양수를 찾지 않는다.

## 7. 새 입력이 있을 때만 계산: 단순한 재사용

기존 compact state/cache·manifest/summary·전용 bounded refresh를 먼저 사용한다. identity/terminal/cost/model/정책/holdout/source-quality revision을 fingerprint에 포함한다. mtime·경로만으로 경제성 currentness를 보증하지 않는다.

- 영향 family의 유효 입력이 불변이면 이전 immutable evaluation SHA/as-of를 재사용한다. 새 조회 시각을 새 평가 완료 시각처럼 표시하지 않는다.
- late terminal/cost 또는 source exclusion 수정은 영향을 받은 parent/aggregate와 후행 hash binding만 갱신한다. 변하지 않은 family replay·provider call은 반복하지 않는다.
- 임의 전체 clean-baseline raw 재스캔·고가 전체 native 재실행·giant cache migration을 기본 경로로 만들지 않는다. growing/64MiB 초과 JSONL은stat 후 manifest/summary/bounded streaming을 사용한다.
- 구현 복잡도가 커지면 fingerprint 기반 family 단위 결과 재사용까지만 먼저 구현한다. 별도 증분 DB·worker pool·성능 watchdog/guard·신규 타이머/cron은 추가하지 않는다.
- 시간이 부족하면 후보 깊이/개수 또는 아직 준비되지 않은 분석을 줄인다. 감소한 범위와 미평가 후보를 명시한다. 모집단을 임의 축소하거나 holdout/cost/safety를 생략해 빨라졌다고 주장하지 않는다.

성능 기준은 측정값·지원 범위를 기록하는 진단이다. 305.35초 이전 실행은 참고이며 이후 입력/범위가 달라지면 동일 비교로 주장하지 않는다. EV 계약 closure보다 wall-time 목표를 앞세우지 않는다.

## 8. producer→consumer 연결 계약

| 연결 | 확인할 계약·closure |
| --- | --- |
| family source/evaluator→Daily | exact source date·native identity·scope·census·self/byte hash·모델/비용/holdout binding. missing/changed source가 valid no-edge로 전달되지 않음 |
| Daily→calibration/cumulative | 같은 family/current generation·period/분모. 방향 추천과 경제성/권한 상태의 독립 projection |
| calibration→AI correction | 실제 적용 심사 대상만 요청. reviewer가 missing economics를 채우거나 source gap을 승인하지 못함 |
| Daily/calibration→EV/runtime summary | 현재 active 평가 vs archive/기존 override selected 분리. positive candidate/validated pair/selected/PID/actual net 개선 수를 각각 표시 |
| calibration→PREOPEN selector | 기존 eligible/allowed/동일 stage/lock/step/cap·새 경제성 계약 확인. legacy 방향 상태 단독 적용 차단 |
| compact→dated publisher/optimizer/consumer | 현재 독립 compact finalize 유지. generic legacy blocker로 family 인계를 막거나 standalone 퇴역 CLI 복원 금지 |
| policy/PREOPEN→runtime loader | trading calendar의 source/publication/effective date·scope·generation/version/rollback binding. stale/mismatch면 기존 guard/원 정책 경계 유지 |
| runtime→post-apply attribution | actual policy version/PID·parent/order/fill/exit/cost receipt. 모델 Δ와 실제 비용 후 손익 분리; 실제 손익 전부를 causal uplift로 부르지 않음 |
| tower/checklist→strict verifier/controller | final parent SHA·추천/부적격 disposition·last consumer. verifier/controller self hash를 source에 포함하지 않음. family PASS와 whole native DONE 분리 |

원 source 기준일을 자정 이후에도 유지한다. 휴장일 publication과 다음 trading effective date는 분리하며 9/18 발행을 9/18 거래 성과로 집계하지 않는다. 여러 family 통합이 다른 family의 미완료 source를 완료로 바꾸지 않는다.

파생 current projection/요약은 기존 bounded refresh 경로로 갱신한다. 과거 원본·frozen ledger·holdout consumption·실제 주문/비용·release/rollback은 보존한다. 현재 checklist의 기존 family owner/Acceptance에 연결하고 퇴역 항목은 복구 OPEN으로 만들지 않는다. 통합 변경의 실행 owner는 후속 구현 intake에서 현재 checklist에 단일 소유를 확인한 후 확정한다.

## 9. 구현 순서·수정 위치·완료 기준

새 Python module/engine-root 파일·호환 wrapper를 기본 요구하지 않는다. 기존 package와 함수를 최소 수정한다. 프로토콜/API parser/FID를 실제 수정할 때에만 Kiwoom official reference gate를 먼저 수행한다.

| package | 기존 수정 위치 | 완료 기준 |
| --- | --- | --- |
| D0 source/authority census | `daily_threshold_cycle_report.py`의 metadata/source loader·현행 owner scrub, 인벤토리/운영 문서 | active/observe/OFF/retired와 실제 caller/소비자 일치. source gap·maturity·historical selected 분리 |
| D1 evidence contract | 기존 family row·`candidate_readiness`/calibration projection·fixtures | 방향/경제성/권한 상태 분리, null/zero/identical/no-effect/no-edge/실패 구분. 현재 source hashes/census 보존 |
| D2 paired adapters | 기존 수량/가격/holding 함수 및 family 평가기의 기존 section | 한 family씩 지원 scope에서 ΔEV·일별 net/tail/capital 확보. 중복 replay engine 없음. 다른 세션의 전용 proof 소비 |
| D3 selection/validation | 기존 calibration·window policy·candidate selection | frozen 후보·existing holdout gate·non-degradation·합동 owner 유지. 학습 우위/추천 방향 단독 선정 없음 |
| D4 minimal reuse | 기존 report source/cache/전용 refresh | 동일 revision grid/provider call0, late cost/terminal 해당 scope 재평가, stale previous PASS 승계 없음 |
| D5 consumer closure | `threshold_cycle_ev_report.py`, `runtime_approval_summary.py`, `threshold_cycle_preopen_apply.py`, strict verifier/summary/checklist 기존 함수 | exact-date/hash/version/권한을 끝까지 소비. 계약 빠진 row·과거 selected·퇴역 family가 새 적용 후보로 승계되지 않음 |
| D6 review/bounded regeneration | 관련 기존 테스트·owning audit/운영 문서 | review→fix→re-review→targeted validation 후 별도 승인된 family refresh만 수행. actual PID/자연 성과는 별도 receipt |

D0–D1을 먼저 닫고 이미 전용 paired proof가 있는 family부터 D2–D3을 연결한다. unresolved source/model gap이 있는 family는 owner/closure만 전달하고 탐색 보류한다. 모든 family 원천 보완을 하나의 대규모 구현으로 묶지 않는다. 최초 완료는 적어도 한 활성 family에서 유효 paired 경제성 값과 후행 수락/보류 사유를 끝까지 재현하는 것이다. 양수·선정·실제 주문은 구현 완료의 필수 조건이 아니다.

## 10. 회귀·검증·완료 판정

기존 `src/tests/test_daily_threshold_cycle_report.py`, `test_daily_threshold_final_review.py`, family 경제성 suites, `test_runtime_approval_summary.py`, `test_postclose_summary_handoff.py`, strict verifier/PREOPEN 관련 기존 테스트에서 필요한 계약 사례만 보완한다. 구조를 그대로 따라가는 대량 테스트나 새로운 테스트 파일은 요구하지 않는다.

필수 사례:

- 동일 정책과 독립 후보의 집계 분리; 추천값 상승이 ΔEV 검증을 대체하지 않음.
- partial/no-fill·미청산·비용 결손·irrecoverable source·유효 무거래의 분리와 null 보존.
- 높은 EV지만 공통 자본 일별 순익 악화/꼬리 악화/미검증 모델이면 승격하지 않음.
- train/test episode 중복·candidate 재선택·holdout 재사용·모델/비용 revision 변경 시 이전 PASS 차단.
- actual/model/CF·report-only/OFF/retired·historical selected/override와 current challenger 구분.
- unchanged source에서 expensive evaluation 없음; late terminal/비용 및 exclusion revision 변화는 결과/후행 SHA 갱신.
- producer→Daily→calibration→EV/summary→PREOPEN selector·dated loader까지 유효/결손/기준일 경계의 통합 fixture. 직접 private cache 주입만으로 PASS를 만들지 않음.
- family 한 곳의 준비 실패가 다른 family를 무효화하지 않음. summary/controller는 mandatory active handoff 실패를 숨기지 않음.

Python 수정은 targeted pytest·compile·diff check, wrapper 수정은 bash-n/관련 계약 테스트, 문서/checklist 수정은 링크/owner/권한 및 print-only backlog parser를 사용한다. 신규 source/module가 필요해지면 위치 gate를 별도로 적용한다.

완료 보고는 코드 closure/선택 release/정책 publication/PREOPEN/PID consumption/자연 행동/actual 비용 후 경제성을 분리한다. 분석 산출물은 source gap/표본 부족/유효 no-effect/valid no-edge/검증된 개선을 포함하며 양수 결과만 성공으로 보고하지 않는다. Report generation/PASS는 economic acceptance가 아니다. 본 문서 작성 단계에서는 문서 self-review·보완·링크/print-only parser만 수행하고 pytest/provider/보고서 재생성/외부 sync는 실행하지 않는다.

## 11. 계획 문서 리뷰 결과

Self-review→보완→re-review에서 신규 공통 허들로 초기 behavior-equivalent baseline을 막을 위험, 보고서 direction 상태와 실제 경제성 상태의 혼동, 퇴역 standalone 호출 복원, 다른 세션 평가기 중복 및 current/과거 selected 집계 혼동을 점검했다. 초기 baseline/override 경계와 source-quality 임의 할인 지표의 diagnostic 한계를 명시해 보완했다. 로컬 링크·작업 package·권한/소비 경계·문서 whitespace 및 print-only backlog parser를 검증한다. 이번 산출물은 계획 문서 하나이며 구현/자동화/실행 일정은 변경하지 않는다.

## 12. 구현 종결과 남은 자연 Acceptance

D0–D6 구현은 [owning review](../audit-reports/2026-09-18-daily-paired-economic-implementation-review.md)와 `tmp/daily-paired-economic-20260918/` 증거로 닫는다. 기존 Daily/calibration row의 `economic_evaluation`은 방향·모델 경제성·적용 권한을 분리하며 source/policy/model/holdout 및 evaluator code revision을 fingerprint로 결속한다. 기존 가격·scale-in proof adapter와 PREOPEN/EV/runtime/strict 소비를 연결했고 새 평가기·Python module·cron은 만들지 않았다. 미지원 family의 causal 비교는 원 owner의 proof 준비 전까지 null/보류다.

`--refresh-economic-evaluation-only`는 기존 최신 producer와 frozen proof만 소비하며 동일 입력은 평가 시각/SHA를 보존한다. 원본 Daily byte SHA archive와 CAS 검증 후 현재 projection을 갱신한다. 이후 기존 calibration 저장·EV/runtime summary·compact finalizer/strict를 순서대로 연결한다. 실제 적용일은 거래 calendar가 결정한다. 본 계획 앞부분의 계획 작성 시 실행 금지는 그 시점 이력이며 후속 사용자 구현 지시를 제한하지 않는다.
