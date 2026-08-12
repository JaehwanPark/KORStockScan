# Cumulative Threshold Cycle Report - 2026-08-12

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-08-12`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 114 | 2015264 | 669 | -0.2648 | 0.4843 | 0.4813 |
| rolling_5d | 5 | 38688 | 0 | - | - | - |
| rolling_10d | 10 | 208519 | 26 | 0.3404 | 0.6538 | 0.3462 |
| rolling_20d | 20 | 248535 | 55 | -0.1393 | 0.6364 | 0.3636 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 669 | -0.2648 | 0.4843 |
| cumulative | sim | 3335 | -1.3177 | 0.2363 |
| cumulative | combined | 4004 | -1.1418 | 0.2777 |
| rolling_5d | real | 0 | - | - |
| rolling_5d | sim | 19 | -1.1126 | 0.3684 |
| rolling_5d | combined | 19 | -1.1126 | 0.3684 |
| rolling_10d | real | 26 | 0.3404 | 0.6538 |
| rolling_10d | sim | 35 | -0.8414 | 0.4286 |
| rolling_10d | combined | 61 | -0.3377 | 0.5246 |
| rolling_20d | real | 55 | -0.1393 | 0.6364 |
| rolling_20d | sim | 48 | -0.8365 | 0.3542 |
| rolling_20d | combined | 103 | -0.4642 | 0.5049 |

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
| rolling_20d | all_completed_valid | 55 | -0.1393 | -3.67 | 1.66 | 0.6364 | 0.3636 |
| rolling_20d | normal_only | 55 | -0.1393 | -3.67 | 1.66 | 0.6364 | 0.3636 |
| rolling_20d | initial_only | 53 | -0.1517 | -3.67 | 1.66 | 0.6415 | 0.3585 |
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
| cumulative | entry_mechanical_momentum | entry | 204260 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 15 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 17574 | True | report_only_reference |
| cumulative | entry_split_order_plan | submit | 1010 | True | report_only_reference |
| cumulative | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 3940 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 160412 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 31957 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 23835 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 100 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 1072 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 232007 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 98362 | False | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 15466 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 15466 | False | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 2663 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 216 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 110 | False | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2701 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 669 | True | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 669 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 1560 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 812 | False | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 237 | True | report_only_reference |
| rolling_5d | entry_split_order_plan | submit | 1010 | True | report_only_reference |
| rolling_5d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 0 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 5973 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 2218 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 817 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 4 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 121 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 1758 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 899 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 149 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 149 | False | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 7 | False | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 8 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 0 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 0 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 1560 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 3213 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 702 | True | report_only_reference |
| rolling_10d | entry_split_order_plan | submit | 1010 | True | report_only_reference |
| rolling_10d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 64 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 22155 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 6709 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 2956 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 6 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 614 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 5743 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 2845 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 452 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 452 | False | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 440 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 7 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 12 | False | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 26 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 26 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 1560 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 4237 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 874 | True | report_only_reference |
| rolling_20d | entry_split_order_plan | submit | 1010 | True | report_only_reference |
| rolling_20d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 141 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 25012 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 8430 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 3273 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 6 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 801 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 8227 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 3699 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 897 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 897 | False | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 545 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 15 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 17 | False | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 55 | True | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 55 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 1560 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
