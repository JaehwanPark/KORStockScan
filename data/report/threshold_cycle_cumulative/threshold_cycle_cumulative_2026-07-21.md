# Cumulative Threshold Cycle Report - 2026-07-21

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-07-21`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 92 | 2281200 | 581 | -0.2786 | 0.4682 | 0.4957 |
| rolling_5d | 5 | 14559 | 23 | -0.1178 | 0.5217 | 0.3913 |
| rolling_10d | 10 | 42978 | 48 | -0.2481 | 0.4167 | 0.5 |
| rolling_20d | 20 | 164380 | 188 | -0.1424 | 0.5266 | 0.4309 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 581 | -0.2786 | 0.4682 |
| cumulative | sim | 4016 | -1.2922 | 0.2423 |
| cumulative | combined | 4597 | -1.1641 | 0.2708 |
| rolling_5d | real | 23 | -0.1178 | 0.5217 |
| rolling_5d | sim | 5 | -0.642 | 0.4 |
| rolling_5d | combined | 28 | -0.2114 | 0.5 |
| rolling_10d | real | 48 | -0.2481 | 0.4167 |
| rolling_10d | sim | 28 | -1.2836 | 0.3214 |
| rolling_10d | combined | 76 | -0.6296 | 0.3816 |
| rolling_20d | real | 188 | -0.1424 | 0.5266 |
| rolling_20d | sim | 159 | -1.7921 | 0.3145 |
| rolling_20d | combined | 347 | -0.8983 | 0.4294 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 581 | -0.2786 | -2.87 | 1.93 | 0.4682 | 0.4957 |
| cumulative | normal_only | 581 | -0.2786 | -2.87 | 1.93 | 0.4682 | 0.4957 |
| cumulative | initial_only | 505 | -0.3038 | -2.71 | 1.93 | 0.4594 | 0.503 |
| cumulative | pyramid_activated | 31 | 0.3365 | -1.45 | 1.59 | 0.6452 | 0.3548 |
| cumulative | reversal_add_activated | 46 | -0.257 | -4.57 | 2.55 | 0.4565 | 0.5 |
| rolling_5d | all_completed_valid | 23 | -0.1178 | -3.29 | 1.41 | 0.5217 | 0.3913 |
| rolling_5d | normal_only | 23 | -0.1178 | -3.29 | 1.41 | 0.5217 | 0.3913 |
| rolling_5d | initial_only | 23 | -0.1178 | -3.29 | 1.41 | 0.5217 | 0.3913 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 48 | -0.2481 | -3.2 | 1.22 | 0.4167 | 0.5 |
| rolling_10d | normal_only | 48 | -0.2481 | -3.2 | 1.22 | 0.4167 | 0.5 |
| rolling_10d | initial_only | 42 | -0.2393 | -3.2 | 1.22 | 0.4048 | 0.5 |
| rolling_10d | pyramid_activated | 3 | 0.52 | 0.13 | 0.93 | 1 | 0 |
| rolling_10d | reversal_add_activated | 3 | -1.14 | -2.96 | -0.23 | 0 | 1 |
| rolling_20d | all_completed_valid | 188 | -0.1424 | -3.88 | 2.25 | 0.5266 | 0.4309 |
| rolling_20d | normal_only | 188 | -0.1424 | -3.88 | 2.25 | 0.5266 | 0.4309 |
| rolling_20d | initial_only | 155 | -0.0828 | -3.83 | 2.25 | 0.5226 | 0.4258 |
| rolling_20d | pyramid_activated | 5 | -0.002 | -2.12 | 0.93 | 0.8 | 0.2 |
| rolling_20d | reversal_add_activated | 28 | -0.4971 | -4.64 | 2.55 | 0.5 | 0.5 |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 296160 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 101 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 18978 | False | report_only_reference |
| cumulative | entry_split_order_plan | submit | 146 | True | report_only_reference |
| cumulative | scale_in_split_order_plan | scale_in | 1 | True | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 3925 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 181375 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 47727 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 23317 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 106 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 624 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 258970 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 109203 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 19395 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 19395 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 1901 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 255 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 118 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2788 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 581 | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 581 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 372 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 556 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 48 | False | report_only_reference |
| rolling_5d | entry_split_order_plan | submit | 146 | True | report_only_reference |
| rolling_5d | scale_in_split_order_plan | scale_in | 1 | True | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 130 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 45 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 4 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 11 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 1 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 3 | False | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 3366 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 1295 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 21 | False | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 21 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 20 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 12 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 23 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 23 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 372 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 1189 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 263 | False | report_only_reference |
| rolling_10d | entry_split_order_plan | submit | 146 | True | report_only_reference |
| rolling_10d | scale_in_split_order_plan | scale_in | 1 | True | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 214 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 1166 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 21 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 176 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 15 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 4 | False | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 9292 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 3655 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 204 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 204 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 142 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 68 | True | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 3 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 29 | False | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 48 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 48 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 372 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 4390 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 12 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 1695 | False | report_only_reference |
| rolling_20d | entry_split_order_plan | submit | 146 | True | report_only_reference |
| rolling_20d | scale_in_split_order_plan | scale_in | 1 | True | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 983 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 7715 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 689 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 1107 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 25 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 63 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 31395 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 12298 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 754 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 754 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 782 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 93 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 21 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 200 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 188 | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 188 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 372 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
