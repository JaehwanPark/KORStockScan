# Cumulative Threshold Cycle Report - 2026-06-25

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-06-25`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 66 | 1990173 | 304 | -0.4566 | 0.4276 | 0.5493 |
| rolling_5d | 5 | 103721 | 8 | -0.8213 | 0.375 | 0.625 |
| rolling_10d | 10 | 566310 | 19 | -1.0068 | 0.3158 | 0.6842 |
| rolling_20d | 20 | 1362462 | 65 | -0.3858 | 0.4308 | 0.5692 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 304 | -0.4566 | 0.4276 |
| cumulative | sim | 3719 | -1.2854 | 0.2358 |
| cumulative | combined | 4023 | -1.2227 | 0.2503 |
| rolling_5d | real | 8 | -0.8213 | 0.375 |
| rolling_5d | sim | 411 | -1.6072 | 0.1776 |
| rolling_5d | combined | 419 | -1.5922 | 0.1814 |
| rolling_10d | real | 19 | -1.0068 | 0.3158 |
| rolling_10d | sim | 1060 | -1.3933 | 0.2066 |
| rolling_10d | combined | 1079 | -1.3865 | 0.2085 |
| rolling_20d | real | 65 | -0.3858 | 0.4308 |
| rolling_20d | sim | 2831 | -1.3233 | 0.2268 |
| rolling_20d | combined | 2896 | -1.3023 | 0.2314 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 304 | -0.4566 | -2.37 | 1.52 | 0.4276 | 0.5493 |
| cumulative | normal_only | 304 | -0.4566 | -2.37 | 1.52 | 0.4276 | 0.5493 |
| cumulative | initial_only | 279 | -0.5185 | -2.39 | 1.52 | 0.4122 | 0.5627 |
| cumulative | pyramid_activated | 24 | 0.2621 | -1.42 | 1.59 | 0.625 | 0.375 |
| cumulative | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |
| rolling_5d | all_completed_valid | 8 | -0.8213 | -3.22 | 3.14 | 0.375 | 0.625 |
| rolling_5d | normal_only | 8 | -0.8213 | -3.22 | 3.14 | 0.375 | 0.625 |
| rolling_5d | initial_only | 8 | -0.8213 | -3.22 | 3.14 | 0.375 | 0.625 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 19 | -1.0068 | -3.44 | 1.38 | 0.3158 | 0.6842 |
| rolling_10d | normal_only | 19 | -1.0068 | -3.44 | 1.38 | 0.3158 | 0.6842 |
| rolling_10d | initial_only | 18 | -0.9978 | -3.44 | 1.38 | 0.3333 | 0.6667 |
| rolling_10d | pyramid_activated | 1 | -1.17 | -1.17 | -1.17 | 0 | 1 |
| rolling_10d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_20d | all_completed_valid | 65 | -0.3858 | -2.67 | 2.8 | 0.4308 | 0.5692 |
| rolling_20d | normal_only | 65 | -0.3858 | -2.67 | 2.8 | 0.4308 | 0.5692 |
| rolling_20d | initial_only | 62 | -0.399 | -2.67 | 2.2 | 0.4355 | 0.5645 |
| rolling_20d | pyramid_activated | 3 | -0.1133 | -2.39 | 3.22 | 0.3333 | 0.6667 |
| rolling_20d | reversal_add_activated | 0 | - | - | - | - | - |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 289588 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 89 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 27938 | True | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 2254 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 169238 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 45876 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 21222 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 69 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 545 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 198366 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 85509 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 17956 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 17956 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 893 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 157 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 78 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 1939 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 304 | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 304 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 6291 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 3159 | False | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 2914 | True | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 288 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 6856 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 1180 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 1550 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 2 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 10 | False | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 12475 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 4963 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 1156 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 1156 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 55 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 1 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 207 | True | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 8 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 8 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 6291 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 75717 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 8674 | True | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 981 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 48125 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 4284 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 6626 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 17 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 30 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 60662 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 25507 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 6442 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 6442 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 265 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 23 | True | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 8 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 832 | True | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 19 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 19 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 6291 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 167846 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 3 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 22305 | True | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 2026 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 107742 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 18482 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 16950 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 45 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 166 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 150052 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 65664 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 11679 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 11679 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 660 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 118 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 49 | True | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 1803 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 65 | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 65 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 6291 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
