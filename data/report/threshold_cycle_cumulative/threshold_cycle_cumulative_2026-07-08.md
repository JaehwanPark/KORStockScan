# Cumulative Threshold Cycle Report - 2026-07-08

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-07-08`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 79 | 2220488 | 511 | -0.2853 | 0.4716 | 0.4951 |
| rolling_5d | 5 | 54071 | 66 | -0.5406 | 0.5758 | 0.4091 |
| rolling_10d | 10 | 205458 | 200 | -0.032 | 0.545 | 0.405 |
| rolling_20d | 20 | 349563 | 215 | -0.0629 | 0.5302 | 0.4233 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 511 | -0.2853 | 0.4716 |
| cumulative | sim | 3967 | -1.2925 | 0.2407 |
| cumulative | combined | 4478 | -1.1776 | 0.2671 |
| rolling_5d | real | 66 | -0.5406 | 0.5758 |
| rolling_5d | sim | 71 | -2.023 | 0.2676 |
| rolling_5d | combined | 137 | -1.3088 | 0.4161 |
| rolling_10d | real | 200 | -0.032 | 0.545 |
| rolling_10d | sim | 179 | -1.4366 | 0.3631 |
| rolling_10d | combined | 379 | -0.6954 | 0.4591 |
| rolling_20d | real | 215 | -0.0629 | 0.5302 |
| rolling_20d | sim | 745 | -1.54 | 0.2215 |
| rolling_20d | combined | 960 | -1.2092 | 0.2906 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 511 | -0.2853 | -2.73 | 2.08 | 0.4716 | 0.4951 |
| cumulative | normal_only | 511 | -0.2853 | -2.73 | 2.08 | 0.4716 | 0.4951 |
| cumulative | initial_only | 445 | -0.3064 | -2.69 | 2.08 | 0.4629 | 0.5034 |
| cumulative | pyramid_activated | 27 | 0.3081 | -2.12 | 3.15 | 0.5926 | 0.4074 |
| cumulative | reversal_add_activated | 40 | -0.2685 | -4.6 | 2.18 | 0.5 | 0.45 |
| rolling_5d | all_completed_valid | 66 | -0.5406 | -5.3 | 3.27 | 0.5758 | 0.4091 |
| rolling_5d | normal_only | 66 | -0.5406 | -5.3 | 3.27 | 0.5758 | 0.4091 |
| rolling_5d | initial_only | 55 | -0.5278 | -5.32 | 3.31 | 0.5636 | 0.4182 |
| rolling_5d | pyramid_activated | 1 | -2.12 | -2.12 | -2.12 | 0 | 1 |
| rolling_5d | reversal_add_activated | 10 | -0.453 | -4.6 | 1.48 | 0.7 | 0.3 |
| rolling_10d | all_completed_valid | 200 | -0.032 | -4.56 | 2.64 | 0.545 | 0.405 |
| rolling_10d | normal_only | 200 | -0.032 | -4.56 | 2.64 | 0.545 | 0.405 |
| rolling_10d | initial_only | 160 | 0.0447 | -4.52 | 2.93 | 0.5563 | 0.3937 |
| rolling_10d | pyramid_activated | 3 | 0.6767 | -2.87 | 7.02 | 0.3333 | 0.6667 |
| rolling_10d | reversal_add_activated | 38 | -0.2255 | -4.6 | 2.55 | 0.5263 | 0.4211 |
| rolling_20d | all_completed_valid | 215 | -0.0629 | -4.48 | 2.75 | 0.5302 | 0.4233 |
| rolling_20d | normal_only | 215 | -0.0629 | -4.48 | 2.75 | 0.5302 | 0.4233 |
| rolling_20d | initial_only | 174 | 0.0102 | -4.32 | 2.93 | 0.5402 | 0.4138 |
| rolling_20d | pyramid_activated | 3 | 0.6767 | -2.87 | 7.02 | 0.3333 | 0.6667 |
| rolling_20d | reversal_add_activated | 39 | -0.2644 | -4.6 | 2.55 | 0.5128 | 0.4359 |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 294226 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 101 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 18507 | True | report_only_reference |
| cumulative | entry_split_order_plan | submit | 5732 | True | report_only_reference |
| cumulative | scale_in_split_order_plan | scale_in | 8 | True | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 3578 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 179612 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 47666 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 23061 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 93 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 620 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 246870 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 103964 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 19166 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 19166 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 1744 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 187 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 115 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2744 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 511 | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 511 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 3609 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 1527 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 12 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 681 | True | report_only_reference |
| rolling_5d | entry_split_order_plan | submit | 5732 | True | report_only_reference |
| rolling_5d | scale_in_split_order_plan | scale_in | 8 | True | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 304 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 2653 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 286 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 523 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 10 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 1 | False | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 9680 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 2612 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 269 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 269 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 594 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 25 | True | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 10 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 57 | True | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 66 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 66 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 3609 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 4585 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 12 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 1968 | True | report_only_reference |
| rolling_10d | entry_split_order_plan | submit | 5732 | True | report_only_reference |
| rolling_10d | scale_in_split_order_plan | scale_in | 8 | True | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 1293 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 9147 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 1521 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 1328 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 24 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 64 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 44695 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 17379 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 1000 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 1000 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 842 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 30 | True | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 36 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 722 | True | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 200 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 200 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 3609 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 8822 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 12 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 4477 | True | report_only_reference |
| rolling_20d | entry_split_order_plan | submit | 5732 | True | report_only_reference |
| rolling_20d | scale_in_split_order_plan | scale_in | 8 | True | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 1745 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 19315 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 2970 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 3389 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 24 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 85 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 62182 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 23924 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 2431 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 2431 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 972 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 30 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 39 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 1068 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 215 | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 215 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 3609 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
