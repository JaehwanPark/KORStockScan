# Main 트레일링·제출 지연 정책 생성 구조 재점검 — 2026-10-10

이 문서는 수리 전 구조 진단이다. 이후 P1–P5를 구현·반복 리뷰한 결과는 [구현 검증](main-trailing-delay-structural-implementation-review-2026-10-10.md)을 따른다. 아래 미실행/구조적 차단 판정은 진단 당시 코드의 기록으로 보존한다.

## 결론

**현재 정상 producer의 데이터를 그대로 더 쌓는 것만으로 신규 트레일링·양수 제출 지연 정책이 생성될 것이라고 판단할 수 없다. 표본 부족에 앞서는 구조적 차단을 재현했다.** 부모 계승 12셀·0초 초기 baseline의 발행 성공은 신규 학습 정책의 생성 가능성을 증명하지 않는다.

검토 기준은 선택 릴리스 `main-trailing-delay-residual-20261010-v6`, commit `78f2c1d784fd5043d5b5bc0fedd7b963f8fe42d4`다. 21:27 KST 기준 아래 10개 대상 source는 작업트리와 선택 릴리스 bytes가 같았다. 이번 검토는 원천→정규화→재생→학습→selector→준비 lookup의 도달 가능성에 대한 읽기 전용 코드·격리 진단이다. 운영 정책·원 원장·봉인된 10/12 checklist·선택 릴리스는 변경하지 않았다. provider·AI·주문 호출, 장후 재생성, 배포·재기동은 모두 0이다.

| 대상 | 시간이 흐르면 해결되는가 | 판정 |
| --- | --- | --- |
| 정상 완료 거래 기반 신규 트레일링 | 정상 quote adapter는 요구되는 원 holding-AI 증빙을 결합하지 않음. 증빙을 별도로 주더라도 새 classifier SHA와 원 진입 pin의 SHA 일치를 요구 | **현행 경로의 구조 수리가 먼저 필요** |
| 대용량 시장 공통 numeric 트레일링 | partitioned holding branch는 표본·성능과 무관하게 `research_candidate=None`을 전달. 대체 typed 경로는 위 AI 조건에 걸림 | **자료 증가만으로 기존 selector에 후보가 전달되지 않음** |
| 신규 양수 제출 지연 | 현행 continuous-reversal 결과에 보조정책 SHA가 없음. 정상 후행 가격쌍이 증가해도 미검증 부모 셀은 0초 | **현행 결과 계약 수리가 먼저 필요** |
| 부모 계승·0초 초기 정책 | 이미 정식 발행했으며 부족한 원천에서 기존 동작을 유지하는 유효 fallback | **생성 가능. 새로운 패턴·최적값 학습과 별도** |
| 수리 후 경제/가격 후보 선정 | 유효 원천과 적격 cohort에서 selector 도달은 가능. 우월한 결과가 실제로 나올지는 이후 자료가 결정 | **가능성을 검증할 수 있으며 수익성은 보장하지 않음** |

## 현재 자료와 기존 완료 판정의 한계

실제 [holding report](../../data/report/monitor_snapshots/holding_exit_observation_2026-10-08.json)는 `main_holding_cohort_reference_v2`의 대용량 경로다. scope는 20,832, 실제 완료 canonical cohort는 0, completed snapshot missing/source-gap/unverified는 1/5/1이다. 시장 공통 후보는 `None`, mechanical population은 incomplete다. 이 과거 결손 자체는 유효 거래나 손익 0으로 바꾸지 않았다.

정식 제출 지연 세대의 source census는 commit 31 / qualified PASS 29 / P0 6 / 가격쌍 21이다. qualified 29건의 부모는 모두 `legacy|legacy`이며 부모 미검증 29건, native 미검증 5건이다. **과거 결손만 관측한 것이 아니라 동일 결손을 앞으로도 생산하는 현재 코드 경로를 확인했다.** [source/릴리스 결속](../../tmp/trailing-delay-generability-20261010/source-binding.json)에 원천 수치·code hash·선택 commit을 기록했다.

[이전 구현 감사](main-trailing-delay-residual-implementation-review-2026-10-10.md)의 자동 입력·분할·성능·부모/0초 발행·최종화·PREOPEN 준비 결과는 당시 수용 범위의 근거다. 그러나 “적격 후보 0은 구현 누락이 아니다”라는 포괄 결론은 아래 정상 producer 계약 검증이 빠져 있었으므로 철회한다. 이전 typed selector 양수 회귀는 `operating_ai_required=False`와 격리된 report verifier를 사용했다([시험](../../src/tests/test_main_trailing_partitioned_research.py), 241–258행). 이는 실제 Main AI 증빙을 거치는 새 후보 생성을 검증한 시험이 아니다.

이번 발견은 거래 손실이나 10/12 기동 실패를 뜻하지 않는다. 기존 부모·0초 준비를 실제 적용·신규 학습·수익성으로 확장해 해석하지 않는다는 뜻이다. 자연 PID 소비는 여전히 적용일 기존 `DirectFamilyPreopenPolicyHandoff`의 별도 수용이다.

## 트레일링의 차단

### TG1 — 정상 quote/완료 거래 adapter와 원 holding-AI 증빙의 계약 단절

[공통 재생](../../src/engine/scalping/universal_trailing_replay.py)의 `quote_projection`(138–162행)은 quote·비용·WS/depth를 저장하지만 `holding_ai` 증빙을 저장하지 않는다. `completed_sources`(180–263행)는 `scalp_trailing_input_transition`의 quote/context/pin을 읽고 별도의 AI 요청·응답 사건을 결합하지 않는다. 실제 [runtime 기록](../../src/engine/sniper_state_handlers.py)의 30517–30534행도 이 projection을 사용한다.

반면 정규화 position은 `holding_ai_required`가 없으면 True, `holding_ai_policy_sha256`는 원 거래의 필드를 사용한다(258–259행). 검토한 runtime/EOD producer에는 이 두 원 필드의 정상 writer가 없었다. 재생의 첫 후보 crossing은 원 vote의 signal/source/context/receipt/policy SHA·PASS/VETO·유예 계약을 필수 검증하며 없으면 `candidate_holding_ai_input_unobserved`로 검열한다(562–575행).

**시간 효과:** 정상 adapter를 통해 만든 유효 quote·비용·terminal 60건과 240건이 각각 전부 같은 사유로 검열됐다. 같은 자료의 AI 불필요 격리 대조군은 `modeled_full_exit`에 도달했다. 대조군은 운영 AI를 OFF하자는 근거나 실제 손익 증거가 아니다. 현재 필드를 생산·연결하지 않는 이상 자료 증가로 누락이 해소되지 않는다.

**보완 방향:** 원 holding-AI request/response/유예 계약과 정확한 crossing·position·원 정책을 결합해야 한다. 아직 실제 발생하지 않은 후보별 AI 입력까지 과거 원 응답으로 요구하는 부분은 기계 재생과 AI overlay의 증거 층을 나눠 검증한다. 원 vote/pin을 합성하거나 운영 AI를 제거해 통과시키지 않는다.

### TG2 — 새 classifier를 과거 진입 때 이미 사용했어야 한다는 순환 조건

[분할 상황 집계](../../src/engine/automation/main_trailing_situation_aggregation.py)의 124–126행은 train의 마지막 `observation_end_at`을 `trained_through`로 넣어 새 classifier SHA를 만든다. 그러나 train·holdout 모두 원 진입 pin의 SHA가 이 **새 SHA**와 같아야 AI compatible로 인정한다(90–95, 133–140행). [원 pin의 인과성 검사](../../src/engine/scalping/trailing_situation_policy.py)는 classifier의 학습 종료가 원 entry보다 늦으면 정상 분류로 인정하지 않는다(111–125행).

즉 새 학습 자료가 끝난 뒤 생성하는 모델을 그보다 앞선 train의 진입에서 이미 사용했어야 한다. `trained_through`가 SHA에 포함되므로 threshold가 같아도 신규 세대 SHA는 달라진다. resident 상황 집계에도 같은 비교가 있다.

**시간 효과:** 원 진입의 causal pin을 유지하고 모든 숫자 성과를 개선한 10일/60건과 40일/240건 모두 `operating_ai_required=True`이면 `parent_carry`, AI compatible=False였다. 같은 수치·표본에서 AI 불필요 대조군은 `research_candidate_requires_existing_selector_review`에 도달했다. 표본 기준 7일·train 30·holdout 10을 넘겨도 해결되지 않았다.

**보완 방향:** hypothesis의 의미 hash와 실제 학습 세대 hash를 분리하고 원 pin/as-of는 유지한다. train 연구 재분류가 미래 모델을 과거에 사용한 AI receipt를 요구하지 않도록 계약을 정리한다. frozen classifier의 holdout/향후 AI 입력 호환성은 별도로 입증하며 과거 원 pin을 새 SHA로 덮지 않는다.

### TG3 — 대용량 holding report가 시장 numeric 후보를 발행하지 않음

[holding report](../../src/engine/holding_exit_observation_report.py)의 `_partitioned_holding_report`는 `trailing_mechanical_market_tuning.status=partitioned_research_reference`, `research_candidate=None`을 무조건 만든다(2750–2752행). [기존 mechanical selector](../../src/engine/automation/scalp_trailing_mechanical_policy_apply.py)는 적격 후보 구조를 요구한다(105–113행). typed bundle은 대체 연결이지만 TG1/TG2에 걸린다.

**시간 효과:** 현재 대용량 report를 그대로 넣으면 `hold_source_gap / mechanical_population_incomplete`다. 격리 대조군에서 census의 complete만 True로 바꿔도 `hold_sample_or_edge / partitioned_research_reference`로 바뀔 뿐 후보가 생기지 않았다. 이 complete 변경은 실제 원천을 검증했다는 뜻이 아니다. 해당 report branch가 유지되는 한 신규 표본이 아무리 좋아도 시장 후보 필드는 계속 None이다.

동시에 9/29부터의 누적창에 남은 1/5/1 snapshot 결손 중 하나라도 있으면 completed/mechanical population을 통째로 incomplete로 만든다(2724–2726, 2739–2746행). 식별 가능한 과거 결손이 향후 정상 적격 거래와 분리되지 않는다.

**보완 방향:** 분할 결과의 적격 경제 cohort·train/holdout 후보를 기존 selector로 전달하는 명시적 bridge가 필요하다. 전체 census 결손과 격리 후 적격 평가 cohort의 완전성을 분리한다. 기존 실제 비용·slippage·one-market 선택·hard safety는 보존한다.

### TG4 — 일반 악화 1건까지 누적 후보를 영구 veto하는 과도한 수용 조건

분할 상황 집계는 실제 거래에서 `max(incumbent modeled PnL, actual PnL)`을 기준으로 비교하고(85행), train/holdout의 **모든 거래 악화 건수 0**을 요구한다(139–140행). selector bridge의 `_type_view`는 이 일반 악화를 `large_loss_worsened_ids`로 연결한다(232–234행). 소폭 잡음과 큰 손실 악화가 구분되지 않는다.

**시간 효과:** 전체 평균·holdout·일별 stress 성과가 양수인 60건/240건에서도 단 한 건을 -1원 악화, 나머지를 +5원 개선으로 주면 둘 다 부모 유지다. 같은 후보·누적창에 그 행이 남아 있는 한 좋은 거래를 추가해도 “악화 0건”이 되지 않는다. 모든 미래 후보가 수학적으로 불가능하다는 뜻은 아니지만, 데이터가 많아질수록 자동으로 완화되는 조건은 아니다.

**보완 방향:** 일반 paired 변화와 큰 손실/tail 악화를 구분한다. 평균·holdout·스트레스 개선을 평가하되 실제 큰 손실 제한과 rollback을 유지한다. 이 조건의 변경은 명시적인 정책 계약 보완이며 이번 진단에서 임계값을 바꾸지 않았다.

## 제출 지연의 차단

### DG1 — 현재 continuous-reversal 보조정책 SHA가 결과·anchor에 전달되지 않음

[현행 compose](../../src/engine/scalping/continuous_reversal_policy.py)(257–326행)는 machine SHA와 `entry_ai_risk_verdict`/`entry_ai_screen_pass`를 반환하지만 `entry_ai_soft_policy_sha256`는 반환하지 않는다. [AI caller](../../src/engine/ai_engine_openai.py)의 2933–2935행은 이 결과를 바로 반환한다. runtime의 `_machine_primary_entry_provenance_fields`는 존재하는 필드만 복사한다. 양수·0초 양쪽 `price_ready` commit은 그 필드를 그대로 읽는다([runtime](../../src/engine/sniper_state_handlers.py), 70463–70466, 70536–70545행).

[초기 지연 정책](../../src/engine/scalping/pre_submit_delay_initial_policy.py)의 190–191행은 없으면 부모를 `legacy`로 묶는다. resident 303–310행과 [분할 연구](../../src/engine/automation/pre_submit_delay_partitioned_research.py)의 284–290행은 해당 미검증 부모에 대해 0초·양수 적용 불가로 처리한다.

**시간 효과:** 실제 compose의 필드 계약을 사용한 격리 조사에서 AI SHA는 None이었다. native/P0/horizon을 모두 정상으로 주고 모든 30초 가격쌍이 +50bp 개선인 60건/240건도 0초였다. 유효한 AI 부모 SHA를 주는 격리 대조군은 양쪽 모두 30초 후보를 만들고 `PreparedPolicy.lookup`이 30초를 읽었다. 이는 기존 generator/loader의 양수 경로가 존재한다는 증거이며 실제 정책 발행·주문·실현 이익의 증거는 아니다.

**보완 방향:** 원 보조판정 payload/prompt/schema/model의 실제 의미 세대 SHA를 요청·결과·price/signal anchor에 함께 전달한다. 현재 정책의 임의 SHA를 과거 행에 붙이거나 날짜별 outer bundle SHA를 의미 hash로 대체하지 않는다. 단순 날짜 변경이 machine 의미 hash를 매일 바꾼다는 가설은 이번 검토에서 확인되지 않았다. 실제 정책 의미가 바뀔 때 부모를 분리하는 것은 별도 정당한 계약이다.

### DG2 — signal-ready 관측이 현행 PASS 표현을 받지 않음

[signal-ready adapter](../../src/engine/scalping/pre_submit_delay_observation.py)의 `register_pass_result`(186–195행)는 `entry_ai_effective_assessment.effective_verdict`만 검사한다. 현행 compose는 그 필드를 반환하지 않고 `entry_ai_risk_verdict=PASS`, `entry_ai_screen_pass=True`를 제공한다. 정상 결과는 관측 등록 전에 False로 돌아간다.

**시간 효과:** compose 결과는 등록 0회, effective assessment를 원 형식에 맞춰 넣은 격리 대조군은 등록됐다. 현행 PASS가 계속 같은 형태면 signal-ready 관측도 계속 빠진다. price-ready의 0초 관측은 이미 존재하므로 “양수 정책이 있어야만 관측한다”는 순환은 확인되지 않았다. DG2 하나만으로 모든 지연 생성이 불가능하다고 판단하지 않는다.

**보완 방향:** 현재 보조 PASS 계약을 공통으로 정규화해 원 complete/deadline/native identity를 유지하고 두 anchor에 연결한다. advisory PASS를 effective PASS로 무조건 승격하지 않는다.

### DG3 — 미검증 native 1건이 같은 부모의 정상 셀 전체를 계속 막음

resident 303–304행과 분할 연구 285–290행은 train/validation에 `native_evaluation_bound=False`가 하나라도 있으면 셀 전체를 0초로 바꾼다. 필수 native 결손을 적격 학습에서 제외하는 대신 동일 parent/session/situation의 모든 정상 행을 차단한다.

**시간 효과:** 정상 부모 SHA·정상 가격쌍인 60건/240건은 30초를 선택했다. 같은 입력에서 1건의 native ID만 결손으로 바꾸면 둘 다 0초가 됐다. 고정 누적창·동일 부모에 그 행이 남는 한 신규 정상 자료로 상쇄되지 않는다.

**보완 방향:** 해당 행을 census에 보존하고 적격 cohort에서 제외한다. global manifest/preflight 무효·분리 불능 손실은 계속 전역 차단한다. 다른 부모의 가격쌍을 합치거나 실제 fill/cost를 가격 연구의 추가 요건으로 넣지 않는다.

### DG4 — 희소 horizon 하나가 기존 정상 공통 비교 모집단을 없앰

초기 정책 `_selection`(243–252행)과 분할 연구 `_select`는 train 중 한 행이라도 관측한 horizon을 전체 후보에 넣고, 그 모든 horizon을 가진 행의 교집합만 사용한다. 30초 유효 train 6 / holdout 4에 180초만 있는 신규 train 1건을 추가하면 기존 자료가 그대로인데 공통 train이 0이 됐다.

**시간 효과:** 이는 매번 영구 불가능하다는 증거는 아니다. 충분히 완전한 horizon 관측이 나중에 들어오면 해결될 수 있다. 다만 자료 증가가 선정 가능성을 오히려 떨어뜨리는 비단조적 coverage 병목이다.

**보완 방향:** 미리 정한 지원 후보의 coverage 자격을 확인하거나 후보별 적격 cohort와 비교 계약을 명시한다. 비교되지 않은 후보를 공통 교집합에 자동 편입해 기존 정상 비교를 소거하지 않는다.

## 수리 우선순위와 종료 검사

후속 [다섯 단계 상세 보완계획 P1–P5](../proposals/main-trailing-delay-policy-generation-structural-remediation-plan-2026-10-10.md)에 실제 수정 위치·pre-signal holding-AI 계약·classifier identity·격리/bridge·수용 조건과 종료 시험을 정리했다. TG4의 -1원 예시는 악화 0건 조건의 누적 지속을 증명한 것이다. 기존 selector도 `paired_delta<0 AND 후보 순손익<0`을 제한하므로, 수리 검증에서는 부모/후보 모두 이익인 10원→9원과 0원→-1원을 구별한다. 일반 악화를 손실 악화로 전부 대입하는 오류만 제거하며 후자의 기존 guard를 자동 완화하지 않는다.

새 runtime 권한·임계값 변경 없이 가능한 원천/계약 수리와 수용 정책 변경을 분리한다. 아래는 이번 진단의 보완 권고이며 실제 코드를 수정·발행한 결과가 아니다. 후속 구현 착수 때 기존 `MainAllScopeTrailingReplay`, `PreSubmitDelaySituationImplementation1010` stable ID의 완료 이력·새 발견·수용을 현재 실행 checklist로 재개한다. 완료된 기록을 현행 OPEN 실행 owner로 사용하지 않는다.

| 순서 | 수리 대상 | 종료 검사 |
| --- | --- | --- |
| 1 | DG1/DG2 현재 PASS·보조 SHA → 두 anchor | 실제 compose→Main provenance→0초 price-ready 및 signal-ready→정규화→분할/단일 연구→준비 lookup을 잇는 시험. valid 부모/후행은 30초 후보에 도달, 실제 결손은 격리 |
| 2 | TG1 원 quote·holding-AI 원천 결합 | 정상 runtime 기록→완료 adapter에서 정확 request/response/policy/context와 비용을 연결. 유효 원 vote는 재생에 도달, mismatched/없는 vote는 검열 |
| 3 | TG2 학습 세대/원 pin 순환 제거 | 원 causal pin 불변, 60→240건의 정상 AI-required 코호트에서 sample 기준을 넘으면 typed 후보 검토 단계에 도달. 미래 정보/원 pin 덮기 금지 |
| 4 | TG3/DG3 식별 가능한 과거 결손 격리·대용량 selector 연결 | 결손 1건을 남긴 채 정상 적격 자료를 추가해 후보가 평가되고 census에는 결손이 남음. partition 크기/재개 변화와 단일 계산 의미 동일 |
| 5 | TG4/DG4 수용 조건·coverage 정리 | 일반 소폭 악화와 큰 손실 제한을 분리. 희소 신규 horizon 추가로 기존 검증 가능한 후보 전체가 사라지지 않음. 변경된 계약의 holdout/authority 회귀 |
| 6 | 마지막 소비/발행 확인 | 적격 후보 전달→기존 selector/loader까지 확인하되 부모 유지도 유효 결과. 신규 발행 시 source/hash/summary/strict/finalization/PREOPEN을 정식 successor로 검증 |

이 순서의 종료는 좋은 입력의 후보 도달 가능성과 나쁜 입력의 격리·guard 거절을 함께 검증하는 것이다. 실제 이익을 강제로 만들거나 적격 후보가 반드시 매번 존재해야 한다는 요건을 추가하지 않는다. 기존 source/cost/정책 세대에 없는 자료를 만들어 연구를 통과시키지 않는다.

## 재현·검증과 범위

- [격리 진단 결과](../../tmp/trailing-delay-generability-20261010/probe-results.json): 60/240건·10/40일, 6개 typed 집계 조건·6개 delay 조건·정상 quote adapter 2개·대용량 selector 2개·PASS adapter·희소 horizon 증분. 공급자/주문 경계는 실행하지 않았다.
- [주요 진단 스크립트](../../tmp/trailing-delay-generability-20261010/probe_generability.py), [추가 진단 스크립트](../../tmp/trailing-delay-generability-20261010/probe_additional.py): 선택 v6 module을 project `.venv`에서 실행했다. 원 AI/provider/source-verifier를 분리한 대조군은 필드 계약·consumer 도달 가능성만 검사한다. 운영 원천 증빙과 혼동하지 않는다.
- [source binding](../../tmp/trailing-delay-generability-20261010/source-binding.json)은 검토한 10개 code byte와 선택 commit, 실제 delay census, 봉인 checklist SHA를 기록한다. 과거 손실 원천 전체의 재생·AI 연구 호출은 수행하지 않았다.
- 기존 전체 pytest를 무변경 반복하지 않았다. 이번 증명에는 자동 adapter의 실제 함수, 집계/selector/lookup 함수와 실패·양수 대조군을 사용했다. 문서 검증은 링크·공백·print-only parser로 닫는다.

문서 재리뷰 결과: 변경 문서 5개·로컬 링크 113개 결손 0, fence·공백·`git diff --check` PASS다. print-only parser는 OPEN 23개·stderr 0이며 10/12 자연 PREOPEN owner는 정확히 하나다. 봉인된 10/12 checklist SHA와 검토한 10개 workspace/선택 릴리스 source SHA의 불변을 다시 확인했다. 오늘 완료 owner를 새 OPEN으로 바꾸거나 외부 Project/Calendar sync를 실행하지 않았다. 새 결함의 코드 수리는 미실행이며 “미해결 finding 0”으로 보고하지 않는다.

**최종 판정:** 단순한 데이터 축적 대기는 현재 구조적 차단의 해결책이 아니다. TG1/TG2/TG3와 DG1/DG2/DG3를 수리한 뒤에야 자연 자료 축적과 표본·성과 검증으로 신규 정책 생성 가능성을 판단할 수 있다. TG4는 별도 수용 계약, DG4는 관측 coverage 효율의 개선 항목이다.
