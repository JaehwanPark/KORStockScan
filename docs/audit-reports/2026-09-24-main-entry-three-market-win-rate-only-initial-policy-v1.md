# Main 진입 상황별 승률 단독 초기 정책 v1 — 2026-09-24

상태: **과거 원천으로 선택한 승률 단독 정책안 `winrate_initial_v1`; 런타임 미발행.** 사용자의 새 목적에 따라 수익률 크기·비용 후 EV·paired 수익 차이는 후보 선택과 순위에서 제외했다. 목표 선도 여부만 1/0으로 세며, 결과가 없거나 원천 계약이 불완전한 행은 승패에 넣지 않는다. `net_target_first`와 `exact_stop_first`는 기존 비용 결속 목표/손절 경로의 이진 결과이고, 이번 선택에서 그 수익률 크기를 사용하지 않는다. 기준 정책이 선택한 REGULAR 29시도에서는 gross `target_first`/`adverse_first`와 승패가 같았지만, 엄격 유효 전체 476행 중 9행은 gross 목표 선도와 비용 결속 손절 선도가 다르다. 정책 승패 라벨은 비용 결속 경로로 고정한다.

## 1. 고정 시장과 실행 가능한 규칙의 범위

| 고정 시장 | 진입 시점 상황 | 초기 정책안 |
| --- | --- | --- |
| PREMARKET | `BASE` | 모든 exact scope에서 기존 기계 판정 유지. 현재 엄격 유효 25행에 기준 `ENTER_NOW`가 0건이어서 선택 진입 승률은 정의되지 않는다. |
| REGULAR | `VWAP_NOT_EXTENDED`: `micro_vwap_available=true`, `minute_candle_window_fresh=true`, 유한한 `features.curr_vs_micro_vwap_bp < 68.75` | 현재 기계 판정 유지. `ENTER_NOW`만 그대로 진입 후보로 남는다. |
| REGULAR | `VWAP_EXTENDED`: 같은 원천 계약 아래 `features.curr_vs_micro_vwap_bp >= 68.75` | 현재 판정이 `ENTER_NOW`인 **해당 시도**만 `BLOCK`하는 후보. 기존 `BLOCK`·`RECHECK`를 승격하지 않는다. |
| REGULAR | `VWAP_UNKNOWN`: 유효 숫자·가용성·신선도 중 하나라도 결손 | 기존 판정 유지, 원천 결손을 별도 기록. 0bp로 채우거나 확장 부정으로 판정하지 않는다. |
| 통합 AFTERMARKET | `BASE` | 모든 exact scope에서 기존 기계 판정 유지. 엄격 유효 100행 중 기준 선택 진입은 6건뿐이며 마지막 날짜는 1건이어서 세부 승률 분기를 정하지 않는다. |

이 규칙의 역사적 지지는 **`KRX|KRX_REGULAR`에만** 있다. 같은 REGULAR 시장의 NXT exact scope나 PREMARKET·AFTERMARKET으로 68.75bp 경계를 옮기지 않는다. 시장 3구간은 거래소가 아닌 세션 분류이며, exact venue/session은 원천·정책 해시와 주문 경로를 묶는 키로 남는다. `VWAP_*`는 종목의 영구 유형이 아니라 매 진입 평가 시점의 상황이다. 기존 hard safety, AI 비승격 경계, broker/order/quantity/cooldown veto가 우선한다. 이 문서는 신규 runtime selector나 날짜별 bundle을 발행하지 않는다.

## 2. 원천, 탐색, 선택

[전체 필드 감사](./2026-09-24-machine-judgement-horizon-and-field-association-audit.md)의 비용 경로 진단 가능 3,078행에 기존 source hash·정확 attempt 충돌·현재 완료봉 구조·terminal label 계약을 적용하면 정책 비교 가능한 476행이 남는다: REGULAR `KRX|KRX_REGULAR` 351행(9/22 222, 9/23 129), PREMARKET 25행, 통합 AFTERMARKET 100행. 이 수는 [기존 비용 중심 결정](./2026-09-24-main-entry-three-market-initial-policy-v1-decision.md)의 원천·제외 분모와 같다. 옛 구조를 현재 구조로 소급 변환하지 않았다.

REGULAR 9/22만 후보 선택에 사용했다. 판정 전 숫자 필드 77개에 대해 **학습 행의 고유 관측값만으로** 9개 분위 경계와 양쪽 방향을 만들었다. 기준 정책에서 이미 `ENTER_NOW`인 시도만 줄이는 단일 필드 후보 중, 선택 진입이 10개 이상 고유 기회에 남고 실제 판정이 바뀌는 후보 697개를 비교했다. 선택 순서는 고유 기회 균등 가중의 **표본수 보정 승률 → 원시 승률 → 남는 기회 수**이며 수익률은 사용하지 않았다. 최고 학습 점수의 경계는 `curr_vs_micro_vwap_bp < 68.75`였다. 이 값은 9/22 유효 행의 해당 필드 **고유 관측값 85번째 백분위 표본값**으로, 9/23 결과를 보고 이동하지 않았다.

이 필드는 [기존 feature producer](../../src/engine/scalping_feature_packet.py)의 `(현재가−micro VWAP)/micro VWAP × 10,000` bp다. producer가 관측 불가 때 숫자 0을 초기값으로 둘 수 있으므로 `micro_vwap_available`와 `minute_candle_window_fresh`가 모두 참인지 함께 검사해야 한다. 이 351행에서는 두 플래그가 모두 참이고 원천 해시가 결속됐다. 현 [strategy selector](../../src/engine/scalping/entry_strategy_policy.py)는 이 필드를 분기 입력으로 노출하지 않으므로 정책안은 아직 런타임 실행 규칙이 아니다.

## 3. 기준 판정 대 승률 단독 정책안

동일한 현재 `current.json` 세대 `99cb0e3af2a3e17e52b5edc4d2ba4ed018fd60fd4e8eca3a3386f91efa622de0`의 `KRX|KRX_REGULAR` 기계 정책을 모든 유효 행에 재생했다. 승률은 선택된 고유 기회마다 시도 승패를 먼저 평균한 뒤 기회에 같은 가중치를 줬다. 표본수 보정 승률은 기존 `machine_support_adjusted_win_rate`의 Wilson형 **순위 점수**이며 통계적 우월성의 신뢰구간이 아니다.

| 기간 | 정책 | 선택 진입 시도 / 고유 기회 | 목표 선도 시도 | 기회 가중 승률 | 표본수 보정 승률 |
| --- | --- | ---: | ---: | ---: | ---: |
| 9/22 학습 | 기준 | 21 / 20 | 13 | 62.50% | 44.23% |
| 9/22 학습 | `winrate_initial_v1` | 11 / 11 | 10 | **90.91%** | **67.72%** |
| 9/23 날짜순 진단 | 기준 | 8 / 8 | 4 | 50.00% | 24.86% |
| 9/23 날짜순 진단 | `winrate_initial_v1` | 4 / 4 | 3 | **75.00%** | **35.62%** |
| 전체 | 기준 | 29 / 28 | 17 | 58.93% | 43.52% |
| 전체 | `winrate_initial_v1` | 15 / 15 | 13 | **86.67%** | **66.64%** |

상황 분류 자체의 전체 분모도 대사했다. `VWAP_NOT_EXTENDED`는 291행 중 목표 선도 212행, `VWAP_EXTENDED`는 60행 중 17행이다. 기준이 실제 `ENTER_NOW`를 선택한 시도만 보면 각각 **13/15**와 **4/14**다. 같은 고유 기회가 시간에 따라 두 상황을 지날 수 있으므로 상황별 고유 기회 수를 서로 더해 전체 모집단으로 쓰지 않는다. 새 규칙은 기준 선택 29시도 중 14시도를 제외한다(9/22: 승리 3·패배 7, 9/23: 승리 1·패배 3). PREMARKET·AFTERMARKET에는 승률로 지지되는 새 분기를 선택하지 않았다.

이전 `+11.895%` 당일 상승폭 분류는 이번 승률 단독 행동 규칙의 유형 기준에서 내린다. 그 분류의 `HIGH_ADVANCE` 무조건 차단은 9/22 표본수 보정 승률을 44.23%→42.55%로 낮췄고, 9/23 보정 승률은 24.86%→25.35%로 거의 같았다. `curr_vs_micro_vwap_bp` 경계는 양일 모두 보정 승률을 올렸다.

## 4. 확정 범위와 다음 소비 계약

`winrate_initial_v1`은 **승률 목적의 초기 정책안으로 규칙과 경계를 고정**한다. 다만 학습에서 697개 후보를 비교했고, 날짜순 진단의 선택 기회는 4개뿐이다. 또한 비교의 기준 `current.json` 세대는 9/23 데이터를 이미 기존 전략 선택에 사용했다. 9/23 성적은 새 경계 선택에는 사용하지 않았지만 기준 전략에 대한 완전 독립 검증은 아니다. 이 수치로 실제 체결 승률이나 다음 영업일 수익을 주장하지 않는다.

실행으로 옮길 때는 `entry_strategy_policy.features/select`의 진입 시점 필드·가용성 플래그, `mechanistic_entry_policy_decision`의 exact-scope `ENTER_NOW` 한정 veto, unknown 원천 결손 기록, 정책 hash·선택/직접 소비 영수증, 장후 전수 승률 분모와 의미 감시기를 같은 계약으로 바꿔야 한다. 현 [Plan Rebase](../plan-korStockScanPerformanceOptimization.rebase.md)는 승률을 진단 지표로 두고 단독 live/canary 승인을 금지한다. 이 문서는 사용자 요청에 따른 **승률 단독 정책 연구 결과**이며 그 전역 실행 권한 계약이나 실제 PID를 변경하지 않는다. 출시 여부를 판단할 때는 그 계약 충돌을 명시적으로 처리해야 한다.

재현 경계: [9/23 원천 report](../../data/report/ai_decision_action_outcome_calibration/ai_decision_action_outcome_calibration_2026-09-23.json)의 `artifact_content_sha256=10b29ced3cf6e61bee35e84de5e456db3dd78b562378cd0aef9db605fdc85564`(파일 바이트 SHA-256 `efa683652379d1ec593505ced80125228b004bfc128c8314f5ab04fdec01b160`), REGULAR current-structure 행 해시 `354291156bc8732b9056673371d1ebafc1f27a26835e48026b1f876b4fcc10d1`. `68.75bp`는 9/22 train의 고정 분위값이고, 9/23은 날짜순 진단에만 사용했다.
