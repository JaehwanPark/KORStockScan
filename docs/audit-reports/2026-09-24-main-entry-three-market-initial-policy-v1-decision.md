# Main 진입 상황 정책 최초 버전 판정 — 2026-09-24

상태: **기준 정책 v1 동결, 상황별 신규 판정 분기는 미선정.** 이 문서는 과거 원천으로 만든 정책 결정 기록이다. 런타임 정책 파일·선택 release·PID·주문은 변경하지 않았다. `promotion_pass`와 실제 비용 개선, 정책 발행, PID 소비는 각각 다른 판정이다.

후속 사용자 지시에 따라 수익률을 선택 지표에서 제외한 별도의 [승률 단독 초기 정책안](./2026-09-24-main-entry-three-market-win-rate-only-initial-policy-v1.md)을 작성했다. 이 문서의 비용 중심 판정과 새 승률 목적의 판정을 혼용하지 않는다.

## 1. 기준 정책과 시장·상황 정의

적용 목표일은 기존 다음 영업일 계약의 `2026-09-28`이다. 기준은 그 날짜에 `mechanistic_entry_runtime_policy.load_effective()`가 반환하는 현 `current.json` 세대 `99cb0e3af2a3e17e52b5edc4d2ba4ed018fd60fd4e8eca3a3386f91efa622de0`이다. 별도의 [9/28 날짜별 bundle](../../data/runtime/mechanistic_entry_policy/policy_2026-09-28.json)은 `03ed27b3971f36ab3e90f4bf91298165da6508d5facb9f058ac3ef2e52216082`/`incumbent_carried`이며, 현재 loader는 `current.json` 세대를 먼저 읽는다. 어느 세대가 실제 매매 PID에 들어갔는지는 여기서 증명하지 않는다.

현재 세대의 최상위 `machine_disposition=evidence_qualified_strategy_update`와 KRX scope 내부의 `machine_disposition=incumbent_carried`도 서로 다르다. 실제 선택 정책은 disposition 문구가 아니라 `current.json`→세대→exact scope의 정책 hash와 activation 영수증으로 판정한다. scope disposition이 정책 변경을 누락한 이유는 발행 소비자/의미 감시의 별도 결함 점검 대상이다.

| 고정 시장 구간 | exact venue/session은 유지 | 최초 버전의 진입 상황과 판정 |
| --- | --- | --- |
| PREMARKET | `PREMARKET_KRX_LIKE|PREMARKET_KRX_LIKE`, `NXT|NXT_PREMARKET`, `PREMARKET_KRX_LIKE|NXT_PREMARKET` | `BASE`: 해당 exact scope의 기존 기계 정책 유지. |
| REGULAR | `KRX|KRX_REGULAR`, `NXT|KRX_REGULAR`, `NXT|NXT_REGULAR_OVERLAP`, `NXT|NXT_REGULAR` | 진입 당시 `current.fluctuation_pct < +11.895%`이면 `LOW_ADVANCE`, 이상이면 `HIGH_ADVANCE`, 결손이면 `UNKNOWN`. **세 상황 모두 해당 exact scope의 기존 기계 정책을 사용한다.** 상황 이름은 판정 override가 아니다. |
| 통합 AFTERMARKET | `NXT|NXT_AFTERMARKET`, `KRX_NXT_INTEGRATED|KRX_NXT_AFTERMARKET` | `BASE`: 해당 exact scope의 기존 기계 정책 유지. |

이 버전은 시장을 거래소별 유형으로 재분류하지 않는다. venue/session은 원천·비용·주문·정책 hash의 정확한 결속 키다. `LOW_ADVANCE/HIGH_ADVANCE`는 종목의 영구 속성이 아니다. 결손을 0 또는 `LOW_ADVANCE`로 채우지 않는다. 현재 selector의 분기 입력에는 `fluctuation_pct`가 없으므로 이 상황 라벨은 아직 런타임 분기 영수증이 아니다. 기준 기계 정책의 `BLOCK|RECHECK|ENTER_NOW`, AI의 비승격 경계와 hard safety는 그대로다.

## 2. 과거 유효 원천 전체와 비교 방법

[전수 진단](./2026-09-24-machine-judgement-horizon-and-field-association-audit.md)의 비용 경로 진단 가능 3,078행에서 기존 `_machine_source_contract_valid`, 정확 attempt 충돌 제외, 현재 `LOCAL_BREAKOUT_VERSION`, `_machine_path_value` 비용·terminal 경로를 **모두** 통과한 행만 판정 후보의 비교 분모에 넣었다. 분모는 [9/23 full report](../../data/report/ai_decision_action_outcome_calibration/ai_decision_action_outcome_calibration_2026-09-23.json)의 exact-scope `accepted_unique_trace_count`와 대사했다. 9/14~16의 이전 구조 행은 캡처된 `strategy_completed_bars`가 없어 현재 구조 계약으로 재구성하지 않았다. 9/17은 유효 비용·경로 결합이 0건이다. 제외 행을 손실·수익 0으로 놓지 않았다.

| 시장·현재 유효 exact scope | 원천일 | 현재 구조·원천·비용 유효 행 | 비교된 고유 기회 | 기준 정책의 `ENTER_NOW` | 기준 선택 경로 CF 평균 |
| --- | --- | ---: | ---: | ---: | ---: |
| REGULAR · `KRX|KRX_REGULAR` | 9/22·23 | 351 | 197 | 29 | −0.35915% |
| PREMARKET · `PREMARKET_KRX_LIKE|PREMARKET_KRX_LIKE` | 9/22·23 | 25 | 17 | 0 | null |
| AFTERMARKET · `KRX_NXT_INTEGRATED|KRX_NXT_AFTERMARKET` | 9/21·22·23 | 100 | 53 | 6 | −0.46493% |

위 CF는 최초 진입 가격의 왕복 보수 비용을 반영한 목표/손절 **첫 도달 경로**다. 실제 체결 bid·수량·청산·자본·실현 순익이 아니다. 다른 exact scope에는 동일 계약의 유효 비교 행이 없으므로 위 세 scope의 효과를 NXT 단독 scope로 전이하지 않는다. 각 scope의 기준 정책 해시는 각각 `c6b5af4e868283ecd100127a679707dcaf04d0eff2cf829a0351028a5ab28f33`, `656cfd8e824f3135c8a5c7f47ece789a9c1837f53e72355d298fa2602f05b011`, `db112846126d5aac160fb4c53ea4aa961c9e5ab321ef5b59f724233e36b3a2e1`이다. 나머지 여섯 exact scope는 모두 기존 `mechanistic_entry_thresholds_initial_v1` 해시 `a11c7325a4b0abebc1c5f6b3c44b47ff02c1a9e6c615626af3f585b6f5d3c6f7`을 유지한다.

REGULAR의 `+11.895%`는 9/14~16 탐색 중앙값으로 미리 정하고 9/21~23 진단에 적용한 분류 경계다. 현재 계약을 통과한 REGULAR 351행은 `LOW_ADVANCE` 257, `HIGH_ADVANCE` 94, `UNKNOWN` 0이다. 이 숫자는 유형의 **관측 분모**이며 유형별 새 판정의 수익 증거가 아니다.

## 3. 신규 판정 후보 대 기준 정책

기존 `build_main_strategy_refinement(..., machine_policy_only=True)`의 한정된 96개 후보 탐색을 위 정확 유효 행에 읽기 전용으로 적용했다. 9/22까지 train, 9/23 holdout으로 분리했다. `overextension_runup_pct`를 높은 상승 확장에만 12·18·20%로 바꾼 추가 직접 재생도 같은 분모에 적용했다. 이는 기존 범위 내 단일 좌표 시험이며 상황별 새 selector를 구현한 것이 아니다.

| 시장 | 탐색된 유효 후보 | 학습 구간의 후보 대 기준 CF paired Δ | 9/23 홀드아웃 후보 대 기준 CF paired Δ | 홀드아웃 선택 진입 CF | 최초 신규 분기 판정 |
| --- | ---: | ---: | ---: | --- | --- |
| REGULAR | 83 | +0.01011%p | **0%p** | 8건 평균 −0.44892% | 개선 재현 없음. 기존 탐색기의 `promotion_pass=true`를 신규 분기 채택으로 쓰지 않는다. |
| PREMARKET | 90 | 평가 가능한 판정 변화 후보 없음 | 평가 가능한 판정 변화 후보 없음 | 진입 0건, 평균 null | 단일 기준 상황 유지. |
| AFTERMARKET | 77 | +0.02889%p | +0.05955%p | 진입 **0건**, 평균 null | 홀드아웃에서 손실 진입 회피만 관측. 양의 선택 진입 EV가 없어 신규 분기 미선정. |

높은 상승 확장에만 적용한 `overextension_runup_pct` 12·18·20% 시험은 세 시장 모두에서 **홀드아웃 판정 변화 0건**이었다. REGULAR의 새 상황 분류를 기존 15% overextension 규칙과 동일시할 수 없다.

REGULAR 상황 분기의 직접 대조로, `HIGH_ADVANCE`만 무조건 `BLOCK`하고 `LOW_ADVANCE`는 현 정책을 유지하는 **가상 후보**도 같은 351행·197기회에서 계산했다. 9/22 학습 구간의 기회 가중 paired Δ는 +0.01377%p, 9/23 진단 구간은 +0.03433%p다. 그러나 9/23에 남은 선택 진입은 3건, 비용 후 경로 평균 **−0.27023%**, 최악 −1.01070%이며 기존 성공 진입 보존율은 **50%**다. 전체를 BLOCK해도 같은 날짜의 paired Δ는 +0.03436%p로 거의 같고 선택 진입은 0건이다. 따라서 이 양의 Δ는 상황별 수익 기회 발견의 증거가 아니며, 무조건 BLOCK 분기를 최초 정책으로 채택하지 않는다. 이 가상 분기는 현재 selector에 없고 실제 주문에 적용한 적이 없다.

**독립성 한계:** 현재 기준 `current.json`의 KRX 전략 활성 세대는 9/22까지를 학습하고 9/23을 이미 홀드아웃으로 소비한 뒤 9/23 밤에 활성화됐다. 따라서 이 세대를 기준으로 한 9/23 재평가는 진단 비교이지 새 정책의 독립 홀드아웃 증명이 아니다. REGULAR·AFTERMARKET의 탐색 PASS가 있어도 선택 경로 EV가 음수 또는 null이고, 현재 버전과 독립된 양의 비용 후 개선은 입증되지 않았다. 과거 데이터만으로 정책을 만들 수 있다는 원칙은 유지한다. **운영 paired 0건은 최초 생성의 탈락 사유가 아니다.**

## 4. 최초 버전의 정확한 결론

1. 지금 확정 가능한 최초 **판정** 정책은 각 exact scope의 위 기준 정책을 유지하는 이 문서의 결정명 `initial_baseline_v1`이다. 이는 런타임 schema/version 필드가 아니다. 시장 3구간과 REGULAR의 진입 상황 라벨은 고정하되 유형별 다른 `BLOCK/RECHECK/ENTER_NOW` 규칙은 확정하지 않는다. 이 결과를 새로운 수익성 정책이나 9/28 PID 적용으로 표현하지 않는다.
2. 유형별 다른 판정 후보는 동일 계약의 역사적 비용 경로에서 기존 정책보다 개선되고, 독립적으로 남긴 날짜·기회에서 선택 진입의 비용 후 결과와 tail이 확인될 때만 별도 버전으로 만든다. 분모와 label이 없으면 기존 기준 정책을 유지한다. 이후 운영 paired는 다음 갱신과 실제 효과 귀속에 사용한다.
3. 현 탐색기의 machine `promotion_pass`는 음의 선택 경로 EV 또는 홀드아웃 선택 진입 0건에서도 참이 될 수 있다. 후보 선택/발행 소비자가 이 값을 실거래 수익 승인으로 읽지 못하도록 구분하는 것이 후속 구현의 우선 결함이다. `fluctuation_pct` selector 입력·unknown fallback·상황별 직접 소비 영수증과 scope disposition의 정책 hash 정합성도 기존 owner에 연결해야 한다. 이 문서는 그 코드 변경을 수행하거나 소급 승인하지 않는다.

재현 경계: 원천 report의 `artifact_content_sha256=10b29ced3cf6e61bee35e84de5e456db3dd78b562378cd0aef9db605fdc85564`(파일 바이트 SHA-256 `efa683652379d1ec593505ced80125228b004bfc128c8314f5ab04fdec01b160`); current-structure 수용 행 해시는 REGULAR `354291156bc8732b9056673371d1ebafc1f27a26835e48026b1f876b4fcc10d1`, PREMARKET `f576235b56a90363ed4d8a18600dc2a8505802a511a698a3ffed2e3942b15582`, AFTERMARKET `99d3e9e9bf44ea5188b566d9d01a94a8e6aca12034c7f091b3565fb4915121fc`다. 비교 함수는 `ai_action_outcome_calibration._machine_path_value`, `_machine_admission_metrics`, `build_main_strategy_refinement`와 `entry_setup_evidence.mechanistic_entry_policy_decision`이다.
