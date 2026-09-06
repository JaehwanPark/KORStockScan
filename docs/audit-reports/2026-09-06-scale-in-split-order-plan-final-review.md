# Scale-in split order plan 최종 보완·리뷰 (2026-09-06)

> 최종 판정: **F1~F7 보완·재리뷰 완료 / 검토 범위 미해결 코드 결함 0건 / 자연 실행·실제 효과 미확인**. 현재 기록은 §6이 우선한다. §1~§4는 이전 구현, §5는 이를 재개방한 결함 기록이다. 이전 910 PASS를 실제 runtime 적용·수익 개선 근거로 사용하지 않는다. 완료 기록은 `ScaleInSplitFinalReviewRepair0907`, 자연 실행 OPEN owner는 `ScaleInSplitNaturalEvidence0907`이다.

## 1. 최종 판정

- 목적은 `position_sizing_dynamic_formula`가 정한 AVG_DOWN 추가매수 총수량을 바꾸지 않고, 해당 수량의 주문 형태만 2개 또는 조건부 3개 leg로 나눠 비용 차감 순이익·체결 참여율·하방을 개선하는 것이다.
- `scalping_avg_down_recovery_calibration`은 AVG_DOWN 실행 여부/pressure 기준을 조정하고, 이 family는 이미 산출된 수량의 실행 형태만 조정하므로 중복 튜닝축이 아니다.
- 생산자와 POSTCLOSE→daily threshold→PREOPEN env/policy→runtime allocator 연결은 자동화되어 있다. 다만 현재 clean evidence에는 적용 가능한 실제 qty>=2 AVG_DOWN 시도가 없으므로 runtime은 정상적으로 OFF다.
- 조건은 rolling 고유 시도 3건이라는 낮은 초기 floor를 사용하되, 같은 3건에 exact terminal outcome과 MFE/MAE가 있어야 하고 비용 차감 EV>0, modeled fill participation>=70%, price join>=80%, downside p10 delta>=-0.30%를 동시에 요구한다. 단순 event 수나 touch 비율만으로 승격되지 않는다.

## 2. 보완한 결함

1. 실제 outcome/MFE-MAE 표본을 항상 0으로 기록해 runtime gate가 영구 도달 불가능하던 생산자 결함을 고쳤다. 제출·체결·terminal SELL receipt를 record/order identity로 결합해 실제 비용 차감 counterfactual을 계산한다.
2. 이벤트 행 수를 표본 수로 사용하던 결함을 고쳤다. 동일 주문의 summary/receipt를 고유 attempt로 중복 제거하고, 기준시점 이전 가격과 다음 AVG_DOWN 시도 이후 가격을 현재 시도의 MFE/MAE에서 제외한다.
3. daily 3행만으로 승격될 수 있던 결함을 고쳤다. clean-baseline 이후 source-quality-pass인 최신 20개 report date의 v2 artifact만 rolling 입력으로 사용한다.
4. 구조 후보에 경제성이 없어도 runtime candidate처럼 보이던 계약을 고쳤다. 비용 차감 EV, fill participation, downside, outcome/MFE-MAE, price coverage를 모두 통과한 context bucket만 policy `buckets`에 기록한다.
5. 미관측 context가 default split으로 실행될 수 있던 경로를 제거했다. 런타임은 명시적으로 승인된 context bucket만 분할하고 그 외에는 원 주문 1건을 그대로 반환한다.
6. 표본 부족과 경제성 부재를 분리했다. `hold_sample`은 fresh하고 이미 검증된 직전 policy만 이월할 수 있지만, source-quality 결손 또는 현재 negative-economic blocker가 있으면 이월하지 않는다. `hold_no_edge`는 자동 해제한다.
7. 무표본일에도 전체 대용량 JSON을 역직렬화하던 비용을 줄였다. binary presence precheck가 실제 AVG_DOWN 제출 anchor가 없는 날을 먼저 닫고, 2026-09-04 읽기 전용 측정은 약 29.7초에서 6.9~7.3초·약 36MB로 줄었다.
8. touch heuristic 하나만 평가해 더 나은 기존 2-leg variant를 놓치고, gate를 통과한 3-leg가 2-leg보다 EV가 낮아도 우선되던 선택 결함을 고쳤다. touch는 기존 variant grid의 seed로만 쓰며 2-leg는 비용 차감 EV→fill participation→downside 순으로 최선을 고른다. 3-leg는 runtime contract를 통과하고 최선 2-leg보다 비용 차감 EV가 엄격히 높을 때만 대체한다.
9. v2 policy의 child shape와 파일 내용이 env 선택 이후 바뀌어도 실행될 수 있던 계약 결손을 고쳤다. PREOPEN과 runtime 모두 허용 variant별 leg/weight/offset의 정확한 shape, env의 policy version, 생성 policy의 content hash를 재검증한다.

## 3. 권한·자동화 경계

- POSTCLOSE wrapper의 producer 기본값은 ON이며 report/Markdown/policy artifact를 생성한다.
- daily threshold report는 rolling exact-attempt 경제성을 calibration state로 변환하고, PREOPEN selector는 strict v2 policy/economic/freshness contract를 다시 검증한다.
- 선택된 policy도 runtime allocator에서 `AVG_DOWN`, qty>=2, fresh v2 policy, 승인 context, 수량보존을 모두 재검증한다.
- initial entry, PYRAMID, requested quantity, cap, provider, bot, broker/account/order/cooldown, stale quote 및 hard/protect/emergency safety는 변경하지 않는다.
- 이번 작업은 bot 재기동, runtime env 수동 적용, 실주문, 산출물 write 재생성을 수행하지 않았다.

## 4. 검증

- 관련 producer/daily/EV/PREOPEN/runtime summary/wrapper/verifier/workorder 회귀: **910 passed**.
- 현재 2026-09-04 최종 읽기 전용 판정: schema v2, `read_mode=avg_down_attempt_presence_precheck`, `daily_unique_attempt_count=0`, `rolling_eligible_runtime_attempt_count=0`, `runtime_apply_allowed=false`, 7.32초·약 36MB.
- 최종 남은 코드 finding: 0건. 실제 체결 개선 효과는 다음 자연 qty>=2 AVG_DOWN 시도 이후 R6 post-apply attribution으로만 확정한다.

## 5. 목적·자동화·조건 달성 가능성 재점검

### 5.1 현재 판정과 확인 범위

- 총수량을 보존하면서 AVG_DOWN 체결 형태의 비용 차감 증분 순이익을 개선한다는 목적은 타당하다. 기존 AVG_DOWN 실행 여부/pressure 보정과 조작 지점이 다르므로 family 전체를 통폐합할 근거는 없다.
- 장후 producer 기본 ON, daily threshold, deterministic PREOPEN handoff, runtime allocator 호출은 코드로 연결되어 있다. 다만 아래 결함 때문에 적용 조건 충족과 적용 후 효과 검증이 완결됐다고 판정할 수 없다.
- 디스크의 해당 report는 42개 모두 v1이다. 이전 v2 결과는 메모리 내 읽기 전용 계산이었다. 2026-09-04/09-07 runtime env manifest에는 해당 family 선택과 env override가 없다. 실제 실행 PID의 v2 소비는 이번 리뷰의 확인 근거에 포함하지 않는다.
- 최근 20개 저장 report 중 AVG_DOWN 관측이 있는 날짜는 2026-08-21뿐이며, 해당 날짜 압축 raw의 실제 제출은 `record_id=34213`, `submitted_qty=1`, `submitted_leg_count=1`이다. 분할 가능 qty>=2 시도의 축적 속도는 현재 근거로 입증되지 않았다. v1을 v2 경제성 근거로 직접 승격하는 것은 금지하며 필요한 과거 raw만 재검증해야 한다.
- 이번 재점검은 코드·원천·산출물 읽기, 메모리 내 실패 사례 재현, 관련 기존 테스트 실행으로 수행했다. 매매 코드나 runtime env는 변경하지 않았다.

### 5.2 재현된 결함 및 수용 조건

1. **F1 / P1 — 정상 매도 주문번호가 청산 결합을 차단한다.** `scale_in_split_order_plan._event_matches_anchor`는 양쪽 order ID가 있으면 교집합으로 즉시 반환한다. 실제 `sniper_execution_receipts`의 최종 SELL에는 별도 매도 `order_no`가 있다. 같은 record의 fixture에 `order_no=SELL1`만 추가하면 `real_outcome_joined=True -> False`, terminal price가 사라진다. 매수 receipt는 매수 주문, 최종 청산은 검증된 position/record lifecycle로 결합하는 stage별 계약이 필요하다. 수용 조건: 다른 BUY/SELL 주문번호의 정상 한 lifecycle은 1건으로 결합하고 다른 record/종목·상충 receipt는 배제한다.
2. **F2 / P1 — 체결 재현이 실제 leg 유효시간을 초과한다.** runtime `_decorate_scale_in_split_leg_ttls`는 scalping에 base 20초와 배수 0.5/1/2를 적용한다. 2-leg는 10/20초, 3-leg는 10/20/40초인데 보고서의 `COUNTERFACTUAL_WINDOW_SEC=180` 및 최저가 비교는 이 유효시간을 적용하지 않는다. 170초에만 할인 가격에 도달한 3개 fixture가 fill=100%, EV=+0.149%p, runtime allowed로 통과했다. 체결 판정은 leg별 제출→유효기간→취소/청산 시계와 검증된 가격 자료를 재현해야 한다. MFE/MAE 관찰 창은 체결 허용 창과 별도로 유지한다. 수용 조건: 만료 후 touch는 체결로 계산되지 않고 참여율·놓친 이익에 반영된다.
3. **F3 / P1 — 적용한 정책을 그 정책의 개선된 실제 체결가와 재비교한다.** `_evaluate_candidate_economics`는 기준 PnL에 `actual_fill_price`를 쓴다. 동일 50:50 정책에서 unsplit 평균가 10,000원은 +0.149%p/allowed였으나 실제 split 평균가 9,985원으로 바꾸면 -0.001%p/blocked가 됐다. 반올림 오차 이전에도 동일 정책 대비 증분은 0으로 수렴한다. 비분할 control과 현재 적용 정책을 같은 가격 경로에서 재현하고, 신규 변경 승인과 현 정책 유지 판정을 분리해야 한다. `post_apply_attribution`의 fill/cancel/MFE/MAE delta는 현재 이름 선언만 있고 해당 값의 policy-version별 산출이 없다. 수용 조건: 이미 개선 중인 정책이 자기 비교 때문에 해제되지 않으며 실제 악화는 policy-version별 R6 결과로 식별된다.
4. **F4 / P2 — 무표본을 음의 경제성으로 처리한다.** EV/fill/downside가 None인 무표본 후보에 negative-economic blocker가 붙고 PREOPEN `_scale_in_split_hold_carry_forward_blockers`가 이를 악화로 해석한다. 재현 결과는 `scale_in_split_negative_economic_evidence`였다. 표본 부족/결측과 실제 관측된 비양수 EV·하방 악화를 구분해야 한다. 수용 조건: 순수 `hold_sample`은 기존 freshness 한도 내 검증 policy를 이월하고, 유효한 악화 증거 또는 source-quality 실패는 이월하지 않는다.
5. **F5 / P1 — 같은 표본 집합과 누적 창을 검증하지 않는다.** outcome 3건·MFE/MAE 4건·eligible 5건으로 price coverage=80%를 만들되 실제 두 조건의 교집합은 2건인 입력도 runtime allowed였다. 경제성 loop가 계산한 행 수를 floor로 검사하지 않는다. 과거 날짜가 전혀 없는 당일 3건만으로도 allowed여서 daily-only 금지 설명과 다르다. 수용 조건: valid paired economic row가 실제 3건 이상이며 적어도 과거 날짜 또는 정식 post-apply version window 확인이 있어야 한다. 매수 receipt 한 건만 남겨도 MFE/MAE joined가 True인 현 계측도 관찰 완료와 분리한다.
6. **F6 / P2 — 시장가 분할은 적용 불가능한 후보로 남아 있다.** market anchor는 receipt/outcome 계산 전 조기 반환하여 outcome=0이고, 시장가 3건을 넣어도 `market_qty_split_only`는 계속 차단된다. 동일 기준가격을 두 시장가 주문으로 나누는 모델에는 양의 증분 EV를 만드는 근거도 없다. 시장가 자동승격 후보를 제거하고 원 주문 유지/명시적 not-applicable 처리하는 방향을 권고한다. 3-leg는 최근 수집량에서 20건 달성 근거가 없으므로 runtime 후보 제외 또는 명시적 진단 전용으로 정리하고 2-leg 수정을 우선한다.
7. **F7 / P2 — false인 lineage도 rising-missed로 분류한다.** `_context_bucket`은 `str(fields)` 전체에서 문자열을 찾기 때문에 `rising_missed_scout=False`라는 key만 있어도 rising-missed로 분류한다. 재현 결과는 `scalping:late_loss_retry:rising_missed`였다. 생산자와 runtime은 명시적 flag와 검증된 원천 값의 같은 정규화 계약을 공유해야 한다. 수용 조건: False/미관측은 normal, 검증된 True만 rising-missed이고 동일 컨텍스트의 report/runtime bucket이 일치한다.

### 5.3 적용 조건 유지·보완·제거 권고

| 조건 | 판정 | 권고 |
| --- | --- | --- |
| qty>=2 | 분할의 물리적 최소 조건 | 유지. 표본을 만들기 위한 수량 증가는 금지한다. |
| 비용 차감 증분 EV>0 | 신규 변경의 목적과 부합 | 유지하되 fixed control 대비 증분으로 정정하고, 이미 적용된 동일 정책 유지에 재사용하지 않는다. 이 값은 최저 수익률 1.1% 같은 목표 수익률 허들이 아니다. |
| rolling 3건 | 숫자 자체가 과도하다는 근거 없음 | 실제 paired row와 과거 날짜/version window를 검증한다. 현재 당일-only 및 2건 우회부터 수정한다. |
| fill>=70% / price join>=80% / p10>=-0.30% | 임시 guard 값이며 합리성이 실증된 상태는 아님 | 실제 TTL·교집합·측정 단위를 고친 후 민감도를 확인한다. qty=2에서는 1주 체결이 50%, qty=3에서는 2주가 66.7%여서 정수수량에 따른 일률 차단도 검토한다. |
| 3-leg 20건+touch 사전조건 | 현 자연 표본 속도에서 달성 가능성 입증 안 됨 | floor를 낮춰 강제 승격하지 말고 runtime 후보 제외/진단 전용 정리를 우선 검토한다. |
| 시장가 분할 양의 EV 승격 | 현 구조에서는 도달 불가능 | 승격 경로를 제거하고 명시적 not-applicable로 종결하는 방향을 권고한다. |
| 무표본 negative-economic 차단 | 부당한 해제 조건 | 결측 판정으로 보완하고 기존 freshness/source-quality 제한을 적용한다. |

### 5.4 검증 및 다음 작업

- 기존 focused 회귀: `test_scale_in_split_order_plan.py` 및 `test_threshold_cycle_preopen_apply.py`의 scale-in/split audit 선택 실행 **45 PASS / 227 deselected**. 이 통과와 별개로 F1~F7의 결함을 코드 대조 및 메모리 재현으로 확인했다.
- 수리 순서: 실제 SELL 결합·leg TTL(F1/F2) → 고정 control·R6·결측 분리(F3/F4) → 유효 paired 분모·window(F5) → 시장가/3-leg 정리·lineage 일치(F6/F7) → 생산자 형식의 통합 회귀와 제한된 v2 재검증.
- 구현 미완료 owner: 현재 checklist의 `ScaleInSplitFinalReviewRepair0907`. 기존 `ScaleInSplitNaturalEvidence0907`은 수리·회귀 완료 후 실제 자연 실행 확인 단계로 유지한다.
- 현재 결론은 **목적 타당 / 자동화 호출 연결 존재 / 경제성·조건·R6 결함으로 runtime 준비 불충분**이다. 이전 §4의 미해결 0건 및 일괄 합리성 판정은 이번 재검토로 대체한다.

## 6. F1~F7 구현 및 반복 리뷰

### 6.1 변경과 수용 조건

- F1: BUY receipt는 매수 주문+execution 번호로, terminal SELL은 같은 종목·position record로 결합한다. 서로 다른 BUY/SELL 주문번호를 정상 fixture 기본형으로 변경했다. 상충 중복 체결/청산, execution 번호 누락, overfill, 청산 이후 매수 receipt는 경제성에서 제외한다.
- F2: runtime의 기존 TTL 계산을 `src/trading/order/split_execution_math.py`의 순수 함수로 공유했다. 기존 scalping 2-leg 10/20초를 변경하지 않고 replay가 이를 소비한다. 20초 경계/170초 뒤 touch는 만료된 두 번째 leg의 체결이 아니다. 180초 관찰 창은 별도 진단이다. 자체 fill receipt만으로 가격 경로를 만들지 않으며 짧은 미해결 경로는 표본 없음으로 처리한다.
- F3: 동일 anchor의 비분할 20초 control·동일 관측 청산가를 고정 기준으로 사용한다. 실제 split의 개선된 평균가는 control을 바꾸지 않는다. 실제 submit 요약에 policy version/variant/original qty/final price를 추가했고 R6는 버전별 full-fill 실제 비용 차감 증분 EV·fill/MFE/MAE·missed-upside를 계산한다. partial/unfilled는 별도 집계한다. 실제 cancel delta는 정확한 cancellation receipt join이 없어 `not_measured`로 명시하고 자동 rollback 조건에서 제외했다. 모델 cancel delta는 paired rows에 계산한다. 버전 provenance 누락은 source-only workorder로 연결한다.
- F4: None EV/fill/p10에 negative blocker를 붙이지 않는다. daily calibration부터 paired sample/date 부족을 `hold_sample`로 분류한다. 기존 검증 v3 policy의 freshness·source-quality·same-stage 조건을 통과한 이월만 허용한다. 관측된 악화 및 표본·날짜를 충족한 R6 음의 EV는 이월하지 않는다.
- F5: 실제 계산된 paired row>=3 및 source date>=2를 producer/daily/PREOPEN/runtime 공통 계약으로 검증한다. 서로 다른 집합의 outcome/MFE count만으로 통과하지 못한다. canonical submit 중복 제거를 context 분류보다 먼저 수행한다. 부분 leg 제출 실패는 원래 요청수량과 구분해 정상 full-fill로 세지 않는다.
- F6: 시장가 분할 자동승격/runtime 허용 shape를 제거했다. 시장가는 원 주문 유지/not-applicable이고 3-leg는 진단 전용이다. 달성 근거 없는 20건 floor를 낮춰 runtime을 열지 않는다.
- F7: 문자열 전체 검색 대신 명시적 boolean·원천 값과 중첩 fields의 동일 정규화를 사용한다. False/0/"false"는 normal, True는 rising-missed다.

### 6.2 조건과 기대효과 최종 해석

- 목적은 새 튜닝축 추가가 아닌 기존 AVG_DOWN 2-leg 실행형태의 순비용 증분 EV 개선이다. AVG_DOWN 실행 여부/pressure·수량 산정·entry/PYRAMID와 소유권이 겹치지 않는다.
- report/policy v3·`ttl_paired_fixed_control_v3`로 계약을 올렸고 기존 v1/v2는 자동승격 근거에서 제외한다. POSTCLOSE producer→daily calibration→PREOPEN policy/env→runtime allocator 연결을 유지하며 조건 충족 시 기존 자동화가 처리한다. 이번 작업은 bot restart·runtime env 적용·실주문·운영 report write 재생성을 하지 않았다.
- 3 paired/2 source dates는 최소한의 누적 근거다. 2주 수량의 두 leg가 20초 안에 관측되면 기존 70% fill·80% join·양의 증분 EV·p10 guard를 통과하는 통합 fixture로 도달 가능성을 확인한다. 반면 2주에서 한 leg만 체결되면 50%여서 70% guard에 막힌다. 이것은 현재 보수적 참여율 guard이며 최적값이 실증됐다는 뜻은 아니다. 자연 표본 없는 상태에서 수량/guard를 완화하지 않는다.
- 이 replay는 sampled market-touch/full-leg 가정과 동일 terminal을 사용한 실행형태 비교다. 독립 시장 충격·queue/부분체결·AI 청산 경로 재현이나 실제 수익 개선 증거가 아니다. 실제 효과는 자연 체결 뒤 R6로 확인해야 한다.

### 6.3 검증과 운영 상태

- 반복 리뷰에서 nested lineage, 부분 제출과 원 요청수량 혼동, 상충 terminal, daily의 잘못된 표본 분모를 추가 발견해 즉시 보완했다.
- 최종 통합 회귀 **943 PASS**: `test_scale_in_split_order_plan`, `test_split_execution_math`, `test_threshold_cycle_preopen_apply`, `test_daily_threshold_cycle_report`, `test_threshold_cycle_ev_report`, `test_build_code_improvement_workorder`, `test_runtime_approval_summary`, `test_threshold_cycle_wrappers`, `test_verify_threshold_cycle_postclose_chain`. Ruff F821/F822/F823/F841, Python compile, `git diff --check` 통과. Checklist parser는 43개 OPEN 항목을 인식하고 이 구현 완료 기록을 OPEN에서 제외했다. 외부 Project/Calendar sync는 실행하지 않았다.
- 최종 2026-09-04 **읽기 전용** 계산: schema v3, daily unique=0, rolling eligible=0, paired=0, source dates=0, runtime allowed=false. EV/fill/p10은 None이고 negative-economic blocker는 없다. 과거 선택 19일은 v3 계약 불일치로 제외했다. 소요 6.86초·최대 RSS 약 36.4MB. 디스크 report/policy 또는 env를 갱신한 결과가 아니다.
- 자연 실행 확인은 `ScaleInSplitNaturalEvidence0907`로 유지한다. qty>=2 실제 대상 부재는 `not_observed`이며 성공·실패 또는 강제 완화 근거가 아니다. 코드 검증 완료와 PID 소비·수익 효과 검증은 분리한다.
