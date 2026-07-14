# Cumulative Threshold Cycle Report - 2026-07-14

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-07-14`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 85 | 2248685 | 536 | -0.2818 | 0.4757 | 0.4925 |
| rolling_5d | 5 | 20946 | 17 | -0.3018 | 0.5882 | 0.4118 |
| rolling_10d | 10 | 82268 | 91 | -0.4499 | 0.5714 | 0.4176 |
| rolling_20d | 20 | 282970 | 235 | -0.0647 | 0.5362 | 0.4213 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 536 | -0.2818 | 0.4757 |
| cumulative | sim | 3999 | -1.2946 | 0.2416 |
| cumulative | combined | 4535 | -1.1749 | 0.2692 |
| rolling_5d | real | 17 | -0.3018 | 0.5882 |
| rolling_5d | sim | 19 | -1.3311 | 0.3684 |
| rolling_5d | combined | 36 | -0.845 | 0.4722 |
| rolling_10d | real | 91 | -0.4499 | 0.5714 |
| rolling_10d | sim | 103 | -1.8749 | 0.2913 |
| rolling_10d | combined | 194 | -1.2064 | 0.4227 |
| rolling_20d | real | 235 | -0.0647 | 0.5362 |
| rolling_20d | sim | 349 | -1.4111 | 0.2865 |
| rolling_20d | combined | 584 | -0.8693 | 0.387 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 536 | -0.2818 | -2.87 | 2.08 | 0.4757 | 0.4925 |
| cumulative | normal_only | 536 | -0.2818 | -2.87 | 2.08 | 0.4757 | 0.4925 |
| cumulative | initial_only | 467 | -0.3099 | -2.71 | 2.07 | 0.4668 | 0.5011 |
| cumulative | pyramid_activated | 28 | 0.3168 | -2.12 | 3.15 | 0.6071 | 0.3929 |
| cumulative | reversal_add_activated | 42 | -0.1945 | -4.57 | 2.55 | 0.5 | 0.4524 |
| rolling_5d | all_completed_valid | 17 | -0.3018 | -3.67 | 1.98 | 0.5882 | 0.4118 |
| rolling_5d | normal_only | 17 | -0.3018 | -3.67 | 1.98 | 0.5882 | 0.4118 |
| rolling_5d | initial_only | 15 | -0.5653 | -3.67 | 1.68 | 0.5333 | 0.4667 |
| rolling_5d | pyramid_activated | 1 | 0.55 | 0.55 | 0.55 | 1 | 0 |
| rolling_5d | reversal_add_activated | 1 | 2.8 | 2.8 | 2.8 | 1 | 0 |
| rolling_10d | all_completed_valid | 91 | -0.4499 | -4.6 | 2.64 | 0.5714 | 0.4176 |
| rolling_10d | normal_only | 91 | -0.4499 | -4.6 | 2.64 | 0.5714 | 0.4176 |
| rolling_10d | initial_only | 77 | -0.4858 | -5.3 | 3.27 | 0.5584 | 0.4286 |
| rolling_10d | pyramid_activated | 2 | -0.785 | -2.12 | 0.55 | 0.5 | 0.5 |
| rolling_10d | reversal_add_activated | 12 | -0.1633 | -3.88 | 2.55 | 0.6667 | 0.3333 |
| rolling_20d | all_completed_valid | 235 | -0.0647 | -4.44 | 2.64 | 0.5362 | 0.4213 |
| rolling_20d | normal_only | 235 | -0.0647 | -4.44 | 2.64 | 0.5362 | 0.4213 |
| rolling_20d | initial_only | 191 | -0.0159 | -4.32 | 2.64 | 0.5445 | 0.4136 |
| rolling_20d | pyramid_activated | 4 | 0.645 | -2.87 | 7.02 | 0.5 | 0.5 |
| rolling_20d | reversal_add_activated | 41 | -0.1888 | -4.57 | 2.55 | 0.5122 | 0.439 |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 295397 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 101 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 18834 | False | report_only_reference |
| cumulative | entry_split_order_plan | submit | 1217 | False | report_only_reference |
| cumulative | scale_in_split_order_plan | scale_in | 1 | True | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 3743 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 180640 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 47707 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 23207 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 104 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 621 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 251856 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 105991 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 19245 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 19245 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 1865 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 187 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 115 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2760 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 536 | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 536 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 548 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 751 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 249 | False | report_only_reference |
| rolling_5d | entry_split_order_plan | submit | 1217 | False | report_only_reference |
| rolling_5d | scale_in_split_order_plan | scale_in | 1 | True | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 96 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 903 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 32 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 120 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 13 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 1 | False | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 3985 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 1464 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 56 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 56 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 115 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 12 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 17 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 17 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 548 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 2698 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 12 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 1008 | False | report_only_reference |
| rolling_10d | entry_split_order_plan | submit | 1217 | False | report_only_reference |
| rolling_10d | scale_in_split_order_plan | scale_in | 1 | True | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 469 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 3681 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 327 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 669 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 21 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 2 | False | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 14666 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 4639 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 348 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 348 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 715 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 25 | True | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 10 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 73 | True | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 91 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 91 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 548 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 5857 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 12 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 2807 | False | report_only_reference |
| rolling_20d | entry_split_order_plan | submit | 1217 | False | report_only_reference |
| rolling_20d | scale_in_split_order_plan | scale_in | 1 | True | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 1608 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 13388 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 2116 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 2379 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 35 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 79 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 56561 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 21714 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 1573 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 1573 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 981 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 30 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 37 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 860 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 235 | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 235 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 548 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
