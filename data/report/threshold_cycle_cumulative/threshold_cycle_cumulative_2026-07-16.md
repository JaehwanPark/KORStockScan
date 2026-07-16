# Cumulative Threshold Cycle Report - 2026-07-16

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-07-16`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 87 | 2266641 | 553 | -0.2865 | 0.4702 | 0.4991 |
| rolling_5d | 5 | 28419 | 21 | -0.4162 | 0.381 | 0.619 |
| rolling_10d | 10 | 84268 | 83 | -0.6473 | 0.506 | 0.4819 |
| rolling_20d | 20 | 251611 | 242 | -0.0788 | 0.5289 | 0.4298 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 553 | -0.2865 | 0.4702 |
| cumulative | sim | 4011 | -1.2931 | 0.2421 |
| cumulative | combined | 4564 | -1.1711 | 0.2697 |
| rolling_5d | real | 21 | -0.4162 | 0.381 |
| rolling_5d | sim | 23 | -1.423 | 0.3043 |
| rolling_5d | combined | 44 | -0.9425 | 0.3409 |
| rolling_10d | real | 83 | -0.6473 | 0.506 |
| rolling_10d | sim | 96 | -1.799 | 0.3125 |
| rolling_10d | combined | 179 | -1.265 | 0.4022 |
| rolling_20d | real | 242 | -0.0788 | 0.5289 |
| rolling_20d | sim | 223 | -1.4173 | 0.3632 |
| rolling_20d | combined | 465 | -0.7207 | 0.4495 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 553 | -0.2865 | -2.87 | 2.03 | 0.4702 | 0.4991 |
| cumulative | normal_only | 553 | -0.2865 | -2.87 | 2.03 | 0.4702 | 0.4991 |
| cumulative | initial_only | 479 | -0.3142 | -2.71 | 2.03 | 0.4593 | 0.5094 |
| cumulative | pyramid_activated | 31 | 0.3365 | -1.45 | 1.59 | 0.6452 | 0.3548 |
| cumulative | reversal_add_activated | 44 | -0.2582 | -4.57 | 2.55 | 0.4773 | 0.4773 |
| rolling_5d | all_completed_valid | 21 | -0.4162 | -2.96 | 0.61 | 0.381 | 0.619 |
| rolling_5d | normal_only | 21 | -0.4162 | -2.96 | 0.61 | 0.381 | 0.619 |
| rolling_5d | initial_only | 16 | -0.4444 | -3.2 | 0.61 | 0.3125 | 0.6875 |
| rolling_5d | pyramid_activated | 3 | 0.52 | 0.13 | 0.93 | 1 | 0 |
| rolling_5d | reversal_add_activated | 2 | -1.595 | -2.96 | -0.23 | 0 | 1 |
| rolling_10d | all_completed_valid | 83 | -0.6473 | -4.6 | 1.93 | 0.506 | 0.4819 |
| rolling_10d | normal_only | 83 | -0.6473 | -4.6 | 1.93 | 0.506 | 0.4819 |
| rolling_10d | initial_only | 71 | -0.7546 | -5.16 | 1.93 | 0.4789 | 0.507 |
| rolling_10d | pyramid_activated | 4 | 0.5275 | 0.13 | 0.93 | 1 | 0 |
| rolling_10d | reversal_add_activated | 8 | -0.2825 | -4.6 | 2.8 | 0.5 | 0.5 |
| rolling_20d | all_completed_valid | 242 | -0.0788 | -4.32 | 2.57 | 0.5289 | 0.4298 |
| rolling_20d | normal_only | 242 | -0.0788 | -4.32 | 2.57 | 0.5289 | 0.4298 |
| rolling_20d | initial_only | 194 | -0.0361 | -4.32 | 2.59 | 0.5309 | 0.4278 |
| rolling_20d | pyramid_activated | 7 | 0.5914 | -2.87 | 7.02 | 0.7143 | 0.2857 |
| rolling_20d | reversal_add_activated | 42 | -0.2188 | -4.57 | 2.55 | 0.5 | 0.4524 |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 295604 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 101 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 18930 | True | report_only_reference |
| cumulative | entry_split_order_plan | submit | 1731 | False | report_only_reference |
| cumulative | scale_in_split_order_plan | scale_in | 3 | True | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 3795 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 181330 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 47723 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 23306 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 106 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 621 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 255604 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 107908 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 19374 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 19374 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 1881 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 255 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 118 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2776 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 553 | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 553 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 797 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 633 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 215 | True | report_only_reference |
| rolling_5d | entry_split_order_plan | submit | 1731 | False | report_only_reference |
| rolling_5d | scale_in_split_order_plan | scale_in | 3 | True | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 84 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 1121 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 17 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 165 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 15 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 1 | False | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 5926 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 2360 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 183 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 183 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 122 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 68 | True | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 3 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 17 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 21 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 21 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 797 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 2247 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 12 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 855 | True | report_only_reference |
| rolling_10d | entry_split_order_plan | submit | 1731 | False | report_only_reference |
| rolling_10d | scale_in_split_order_plan | scale_in | 3 | True | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 435 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 3515 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 209 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 591 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 21 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 1 | False | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 15625 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 5474 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 436 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 436 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 658 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 68 | True | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 11 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 64 | True | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 83 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 83 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 797 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 5963 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 12 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 2391 | True | report_only_reference |
| rolling_20d | entry_split_order_plan | submit | 1731 | False | report_only_reference |
| rolling_20d | scale_in_split_order_plan | scale_in | 3 | True | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 1510 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 10865 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 1578 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 1573 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 37 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 65 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 53429 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 21323 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 1208 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 1208 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 979 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 98 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 39 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 754 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 242 | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 242 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 797 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
