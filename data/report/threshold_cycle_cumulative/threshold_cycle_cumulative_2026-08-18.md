# Cumulative Threshold Cycle Report - 2026-08-18

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-08-18`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 120 | 2078164 | 683 | -0.2636 | 0.4846 | 0.4788 |
| rolling_5d | 5 | 43409 | 8 | -0.1631 | 0.625 | 0.375 |
| rolling_10d | 10 | 101588 | 14 | -0.2061 | 0.5 | 0.3571 |
| rolling_20d | 20 | 302029 | 47 | -0.0071 | 0.617 | 0.3404 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 683 | -0.2636 | 0.4846 |
| cumulative | sim | 3384 | -1.3092 | 0.2382 |
| cumulative | combined | 4067 | -1.1336 | 0.2796 |
| rolling_5d | real | 8 | -0.1631 | 0.625 |
| rolling_5d | sim | 35 | -0.7677 | 0.3429 |
| rolling_5d | combined | 43 | -0.6552 | 0.3953 |
| rolling_10d | real | 14 | -0.2061 | 0.5 |
| rolling_10d | sim | 68 | -0.8385 | 0.3676 |
| rolling_10d | combined | 82 | -0.7306 | 0.3902 |
| rolling_20d | real | 47 | -0.0071 | 0.617 |
| rolling_20d | sim | 90 | -0.8049 | 0.3778 |
| rolling_20d | combined | 137 | -0.5312 | 0.4599 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 683 | -0.2636 | -3.16 | 1.89 | 0.4846 | 0.4788 |
| cumulative | normal_only | 683 | -0.2636 | -3.16 | 1.89 | 0.4846 | 0.4788 |
| cumulative | initial_only | 602 | -0.2795 | -3.14 | 1.89 | 0.4801 | 0.4817 |
| cumulative | pyramid_activated | 31 | 0.3365 | -1.45 | 1.59 | 0.6452 | 0.3548 |
| cumulative | reversal_add_activated | 51 | -0.2973 | -4.32 | 2.18 | 0.451 | 0.5098 |
| rolling_5d | all_completed_valid | 8 | -0.1631 | -3.22 | 1.86 | 0.625 | 0.375 |
| rolling_5d | normal_only | 8 | -0.1631 | -3.22 | 1.86 | 0.625 | 0.375 |
| rolling_5d | initial_only | 8 | -0.1631 | -3.22 | 1.86 | 0.625 | 0.375 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 14 | -0.2061 | -3.22 | 1.63 | 0.5 | 0.3571 |
| rolling_10d | normal_only | 14 | -0.2061 | -3.22 | 1.63 | 0.5 | 0.3571 |
| rolling_10d | initial_only | 14 | -0.2061 | -3.22 | 1.63 | 0.5 | 0.3571 |
| rolling_10d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_10d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_20d | all_completed_valid | 47 | -0.0071 | -3.33 | 2.03 | 0.617 | 0.3404 |
| rolling_20d | normal_only | 47 | -0.0071 | -3.33 | 2.03 | 0.617 | 0.3404 |
| rolling_20d | initial_only | 45 | -0.0159 | -3.33 | 2.03 | 0.6222 | 0.3333 |
| rolling_20d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_20d | reversal_add_activated | 2 | 0.19 | -0.32 | 0.7 | 0.5 | 0.5 |

## Smoothing Source-Only Rolling Decision

| family | decision | samples_ready | EV_windows_positive | risk_ready | risk_review | next_action |
| --- | --- | --- | ---: | --- | --- | --- |
| soft_stop_whipsaw_confirmation | hold_sample | False | 0 | False | False | keep_collecting_exact_paths |
| holding_flow_ofi_smoothing | hold_sample | False | 0 | False | False | keep_collecting_exact_paths |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 206220 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 15 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 17838 | True | report_only_reference |
| cumulative | entry_split_order_plan | submit | 3171 | True | report_only_reference |
| cumulative | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 3980 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 165914 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 33481 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 24491 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 100 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 1474 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 238100 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 100758 | False | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 16401 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 16401 | False | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 3201 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 216 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 112 | False | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2707 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 683 | True | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 683 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 3145 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 1506 | False | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 169 | True | report_only_reference |
| rolling_5d | entry_split_order_plan | submit | 3171 | True | report_only_reference |
| rolling_5d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 30 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 3673 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 1152 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 471 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 0 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 308 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 3653 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 1500 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 739 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 739 | False | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 528 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 1 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 3 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 8 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 8 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 3145 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 2772 | False | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 501 | True | report_only_reference |
| rolling_10d | entry_split_order_plan | submit | 3171 | True | report_only_reference |
| rolling_10d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 40 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 11475 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 3742 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 1473 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 4 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 523 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 7851 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 3295 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 1084 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 1084 | False | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 545 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 2 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 14 | False | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 14 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 14 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 3145 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 5717 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 1093 | True | report_only_reference |
| rolling_20d | entry_split_order_plan | submit | 3171 | True | report_only_reference |
| rolling_20d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 120 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 30223 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 9954 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 3919 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 6 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 1131 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 13388 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 5859 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 1530 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 1530 | False | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 985 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 11 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 23 | False | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 47 | True | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 47 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 3145 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
