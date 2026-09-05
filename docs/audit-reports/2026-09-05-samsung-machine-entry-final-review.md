# Samsung machine entry tuning 최종 목적·자동화·달성 가능성 리뷰

현재 구현 결과는 §7을 따른다. §1–6은 보완 전 발견사항과 당시 판정의 보존 기록이다.

검토일: 2026-09-05 KST. 원천 기준일: 2026-09-04. 판정: **최종 통과 보류 — 전략 목적 불일치와 판정/근거 결함이 남아 있다.**

## 1. 검토 범위와 결론

현재 작업 트리의 Samsung report v8, candidate/applied v2, 실제 morning/midday/afternoon 및 morning reentry 정책, 공통 진입 타이밍 consumer와 설치된 systemd 연결을 검토했다. 기존 변경을 되돌리거나 전략 코드, 운영 보고서, 후보/applied 파일, env, lock, 주문, 봇 상태를 변경하지 않았다. 이번 변경은 이 검토 기록과 일일 체크리스트뿐이다.

사용자의 핵심 목표는 무조건 매수가 아니라 상승·반등을 확인하는 진입을 통해 비용 차감 EV와 순이익을 높이는 것이다. 현재 구현은 후일 청산/수동손실 보존과 근거 hash 결속은 개선했지만, Samsung tuner 자체는 morning을 고정하고 midday/afternoon의 하락폭·저점 근접도만 강화한다. **성과 집계 보완과 상승·반등 전략 구현은 동일하지 않다.**

| 검토축 | 판정 | 근거 |
| --- | --- | --- |
| 목적 부합성 | 불충분 | 기본 morning은 시가 아래 예약 지정가, midday/afternoon은 하락폭과 저점 근접 조건이다. 반등 확인은 필수가 아니다. |
| 자동화 연결 | 존재 | 장후 wrapper → candidate → exact-date apply → 서비스 policy loader → signal features/장후 귀속 경로가 있다. |
| 개선값 실적용 | 미확인, 현재 0건 | 운영 candidate 18개와 applied 18개 모두 mutation이 없다. 최신 운영 candidate는 여전히 v1이다. |
| 현 후보의 개선 가능성 | 근거 없음 | near-low 0.10은 현행과 같은 표본/성과, drawdown 1.50은 표본 0이다. |
| 적용 허들 | 일부 재설계 필요 | 현행 EV 양수 선행 veto, 희소 신호에 대한 고정 10일 표본창, 불완전한 달성 ETA가 문제다. 모든 guard를 완화할 사안은 아니다. |

## 2. 재계산 결과

`samsung_machine_entry_tuning.build_report()`를 직접 호출해 9월 4일 결과를 메모리에서만 재계산했다. canonical JSON/Markdown과 정책 파일은 덮어쓰지 않았다. 최근 정책 cohort 기준이며 target/quantity가 다른 과거 세대는 합산하지 않았다.

| 머신 | 종결 에피소드 | broker 가격 확인 청산 leg | 보고서 EV | 실체결가 기반 비용 차감 추정 순손익 | 판정 |
| --- | ---: | ---: | ---: | ---: | --- |
| Morning | 6 | 6 | -0.702311% | -215,750원 | 손실 확인. tuner는 baseline-only여서 개선 정책을 만들지 않음 |
| Morning reentry | 1 | 2 | +0.357103% | +19,230원 | 표본 부족, 현재 gate는 source-quality blocked. 고정 정책 관찰 전용 |
| Midday | 1 | 0 | 0.000000% | 0원 | 청산 실적 없음. 성공/양의 EV 근거가 아님 |
| Afternoon | 2 | 4 | +0.257972% | +39,560원 | 양의 초기 실적이나 후보의 추가 개선 근거는 없음 |

주의: 종결 에피소드는 무체결 종료를 포함할 수 있다. 위 EV는 현재 구현이 사용한 `broker 순손익 / 시도한 주문금액`이고 체결금액 가중 EV와 같지 않다. 순손익도 broker 체결가에 고정 왕복 비용 0.20%를 차감한 추정치이지 정확한 수수료·세금 정산액이 아니다. 열린 포지션의 미실현손익을 섞지 않았다.

수동손실을 포함한 outcome amendment ledger는 20건, status=pass로 재구성됐다. 후보 재계산 결과 `policy_mutations=[]`다.

| 후보축 | Midday | Afternoon | 의미 |
| --- | --- | --- | --- |
| near-low 0.20 → 0.10 | 현행 표본 100% 유지, EV/순손익 동일 | 현행 표본 100% 유지, EV/순손익 동일 | 현 표본에서 행동·경제성 차이가 없다. 최소 uplift 0.005%p를 낮춰도 새로운 개선 근거가 생기지 않는다. |
| drawdown 1.25 → 1.50 | 종결 0, broker 청산 0 | 종결 0, broker 청산 0 | 현재 입력에서 후보 성과가 없다. 기다리면 반드시 생긴다는 근거는 없다. |

## 3. 미해결 findings

### F1 / P1 — 상승·반등 확인이 기본 진입의 필수 조건이 아니다

- [midday policy](../../src/trading/samsung_midday_one_share/policy.py), [afternoon policy](../../src/trading/samsung_afternoon_one_share/policy.py)의 `evaluate()`는 `drawdown >= threshold`와 `near_low <= threshold`를 확인하지만 저점 이탈 중단, 가격 회복, 추세 전환을 확인하지 않는다.
- 연속 30개 하락봉으로 두 `evaluate()`를 호출했을 때 모두 신호를 반환했다. 이는 신호 생성 반례이며 broker 주문을 실행한 결과는 아니다. 후단 market-weakness/account/liquidity/velocity/broker guard는 별도로 남아 있다. 거래량·체결속도 guard를 통과하는 것 자체가 상승 확인은 아니다.
- [morning policy](../../src/trading/samsung_morning_one_share/policy.py)의 기본 episode는 시가 아래 가격으로 주문을 계획한다. ‘아무 가격에 시장가 매수’는 아니지만 반등 전 저가 체결이 가능하다.
- 같은 파일의 morning reentry에는 setup 저점 유지와 1 tick reclaim 확인이 이미 존재한다. 그러나 이 고정 재진입 정책은 tuner의 신규 자동 개선축이 아니다.
- 별도 entry timing의 동적 확인 코드는 존재하지만 9월 4일과 9월 7일 applied의 `scopes={}`이며 다음 거래일 resolver도 `baseline_immediate`다. 따라서 이것을 현재 Samsung 전체의 반등 필수 확인으로 볼 수 없다.

보완 방향: 하락·저점 근접은 setup, 상승/반등은 confirmation으로 역할을 분리하고 기존 timing owner와 통합한다. 가격 회복/저점 유지/체결 뒷받침 중 무엇을 필수로 할지는 exact-route 원천으로 비교해야 한다. 단순히 모든 확인 조건을 AND로 추가해서 주문을 고갈시키지 않는다. 기존 timing fallback을 실제 매수 금지로 바꾸는 것은 전략 권한 변경이므로 이번 리뷰에서 시행하지 않았다.

### F2 / P1 — 현행 신호 subset은 변경 정책의 전체 행동을 재현하지 않는다

- [tuner `_axis_observations()`](../../src/engine/monitoring/samsung_machine_entry_tuning.py)는 이미 발생한 진입 신호의 당시 feature로 subset을 만든다. 신규 신호 시점·가격·5-bar 유효기간·체결·후속 기회를 재생하지 않는다. 코드도 `tightening_subset_only_not_a_relaxation_backtest`라고 명시한다.
- 현행 최초 신호를 강화 정책이 거절해도 같은 scan window의 더 늦은 봉에서 다시 신호가 발생할 수 있다. 해당 경로의 가격과 손익은 현행 subset에서 알 수 없다.
- 상승·반등 확인을 추가했을 때의 체결률, 상승 후 미체결, 늦은 재진입, 다음 기회 확보 효과 역시 현재 보고서만으로 입증할 수 없다.

보완 방향: 현행/후보를 같은 시간순 기회에서 비교하고 각 정책의 최초 신호와 후속 기회를 재현한다. 기존 원천으로 재현 불가능한 부분은 결손으로 명시한다. subset은 진단/가설 근거로 유지하되 완전한 runtime 개선 증거로 승격하지 않는다. replay의 가상 체결도 실제 broker 실행품질과 구분한다.

### F3 / P1 — 현행 EV가 음수이면 양의 개선 후보도 평가 진입이 차단된다

- `_aggregate_rows()`는 현행 equal-weight EV가 0 이하이면 `hold_non_positive_ev`, `build_policy_candidate()`는 현행 gate가 `auto_bounded_candidate_ready`여야 tightening 후보를 평가한다.
- 통제 반례: 현행 EV -0.10%, 후보 +0.10%, 표본·rolling·순이익 개선 요건을 만족하는 fixture에서 현행 gate만 `hold_non_positive_ev`이면 mutation 0건이다. 나머지 값은 유지하고 gate만 ready로 바꾸면 단일축 후보가 선택된다.

보완 방향: 현행 성과의 부호는 비교 기준/진단으로 남기고, 후보 자체의 양의 비용 차감 EV·현행 대비 순기여 개선·유효 표본·source quality를 판정한다. 손실 정책 개선을 막는 현행 양수 선행 veto는 제거 검토 대상이다. equal-weight 진단값과 notional 주지표의 역할도 일치시킨다.

### F4 / P1 — 희소 신호의 고정 시간창과 유지 분기가 영구 대기로 이어질 수 있다

- 누적 8회·broker leg 8개 외에 rolling 10거래일 종결 4회와 양의 uplift를 요구한다. Midday 관찰 15일/시도 1회/가격 확인 청산 0개에 같은 속도를 대입하면 10일 기대 시도 약 0.67회다. 현재 표본으로 달성 시기를 보장할 수 없다.
- 보고서의 예상 잔여 105일(midday), 22일(afternoon)은 시도 횟수로 계산한다. broker 청산 floor나 10일창 4회 달성을 추정한 수치가 아니다. Afternoon도 시도 3회와 종결 2회가 다르다.
- 한 축을 강화한 뒤에는 `carry_forward_single_active_axis_post_apply_observation`에 머물며, 음수 성과에 의한 환원도 종결/가격 확인 4개가 필요하다. 강화 후 신호가 사라지면 그 성과 표본도 생산되지 않는다.

보완 방향: 무신호, 유효 신호 미체결, source 결손, 표본 미성숙, 후보와 현행 행동 동일을 분리한다. 희소 머신은 동일 정책 누적/최근 유효 episode 창과 달력일 freshness를 조합하는 설계를 검토한다. 8회 숫자를 임의로 낮추는 것이 우선이 아니다. 무신호가 지속되는 시험의 평가 종료와 승인된 bounded 환원 계약을 별도로 설계한다. 자연 신호 0건을 즉시 코드 결함으로 단정하거나 임의로 머신을 OFF하지 않는다.

### F5 / P1 — 롤백 근거가 실제 적용 정책과 결속되지 않는다

- `build_policy_candidate()`의 rollback은 직전 candidate 정책에서 active axis를 찾지만 post-apply summary가 그 정책에서 나온 것인지 확인하지 않는다. PREOPEN consumer도 직전 candidate와의 lineage 및 동일 builder 재계산을 확인하므로 이 의미 오류 자체는 해결하지 못한다.
- 통제 반례: 실제 보고서 post-apply cohort drawdown=1.25, prior candidate drawdown=1.50, post-apply summary를 음수/4회로 설정하면 1.50→1.25 rollback을 생성했다. `validate_candidate(candidate, source_report=report)`도 `(True, 'valid')`였다. 이 반례로 canonical 정책을 쓰거나 broker를 호출하지 않았다.

보완 방향: candidate가 아니라 실제 적용 정책·적용 구간·머신별 설정을 post-apply 원천과 결속하고, 동일 버전 재적용도 별도 적용 episode로 구분한다. 잘못된 cohort의 손익은 mutation/rollback 근거가 될 수 없어야 한다. hash가 일치하는 것과 경제 근거가 해당 정책에서 생산된 것은 별도 검증이다.

### F6 / P2 — 다른 머신의 변경이 무관한 머신 표본을 분리한다

- [정책 loader](../../src/trading/order/samsung_entry_policy.py)의 `load_applied_machine_policy()`는 선택 머신 정책과 함께 전체 3개 머신 정책 hash를 반환한다. `_policy_cohort_contract()`는 이 전체 hash를 각 머신 cohort ID에 넣는다.
- Midday만 바꾸어도 전체 hash가 변하므로 변하지 않은 morning/afternoon까지 다른 cohort로 분리된다. 드문 신호에서 불필요한 표본 재축적이 발생한다.

보완 방향: 전체 artifact hash는 무결성/provenance로 보존하고, 성과 cohort는 실제 해당 머신에 영향을 준 entry·timing·target·quantity 설정과 적용 구간으로 구성한다. 무관한 머신 변화로 표본을 버리지 않는다.

### F7 / P1 — 과거 기준일 재생성에 미래 청산 receipt가 들어간다

- `_apply_broker_receipt_amendments()`는 owner/entry date/symbol/status를 확인하지만 receipt 청산·관측 시각이 report cutoff 이내인지 확인하지 않는다.
- 실제 기존 자료로 2026-08-27 report를 메모리 재구성하자, 2026-08-24 morning episode에 2026-08-28 17:47:42의 manual-exit receipt가 붙어 두 손실 leg가 완료로 들어왔다.

보완 방향: 진입 귀속일, 실제 체결일, 최초 관측일, report cutoff를 분리한다. 후일 보고서에서 과거 진입일 손익을 정정하는 것은 유지하되, 과거 시점 후보의 as-of 근거로 미래 결과를 사용하지 못하게 한다. 최신 지식으로 복원하는 사후 감사본은 별도 권한으로 표시하고 PREOPEN 근거로 재사용하지 않는다.

### F8 / P2 — 순이익·보유시간 추가만으로 경제성 목적을 충족하지 못한다

- `notional_weighted_ev_pct`의 분모가 실제 체결원금이 아니라 미체결을 포함한 요청금액이다. 이를 유지하려면 시도당 자금 기회효율로 구별해야 하며 broker 체결금액 EV도 별도로 필요하다.
- 관찰일 분모는 기본적으로 `eligible` 행 수다. source 결손/미완료로 제외된 보유일을 달력일 기회비용이나 자본 점유에서 평가하지 않는다. 완료 손익과 열린 손익을 섞어서는 안 되지만 장기 보유 비용을 평가에서 지워서도 안 된다.
- 현행/후보 subset의 관찰일 분모가 같을 때 총순이익 delta와 일평균 순이익 delta의 비음수 조건은 수학적으로 중복된다. 실제 새로운 기회나 자본 재사용 효과를 측정하는 별도 조건이 아니다.

보완 방향: 체결원금 EV, 동일 관찰기간 순이익/일, 무체결률, 미청산 자본 점유/기간을 분리한다. 완료 표본만 EV에 사용하고 미청산은 censored/자본점유 진단으로 남긴다. 중복 판정은 하나로 줄이되 순이익을 잃고 평균 EV만 높이는 후보를 승인하지 않는다.

## 4. 자동화 상태와 운영 경계

- `deploy/run_threshold_cycle_postclose.sh`의 Samsung producer 실행 기본값은 true다.
- 설치된 morning 시작 timer는 다음 거래일 07:57, midday preflight/시작은 13:12/13:14, afternoon은 13:57/13:59다. Morning 서비스는 preflight service를 Requires로 연결한다. 각 preflight wrapper는 같은 날짜 Samsung policy apply를 호출하며 live service는 exact-date loader 결과를 정책 객체에 반영한다.
- 운영 후보 18개와 적용본 18개에서 nonzero mutation은 모두 0개다. `candidate_applied`라는 상태명만으로 개선값 적용으로 해석하면 안 된다.
- 현 코드로 9월 7일 apply를 **읽기 전용 계산**하면 기존 9월 4일 v1 후보는 `baseline_legacy_candidate_without_evidence_binding`으로 처리된다. 유효 baseline payload가 나오며 mutation은 0개다. v8/v2 생산 체인의 자연 실행 성공과 개선 효과는 아직 확인되지 않았다.
- 정상 후보를 전달하는 배관은 보존할 가치가 있다. 그러나 F5/F7 같은 근거 결함이 남은 상태를 신규 개선값 실적용 준비 완료로 보고해서는 안 된다. 현재 lock 해제, baseline 제거, 수량/target/holding 정책 변경이나 봇 재기동을 시행하지 않았다.

## 5. 보완·제거 판단 순서와 acceptance

| 순서 | 권장 결정 | 완료 판정 |
| --- | --- | --- |
| 1 | F5/F7 근거 결속 결함을 먼저 보완 | 다른 적용 정책 손익으로 rollback 0건. cutoff 이후 receipt는 당시 후보에 유입 0건. 정당한 후일 손익 정정은 유지. |
| 2 | F1/F2 상승·반등 목적의 진입 설계를 기존 timing owner와 통합 검토 | 연속 하락은 confirmation 미통과, 유효 반등은 기존 안전 guard를 거쳐 진입 가능. 현행/후보의 최초·후속 신호와 체결/미체결을 같은 시간순 원천에서 비교. |
| 3 | F3/F4/F6 불필요한 veto·표본 리셋·영구 대기를 제거/대체 | 음수 현행보다 우월한 양수 후보 평가 가능. 무관한 머신 변경은 표본 유지. 무신호/미체결/표본부족 각각 종료·재평가 경로와 올바른 floor 도달 판정. |
| 4 | F8 경제성 평가 정리 | 동일 기간의 비용 차감 순기여 양수와 EV 개선을 함께 확인. 미체결·미청산·자본 점유는 누락되지 않고 실현손익과도 혼합되지 않음. |
| 5 | 장후/장전 handoff 최종 검증 | source→report→candidate→applied→runtime provenance 동일 정책 결속. 유효 개선 후보가 없으면 명시적 hold이며 억지 mutation 없음. |

유지 권장: 실제 청산/손실 원장, source-quality 검증, 정확일자 배포/무결성, broker/account/수량/가격 freshness guard.

제거·대체 검토: 현행 EV 양수 선행 veto, 무관한 전체-policy hash에 따른 표본 재시작, 중복 순이익 허들, 신호가 사라져도 결과를 요구하며 무한 유지하는 판정. 현행 subset 그리드는 진단으로 남기되 상승·반등 최적화 완료/자동개선 주체로 간주하지 않는다. Morning baseline-only 보고는 손실감사로 유지할 수 있으나 계속 기다리면 자동 개선값이 나올 작업으로 분류해서는 안 된다.

이번 요청은 최종 점검이므로 위 전략/판정 수정은 시행하지 않았다. 실제 전략 변경·실적용은 범위 확정과 재검증이 필요하다. 후속 검토 owner는 [SamsungEntryFinalReviewDecision0907](../checklists/2026-09-07-stage2-todo-checklist.md)이다.

## 6. 검증 기록

- Tuner, candidate/applied, morning preflight 기존 테스트: 83 passed.
- Morning/midday/afternoon, morning reentry, midday/afternoon preflight, entry timing 기존 테스트: 181 passed. 합계 264 passed.
- 별도 메모리 반례: 연속 하락 신호 생성, 음수 현행 gate의 개선 후보 차단, 다른 정책 근거 rollback/validator 통과, 전체 hash의 무관 머신 결합, 8월 27일 report에 8월 28일 receipt 유입을 확인했다.
- 테스트 통과는 기존 계약의 회귀 결과이지 위 findings가 해소됐다는 증거가 아니다. 코드 무결함 판정 및 신규 실적용 게이트는 닫히지 않았다.

## 7. 사용자 지시에 따른 구현·재리뷰 결과

구현일: 2026-09-05. 범위는 원천/후보 판정과 기존 Samsung entry-confirmation 런타임 연결이다. 실제 정책 파일 적용, 주문·취소, 봇 재기동, lock/env 변경이나 canonical 운영 보고서 덮어쓰기는 시행하지 않았다.

| 순서/발견사항 | 구현 결과 | 권한과 잔여 판단 |
| --- | --- | --- |
| 1 / F5·F7 | v9 report/candidate/PREOPEN이 source-date 실제 applied 정책을 결속한다. 미소비 후보를 적용 정책으로 간주하지 않는다. 미래 receipt·fill, 기록일 뒤 legacy 정정, 날짜가 다른 source-quality audit를 차단했다. 청산시각 없는 mutable 과거 state는 후일 완료 근거로 쓰지 않는다. 같은 날짜 재실행도 청산 원장을 보존한다. | 다른 정책/미래 근거로 rollback 불가. 정당한 후일 청산은 원래 episode에 귀속한다. |
| 2 / F1·F2 | subset 신규 tightening 권한을 제거하고 진단으로 남겼다. 기존 timing owner에 Samsung 전용 상승·반등 recipe를 연결했다. 신호 기준 bid +2bps 또는 관찰 저점 대비 +2bps 회복과 trade backing·refill·양의 비용 차감 edge·실행가능가격을 함께 요구한다. 횡보·하락·자료 결손은 확인 통과가 아니다. | 정확일자 정책에 선택된 scope만 동작한다. 기본 morning/drawdown/near-low와 target·수량은 그대로다. 이 모델은 신호별 bounded canary이며 후속 모든 재진입/보유를 재현한 일일 수익 극대화 보장이 아니다. |
| 2 재리뷰 / runtime 우회 | Morning의 NXT→SOR/사전 예약 PLANNED 경로에도 route별 선택 정책을 확인했다. WAIT는 제출을 미루고 REJECT는 해당 미제출 계획을 종료한다. 이미 거절한 morning opening route를 매 poll마다 새 신호로 재시작하지 않는다. | 계좌·유동성·velocity·market weakness·주문 소유권 guard는 기존 제출 경로에서 유지한다. 기존 미선택 baseline은 바꾸지 않는다. |
| 3 / F3·F4·F6 | 현행 EV 양수 선행 veto 제거, 기계별 정책 cohort 분리, 같은 dynamic recipe의 1/3/5초 결과 분할 제거, 누락 거래일을 넘는 post-apply 기간 병합 차단. Samsung 신호 freshness는 최근 5거래일(max lag 4)로 맞췄다. | dynamic 8 unique lifecycle/8 paired 완료·5 관찰일·최근 5 source-day 양의 개선·85% coverage·same-stage 한 scope는 유지한다. other scope는 max lag 1 유지. 무신호/미체결을 EV=0이나 승인 ETA로 만들지 않는다. |
| 4 / F8 | 실제 broker 청산 체결금액을 EV 분모로 사용한다. 주문 시도 금액 수익률, 미청산 점유금액, proxy, observation coverage, 완료 표본 생성률은 별도 진단이다. | 고정 왕복 비용 차감 추정 손익이며 정확한 broker 정산 수수료/세금 PnL이 아니다. |
| 5 / 검증 | 유효 상승 paired fixture가 candidate → applied validator → exact scope runtime loader까지 통과한다. 2일 무신호 후에도 Samsung 후보를 유지하고, 기존 flat recipe는 해당 scope의 신규 근거가 되지 않는다. | 실제 생산 후보/서비스 소비·실현 EV 개선은 자연 증거로 확인해야 한다. 코드 테스트 통과를 실수익으로 보고하지 않는다. |

### 7.1 실제 보관 자료의 읽기 전용 재계산

9월 4일 Samsung v9는 source-quality PASS, 실제 applied binding READY, 원장 21건/검증 문제 0건, candidate validator PASS, mutation 0건이었다. 원장 수가 이전 20건과 다른 이유는 동일 날짜의 기존 원장도 보존하기 때문이다. 실제 순손익은 바뀌지 않았고 EV 분모만 바로잡았다.

| 머신 | broker 가격 확인 청산 leg | 수정된 체결금액 EV | 비용 차감 추정 순손익 |
| --- | ---: | ---: | ---: |
| Morning | 6 | -1.403252% | -215,750원 |
| Morning reentry | 2 | +0.357103% | +19,230원 |
| Midday | 0 | 계산 불가(null) | 0원 |
| Afternoon | 4 | +0.387084% | +39,560원 |

8월 27일 as-of 재계산은 원장 13건/문제 0건, mutation 0건이었다. 미래 8월 28일 manual exit를 당시 손실로 끌어오지 않는다. 이 검사는 API 시세·계좌·주문 호출 없이 로컬 자료만 읽었다.

9월 4일 timing 재계산은 여전히 `baseline_immediate_entry_carry_forward`다. 당일 actual anchor 6건 모두 receipt/BBO/ask-depletion 결손이며, Samsung morning/afternoon의 동적 paired 완료는 0건이다. 보관된 원천에 없는 0B/0D·receipt를 코드 수정이나 반복 재실행으로 합성하지 않는다. 해당 source date는 기존 quarantine 계약을 따르고 다음 자연 수집을 검증해야 한다.

**기대효과 판정:** 유효한 상승·반등 입력과 양의 개선 성과가 쌓이면 다음 거래일 자동 적용 후보가 나오는 경로는 테스트로 확인했다. 지금 보관 자료에서 수익 개선값이 확보됐거나 앞으로 반드시 생긴다는 결론은 아니다. 현재 신호 subset의 0건/동일 행동만 기다리는 작업은 신규 승격 주체에서 제외했다. 다음 확인은 `SamsungEntryRiseReboundNaturalEvidence0907`이 소유한다.

### 7.2 리뷰·검증 기록

- 구현 → 자체리뷰 → 보완 → 재리뷰 과정에서 source cutoff, actual-policy lineage, 동적 cohort, morning SOR 예약 경로를 추가 수정했다.
- Samsung report/policy, timing/microstructure, micro confirmation, morning/reentry/midday/afternoon, 저가주 공통 런타임, 각 preflight, postclose verifier/PREOPEN 영향 테스트 **962 passed**. 변경 Python의 Ruff·Black check·compile, `git diff --check`, 실제 checklist parser 검증을 통과했다. 최종 재리뷰에서 구현 범위 내 미해결 finding 0건으로 review gate를 종결했다.
- 운영 서비스 배포·기동·자연 PREOPEN 소비·실현 수익 검증은 이번 테스트 범위 밖이다. 전체 저장소의 무결함이나 수익 보장을 주장하지 않는다.
- 문서 재리뷰와 checklist parser 검증을 통과했다. 파서는 34개 작업을 인식했고 신규 `SamsungEntryFinalReviewDecision0907`의 날짜/시간창을 정상 추출했다. `git diff --check`도 통과했다. Project/Calendar 동기화와 운영 재생성은 실행하지 않았다.
