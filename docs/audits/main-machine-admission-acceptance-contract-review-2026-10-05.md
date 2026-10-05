# Main 기계 진입 후보 수용조건 재점검 — 2026-10-05

## 1. 결론과 앞선 설명 정정

현재 비삼성 `pullback_p60_v0` 승계의 직접 원인은 **native 부분집합에서 기존 successor gate를 통과하지 못하고 새 독립 날짜가 없는 것**이다. 전체 연구의 개선은 현재 생성기에서도 재현된다. 앞선 실행 보고의32건17승 대3건1승을 전체 연구 후보의 성능으로 읽으면 잘못된 결론이 된다.

원천·규칙 손상이나 기계/보조 AI 혼합으로 개선이 사라진 것이 아니다. 연구의 최초 신호 사건·종목/날짜 동일 가중 비교와 운영 생성기의 scanner/fixed-watch 기회 비교가 다르다. 현재 계약을 적용한 incumbent 승계는 계산과 일치하지만, 새 admission 후보의 연구 근거를 운영 수용에 연결하는 계약은 별도 보완이 필요하다.

이번 범위는 수용조건 점검과 설명 정정이다. 현재 policy/loader/PREOPEN/selector, native 신원, 학습 날짜 및 원 보고서 bytes는 유지했다. 정책 선정조건 변경·실제 적용은 이번 산출물이 실행하지 않는다.

## 2. 기존 연구와 현재 계산의 대사

현재 [생성 보고서](../../data/report/ai_decision_action_outcome_calibration/winrate_policy_2026-10-02.json)의 `admission_analysis.groups.non_samsung`과 [고정 연구 비교](../../tmp/non-samsung-final-policy-decision-20261005/comparisons.json)를 대사했다. 고정 선택 합집합401개에서 날짜·종목·판정시각·raw SHA·부모/후보 행동·확정 이진 결과의 차이는0이다. 날짜별 주승률도 일치한다.

| 비교 계약 | 기존 | 후보 | 해석 |
| --- | ---: | ---: | --- |
| 연구 학습9/29·9/30 주승률 |42.59% |67.75% | 탐색 학습의 군집 동일 가중 결과 |
| 연구10/2 비교 주승률 |53.70% |75.00% | 이미 사용한 비교 날짜, pristine holdout 아님 |
| 전체3일 최초 신호 선택 |217개 |197개 | 종목/날짜/venue/session 사건 및 가상 점유 계약 |
| 전체3일 목표 / 손절 |80 /75 |93 /48 | 미도달·미확정 별도 |
| 전체3일 주승률 |45.75% |70.20% | 현재 nested 분석에서도 동일 |
| 최종 native 학습 기회 |32개 |3개 | scanner promotion 또는 fixed-watch admission/generation ID 필수 |
| 최종 native 학습 승리 |17개 |1개 | 서로 다른 작은 운영 부분집합 |
| 최종 native 학습 승률 |53.125% |33.333% | 연구 전체 우월성을 기각하는 비교가 아님 |

연구와 운영의 sample floor·coverage·지원조정 승률을 비교할 때 평가 단위를 명시해야 한다. 관측 군집 수를 scanner 승격 기회로 바꿔 적거나 두 종류의 표본을 합산하지 않는다.

45.75→70.20%는 각 정책이 선택한 서로 다른 집단의 관측 승률이다. 원 연구의 양쪽 경계확정 공통39군집은52.47→53.24%였고,10/2 미확정 승패 배정 민감도는 후보−부모-17.54~+41.23pp였다. 이 차이는 대상 선택 효과와 결과 결손의 영향을 함께 포함한다. 이번 대사는 기존 연구 수치의 재현을 확인하며, 새 독립 검증이나 실현 수익을 입증하지 않는다.

## 3. 6,550개가124개로 축소되는 경로

- 비삼성6,550관측 가운데 가격 순서·원 비용·원 stop을 결합한 목표/손절 확정은4,368개다.
- 확정4,368개 중4,244개(97.16%)는 `native_opportunity_identity_missing`으로 정식 비교에서 제외된다. 이들의 가격 승패를 결손/실패/0으로 바꾼 것은 아니다.
- 남는 native 확정은124개다:9/29 89개,9/30 18개,10/2 17개. 이 중 부모 ENTER32개, 후보 ENTER3개다. 후보3개는 모두9/29다.
- 연구의 첫 신호 선택과 ID를 직접 교차하면 부모217개 중 native0개, 후보197개 중 native1개다. 정식 생성기의 부모32개는 원 연구의 부모 첫 선택과 겹치지 않는다. 후보3개 중1개만 원 후보 첫 선택과 겹친다.
- 연구는 관측된 첫 신호·가상 점유를 사용한다. 생성기는 각 native 기회에 속한 적격 판정을 사용한다. 현재 작은 native 결과에는 대상 선택과 시점 선택이 함께 바뀐 효과가 들어 있다.

`opportunity_identity`는 scanner의 `scanner_promotion_id`, 또는 `MAIN_FIXED_WATCH`의 `watch_admission_id + watch_generation_id`를 요구한다. 관측/probe의 원 capture 신원과 native 기회 신원은 서로 다른 계약이다. 추가로 승격 ID를 합성해 위4,244개를 native로 만드는 것은 허용되지 않는다.

직접 코드: [분석의 전체 비교와 native 표시](../../src/engine/scalping/entry_admission_analysis.py:193), [native 필터](../../src/engine/scalping/ai_action_outcome_calibration.py:9670), [기회 신원](../../src/engine/scalping/postclose_entry_validation.py:66), [기회별 지표](../../src/engine/scalping/ai_action_outcome_calibration.py:9563).

## 4. 실제 수용조건과 통과 여부

| 조건 | 현재 native 후보 | 점검 판단 |
| --- | --- | --- |
| 학습 선택30기회 이상 |3개, FAIL | 기존 successor floor. 관측 선택197개와 다른 단위 |
| 학습 기존 대비 선택 기회50% 이상 |3/32=9.375%, FAIL | 선택 coverage이며 성공 보존율 아님. 좁은 유형 정책에 대한 일반 gate 적합성은 별도 검토 |
| 학습 raw 승률 개선 |33.33% 대53.125%, FAIL | native 부분집합 결과 |
| 학습 지원조정 승률+5pp |7.83% 대38.95%, FAIL | sample size를 반영한 별도 hurdle |
| 새 독립 날짜 | 없음, FAIL | recipe 탐색 종료일10/2 이후의 미소비 날짜만 holdout |
| 검증 선택10기회·승률/지원조정/coverage | 검증 날짜/표본 없음 | `not_observed`; 실패 수익으로 해석하지 않음 |
| publisher의 학습·검증 날짜 전부에 후보 선택 존재 | 후보 학습 날짜는9/29뿐 | publisher는 각 분할의 `source_dates == expected_dates`를 요구한다. 생성기 학습 검사인1날짜 이상과도 차이가 있어 계약 대사 필요 |
| 기존 성공100%·80% 보존 | 탈락 조건 없음 | 성공 제외량은 diagnostic. 복구하지 않음 |
| 양의 청산CF·AI 응답 존재 | 이번 수용 gate 없음 | 기계 진입 승률에 보조/청산 지표를 혼합하지 않음 |

생성기와 dated publisher 모두30/10·50%·raw 개선·지원조정+5pp·날짜 조건을 확인한다. 한쪽만 수정하면 발행 단계가 거절한다. [학습 후보 hurdle](../../src/engine/scalping/ai_action_outcome_calibration.py:9798), [후단 검증](../../src/engine/scalping/ai_action_outcome_calibration.py:9860), [publisher 재검증](../../src/engine/scalping/mechanistic_entry_runtime_policy.py:1508)을 함께 소유 범위로 봐야 한다.

현재 native 필수 조건은 `recipe_mode`에서 켜진다. 기존 VWAP veto successor와 새 RECHECK/ENTER 교체 admission 후보가 같은 최종 수용 함수를 사용한다. 연구 구현계획은 운영 family 요건을 별도 대사하도록 명시했으므로 새 독립 날짜 필요 자체가 뒤늦게 발견된 원천 결함은 아니다. 다만 현재 전 연결 결과를 ‘연구에서 더 나쁜 후보가 나왔다’로 보고하는 것은 부정확하다.

삼성005930은 이 recipe의 선택 대상 밖이다. 삼성 승계 사유에 비삼성3개 결과를 적용하지 않는다. 삼성은 별도 고정 후보의 이후 날짜 검증 owner가 유지된다.

## 5. 보완할 계약과 보고 방식

1. **연구 비교와 운영 자격의 별도 상태:** `observation_candidate_recommended`와 `native_promotion_hold`를 동시에 기록한다. 실제 어떤 집단/시점/기회 단위에서 개선 또는 미충족인지 표시한다.
2. **admission 후보용 수용 계약:** 고정 연구의 원 관측·첫 신호·비중복 선택·군집 주승률·원 비용/stop/경로·as-of/parent/hash를 정책 후보 비교에 어떻게 소비할지 명시한다. 기존 veto의 native 분모를 자동으로 동일시하지 않는다. 기존 native 검증을 관측 검증으로 대체하려면 producer·report·dated publisher·loader의 명시적 계약 변경으로 구현한다. 관측 결과는 실제 주문/체결/PnL 증거가 되지 않는다.
3. **sample/coverage 단위:**30/10·50%·+5pp의 역할과 적용 단위를 따로 선언한다. 동일 단위로 먼저 재대사하며 더 높은 승률의 좁은 유형 정책을 일반 coverage가 배제하는지는 별도 가설로 점검한다. 성공 보존 veto를 추가하거나 현재 검사에서 즉시 floor를 낮추지 않는다.
4. **새 날짜 검증:**9/29·9/30·10/2는 고정 학습/탐색 자료다. 수정된 계약에서도10/2를 fresh holdout으로 재라벨링하지 않는다.10/6 이후 자료로 고정 후보와 부모를 같은 계약에서 비교하고 만족하면 다음 유효일 선정 여부를 판단한다. 이는 이후 검증이며10/6 기동 전에 새 정책이 자동 선택된다는 약속이 아니다.
5. **계산/적격/선택 필드 분리:** 현재 `candidate_evaluated=bool(chosen)`이고 train gate에서 탈락하면 `candidate.train`이0/null로 채워진다. 실제3개 평가 지표는 `candidate_training_diagnostics`에 있다. `candidate_computed`, `candidate_train_qualified`, `candidate_selected`를 구분하는 report/schema 보완이 필요하다. 현재0을 ‘후보 미평가’ 또는 ‘유효 가격 패턴0’으로 요약하지 않는다. training diagnostic의 `metric_role=sim_probe_ev`도 Main winrate 역할과 대사할 대상이다.
6. **날짜 검사·성공 보존 diagnostic 일치:** publisher가 요구하는 후보의 학습 날짜 전부 포괄 조건을 생성기의 후보 진단에서도 명시해 앞단 통과/발행 거절의 차이를 없앤다. `retained_baseline_winning_attempt_count`는 현재 후보 승리 전체 수를 넣어1로 표시하지만, 부모 승리 trace와의 실제 교집합은0이다. 기존 성공 보존 diagnostic을 쓰려면 교집합으로 수정하고 새 성공을 별도 필드로 표시한다. 이 값은 탈락 gate가 아니므로 이번 승계 결과를 바꾸지는 않는다.

이 보완은 새로운 source 수집·임계치 탐색이나 기존 연구 재개와 별개다. source/as-of/route·future leakage·Main/Widget/Episode/manual custody·broker/account/order/quantity/cooldown/provider·hard guard 및 부모 CAS를 유지한다. 이번 점검은 새 운영 수용 계약을 발행하거나 승인하지 않는다.

## 6. 검증·근거

[대사 산출물](../../tmp/machine-admission-acceptance-review-20261005/acceptance-reconciliation.json): 원401선택의 identity/raw/action/binary 차이0, 날짜별 주승률 일치,4,368→124 분모 대사, 첫 신호/native 교차, 각 hurdle와 빈 holdout을 확인했다. 추가 비교의 `first_signal_mask_removed_same_observation_replay`는 첫 신호 mask를 제거한 기존 가상 점유 replay이고, `native_only_same_observation_replay`는 native로 제한한 같은 replay다. 이 두 비교를 실제 주문/실현 PnL로 표시하지 않는다.

원 보고서/고정 선택 파일 SHA 보존, 가격 원천3개·계산 kernel8개 manifest 일치, 현재/10/6 준비 정책 hash 보존, 로컬 링크·현재 단일 소유 기록·diff·print-only parser를 확인해 [검증 기록](../../tmp/machine-admission-acceptance-review-20261005/validation.json)에 남겼다. 기존 선택 릴리스의 read-only10/6 `current_full_contract` 재검증은 PASS/findings0이며 실제 PID 소비 증거는 아니다.

Python 변경 없이 점검·문서 리뷰와 보완을 수행했다. 거래 pytest/프로토콜 호출/전체 장후 재생성·배포·재기동은 실행하지 않았다. 새 admission 수용 계약, 계산/선정 상태 표시, 날짜 검사 및 성공 보존 diagnostic의 코드 보완은 후속 구현 대상으로 남으며 이번 리뷰에서 수정 완료를 주장하지 않는다.
