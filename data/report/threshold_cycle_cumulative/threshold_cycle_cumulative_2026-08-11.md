# Cumulative Threshold Cycle Report - 2026-08-11

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-08-11`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 113 | 1999816 | 669 | -0.2648 | 0.4843 | 0.4813 |
| rolling_5d | 5 | 38753 | 0 | - | - | - |
| rolling_10d | 10 | 193071 | 26 | 0.3404 | 0.6538 | 0.3462 |
| rolling_20d | 20 | 238846 | 68 | -0.1809 | 0.6176 | 0.3676 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 669 | -0.2648 | 0.4843 |
| cumulative | sim | 3331 | -1.318 | 0.2363 |
| cumulative | combined | 4000 | -1.1419 | 0.2777 |
| rolling_5d | real | 0 | - | - |
| rolling_5d | sim | 17 | -0.9241 | 0.4706 |
| rolling_5d | combined | 17 | -0.9241 | 0.4706 |
| rolling_10d | real | 26 | 0.3404 | 0.6538 |
| rolling_10d | sim | 31 | -0.8145 | 0.4516 |
| rolling_10d | combined | 57 | -0.2877 | 0.5439 |
| rolling_20d | real | 68 | -0.1809 | 0.6176 |
| rolling_20d | sim | 45 | -0.804 | 0.3556 |
| rolling_20d | combined | 113 | -0.429 | 0.5133 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 669 | -0.2648 | -3.16 | 1.93 | 0.4843 | 0.4813 |
| cumulative | normal_only | 669 | -0.2648 | -3.16 | 1.93 | 0.4843 | 0.4813 |
| cumulative | initial_only | 588 | -0.2813 | -3.14 | 1.93 | 0.4796 | 0.4847 |
| cumulative | pyramid_activated | 31 | 0.3365 | -1.45 | 1.59 | 0.6452 | 0.3548 |
| cumulative | reversal_add_activated | 51 | -0.2973 | -4.32 | 2.18 | 0.451 | 0.5098 |
| rolling_5d | all_completed_valid | 0 | - | - | - | - | - |
| rolling_5d | normal_only | 0 | - | - | - | - | - |
| rolling_5d | initial_only | 0 | - | - | - | - | - |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 26 | 0.3404 | -3.28 | 3.14 | 0.6538 | 0.3462 |
| rolling_10d | normal_only | 26 | 0.3404 | -3.28 | 3.14 | 0.6538 | 0.3462 |
| rolling_10d | initial_only | 24 | 0.3529 | -3.28 | 3.14 | 0.6667 | 0.3333 |
| rolling_10d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_10d | reversal_add_activated | 2 | 0.19 | -0.32 | 0.7 | 0.5 | 0.5 |
| rolling_20d | all_completed_valid | 68 | -0.1809 | -3.67 | 1.64 | 0.6176 | 0.3676 |
| rolling_20d | normal_only | 68 | -0.1809 | -3.67 | 1.64 | 0.6176 | 0.3676 |
| rolling_20d | initial_only | 64 | -0.1436 | -3.56 | 1.64 | 0.625 | 0.3594 |
| rolling_20d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_20d | reversal_add_activated | 4 | -0.7775 | -3.68 | 0.7 | 0.5 | 0.5 |

## Smoothing Source-Only Rolling Decision

| family | decision | samples_ready | EV_windows_positive | risk_ready | risk_review | next_action |
| --- | --- | --- | ---: | --- | --- | --- |
| soft_stop_whipsaw_confirmation | hold_sample | False | 0 | False | False | keep_collecting_exact_paths |
| holding_flow_ofi_smoothing | hold_sample | False | 0 | False | False | keep_collecting_exact_paths |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 203669 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 15 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 17519 | True | report_only_reference |
| cumulative | entry_split_order_plan | submit | 122 | True | report_only_reference |
| cumulative | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 3940 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 158570 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 31456 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 23639 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 96 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 1008 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 231243 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 97976 | False | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 15419 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 15419 | False | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 2662 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 216 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 110 | False | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2699 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 669 | True | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 669 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 525 | False | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 435 | False | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 215 | True | report_only_reference |
| rolling_5d | entry_split_order_plan | submit | 122 | True | report_only_reference |
| rolling_5d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 0 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 6386 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 2054 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 1002 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 0 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 91 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 1196 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 584 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 103 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 103 | False | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 8 | False | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 6 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 0 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 0 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 525 | False | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 2622 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 647 | True | report_only_reference |
| rolling_10d | entry_split_order_plan | submit | 122 | True | report_only_reference |
| rolling_10d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 64 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 20313 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 6208 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 2760 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 19 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 550 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 4979 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 2459 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 405 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 405 | False | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 439 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 7 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 10 | False | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 26 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 26 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 525 | False | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 3848 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 867 | True | report_only_reference |
| rolling_20d | entry_split_order_plan | submit | 122 | True | report_only_reference |
| rolling_20d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 167 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 23338 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 7929 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 3083 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 19 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 751 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 8549 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 3624 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 860 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 860 | False | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 742 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 18 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 17 | False | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 68 | True | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 68 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 525 | False | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
