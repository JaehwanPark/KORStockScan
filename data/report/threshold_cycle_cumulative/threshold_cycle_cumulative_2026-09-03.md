# Cumulative Threshold Cycle Report - 2026-09-03

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-09-03`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 136 | 2326300 | 748 | -0.251 | 0.5067 | 0.4612 |
| rolling_5d | 5 | 75442 | 9 | 0.0467 | 0.6667 | 0.3333 |
| rolling_10d | 10 | 157256 | 25 | 0.0746 | 0.76 | 0.24 |
| rolling_20d | 20 | 270183 | 67 | -0.1172 | 0.7164 | 0.2836 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 748 | -0.251 | 0.5067 |
| cumulative | sim | 3540 | -1.2954 | 0.2452 |
| cumulative | combined | 4288 | -1.1132 | 0.2908 |
| rolling_5d | real | 9 | 0.0467 | 0.6667 |
| rolling_5d | sim | 47 | -1.2409 | 0.3404 |
| rolling_5d | combined | 56 | -1.0339 | 0.3929 |
| rolling_10d | real | 25 | 0.0746 | 0.76 |
| rolling_10d | sim | 104 | -1.0101 | 0.3846 |
| rolling_10d | combined | 129 | -0.7999 | 0.4574 |
| rolling_20d | real | 67 | -0.1172 | 0.7164 |
| rolling_20d | sim | 180 | -1.0397 | 0.3833 |
| rolling_20d | combined | 247 | -0.7895 | 0.4737 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 748 | -0.251 | -3.18 | 1.82 | 0.5067 | 0.4612 |
| cumulative | normal_only | 748 | -0.251 | -3.18 | 1.82 | 0.5067 | 0.4612 |
| cumulative | initial_only | 665 | -0.2654 | -3.16 | 1.77 | 0.5053 | 0.4617 |
| cumulative | pyramid_activated | 32 | 0.3794 | -1.45 | 1.71 | 0.6562 | 0.3438 |
| cumulative | reversal_add_activated | 52 | -0.3152 | -4.32 | 2.18 | 0.4423 | 0.5192 |
| rolling_5d | all_completed_valid | 9 | 0.0467 | -3.04 | 2.12 | 0.6667 | 0.3333 |
| rolling_5d | normal_only | 9 | 0.0467 | -3.04 | 2.12 | 0.6667 | 0.3333 |
| rolling_5d | initial_only | 9 | 0.0467 | -3.04 | 2.12 | 0.6667 | 0.3333 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 25 | 0.0746 | -3.04 | 1.29 | 0.76 | 0.24 |
| rolling_10d | normal_only | 25 | 0.0746 | -3.04 | 1.29 | 0.76 | 0.24 |
| rolling_10d | initial_only | 25 | 0.0746 | -3.04 | 1.29 | 0.76 | 0.24 |
| rolling_10d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_10d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_20d | all_completed_valid | 67 | -0.1172 | -3.38 | 1.23 | 0.7164 | 0.2836 |
| rolling_20d | normal_only | 67 | -0.1172 | -3.38 | 1.23 | 0.7164 | 0.2836 |
| rolling_20d | initial_only | 65 | -0.1282 | -3.38 | 1.2105 | 0.7231 | 0.2769 |
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
| cumulative | entry_mechanical_momentum | entry | 215122 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 15 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 18625 | True | report_only_reference |
| cumulative | entry_split_order_plan | submit | 4085 | True | report_only_reference |
| cumulative | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 4342 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 182135 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 38164 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 26934 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 115 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 2952 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 3 | False | report_only_reference |
| cumulative | reversal_add | holding_exit | 108123 | False | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 18444 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 18444 | False | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 4726 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 216 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 122 | False | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2753 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 748 | True | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 748 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 2922 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 3092 | False | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 195 | True | report_only_reference |
| rolling_5d | entry_split_order_plan | submit | 4085 | True | report_only_reference |
| rolling_5d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 112 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 5069 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 1385 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 886 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 11 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 311 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 3 | False | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 2358 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 438 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 438 | False | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 26 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 1 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 4 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 9 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 9 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 2922 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 6270 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 468 | True | report_only_reference |
| rolling_10d | entry_split_order_plan | submit | 4085 | True | report_only_reference |
| rolling_10d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 224 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 10059 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 2924 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 1604 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 30 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 801 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 3 | False | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 5349 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 811 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 811 | False | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 67 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 3 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 40 | True | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 25 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 25 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 2922 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 9745 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 878 | True | report_only_reference |
| rolling_20d | entry_split_order_plan | submit | 4085 | True | report_only_reference |
| rolling_20d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 366 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 18047 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 5291 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 2696 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 55 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 1669 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 3 | False | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 8118 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 2686 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 2686 | False | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 1588 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 10 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 46 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 67 | True | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 67 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 2922 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
