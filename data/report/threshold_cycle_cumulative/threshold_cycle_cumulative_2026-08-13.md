# Cumulative Threshold Cycle Report - 2026-08-13

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-08-13`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 115 | 2034753 | 672 | -0.2657 | 0.4851 | 0.4807 |
| rolling_5d | 5 | 58177 | 3 | -0.4767 | 0.6667 | 0.3333 |
| rolling_10d | 10 | 183110 | 16 | -0.1812 | 0.625 | 0.375 |
| rolling_20d | 20 | 265238 | 56 | -0.1759 | 0.625 | 0.375 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 672 | -0.2657 | 0.4851 |
| cumulative | sim | 3349 | -1.3149 | 0.2371 |
| cumulative | combined | 4021 | -1.1396 | 0.2785 |
| rolling_5d | real | 3 | -0.4767 | 0.6667 |
| rolling_5d | sim | 33 | -0.9136 | 0.3939 |
| rolling_5d | combined | 36 | -0.8772 | 0.4167 |
| rolling_10d | real | 16 | -0.1812 | 0.625 |
| rolling_10d | sim | 47 | -0.8079 | 0.4255 |
| rolling_10d | combined | 63 | -0.6487 | 0.4762 |
| rolling_20d | real | 56 | -0.1759 | 0.625 |
| rolling_20d | sim | 61 | -0.8021 | 0.377 |
| rolling_20d | combined | 117 | -0.5024 | 0.4957 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 672 | -0.2657 | -3.16 | 1.9 | 0.4851 | 0.4807 |
| cumulative | normal_only | 672 | -0.2657 | -3.16 | 1.9 | 0.4851 | 0.4807 |
| cumulative | initial_only | 591 | -0.2823 | -3.14 | 1.9 | 0.4805 | 0.4839 |
| cumulative | pyramid_activated | 31 | 0.3365 | -1.45 | 1.59 | 0.6452 | 0.3548 |
| cumulative | reversal_add_activated | 51 | -0.2973 | -4.32 | 2.18 | 0.451 | 0.5098 |
| rolling_5d | all_completed_valid | 3 | -0.4767 | -4.01 | 1.63 | 0.6667 | 0.3333 |
| rolling_5d | normal_only | 3 | -0.4767 | -4.01 | 1.63 | 0.6667 | 0.3333 |
| rolling_5d | initial_only | 3 | -0.4767 | -4.01 | 1.63 | 0.6667 | 0.3333 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 16 | -0.1812 | -3.33 | 2.03 | 0.625 | 0.375 |
| rolling_10d | normal_only | 16 | -0.1812 | -3.33 | 2.03 | 0.625 | 0.375 |
| rolling_10d | initial_only | 14 | -0.2343 | -3.33 | 2.03 | 0.6429 | 0.3571 |
| rolling_10d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_10d | reversal_add_activated | 2 | 0.19 | -0.32 | 0.7 | 0.5 | 0.5 |
| rolling_20d | all_completed_valid | 56 | -0.1759 | -3.71 | 1.66 | 0.625 | 0.375 |
| rolling_20d | normal_only | 56 | -0.1759 | -3.71 | 1.66 | 0.625 | 0.375 |
| rolling_20d | initial_only | 54 | -0.1894 | -3.71 | 1.66 | 0.6296 | 0.3704 |
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
| cumulative | entry_mechanical_momentum | entry | 204714 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 15 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 17669 | True | report_only_reference |
| cumulative | entry_split_order_plan | submit | 2708 | True | report_only_reference |
| cumulative | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 3950 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 162241 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 32329 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 24020 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 100 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 1166 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 234447 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 99258 | False | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 15662 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 15662 | False | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 2673 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 216 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 111 | False | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2704 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 672 | True | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 672 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 2860 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 1266 | False | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 332 | True | report_only_reference |
| rolling_5d | entry_split_order_plan | submit | 2708 | True | report_only_reference |
| rolling_5d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 10 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 7802 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 2590 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 1002 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 4 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 215 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 4198 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 1795 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 345 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 345 | False | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 17 | False | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 1 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 11 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 3 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 3 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 2860 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 2867 | False | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 600 | True | report_only_reference |
| rolling_10d | entry_split_order_plan | submit | 2708 | True | report_only_reference |
| rolling_10d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 36 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 21239 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 5957 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 2583 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 6 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 524 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 6941 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 3175 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 612 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 612 | False | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 418 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 6 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 15 | False | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 16 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 16 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 2860 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 4454 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 968 | True | report_only_reference |
| rolling_20d | entry_split_order_plan | submit | 2708 | True | report_only_reference |
| rolling_20d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 148 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 26836 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 8802 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 3457 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 6 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 895 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 10443 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 4536 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 982 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 982 | False | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 552 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 16 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 20 | False | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 56 | True | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 56 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 2860 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
