# Cumulative Threshold Cycle Report - 2026-07-30

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-07-30`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 101 | 1851354 | 637 | -0.2902 | 0.4741 | 0.4898 |
| rolling_5d | 5 | 10531 | 21 | -0.7695 | 0.5238 | 0.4762 |
| rolling_10d | 10 | 35038 | 59 | -0.4544 | 0.5085 | 0.4576 |
| rolling_20d | 20 | 71626 | 104 | -0.3359 | 0.4808 | 0.4615 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 637 | -0.2902 | 0.4741 |
| cumulative | sim | 3328 | -1.3192 | 0.2338 |
| cumulative | combined | 3965 | -1.1539 | 0.2724 |
| rolling_5d | real | 21 | -0.7695 | 0.5238 |
| rolling_5d | sim | 9 | -0.5533 | 0.2222 |
| rolling_5d | combined | 30 | -0.7047 | 0.4333 |
| rolling_10d | real | 59 | -0.4544 | 0.5085 |
| rolling_10d | sim | 19 | -0.8789 | 0.1053 |
| rolling_10d | combined | 78 | -0.5578 | 0.4103 |
| rolling_20d | real | 104 | -0.3359 | 0.4808 |
| rolling_20d | sim | 46 | -1.1393 | 0.2391 |
| rolling_20d | combined | 150 | -0.5823 | 0.4067 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 637 | -0.2902 | -3.16 | 1.89 | 0.4741 | 0.4898 |
| cumulative | normal_only | 637 | -0.2902 | -3.16 | 1.89 | 0.4741 | 0.4898 |
| cumulative | initial_only | 558 | -0.3096 | -2.89 | 1.89 | 0.4677 | 0.4946 |
| cumulative | pyramid_activated | 31 | 0.3365 | -1.45 | 1.59 | 0.6452 | 0.3548 |
| cumulative | reversal_add_activated | 49 | -0.3171 | -4.57 | 2.55 | 0.449 | 0.5102 |
| rolling_5d | all_completed_valid | 21 | -0.7695 | -3.71 | 1.37 | 0.5238 | 0.4762 |
| rolling_5d | normal_only | 21 | -0.7695 | -3.71 | 1.37 | 0.5238 | 0.4762 |
| rolling_5d | initial_only | 21 | -0.7695 | -3.71 | 1.37 | 0.5238 | 0.4762 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 59 | -0.4544 | -3.68 | 1.37 | 0.5085 | 0.4576 |
| rolling_10d | normal_only | 59 | -0.4544 | -3.68 | 1.37 | 0.5085 | 0.4576 |
| rolling_10d | initial_only | 56 | -0.4123 | -3.67 | 1.37 | 0.5179 | 0.4464 |
| rolling_10d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_10d | reversal_add_activated | 3 | -1.24 | -3.68 | 0.19 | 0.3333 | 0.6667 |
| rolling_20d | all_completed_valid | 104 | -0.3359 | -3.56 | 1.22 | 0.4808 | 0.4615 |
| rolling_20d | normal_only | 104 | -0.3359 | -3.56 | 1.22 | 0.4808 | 0.4615 |
| rolling_20d | initial_only | 95 | -0.3089 | -3.56 | 1.24 | 0.4842 | 0.4526 |
| rolling_20d | pyramid_activated | 3 | 0.52 | 0.13 | 0.93 | 1 | 0 |
| rolling_20d | reversal_add_activated | 6 | -1.19 | -3.68 | 0.19 | 0.1667 | 0.8333 |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 205041 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 15 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 16794 | True | report_only_reference |
| cumulative | entry_split_order_plan | submit | 181 | False | report_only_reference |
| cumulative | scale_in_split_order_plan | scale_in | 1 | True | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 3869 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 137578 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 24351 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 20669 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 95 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 385 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 227043 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 95641 | False | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 15237 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 15237 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 2219 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 216 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 104 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2696 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 637 | True | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 637 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 125 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 254 | False | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 59 | True | report_only_reference |
| rolling_5d | entry_split_order_plan | submit | 181 | False | report_only_reference |
| rolling_5d | scale_in_split_order_plan | scale_in | 1 | True | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 64 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 504 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 0 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 13 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 0 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 114 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 926 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 225 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 323 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 323 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 96 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 8 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 0 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 21 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 21 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 125 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 1252 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 190 | True | report_only_reference |
| rolling_10d | entry_split_order_plan | submit | 181 | False | report_only_reference |
| rolling_10d | scale_in_split_order_plan | scale_in | 1 | True | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 208 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 935 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 2 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 28 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 2 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 143 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 5738 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 2036 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 470 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 470 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 518 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 13 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 4 | False | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 59 | True | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 59 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 125 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 2159 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 442 | True | report_only_reference |
| rolling_20d | entry_split_order_plan | submit | 181 | False | report_only_reference |
| rolling_20d | scale_in_split_order_plan | scale_in | 1 | True | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 382 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 2070 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 21 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 201 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 10 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 144 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 13429 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 5169 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 669 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 669 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 658 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 68 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 16 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 33 | False | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 104 | True | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 104 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 125 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
