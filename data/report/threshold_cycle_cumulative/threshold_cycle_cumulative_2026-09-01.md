# Cumulative Threshold Cycle Report - 2026-09-01

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-09-01`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 134 | 2288275 | 744 | -0.2481 | 0.5067 | 0.461 |
| rolling_5d | 5 | 52580 | 10 | 0.191 | 0.8 | 0.2 |
| rolling_10d | 10 | 140792 | 30 | -0.1451 | 0.7333 | 0.2667 |
| rolling_20d | 20 | 273011 | 75 | -0.1021 | 0.6933 | 0.28 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 744 | -0.2481 | 0.5067 |
| cumulative | sim | 3515 | -1.2937 | 0.2452 |
| cumulative | combined | 4259 | -1.1111 | 0.2909 |
| rolling_5d | real | 10 | 0.191 | 0.8 |
| rolling_5d | sim | 31 | -1.0152 | 0.3871 |
| rolling_5d | combined | 41 | -0.721 | 0.4878 |
| rolling_10d | real | 30 | -0.1451 | 0.7333 |
| rolling_10d | sim | 98 | -0.7851 | 0.4082 |
| rolling_10d | combined | 128 | -0.6351 | 0.4844 |
| rolling_20d | real | 75 | -0.1021 | 0.6933 |
| rolling_20d | sim | 180 | -0.8491 | 0.4111 |
| rolling_20d | combined | 255 | -0.6294 | 0.4941 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 744 | -0.2481 | -3.18 | 1.8 | 0.5067 | 0.461 |
| cumulative | normal_only | 744 | -0.2481 | -3.18 | 1.8 | 0.5067 | 0.461 |
| cumulative | initial_only | 661 | -0.2622 | -3.16 | 1.76 | 0.5053 | 0.4614 |
| cumulative | pyramid_activated | 32 | 0.3794 | -1.45 | 1.71 | 0.6562 | 0.3438 |
| cumulative | reversal_add_activated | 52 | -0.3152 | -4.32 | 2.18 | 0.4423 | 0.5192 |
| rolling_5d | all_completed_valid | 10 | 0.191 | -3.51 | 1.29 | 0.8 | 0.2 |
| rolling_5d | normal_only | 10 | 0.191 | -3.51 | 1.29 | 0.8 | 0.2 |
| rolling_5d | initial_only | 10 | 0.191 | -3.51 | 1.29 | 0.8 | 0.2 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 30 | -0.1451 | -3.51 | 1.07 | 0.7333 | 0.2667 |
| rolling_10d | normal_only | 30 | -0.1451 | -3.51 | 1.07 | 0.7333 | 0.2667 |
| rolling_10d | initial_only | 30 | -0.1451 | -3.51 | 1.07 | 0.7333 | 0.2667 |
| rolling_10d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_10d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_20d | all_completed_valid | 75 | -0.1021 | -3.38 | 1.23 | 0.6933 | 0.28 |
| rolling_20d | normal_only | 75 | -0.1021 | -3.38 | 1.23 | 0.6933 | 0.28 |
| rolling_20d | initial_only | 73 | -0.1115 | -3.38 | 1.2105 | 0.6986 | 0.274 |
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
| cumulative | entry_mechanical_momentum | entry | 213646 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 15 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 18531 | True | report_only_reference |
| cumulative | entry_split_order_plan | submit | 3995 | True | report_only_reference |
| cumulative | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 4281 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 179660 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 37543 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 26480 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 115 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 2806 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 2 | False | report_only_reference |
| cumulative | reversal_add | holding_exit | 106566 | False | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 18176 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 18176 | False | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 4718 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 216 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 121 | False | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2752 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 744 | True | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 744 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 2284 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 2277 | False | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 162 | True | report_only_reference |
| rolling_5d | entry_split_order_plan | submit | 3995 | True | report_only_reference |
| rolling_5d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 105 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 4022 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 1077 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 604 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 11 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 246 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 2 | False | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 1277 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 219 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 219 | False | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 24 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 1 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 6 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 10 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 10 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 2284 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 5402 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 475 | True | report_only_reference |
| rolling_10d | entry_split_order_plan | submit | 3995 | True | report_only_reference |
| rolling_10d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 193 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 9262 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 2789 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 1377 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 27 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 780 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 2 | False | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 4222 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 927 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 927 | False | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 100 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 5 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 39 | True | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 30 | True | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 30 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 2284 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 9386 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 957 | True | report_only_reference |
| rolling_20d | entry_split_order_plan | submit | 3995 | True | report_only_reference |
| rolling_20d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 341 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 19248 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 5586 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 2645 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 55 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 1734 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 2 | False | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 8204 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 2710 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 2710 | False | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 2055 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 11 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 51 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 75 | True | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 75 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 2284 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
