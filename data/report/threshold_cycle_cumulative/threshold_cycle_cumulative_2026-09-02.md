# Cumulative Threshold Cycle Report - 2026-09-02

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-09-02`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 135 | 2306206 | 745 | -0.2511 | 0.506 | 0.4617 |
| rolling_5d | 5 | 55348 | 6 | 0.175 | 0.6667 | 0.3333 |
| rolling_10d | 10 | 158723 | 31 | -0.2227 | 0.7097 | 0.2903 |
| rolling_20d | 20 | 271451 | 70 | -0.1232 | 0.7143 | 0.2857 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 745 | -0.2511 | 0.506 |
| cumulative | sim | 3527 | -1.2932 | 0.2458 |
| cumulative | combined | 4272 | -1.1115 | 0.2912 |
| rolling_5d | real | 6 | 0.175 | 0.6667 |
| rolling_5d | sim | 34 | -0.9903 | 0.4412 |
| rolling_5d | combined | 40 | -0.8155 | 0.475 |
| rolling_10d | real | 31 | -0.2227 | 0.7097 |
| rolling_10d | sim | 110 | -0.8233 | 0.4091 |
| rolling_10d | combined | 141 | -0.6912 | 0.4752 |
| rolling_20d | real | 70 | -0.1232 | 0.7143 |
| rolling_20d | sim | 178 | -0.8845 | 0.4101 |
| rolling_20d | combined | 248 | -0.6696 | 0.496 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 745 | -0.2511 | -3.18 | 1.8 | 0.506 | 0.4617 |
| cumulative | normal_only | 745 | -0.2511 | -3.18 | 1.8 | 0.506 | 0.4617 |
| cumulative | initial_only | 662 | -0.2656 | -3.16 | 1.76 | 0.5045 | 0.4622 |
| cumulative | pyramid_activated | 32 | 0.3794 | -1.45 | 1.71 | 0.6562 | 0.3438 |
| cumulative | reversal_add_activated | 52 | -0.3152 | -4.32 | 2.18 | 0.4423 | 0.5192 |
| rolling_5d | all_completed_valid | 6 | 0.175 | -2.55 | 1.88 | 0.6667 | 0.3333 |
| rolling_5d | normal_only | 6 | 0.175 | -2.55 | 1.88 | 0.6667 | 0.3333 |
| rolling_5d | initial_only | 6 | 0.175 | -2.55 | 1.88 | 0.6667 | 0.3333 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 31 | -0.2227 | -3.215 | 1.07 | 0.7097 | 0.2903 |
| rolling_10d | normal_only | 31 | -0.2227 | -3.215 | 1.07 | 0.7097 | 0.2903 |
| rolling_10d | initial_only | 31 | -0.2227 | -3.215 | 1.07 | 0.7097 | 0.2903 |
| rolling_10d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_10d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_20d | all_completed_valid | 70 | -0.1232 | -3.38 | 1.2105 | 0.7143 | 0.2857 |
| rolling_20d | normal_only | 70 | -0.1232 | -3.38 | 1.2105 | 0.7143 | 0.2857 |
| rolling_20d | initial_only | 68 | -0.1339 | -3.38 | 1.2105 | 0.7206 | 0.2794 |
| rolling_20d | pyramid_activated | 1 | 1.71 | 1.71 | 1.71 | 1 | 0 |
| rolling_20d | reversal_add_activated | 1 | -1.23 | -1.23 | -1.23 | 0 | 1 |

## Smoothing Source-Only Rolling Decision

| family | decision | samples_ready | EV_windows_positive | risk_ready | risk_review | next_action |
| --- | --- | --- | ---: | --- | --- | --- |
| soft_stop_whipsaw_confirmation | hold_sample | False | 2 | True | True | keep_collecting_exact_paths |
| holding_flow_ofi_smoothing | hold_sample | False | 0 | False | False | keep_collecting_exact_paths |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 214528 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 15 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 18571 | True | report_only_reference |
| cumulative | entry_split_order_plan | submit | 3474 | True | report_only_reference |
| cumulative | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 4327 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 180664 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 37945 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 26711 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 115 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 2907 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 0 | False | report_only_reference |
| cumulative | reversal_add | holding_exit | 107229 | False | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 18325 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 18325 | False | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 4723 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 216 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 121 | False | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2752 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 745 | True | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 745 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 2316 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 2498 | False | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 141 | True | report_only_reference |
| rolling_5d | entry_split_order_plan | submit | 3474 | True | report_only_reference |
| rolling_5d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 97 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 3598 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 1166 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 663 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 11 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 266 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 0 | False | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 1464 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 319 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 319 | False | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 23 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 3 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 6 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 6 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 2316 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 6284 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 515 | True | report_only_reference |
| rolling_10d | entry_split_order_plan | submit | 3474 | True | report_only_reference |
| rolling_10d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 239 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 10266 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 3191 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 1608 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 27 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 881 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 0 | False | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 4885 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 1076 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 1076 | False | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 105 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 5 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 39 | True | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 31 | True | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 31 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 2316 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 9814 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 902 | True | report_only_reference |
| rolling_20d | entry_split_order_plan | submit | 3474 | True | report_only_reference |
| rolling_20d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 377 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 18423 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 5616 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 2691 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 55 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 1741 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 0 | False | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 7971 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 2663 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 2663 | False | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 2050 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 10 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 48 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 70 | True | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 70 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 2316 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
