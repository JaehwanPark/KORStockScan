# Cumulative Threshold Cycle Report - 2026-08-28

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-08-28`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 130 | 2250858 | 739 | -0.2546 | 0.5047 | 0.4628 |
| rolling_5d | 5 | 103375 | 25 | -0.3181 | 0.72 | 0.28 |
| rolling_10d | 10 | 172694 | 56 | -0.1495 | 0.7321 | 0.2679 |
| rolling_20d | 20 | 274282 | 70 | -0.1608 | 0.6857 | 0.2857 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 739 | -0.2546 | 0.5047 |
| cumulative | sim | 3493 | -1.2961 | 0.2439 |
| cumulative | combined | 4232 | -1.1143 | 0.2895 |
| rolling_5d | real | 25 | -0.3181 | 0.72 |
| rolling_5d | sim | 76 | -0.7486 | 0.3947 |
| rolling_5d | combined | 101 | -0.642 | 0.4752 |
| rolling_10d | real | 56 | -0.1495 | 0.7321 |
| rolling_10d | sim | 109 | -0.889 | 0.422 |
| rolling_10d | combined | 165 | -0.638 | 0.5273 |
| rolling_20d | real | 70 | -0.1608 | 0.6857 |
| rolling_20d | sim | 177 | -0.8696 | 0.4011 |
| rolling_20d | combined | 247 | -0.6687 | 0.4818 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 739 | -0.2546 | -3.1906 | 1.8 | 0.5047 | 0.4628 |
| cumulative | normal_only | 739 | -0.2546 | -3.1906 | 1.8 | 0.5047 | 0.4628 |
| cumulative | initial_only | 656 | -0.2696 | -3.16 | 1.76 | 0.503 | 0.4634 |
| cumulative | pyramid_activated | 32 | 0.3794 | -1.45 | 1.71 | 0.6562 | 0.3438 |
| cumulative | reversal_add_activated | 52 | -0.3152 | -4.32 | 2.18 | 0.4423 | 0.5192 |
| rolling_5d | all_completed_valid | 25 | -0.3181 | -3.51 | 1.04 | 0.72 | 0.28 |
| rolling_5d | normal_only | 25 | -0.3181 | -3.51 | 1.04 | 0.72 | 0.28 |
| rolling_5d | initial_only | 25 | -0.3181 | -3.51 | 1.04 | 0.72 | 0.28 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 56 | -0.1495 | -3.51 | 1.16 | 0.7321 | 0.2679 |
| rolling_10d | normal_only | 56 | -0.1495 | -3.51 | 1.16 | 0.7321 | 0.2679 |
| rolling_10d | initial_only | 54 | -0.1639 | -3.51 | 1.14 | 0.7407 | 0.2593 |
| rolling_10d | pyramid_activated | 1 | 1.71 | 1.71 | 1.71 | 1 | 0 |
| rolling_10d | reversal_add_activated | 1 | -1.23 | -1.23 | -1.23 | 0 | 1 |
| rolling_20d | all_completed_valid | 70 | -0.1608 | -3.51 | 1.16 | 0.6857 | 0.2857 |
| rolling_20d | normal_only | 70 | -0.1608 | -3.51 | 1.16 | 0.6857 | 0.2857 |
| rolling_20d | initial_only | 68 | -0.1726 | -3.51 | 1.16 | 0.6912 | 0.2794 |
| rolling_20d | pyramid_activated | 1 | 1.71 | 1.71 | 1.71 | 1 | 0 |
| rolling_20d | reversal_add_activated | 1 | -1.23 | -1.23 | -1.23 | 0 | 1 |

## Smoothing Source-Only Rolling Decision

| family | decision | samples_ready | EV_windows_positive | risk_ready | risk_review | next_action |
| --- | --- | --- | ---: | --- | --- | --- |
| soft_stop_whipsaw_confirmation | hold_sample | False | 3 | True | True | keep_collecting_exact_paths |
| holding_flow_ofi_smoothing | hold_sample | False | 0 | False | False | keep_collecting_exact_paths |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 212030 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 15 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 18430 | True | report_only_reference |
| cumulative | entry_split_order_plan | submit | 2331 | True | report_only_reference |
| cumulative | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 4230 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 177066 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 36779 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 26048 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 111 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 2641 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 3 | False | report_only_reference |
| cumulative | reversal_add | holding_exit | 105765 | False | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 18006 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 18006 | False | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 4700 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 216 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 121 | False | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2749 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 739 | True | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 739 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 1610 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 3786 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 374 | True | report_only_reference |
| rolling_5d | entry_split_order_plan | submit | 2331 | True | report_only_reference |
| rolling_5d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 142 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 6668 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 2025 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 945 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 38 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 615 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 3 | False | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 3421 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 757 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 757 | False | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 82 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 5 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 36 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 25 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 25 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 1610 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 5810 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 592 | True | report_only_reference |
| rolling_10d | entry_split_order_plan | submit | 2331 | True | report_only_reference |
| rolling_10d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 250 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 11152 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 3298 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 1557 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 71 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 1167 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 3 | False | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 5007 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 1605 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 1605 | False | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 1499 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 9 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 42 | True | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 56 | True | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 56 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 1610 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 8582 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 1093 | True | report_only_reference |
| rolling_20d | entry_split_order_plan | submit | 2331 | True | report_only_reference |
| rolling_20d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 290 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 22627 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 7040 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 3030 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 53 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 1690 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 3 | False | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 8302 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 2689 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 2689 | False | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 2044 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 11 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 56 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 70 | True | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 70 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 1610 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
