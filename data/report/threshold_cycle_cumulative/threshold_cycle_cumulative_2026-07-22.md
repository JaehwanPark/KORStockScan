# Cumulative Threshold Cycle Report - 2026-07-22

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-07-22`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 93 | 2290772 | 600 | -0.2765 | 0.4683 | 0.495 |
| rolling_5d | 5 | 24131 | 42 | -0.161 | 0.5 | 0.4286 |
| rolling_10d | 10 | 52550 | 67 | -0.2382 | 0.4328 | 0.4925 |
| rolling_20d | 20 | 147181 | 182 | -0.221 | 0.522 | 0.4396 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 600 | -0.2765 | 0.4683 |
| cumulative | sim | 4023 | -1.2927 | 0.2419 |
| cumulative | combined | 4623 | -1.1608 | 0.2713 |
| rolling_5d | real | 42 | -0.161 | 0.5 |
| rolling_5d | sim | 12 | -1.1867 | 0.1667 |
| rolling_5d | combined | 54 | -0.3889 | 0.4259 |
| rolling_10d | real | 67 | -0.2382 | 0.4328 |
| rolling_10d | sim | 35 | -1.342 | 0.2571 |
| rolling_10d | combined | 102 | -0.617 | 0.3725 |
| rolling_20d | real | 182 | -0.221 | 0.522 |
| rolling_20d | sim | 145 | -1.6676 | 0.3103 |
| rolling_20d | combined | 327 | -0.8624 | 0.4281 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 600 | -0.2765 | -3.14 | 1.93 | 0.4683 | 0.495 |
| cumulative | normal_only | 600 | -0.2765 | -3.14 | 1.93 | 0.4683 | 0.495 |
| cumulative | initial_only | 523 | -0.3007 | -2.73 | 1.93 | 0.4608 | 0.501 |
| cumulative | pyramid_activated | 31 | 0.3365 | -1.45 | 1.59 | 0.6452 | 0.3548 |
| cumulative | reversal_add_activated | 47 | -0.2564 | -4.57 | 2.55 | 0.4468 | 0.5106 |
| rolling_5d | all_completed_valid | 42 | -0.161 | -3.29 | 1.44 | 0.5 | 0.4286 |
| rolling_5d | normal_only | 42 | -0.161 | -3.29 | 1.44 | 0.5 | 0.4286 |
| rolling_5d | initial_only | 41 | -0.1593 | -3.29 | 1.44 | 0.5122 | 0.4146 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 1 | -0.23 | -0.23 | -0.23 | 0 | 1 |
| rolling_10d | all_completed_valid | 67 | -0.2382 | -3.26 | 1.24 | 0.4328 | 0.4925 |
| rolling_10d | normal_only | 67 | -0.2382 | -3.26 | 1.24 | 0.4328 | 0.4925 |
| rolling_10d | initial_only | 60 | -0.2312 | -3.29 | 1.24 | 0.4333 | 0.4833 |
| rolling_10d | pyramid_activated | 3 | 0.52 | 0.13 | 0.93 | 1 | 0 |
| rolling_10d | reversal_add_activated | 4 | -0.9125 | -2.96 | -0.23 | 0 | 1 |
| rolling_20d | all_completed_valid | 182 | -0.221 | -3.88 | 1.98 | 0.522 | 0.4396 |
| rolling_20d | normal_only | 182 | -0.221 | -3.88 | 1.98 | 0.522 | 0.4396 |
| rolling_20d | initial_only | 151 | -0.1824 | -3.86 | 1.98 | 0.5232 | 0.4305 |
| rolling_20d | pyramid_activated | 5 | -0.002 | -2.12 | 0.93 | 0.8 | 0.2 |
| rolling_20d | reversal_add_activated | 26 | -0.4873 | -4.6 | 2.55 | 0.4615 | 0.5385 |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 296437 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 101 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 19049 | True | report_only_reference |
| cumulative | entry_split_order_plan | submit | 1226 | True | report_only_reference |
| cumulative | scale_in_split_order_plan | scale_in | 4 | True | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 4000 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 181602 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 47727 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 23322 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 107 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 636 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 260871 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 110122 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 19416 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 19416 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 2120 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 255 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 120 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2790 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 600 | True | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 600 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 785 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 833 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 119 | True | report_only_reference |
| rolling_5d | entry_split_order_plan | submit | 1226 | True | report_only_reference |
| rolling_5d | scale_in_split_order_plan | scale_in | 4 | True | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 205 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 272 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 4 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 16 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 2 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 15 | False | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 5267 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 2214 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 42 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 42 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 239 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 2 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 14 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 42 | True | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 42 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 785 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 1466 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 334 | True | report_only_reference |
| rolling_10d | entry_split_order_plan | submit | 1226 | True | report_only_reference |
| rolling_10d | scale_in_split_order_plan | scale_in | 4 | True | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 289 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 1393 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 21 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 181 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 10 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 16 | False | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 11193 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 4574 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 225 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 225 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 361 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 68 | True | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 5 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 31 | False | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 67 | True | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 67 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 785 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 4234 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 12 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 1423 | True | report_only_reference |
| rolling_20d | entry_split_order_plan | submit | 1226 | True | report_only_reference |
| rolling_20d | scale_in_split_order_plan | scale_in | 4 | True | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 904 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 6453 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 450 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 899 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 26 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 62 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 28445 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 11052 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 677 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 677 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 984 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 93 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 20 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 132 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 182 | True | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 182 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 785 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
