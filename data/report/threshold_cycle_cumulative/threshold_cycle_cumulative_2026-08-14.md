# Cumulative Threshold Cycle Report - 2026-08-14

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-08-14`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 116 | 2056117 | 680 | -0.2627 | 0.4853 | 0.4779 |
| rolling_5d | 5 | 79541 | 11 | -0.14 | 0.5455 | 0.2727 |
| rolling_10d | 10 | 150814 | 11 | -0.14 | 0.5455 | 0.2727 |
| rolling_20d | 20 | 286602 | 64 | -0.1556 | 0.6094 | 0.3594 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 680 | -0.2627 | 0.4853 |
| cumulative | sim | 3360 | -1.3091 | 0.2378 |
| cumulative | combined | 4040 | -1.133 | 0.2795 |
| rolling_5d | real | 11 | -0.14 | 0.5455 |
| rolling_5d | sim | 44 | -0.5702 | 0.4091 |
| rolling_5d | combined | 55 | -0.4842 | 0.4364 |
| rolling_10d | real | 11 | -0.14 | 0.5455 |
| rolling_10d | sim | 53 | -0.6062 | 0.4151 |
| rolling_10d | combined | 64 | -0.5261 | 0.4375 |
| rolling_20d | real | 64 | -0.1556 | 0.6094 |
| rolling_20d | sim | 72 | -0.6093 | 0.3889 |
| rolling_20d | combined | 136 | -0.3958 | 0.4926 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 680 | -0.2627 | -3.16 | 1.89 | 0.4853 | 0.4779 |
| cumulative | normal_only | 680 | -0.2627 | -3.16 | 1.89 | 0.4853 | 0.4779 |
| cumulative | initial_only | 599 | -0.2787 | -3.14 | 1.9 | 0.4808 | 0.4808 |
| cumulative | pyramid_activated | 31 | 0.3365 | -1.45 | 1.59 | 0.6452 | 0.3548 |
| cumulative | reversal_add_activated | 51 | -0.2973 | -4.32 | 2.18 | 0.451 | 0.5098 |
| rolling_5d | all_completed_valid | 11 | -0.14 | -3.22 | 1.63 | 0.5455 | 0.2727 |
| rolling_5d | normal_only | 11 | -0.14 | -3.22 | 1.63 | 0.5455 | 0.2727 |
| rolling_5d | initial_only | 11 | -0.14 | -3.22 | 1.63 | 0.5455 | 0.2727 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 11 | -0.14 | -3.22 | 1.63 | 0.5455 | 0.2727 |
| rolling_10d | normal_only | 11 | -0.14 | -3.22 | 1.63 | 0.5455 | 0.2727 |
| rolling_10d | initial_only | 11 | -0.14 | -3.22 | 1.63 | 0.5455 | 0.2727 |
| rolling_10d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_10d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_20d | all_completed_valid | 64 | -0.1556 | -3.67 | 1.66 | 0.6094 | 0.3594 |
| rolling_20d | normal_only | 64 | -0.1556 | -3.67 | 1.66 | 0.6094 | 0.3594 |
| rolling_20d | initial_only | 62 | -0.1668 | -3.67 | 1.66 | 0.6129 | 0.3548 |
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
| cumulative | entry_mechanical_momentum | entry | 205377 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 15 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 17747 | True | report_only_reference |
| cumulative | entry_split_order_plan | submit | 2662 | True | report_only_reference |
| cumulative | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 3976 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 164088 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 32873 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 24238 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 100 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 1283 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 236539 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 100005 | False | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 15758 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 15758 | False | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 3138 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 216 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 112 | False | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2707 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 680 | True | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 680 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 2964 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 1929 | False | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 410 | True | report_only_reference |
| rolling_5d | entry_split_order_plan | submit | 2662 | True | report_only_reference |
| rolling_5d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 36 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 9649 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 3134 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 1220 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 4 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 332 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 6290 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 2542 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 441 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 441 | False | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 482 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 2 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 14 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 11 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 11 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 2964 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 3063 | False | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 557 | True | report_only_reference |
| rolling_10d | entry_split_order_plan | submit | 2662 | True | report_only_reference |
| rolling_10d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 36 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 19593 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 4552 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 2368 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 5 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 377 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 6793 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 2774 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 538 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 538 | False | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 486 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 2 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 14 | False | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 11 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 11 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 2964 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 5117 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 1046 | True | report_only_reference |
| rolling_20d | entry_split_order_plan | submit | 2662 | True | report_only_reference |
| rolling_20d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 174 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 28683 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 9346 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 3675 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 6 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 1012 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 12535 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 5283 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 1078 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 1078 | False | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 1017 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 17 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 23 | False | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 64 | True | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 64 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 2964 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
