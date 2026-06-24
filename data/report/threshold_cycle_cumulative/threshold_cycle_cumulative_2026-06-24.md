# Cumulative Threshold Cycle Report - 2026-06-24

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-06-24`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 65 | 1965715 | 301 | -0.4512 | 0.4286 | 0.5482 |
| rolling_5d | 5 | 79263 | 5 | -0.716 | 0.4 | 0.6 |
| rolling_10d | 10 | 664145 | 18 | -0.9611 | 0.2778 | 0.7222 |
| rolling_20d | 20 | 1483671 | 63 | -0.3906 | 0.4286 | 0.5714 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 301 | -0.4512 | 0.4286 |
| cumulative | sim | 3650 | -1.2834 | 0.2373 |
| cumulative | combined | 3951 | -1.22 | 0.2518 |
| rolling_5d | real | 5 | -0.716 | 0.4 |
| rolling_5d | sim | 342 | -1.6514 | 0.1813 |
| rolling_5d | combined | 347 | -1.638 | 0.1844 |
| rolling_10d | real | 18 | -0.9611 | 0.2778 |
| rolling_10d | sim | 1113 | -1.3643 | 0.2075 |
| rolling_10d | combined | 1131 | -1.3579 | 0.2087 |
| rolling_20d | real | 63 | -0.3906 | 0.4286 |
| rolling_20d | sim | 2913 | -1.3176 | 0.2279 |
| rolling_20d | combined | 2976 | -1.2979 | 0.2322 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 301 | -0.4512 | -2.36 | 1.52 | 0.4286 | 0.5482 |
| cumulative | normal_only | 301 | -0.4512 | -2.36 | 1.52 | 0.4286 | 0.5482 |
| cumulative | initial_only | 276 | -0.5133 | -2.38 | 1.52 | 0.413 | 0.5616 |
| cumulative | pyramid_activated | 24 | 0.2621 | -1.42 | 1.59 | 0.625 | 0.375 |
| cumulative | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |
| rolling_5d | all_completed_valid | 5 | -0.716 | -3.22 | 3.14 | 0.4 | 0.6 |
| rolling_5d | normal_only | 5 | -0.716 | -3.22 | 3.14 | 0.4 | 0.6 |
| rolling_5d | initial_only | 5 | -0.716 | -3.22 | 3.14 | 0.4 | 0.6 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 18 | -0.9611 | -3.44 | 1.38 | 0.2778 | 0.7222 |
| rolling_10d | normal_only | 18 | -0.9611 | -3.44 | 1.38 | 0.2778 | 0.7222 |
| rolling_10d | initial_only | 17 | -0.9488 | -3.44 | 1.38 | 0.2941 | 0.7059 |
| rolling_10d | pyramid_activated | 1 | -1.17 | -1.17 | -1.17 | 0 | 1 |
| rolling_10d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_20d | all_completed_valid | 63 | -0.3906 | -2.55 | 2.8 | 0.4286 | 0.5714 |
| rolling_20d | normal_only | 63 | -0.3906 | -2.55 | 2.8 | 0.4286 | 0.5714 |
| rolling_20d | initial_only | 60 | -0.4045 | -2.67 | 2.2 | 0.4333 | 0.5667 |
| rolling_20d | pyramid_activated | 3 | -0.1133 | -2.39 | 3.22 | 0.3333 | 0.6667 |
| rolling_20d | reversal_add_activated | 0 | - | - | - | - | - |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 289540 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 89 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 27546 | True | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 2135 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 167252 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 45591 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 20828 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 69 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 542 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 195295 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 84277 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 17672 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 17672 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 884 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 157 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 78 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 1900 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 301 | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 301 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 6192 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 3111 | False | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 2522 | True | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 169 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 4870 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 895 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 1156 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 1 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 7 | False | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 9404 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 3731 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 872 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 872 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 46 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 1 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 168 | True | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 5 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 5 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 6192 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 92237 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 3 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 9798 | True | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 977 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 55094 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 5367 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 7344 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 25 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 60 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 71244 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 31045 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 7249 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 7249 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 276 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 25 | True | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 8 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 850 | True | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 18 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 18 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 6192 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 192924 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 3 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 23186 | True | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 1908 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 120882 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 21391 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 18062 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 57 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 163 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 157118 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 68507 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 12815 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 12815 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 684 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 118 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 50 | True | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 1792 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 63 | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 63 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 6192 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
