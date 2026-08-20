# Cumulative Threshold Cycle Report - 2026-08-19

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-08-19`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 121 | 2097503 | 685 | -0.268 | 0.4847 | 0.4788 |
| rolling_5d | 5 | 41386 | 4 | -0.8708 | 0.5 | 0.5 |
| rolling_10d | 10 | 120927 | 16 | -0.4041 | 0.5 | 0.375 |
| rolling_20d | 20 | 317457 | 48 | 0.0265 | 0.625 | 0.3333 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 685 | -0.268 | 0.4847 |
| cumulative | sim | 3394 | -1.31 | 0.239 |
| cumulative | combined | 4079 | -1.135 | 0.2802 |
| rolling_5d | real | 4 | -0.8708 | 0.5 |
| rolling_5d | sim | 34 | -1.4012 | 0.3529 |
| rolling_5d | combined | 38 | -1.3453 | 0.3684 |
| rolling_10d | real | 16 | -0.4041 | 0.5 |
| rolling_10d | sim | 78 | -0.9324 | 0.3846 |
| rolling_10d | combined | 94 | -0.8425 | 0.4043 |
| rolling_20d | real | 48 | 0.0265 | 0.625 |
| rolling_20d | sim | 97 | -0.8921 | 0.3918 |
| rolling_20d | combined | 145 | -0.588 | 0.469 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 685 | -0.268 | -3.16 | 1.89 | 0.4847 | 0.4788 |
| cumulative | normal_only | 685 | -0.268 | -3.16 | 1.89 | 0.4847 | 0.4788 |
| cumulative | initial_only | 604 | -0.2845 | -3.14 | 1.89 | 0.4801 | 0.4818 |
| cumulative | pyramid_activated | 31 | 0.3365 | -1.45 | 1.59 | 0.6452 | 0.3548 |
| cumulative | reversal_add_activated | 51 | -0.2973 | -4.32 | 2.18 | 0.451 | 0.5098 |
| rolling_5d | all_completed_valid | 4 | -0.8708 | -4.4477 | 0.8668 | 0.5 | 0.5 |
| rolling_5d | normal_only | 4 | -0.8708 | -4.4477 | 0.8668 | 0.5 | 0.5 |
| rolling_5d | initial_only | 4 | -0.8708 | -4.4477 | 0.8668 | 0.5 | 0.5 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 16 | -0.4041 | -4.01 | 1.63 | 0.5 | 0.375 |
| rolling_10d | normal_only | 16 | -0.4041 | -4.01 | 1.63 | 0.5 | 0.375 |
| rolling_10d | initial_only | 16 | -0.4041 | -4.01 | 1.63 | 0.5 | 0.375 |
| rolling_10d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_10d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_20d | all_completed_valid | 48 | 0.0265 | -3.33 | 2.03 | 0.625 | 0.3333 |
| rolling_20d | normal_only | 48 | 0.0265 | -3.33 | 2.03 | 0.625 | 0.3333 |
| rolling_20d | initial_only | 46 | 0.0194 | -3.33 | 2.03 | 0.6304 | 0.3261 |
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
| cumulative | entry_mechanical_momentum | entry | 206699 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 15 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 17896 | True | report_only_reference |
| cumulative | entry_split_order_plan | submit | 965 | True | report_only_reference |
| cumulative | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 4012 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 167240 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 33881 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 24717 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 101 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 1668 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 239466 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 100798 | False | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 16613 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 16613 | False | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 3214 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 216 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 113 | False | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2707 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 685 | True | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 685 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 873 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 1322 | False | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 149 | True | report_only_reference |
| rolling_5d | entry_split_order_plan | submit | 965 | True | report_only_reference |
| rolling_5d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 36 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 3152 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 1008 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 479 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 1 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 385 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 2927 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 793 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 855 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 855 | False | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 76 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 1 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 0 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 4 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 4 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 873 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 3251 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 559 | True | report_only_reference |
| rolling_10d | entry_split_order_plan | submit | 965 | True | report_only_reference |
| rolling_10d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 72 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 12801 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 4142 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 1699 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 5 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 717 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 9217 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 3335 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 1296 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 1296 | False | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 558 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 3 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 14 | False | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 16 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 16 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 873 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 6185 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 1136 | True | report_only_reference |
| rolling_20d | entry_split_order_plan | submit | 965 | True | report_only_reference |
| rolling_20d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 146 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 31331 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 10354 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 4141 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 7 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 1283 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 14536 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 5851 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 1610 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 1610 | False | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 997 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 10 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 23 | False | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 48 | True | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 48 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 873 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
