# PYRAMID 기존 튜닝축 경제성 평가 개선 계획

- 작성: `2026-09-05 KST`
- 상태: `implemented_review_closed_source_observation_pending`; 코드·계약 구현은 완료됐고 자연 런타임 표본과 실제 PREOPEN 적용은 아직 발생하지 않았다.
- 기존 owner: `scalping_pyramid_quality_gate`, stage=`scale_in`
- 변경 가능한 전략 값: `SCALPING_PYRAMID_MIN_PROFIT_PCT` 한 개
- 실행 항목 owner: [2026-09-07 체크리스트](../checklists/2026-09-07-stage2-todo-checklist.md)의 `PyramidExistingAxisReplayPlan0907`
- 원칙: [Plan Rebase](../plan-korStockScanPerformanceOptimization.rebase.md) §1~§8; 현행 계약: [report traceability](../report-based-automation-traceability.md)

## 1. 결론과 목표

기존 PYRAMID 축의 **평가 자료 → 추가매수 가능성 재현 → 비용 차감 비교 → 후보 판정 → 자동화 전달**을 개선한다. 1.1%를 미리 특정 값으로 낮추는 것이 목표가 아니다. 기존 매도·보유·수량 정책 아래에서 더 작은 수익 기회를 자주 확보하는 것이 실제 순기여 개선으로 이어지는지를 판정하는 것이 목표다.

추가 leg 전용 익절, 짧은 보유시간, 새 진입 family, 독립 자동화체인, 새 shadow 운용은 만들지 않는다. AVG_DOWN, 독립 `post_probe_winner_recovery`, strong-continuation 설정, runtime-prior 설정도 이번 조정축에 포함하지 않는다. 다만 기존 PYRAMID 판단에 이들이 영향을 주는 사실은 재현·귀속에서 누락하지 않는다.

기대효과는 잘못 계산된 추가매수 기회·비용·차단 원인에 의한 추천을 줄이고, 작은 양의 순기여 후보를 기존 자동화가 놓치지 않도록 하는 것이다. 수익 증가 자체는 아직 검증되지 않았으며 보장하지 않는다.

## 2. 현재 근거와 남은 한계

| 확인한 구현 | 개선이 필요한 지점 |
| --- | --- |
| `_profit_threshold_grid`는 최고수익률이 임계값을 넘은 행에 대해 임계값 가격 진입을 가정하고 종료수익률로 평가한다. | 실제 평가시각·가격·동시 차단조건을 재현하지 못한다. 최고가 도달만으로 주문 가능한 기회라고 볼 수 없다. |
| `_pyramid_blocked_record`와 `_update_snapshot`은 일부 특징·임계값·최고/최저/종료 수익률을 보존한다. | raw event의 `base_min_profit_pct`, `profit_gate_mode`, quality 결과·prior 적용 정보 등을 평가용 행까지 보존하는지 전수 확인해야 한다. 실제 사용 가능한 호가와 원가 기준의 완결성은 미확인이다. |
| `evaluate_scalping_pyramid`는 base 외에 strong-continuation, scout bridge, runtime-prior 경로를 사용한다. | 관측 `min_profit_pct`가 설정 기본값인지 해당 호출의 유효값인지 구분해야 한다. 유효값을 기본 env로 역추정하지 않는다. |
| real scale-in 행은 주문번호·체결가·체결수량·venue·receipt 계약을 가진다. | quote 기반 가정과 실제 체결 증거를 분리해야 한다. 원포지션 종료수익률을 추가 leg 수익률로 바로 치환하지 않는다. |
| 현재 calibration은 적격 one-share opportunity가 있으면 그 표본을 우선한다. | 그 결과를 일반 PYRAMID 전체의 효과로 일반화하지 않는다. 정책 버전·수량 출처·entry lineage·venue별 호환성을 확인한다. |
| 같은 날짜 PYRAMID direct 후보의 daily AI 입력 병합은 보완됐다. | 새 코드로 생성된 자연 장후 AI 결과와 PREOPEN 소비 증거는 별도 확인이 필요하다. |

참고로 `2026-09-04` 대상의 `2026-09-05 11:45 KST` 임시 재평가에서는 유효 proxy 80행에 대해 1.1%의 기회당 비용 차감 기여가 약 `-0.1147%`, 1.0%가 `-0.0923%`, 탐색 최선 0.4%도 `-0.0220%`였다. 이는 **현재 proxy 모형에서 낮추기만 하는 가설이 지지되지 않았다는 뜻**이지, 1.1%가 최적이거나 실제 실행 가능한 PYRAMID 전체가 비경제적이라는 결론은 아니다. 생산 리포트·런타임 적용 증거로 취급하지 않는다.

## 3. 구현 순서와 완료 기준

### P0. 입력 계약과 표본 범위를 먼저 확정

- 기존 feedback producer에서 `position/record ID + symbol + venue/session + evaluation timestamp + event ID`로 평가 기회를 식별한다. 반복 로그와 독립 추가매수 기회를 구분한다.
- `configured_min_profit_pct`, `effective_min_profit_pct`, `profit_gate_mode`, runtime policy/version, source ID를 구분한다. 설정값은 검증된 동일 날짜 env 또는 의미가 명확한 base 관측으로만 확정한다. 모순·결손은 임의 복원하지 않는다.
- 평가시각의 원가·현재가·호가 timestamp·price source·quality/prior 결과·downstream blocker·주문/체결/종료 연결·비용 포함 여부를 inventory로 작성한다. 불필요한 전체 tick 수집이나 신규 API 호출은 만들지 않는다.
- clean baseline 이후의 적격 기존 보유 평가 universe를 조사한다. one-share, 일반 PYRAMID, recovery와 sim/real을 명시적으로 구분하고, 관측이 있다는 이유로 다른 family의 실주문 권한에 합산하지 않는다.
- 결손은 가능한 row/window만 제외한다. 진행 중 포지션은 `pending_outcome`이며 실패나 수익률 0이 아니다. 과거 복원 불가능 결손은 날짜·범위를 명시해 종결하고, 필요한 필드만 기존 event producer에 source-only로 보강한다.
- 완료 기준: 전체 기회 수가 재현 가능·명시적 차단·pending·결손/충돌·중복 제외로 빠짐없이 대사된다. 가격·정책·비용의 미확인 항목마다 owner, repair, acceptance test가 있다. 원본 일중 전체 모집단이 없으면 coverage 범위를 부분 관측으로 표시한다.

### P1. 실제 시점의 기존 판단을 재현

- 동일 episode에서 현재 임계값과 후보 임계값 각각에 대해, 당시까지 알려진 데이터만으로 처음 통과 가능한 **기존 평가 이벤트**를 선택한다. 일중 최고가나 미래 종료결과로 진입시각을 선택하지 않는다.
- 기존 PYRAMID 평가 로직을 재사용한다. 필요하면 threshold를 명시 입력으로 받는 순수 계산부로 분리하되 기존 호출의 결과 동등성을 먼저 검증한다. 전역 env/설정값을 바꿔가며 replay하지 않는다.
- base, strong-continuation, scout bridge, runtime-prior의 원래 우선순위와 당시 값을 고정한다. 후보 min-profit 이외의 score/pressure/tick/micro/confirmation/sizing 값은 바꾸지 않는다.
- threshold-only, 다른 조건 차단, 복합 차단, downstream 미평가를 구분한다. AI 50 sentinel, stale quote, 가격/계좌/주문/수량/cooldown guard의 unknown을 pass로 바꾸지 않는다. 기존 raw에 없었던 AI 판단을 사후 생성해 실제 판단처럼 사용하지 않는다.
- `gate_eligible`과 `submit_evaluable`을 별도 집계한다. 과거 profit gate에서 조기 반환하여 downstream AI가 실행되지 않은 경우, gate/가격의 source-only 비교까지 막거나 끝없이 실체결을 기다리지 않는다. 해당 비교의 권한을 gate 수준으로 제한하고 실제 submit 효과는 미확인으로 종결한다. P0 완료 시 복원 가능한 평가 계층을 먼저 확정한 뒤 그 범위만 구현한다.
- 당시 동일 route의 fresh quote와 기존 price resolver 결과를 사용한다. 호가만 있으면 `quote_based_counterfactual`, 영수증이 있으면 `real_fill`로 구분한다. 호가 존재는 체결 보장이 아니다. 가격 점프가 있으면 임계값 가격의 가상 체결로 메우지 않는다.
- 완료 기준: 현재값 replay가 재현 가능한 실제 gate 결과와 일치하고 불일치는 모두 귀속된다. threshold-only 행만 후보에 의해 바뀌며, 다른 safety veto·미평가 행은 주문 가능 표본으로 승격되지 않는다.

### P2. 같은 기회에서 비용 차감 순기여를 비교

- A=현재값, B=한 단계 후보, C=추가매수 없음의 **증분 기여 기준선**을 같은 episode 집합에서 비교한다. C의 증분 기여 0은 전체 포지션 손익 0을 뜻하지 않는다.
- 순수익률은 원칙적으로 실제/가정 추가매수가와 연결된 매도가에서 계산하고 추가 leg의 수수료·세금을 한 번만 차감한다. 입력 `profit_rate`가 이미 비용 차감인지 검증한다. 비용은 기존 공통 cost owner와 날짜/상품 provenance를 사용하고 상수 0.23%를 새로운 영구 기준으로 고정하지 않는다.
- 사용자가 요청한 슬리피지 제외 경제성을 기본 비교로 명시한다. 관측 spread/실제 fill 가격 차이에 이미 반영된 비용을 다시 빼지 않는다. 실제 체결 증거·미체결·슬리피지 민감도는 별도 진단이며 실제 순익과 혼합하지 않는다.
- 기존 매도 정책은 고정한다. 관측 종료가격을 고정한 비교는 `fixed_observed_exit_counterfactual`로 표시한다. 추가매수로 평단·trailing·stop 상태가 달라지는 경로는 인과적 runtime 효과라고 주장하지 않는다. 기존 simulator로 동일 exit 정책을 재현할 수 있는 경우만 그 결과를 별도 계층으로 만들고, 불가능하면 해당 한계를 명시한 source-only 분석으로 닫는다.
- 주 지표는 동일 기회 집합의 `source_quality_adjusted_ev_pct`와 B-A 차이다. 계산 계약은 `sum(각 기회의 비용 차감 추가-leg 수익률) / 비교 가능한 전체 기회 수`로 고정한다. 정상적으로 추가매수하지 않는 완결 기회는 증분 0; 결과·가격 미확인 기회는 0으로 대체하지 않는다. 어느 한쪽만 평가 불가능하면 paired 비교 양쪽에서 제외하고 원래 모집단·제외율·편향 위험을 함께 표시한다.
- `equal_weight_avg_profit_pct`는 추가 leg 발생 표본의 평균, `notional_weighted_ev_pct`와 증분 순이익 KRW는 금액·수량 provenance가 있는 표본만 별도로 계산한다. 동일 sizing 공식과 기존 cap을 유지하며 수량을 최적화하지 않는다. 빈도·보유시간·승률은 진단값이다.
- full/partial fill, quote 가정/실제 체결, entry lineage와 정책 변경 전후는 분리한다. 호환 가능한 parent 집계로 충분한 표본을 확보하되 NXT-only 자료로 common/KRX env를 변경하지 않는다.
- 경제성 지표의 필수 가격·비용·종료 자료는 양쪽에 동일하게 요구하되, gate 수준 비교에 실제 주문번호·실체결 20건 같은 요건을 잘못 부과하지 않는다. 반대로 gate 비교 양수를 submit-ready나 live approval로 해석하지 않는다.
- 완료 기준: 손계산 fixture에서 가격·비용·분모·paired delta가 일치한다. 동일 입력/정책 hash로 결과가 재현되고, missing·평단 변경·partial fill·미체결이 성과에 조용히 섞이지 않는다.

### P3. 달성 가능하고 명확하게 종결되는 후보 조건

| 조건 | 계획 |
| --- | --- |
| 1.1% 기본값 | 최적값이나 수익 목표로 취급하지 않는다. 검증된 현재값으로 비교한다. |
| 후보 탐색 | 기존 0.2~2.5%, 0.1%p grid를 탐색 진단으로 유지하고 후보값 자체를 강제하지 않는다. 현재값이 grid 밖/비정렬이면 정확한 현재값 비교를 추가하되 live bounds 밖 값을 자동 승인하지 않는다. |
| 일일 변경폭 | 기존 0.1%p를 초기 적용 경계로 유지한다. 먼 값만 양수이면 손해인 중간 단계를 자동 통과시키지 않고 `bounded_path_redesign_required`로 종결한다. 변경폭 확대는 근거와 별도 승인 범위를 제시하며 이번 계획에서 승인하지 않는다. |
| 경제성 | 후보 자체 비용 차감 증분 기여 > 0, 동일 기회에서 현재 대비 개선을 요구한다. 단지 손실이 작아졌다는 이유로 추가매수 확대를 추천하지 않는다. 별도의 최소 +1% 수익/개선율을 새로 요구하지 않는다. |
| 표본·기간 | 기존 후보 eligible floor 20을 초기 기준으로 유지한다. 동일 episode의 반복 이벤트로 채우지 않는다. 기존 rolling/cumulative 또는 적용 버전 window를 사용하며, 추가로 모든 작은 child bucket에 20건·연속 며칠 전부 양수 등의 조건을 붙이지 않는다. 수집속도·유효율·표본 집중도를 공개하고 구조적 결손과 자연적 희소성을 구분한다. |
| 과적합 | 탐색에 쓴 결과를 독립 검증이라고 부르지 않는다. 기존 시간순 window에서 후보를 고정한 뒤 후행 유효 자료의 방향성을 확인한다. 임의의 새 장기 대기기간·과도한 유의수준을 자동 gate로 추가하지 않는다. 검증 자료 미성숙은 명시 상태로 남긴다. |
| 중복/무관 조건 | 다른 진입 anchor의 전체 EV, 라벨 성공률, score 단독, 중복 표본 gate를 추천 veto로 재도입하지 않는다. 제거는 실제 의존성·안전 역할이 없음을 테스트한 조건에 한한다. |
| 미달 종결 | `source_quality_blocked`, `hold_sample`, `hold_no_edge`, `bounded_path_redesign_required`, `candidate_reviewed_preopen_pending`를 구별한다. 재평가 trigger는 새 완결 표본, 원천 복구 또는 모형 버전 변경이며 동일 자료로 무한 재시도하지 않는다. |

모든 새 평가 metric은 `metric_role`, `decision_authority`, `window_policy`, `sample_floor`, `primary_decision_metric`, `source_quality_gate`, `forbidden_uses`를 명시한다. 기존 noncanonical 기여 필드는 필요하면 compatibility alias로만 유지하고 주 판단 metric과 중복 권한을 만들지 않는다.

### P4. 기존 자동화 연결과 회귀 검증

기존 `intraday_feedback → quality_calibration → daily AI review → PREOPEN apply → runtime provenance → post-apply attribution` 순서와 family/env 하나를 유지한다. 새 cron, 별도 리포트 체인, 독립 approval owner는 만들지 않는다.

- 기존 feedback JSON에 event/coverage 계약을 확장하고 calibration에 paired 결과·feasibility를 전달한다. schema 변경 시 old artifact는 명시적인 proxy diagnostic이며 exact replay-ready로 자동 승격하지 않는다.
- AI와 PREOPEN이 같은 target/source date, candidate ID/hash, 현재/추천값, evidence version, 비용·window 계약을 검토하도록 연결한다. AI missing/reject, hash/date mismatch, source 결손, same-stage conflict는 실제 차단 테스트로 검증한다. 단순 family명 일치만으로 오래된 AI 승인을 재사용하지 않는다.
- source-only replay 양수는 기존 real 승인 계약을 대체하지 않는다. `runtime_effect=false`인 분석과 허용된 PREOPEN 후보, 실제 적용 env/PID, 실제 매매 성과를 각각 구분한다.
- apply 완료는 report 생성이 아니라 같은 후보의 검토·정확한 PREOPEN env·프로세스 관측까지 연결된 상태다. 자연 match 0은 미적용/경제성 실패로 단정하지 않고 관측 없음으로 보고한다.
- 적용 후에는 동일 policy version의 applied/not-applied 기회·guard·실체결·EV를 귀속한다. 일반적인 EV 미달은 다음 calibration hold/freeze이며 safety rollback과 구분한다. 주문 실패·provenance 손상·owner 충돌·hard safety 침해 시 기존 rollback guard를 유지한다.
- 완료 기준: 정상 후보는 기존 경로에서 오직 min-profit 한 값만 전달되고, 모든 결손/충돌 fixture는 env를 만들지 않는다. source-only 지표가 standalone 실주문 권한으로 변환되는 경로가 없다.

## 4. 수정 위치와 검증 범위

| 역할 | 우선 수정/확인 위치 |
| --- | --- |
| 기존 event 계측·판단 의미 | `src/engine/sniper_state_handlers.py`의 `_log_scale_in_arm_blocked` / `_append_pyramid_probe_fields`; `src/engine/sniper_scale_in.py`의 `evaluate_scalping_pyramid` |
| event 정규화·coverage·종료 연결 | `src/engine/monitoring/scalping_pyramid_intraday_feedback.py` |
| 경제성 replay·단일축 추천 | `src/engine/monitoring/scalping_pyramid_quality_calibration.py` |
| AI/PREOPEN handoff | `src/engine/daily_threshold_cycle_report.py`, `src/engine/threshold_cycle_preopen_apply.py`의 기존 PYRAMID 경로 |
| 테스트 | 기존 `test_scalping_pyramid_intraday_feedback.py`, `test_scalping_pyramid_quality_calibration.py`, `test_daily_threshold_cycle_report.py`, `test_threshold_cycle_preopen_apply.py`, `test_sniper_scale_in.py`, `test_handle_holding.py` |

새 독립 Python root module은 만들지 않는다. 계산 분리가 꼭 필요할 때만 인접 구조를 확인하고 offline 분석은 `src/engine/monitoring/`, 실제 공통 판단은 `src/engine/scalping/` 소유로 둔다. broker 요청/응답/호가 protocol 변경은 계획에 포함하지 않으며, 필요해지면 공식 Kiwoom reference gate와 별도 범위 확인을 먼저 수행한다.

필수 회귀 사례: configured/effective 혼동, strong/prior/bridge 적용, 현재값 비정렬, 가격 jump, stale/다른 venue 호가, duplicate ID/시간 역전, missing downstream AI, AI 50, 종료 전후 평단 변경, partial fill, 비용 중복 차감, 비용 차감 후 음수, 후보 floor 미달, 먼 후보만 양수, 일부 source row 제외, one-share/general 오합산, old schema, stale AI hash/date, same-stage conflict, 정상 한 축 apply.

각 단계는 `구현 → 자체 리뷰 → 결함 수정 → 재리뷰 → 해당 targeted test`로 닫는다. 최종 영향 테스트·compile·`git diff --check`와 문서 parser를 통과한 뒤에만 허용된 다음 runtime 작업을 검토한다. 이번 계획 수립에서는 전략 코드·봇·주문·env·생산 보고서를 변경하지 않는다.

## 5. 다음 실행과 최종 판정

첫 구현 묶음은 **P0 입력 대사 + P1 현재값 재현 + P2 고정 종료가격의 source-only paired 비교**다. 데이터가 부족하면 source-only 최소 계측과 정확한 결손 범위로 닫고, 과거 호가/AI를 합성하지 않는다. 이후 P3 후보 판정과 P4 연결을 보완한다. 기존 exit 정책의 인과 재현이 불가능한 경우 이는 별도 exit 튜닝을 시작할 이유가 아니며 명시적인 승격 제한이다.

최종 결과는 세 질문으로 보고한다: (1) 유효한 자료로 실제 추가매수 기회가 식별됐는가, (2) 비용 차감 후보의 개선이 검증됐는가, (3) AI/PREOPEN/runtime/post-apply 중 어디까지 자동 반영됐고 무엇이 남았는가. 후보가 없더라도 원인이 경제성 부재인지 자료 결손인지 명확히 종결되면 평가 개선은 완료할 수 있다. 수익을 만들기 위해 불리한 결과나 안전조건을 삭제하지 않는다.

## 6. 2026-09-05 구현·리뷰 종결

- P0: 기존 PYRAMID gate 로그에 configured/effective threshold, 현재가·원가, 같은 WS snapshot BBO, 기존 scale-in price resolver의 allowed/reason/order price/source, quality 결과를 source-only로 추가했다. Feedback schema v5는 event/position/venue/session/terminal sell을 연결하고 ready, pending, price/resolver gap, owner/prior conflict를 전수 대사한다. 과거 로그는 필드를 합성하지 않는다.
- P1: calibration은 timestamp 순서에서 후보별 최초 기존 gate 통과 이벤트를 선택하며 실제 configured threshold의 관측 selected 결과와 replay 결과가 다르면 episode 전체를 제외한다. Quality 판정은 runtime의 `_pyramid_quality_decision`을 재사용한다. Strong-continuation은 후보 base threshold에 맞춰 effective minimum만 재계산하고 scout bridge 또는 runtime-prior가 실제 판정을 바꾼 episode는 독립 threshold 근거에서 제외한다.
- P2: 모든 threshold가 같은 complete parent episode 집합을 사용한다. 진입가는 최고가/임계값 가격/mark가 아니라 당시 기존 resolver의 관측 limit price이고, 종료가는 후행 observed sell price로 고정한다. 공통 `trade_profit` 비용률을 한 번 차감하고 추가 slippage는 넣지 않는다. Primary는 `source_quality_adjusted_ev_pct`; notional·수량 provenance가 없는 비교에는 `notional_weighted_ev_pct`를 만들지 않는다. 결과는 fixed-observed-exit source-only이며 인과적 실런타임 효과나 체결 보장을 주장하지 않는다.
- P3: exact comparable episode 0은 `source_quality_blocked`, 유효하되 candidate eligible episode 20 미만은 `hold_sample`, 비용 차감 후보 EV가 양수이면서 현재 대비 개선되는 한 단계만 `adjust_up/down`이다. Grid는 0.2~2.5%, PREOPEN 변경폭은 0.1%p이고 추천 env는 `SCALPING_PYRAMID_MIN_PROFIT_PCT` 하나뿐이다. Legacy peak/label/one-share grid는 진단 전용이다.
- P3 runtime scope: 공통 env를 NXT-only 자료로 변경하지 않도록 parent episode의 venue별 표본·EV를 함께 기록한다. 전체 parent floor 외에 child별 20건을 추가하지는 않지만, KRX 비교 근거가 전혀 없으면 `hold_runtime_scope:common_runtime_axis_krx_evidence_missing`으로 종결한다.
- P4: same-date direct candidate를 daily AI 입력에 병합하고 `quality_update_id + pyramid_fixed_exit_replay_v1 + SHA-256 evidence_digest`를 AI 결과와 PREOPEN 계약까지 보존한다. missing/reject/stale ID/version/hash, source 결손, 누적 scale-in owner 충돌은 env 생성을 차단한다. 새 cron/family/TP/holding/sizing/provider/bot/broker/hard-safety 권한은 추가하지 않았다.
- Review 보완: calibration consumer가 producer 표식을 그대로 신뢰하지 않도록 schema v5, event schema v2, source-only authority, fresh 평가시각 BBO, resolver BBO 일치, 허용된 passive-limit price source, resolver/order-price 동일성, 평가시각 venue/session을 독립 재검증한다. 종료 receipt는 파일 물리순서가 아니라 event timestamp상 최신 `sell_completed`를 사용한다. selected-only 평가일도 configured v2 threshold census에 포함하고, 구형 `min_profit_pct`는 진단값으로만 유지한다.
- 과거자료 판정: 2026-09-04 raw를 생산물 비변경 임시 경로에서 재생성한 결과 관측 gate event 2건, exact-ready 0건이었다. 두 건 모두 scout bridge owner와 겹치고 구형 로그에 fresh BBO/resolver 관측이 없어 `source_quality_blocked: threshold_replay_no_comparable_episodes`가 맞다. 구형 단일 1.1% 관측은 `legacy_unique_threshold_observation_no_runtime_authority`로 분류됐다. 이는 임계값 경제성 실패가 아니라 과거 exact 자료 결손이다.
- 런타임 판정: 코드 경로는 다음 자연 프로세스 기동 후부터 source-only 필드를 기록할 수 있다. 자연 postclose에서 valid eligible parent episode 20건, KRX parent 근거, 양의 next-step EV와 current 대비 개선, parsed same-ID/version/hash AI, PREOPEN 단일 scale-in owner를 모두 통과하기 전에는 env 적용이 없다. 이번 구현 작업은 봇 재기동, env 변경, 생산 리포트 덮어쓰기, 실주문을 수행하지 않았다.
- 검증: PYRAMID feedback/calibration/daily-AI/PREOPEN 430건과 보유·scale-in 1,023건, 합계 1,453건이 통과했다. Ruff, Black, 변경 모듈 `py_compile`, checklist parser 35건, `git diff --check`도 통과했으며 검토 범위 내 미해결 결함은 0건이다. pandas-ta의 pandas 4 deprecation warning 1건은 본 변경과 무관한 기존 경고다.
