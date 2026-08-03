# Cumulative Threshold Cycle Report - 2026-08-03

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-08-03`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 105 | 1851643 | 655 | -0.27 | 0.4809 | 0.484 |
| rolling_5d | 5 | 75508 | 19 | 0.15 | 0.6842 | 0.3158 |
| rolling_10d | 10 | 82128 | 39 | -0.2082 | 0.6154 | 0.3846 |
| rolling_20d | 20 | 132760 | 112 | -0.1888 | 0.5268 | 0.4196 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 655 | -0.27 | 0.4809 |
| cumulative | sim | 3302 | -1.3221 | 0.2344 |
| cumulative | combined | 3957 | -1.148 | 0.2752 |
| rolling_5d | real | 19 | 0.15 | 0.6842 |
| rolling_5d | sim | 8 | -0.95 | 0.25 |
| rolling_5d | combined | 27 | -0.1759 | 0.5556 |
| rolling_10d | real | 39 | -0.2082 | 0.6154 |
| rolling_10d | sim | 14 | -0.7829 | 0.2143 |
| rolling_10d | combined | 53 | -0.36 | 0.5094 |
| rolling_20d | real | 112 | -0.1888 | 0.5268 |
| rolling_20d | sim | 40 | -0.8772 | 0.25 |
| rolling_20d | combined | 152 | -0.3699 | 0.4539 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 655 | -0.27 | -3.16 | 1.9 | 0.4809 | 0.484 |
| cumulative | normal_only | 655 | -0.27 | -3.16 | 1.9 | 0.4809 | 0.484 |
| cumulative | initial_only | 576 | -0.2859 | -2.89 | 1.9 | 0.4757 | 0.4878 |
| cumulative | pyramid_activated | 31 | 0.3365 | -1.45 | 1.59 | 0.6452 | 0.3548 |
| cumulative | reversal_add_activated | 49 | -0.3171 | -4.57 | 2.55 | 0.449 | 0.5102 |
| rolling_5d | all_completed_valid | 19 | 0.15 | -4.27 | 3.25 | 0.6842 | 0.3158 |
| rolling_5d | normal_only | 19 | 0.15 | -4.27 | 3.25 | 0.6842 | 0.3158 |
| rolling_5d | initial_only | 19 | 0.15 | -4.27 | 3.25 | 0.6842 | 0.3158 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 39 | -0.2082 | -3.93 | 1.66 | 0.6154 | 0.3846 |
| rolling_10d | normal_only | 39 | -0.2082 | -3.93 | 1.66 | 0.6154 | 0.3846 |
| rolling_10d | initial_only | 39 | -0.2082 | -3.93 | 1.66 | 0.6154 | 0.3846 |
| rolling_10d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_10d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_20d | all_completed_valid | 112 | -0.1888 | -3.56 | 1.41 | 0.5268 | 0.4196 |
| rolling_20d | normal_only | 112 | -0.1888 | -3.56 | 1.41 | 0.5268 | 0.4196 |
| rolling_20d | initial_only | 104 | -0.1518 | -3.56 | 1.44 | 0.5288 | 0.4135 |
| rolling_20d | pyramid_activated | 3 | 0.52 | 0.13 | 0.93 | 1 | 0 |
| rolling_20d | reversal_add_activated | 5 | -1.382 | -3.68 | 0.19 | 0.2 | 0.8 |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 201847 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 15 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 17069 | True | report_only_reference |
| cumulative | entry_split_order_plan | submit | 372 | True | report_only_reference |
| cumulative | scale_in_split_order_plan | scale_in | 1 | True | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 3914 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 141002 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 26372 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 21437 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 95 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 642 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 227506 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 96083 | False | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 15050 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 15050 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 2255 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 216 | False | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 105 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2689 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 655 | True | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 655 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 1535 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 1344 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 324 | True | report_only_reference |
| rolling_5d | entry_split_order_plan | submit | 372 | True | report_only_reference |
| rolling_5d | scale_in_split_order_plan | scale_in | 1 | True | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 54 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 5311 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 2845 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 865 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 0 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 299 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 2794 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 1184 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 179 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 179 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 39 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 4 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 5 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 19 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 19 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 1535 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 1587 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 368 | True | report_only_reference |
| rolling_10d | entry_split_order_plan | submit | 372 | True | report_only_reference |
| rolling_10d | scale_in_split_order_plan | scale_in | 1 | True | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 112 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 5597 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 2845 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 874 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 0 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 371 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 3502 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 1361 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 370 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 370 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 134 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 10 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 5 | False | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 39 | True | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 39 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 1535 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 3066 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 632 | True | report_only_reference |
| rolling_20d | entry_split_order_plan | submit | 372 | True | report_only_reference |
| rolling_20d | scale_in_split_order_plan | scale_in | 1 | True | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 398 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 6732 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 2865 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 996 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 10 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 400 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 13827 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 5862 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 662 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 662 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 590 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 68 | False | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 18 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 37 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 112 | True | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 112 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 1535 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
