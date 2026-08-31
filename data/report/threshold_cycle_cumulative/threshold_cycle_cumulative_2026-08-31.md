# Cumulative Threshold Cycle Report - 2026-08-31

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-08-31`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 133 | 2273410 | 741 | -0.2515 | 0.5047 | 0.4629 |
| rolling_5d | 5 | 57793 | 9 | 0.2222 | 0.7778 | 0.2222 |
| rolling_10d | 10 | 125927 | 27 | -0.2275 | 0.7037 | 0.2963 |
| rolling_20d | 20 | 273594 | 72 | -0.1312 | 0.6806 | 0.2917 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 741 | -0.2515 | 0.5047 |
| cumulative | sim | 3504 | -1.2954 | 0.2446 |
| cumulative | combined | 4245 | -1.1132 | 0.29 |
| rolling_5d | real | 9 | 0.2222 | 0.7778 |
| rolling_5d | sim | 30 | -0.728 | 0.5 |
| rolling_5d | combined | 39 | -0.5087 | 0.5641 |
| rolling_10d | real | 27 | -0.2275 | 0.7037 |
| rolling_10d | sim | 87 | -0.7905 | 0.4023 |
| rolling_10d | combined | 114 | -0.6571 | 0.4737 |
| rolling_20d | real | 72 | -0.1312 | 0.6806 |
| rolling_20d | sim | 173 | -0.8605 | 0.4046 |
| rolling_20d | combined | 245 | -0.6461 | 0.4857 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 741 | -0.2515 | -3.18 | 1.8 | 0.5047 | 0.4629 |
| cumulative | normal_only | 741 | -0.2515 | -3.18 | 1.8 | 0.5047 | 0.4629 |
| cumulative | initial_only | 658 | -0.2661 | -3.16 | 1.77 | 0.503 | 0.4635 |
| cumulative | pyramid_activated | 32 | 0.3794 | -1.45 | 1.71 | 0.6562 | 0.3438 |
| cumulative | reversal_add_activated | 52 | -0.3152 | -4.32 | 2.18 | 0.4423 | 0.5192 |
| rolling_5d | all_completed_valid | 9 | 0.2222 | -3.51 | 1.88 | 0.7778 | 0.2222 |
| rolling_5d | normal_only | 9 | 0.2222 | -3.51 | 1.88 | 0.7778 | 0.2222 |
| rolling_5d | initial_only | 9 | 0.2222 | -3.51 | 1.88 | 0.7778 | 0.2222 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 27 | -0.2275 | -3.51 | 1.07 | 0.7037 | 0.2963 |
| rolling_10d | normal_only | 27 | -0.2275 | -3.51 | 1.07 | 0.7037 | 0.2963 |
| rolling_10d | initial_only | 27 | -0.2275 | -3.51 | 1.07 | 0.7037 | 0.2963 |
| rolling_10d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_10d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_20d | all_completed_valid | 72 | -0.1312 | -3.38 | 1.2105 | 0.6806 | 0.2917 |
| rolling_20d | normal_only | 72 | -0.1312 | -3.38 | 1.2105 | 0.6806 | 0.2917 |
| rolling_20d | initial_only | 70 | -0.1418 | -3.51 | 1.16 | 0.6857 | 0.2857 |
| rolling_20d | pyramid_activated | 1 | 1.71 | 1.71 | 1.71 | 1 | 0 |
| rolling_20d | reversal_add_activated | 1 | -1.23 | -1.23 | -1.23 | 0 | 1 |

## Smoothing Source-Only Rolling Decision

| family | decision | samples_ready | EV_windows_positive | risk_ready | risk_review | next_action |
| --- | --- | --- | ---: | --- | --- | --- |
| soft_stop_whipsaw_confirmation | hold_sample | False | 2 | True | True | keep_collecting_exact_paths |
| holding_flow_ofi_smoothing | hold_sample | False | 0 | False | False | keep_collecting_exact_paths |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 213175 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 15 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 18487 | True | report_only_reference |
| cumulative | entry_split_order_plan | submit | 2758 | True | report_only_reference |
| cumulative | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 4263 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 178301 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 37187 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 26264 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 113 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 2686 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 2 | False | report_only_reference |
| cumulative | reversal_add | holding_exit | 106127 | False | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 18122 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 18122 | False | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 4707 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 216 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 121 | False | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2752 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 741 | True | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 741 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 1949 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 2702 | False | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 174 | True | report_only_reference |
| rolling_5d | entry_split_order_plan | submit | 2758 | True | report_only_reference |
| rolling_5d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 103 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 3946 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 1208 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 570 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 23 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 151 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 2 | False | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 1253 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 182 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 182 | False | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 22 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 2 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 39 | True | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 9 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 9 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 1949 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 4931 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 431 | True | report_only_reference |
| rolling_10d | entry_split_order_plan | submit | 2758 | True | report_only_reference |
| rolling_10d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 175 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 7903 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 2433 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 1161 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 34 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 660 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 2 | False | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 3783 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 873 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 873 | False | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 89 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 5 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 39 | True | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 27 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 27 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 1949 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 9506 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 968 | True | report_only_reference |
| rolling_20d | entry_split_order_plan | submit | 2758 | True | report_only_reference |
| rolling_20d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 323 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 19731 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 5731 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 2625 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 49 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 1678 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 2 | False | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 8151 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 2703 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 2703 | False | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 2045 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 11 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 53 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 72 | True | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 72 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 1949 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
