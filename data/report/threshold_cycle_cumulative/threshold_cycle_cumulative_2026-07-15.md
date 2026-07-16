# Cumulative Threshold Cycle Report - 2026-07-15

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-07-15`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 86 | 2262505 | 550 | -0.2868 | 0.4727 | 0.4964 |
| rolling_5d | 5 | 24283 | 19 | -0.4358 | 0.4211 | 0.5789 |
| rolling_10d | 10 | 96088 | 105 | -0.454 | 0.5429 | 0.4476 |
| rolling_20d | 20 | 272332 | 246 | -0.077 | 0.5285 | 0.4309 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 550 | -0.2868 | 0.4727 |
| cumulative | sim | 4004 | -1.2946 | 0.2415 |
| cumulative | combined | 4554 | -1.1728 | 0.2694 |
| rolling_5d | real | 19 | -0.4358 | 0.4211 |
| rolling_5d | sim | 16 | -1.8556 | 0.1875 |
| rolling_5d | combined | 35 | -1.0849 | 0.3143 |
| rolling_10d | real | 105 | -0.454 | 0.5429 |
| rolling_10d | sim | 108 | -1.8472 | 0.287 |
| rolling_10d | combined | 213 | -1.1604 | 0.4131 |
| rolling_20d | real | 246 | -0.077 | 0.5285 |
| rolling_20d | sim | 285 | -1.4143 | 0.3158 |
| rolling_20d | combined | 531 | -0.7948 | 0.4143 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 550 | -0.2868 | -2.89 | 2.03 | 0.4727 | 0.4964 |
| cumulative | normal_only | 550 | -0.2868 | -2.89 | 2.03 | 0.4727 | 0.4964 |
| cumulative | initial_only | 477 | -0.3145 | -2.71 | 2.03 | 0.4612 | 0.5073 |
| cumulative | pyramid_activated | 31 | 0.3365 | -1.45 | 1.59 | 0.6452 | 0.3548 |
| cumulative | reversal_add_activated | 43 | -0.2588 | -4.57 | 2.55 | 0.4884 | 0.4651 |
| rolling_5d | all_completed_valid | 19 | -0.4358 | -3.2 | 0.7 | 0.4211 | 0.5789 |
| rolling_5d | normal_only | 19 | -0.4358 | -3.2 | 0.7 | 0.4211 | 0.5789 |
| rolling_5d | initial_only | 15 | -0.4587 | -3.2 | 0.61 | 0.3333 | 0.6667 |
| rolling_5d | pyramid_activated | 3 | 0.52 | 0.13 | 0.93 | 1 | 0 |
| rolling_5d | reversal_add_activated | 1 | -2.96 | -2.96 | -2.96 | 0 | 1 |
| rolling_10d | all_completed_valid | 105 | -0.454 | -4.56 | 2.55 | 0.5429 | 0.4476 |
| rolling_10d | normal_only | 105 | -0.454 | -4.56 | 2.55 | 0.5429 | 0.4476 |
| rolling_10d | initial_only | 87 | -0.4913 | -5.16 | 2.64 | 0.5172 | 0.4713 |
| rolling_10d | pyramid_activated | 5 | -0.002 | -2.12 | 0.93 | 0.8 | 0.2 |
| rolling_10d | reversal_add_activated | 13 | -0.3785 | -3.88 | 2.55 | 0.6154 | 0.3846 |
| rolling_20d | all_completed_valid | 246 | -0.077 | -4.32 | 2.59 | 0.5285 | 0.4309 |
| rolling_20d | normal_only | 246 | -0.077 | -4.32 | 2.59 | 0.5285 | 0.4309 |
| rolling_20d | initial_only | 198 | -0.0271 | -4.32 | 2.64 | 0.5303 | 0.4293 |
| rolling_20d | pyramid_activated | 7 | 0.5914 | -2.87 | 7.02 | 0.7143 | 0.2857 |
| rolling_20d | reversal_add_activated | 42 | -0.2548 | -4.57 | 2.55 | 0.5 | 0.4524 |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 295548 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 101 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 18905 | True | report_only_reference |
| cumulative | entry_split_order_plan | submit | 1812 | True | report_only_reference |
| cumulative | scale_in_split_order_plan | scale_in | 12 | True | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 3790 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 181234 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 47722 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 23297 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 106 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 621 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 254809 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 107430 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 19363 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 19363 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 1875 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 255 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 118 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2774 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 550 | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 550 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 1081 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 577 | False | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 190 | True | report_only_reference |
| rolling_5d | entry_split_order_plan | submit | 1812 | True | report_only_reference |
| rolling_5d | scale_in_split_order_plan | scale_in | 12 | True | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 79 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 1025 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 16 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 156 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 15 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 1 | False | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 5131 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 1882 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 172 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 172 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 116 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 68 | True | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 3 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 15 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 19 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 19 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 1081 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 2849 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 12 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 1079 | True | report_only_reference |
| rolling_10d | entry_split_order_plan | submit | 1812 | True | report_only_reference |
| rolling_10d | scale_in_split_order_plan | scale_in | 12 | True | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 516 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 4275 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 342 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 759 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 23 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 2 | False | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 17619 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 6078 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 466 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 466 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 725 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 93 | True | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 13 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 87 | True | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 105 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 105 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 1081 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 5960 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 12 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 2624 | True | report_only_reference |
| rolling_20d | entry_split_order_plan | submit | 1812 | True | report_only_reference |
| rolling_20d | scale_in_split_order_plan | scale_in | 12 | True | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 1536 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 11996 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 1846 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 2075 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 37 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 76 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 56443 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 21921 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 1407 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 1407 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 982 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 98 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 40 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 835 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 246 | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 246 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 1081 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
