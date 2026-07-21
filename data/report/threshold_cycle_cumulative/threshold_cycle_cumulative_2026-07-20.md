# Cumulative Threshold Cycle Report - 2026-07-20

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-07-20`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 91 | 2274810 | 573 | -0.2738 | 0.4747 | 0.4887 |
| rolling_5d | 5 | 12305 | 20 | 0.0655 | 0.6 | 0.25 |
| rolling_10d | 10 | 36588 | 41 | -0.1756 | 0.4878 | 0.4146 |
| rolling_20d | 20 | 195772 | 213 | -0.0369 | 0.5493 | 0.3944 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 573 | -0.2738 | 0.4747 |
| cumulative | sim | 4015 | -1.2925 | 0.2423 |
| cumulative | combined | 4588 | -1.1653 | 0.2714 |
| rolling_5d | real | 20 | 0.0655 | 0.6 |
| rolling_5d | sim | 11 | -0.5473 | 0.5455 |
| rolling_5d | combined | 31 | -0.1519 | 0.5806 |
| rolling_10d | real | 41 | -0.1756 | 0.4878 |
| rolling_10d | sim | 27 | -1.3226 | 0.3333 |
| rolling_10d | combined | 68 | -0.631 | 0.4265 |
| rolling_20d | real | 213 | -0.0369 | 0.5493 |
| rolling_20d | sim | 175 | -1.597 | 0.3486 |
| rolling_20d | combined | 388 | -0.7405 | 0.4588 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 573 | -0.2738 | -2.87 | 1.98 | 0.4747 | 0.4887 |
| cumulative | normal_only | 573 | -0.2738 | -2.87 | 1.98 | 0.4747 | 0.4887 |
| cumulative | initial_only | 499 | -0.2985 | -2.71 | 1.98 | 0.4649 | 0.497 |
| cumulative | pyramid_activated | 31 | 0.3365 | -1.45 | 1.59 | 0.6452 | 0.3548 |
| cumulative | reversal_add_activated | 44 | -0.2582 | -4.57 | 2.55 | 0.4773 | 0.4773 |
| rolling_5d | all_completed_valid | 20 | 0.0655 | -4.1 | 1.41 | 0.6 | 0.25 |
| rolling_5d | normal_only | 20 | 0.0655 | -4.1 | 1.41 | 0.6 | 0.25 |
| rolling_5d | initial_only | 19 | 0.0811 | -4.1 | 1.51 | 0.6316 | 0.2105 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 1 | -0.23 | -0.23 | -0.23 | 0 | 1 |
| rolling_10d | all_completed_valid | 41 | -0.1756 | -2.96 | 1.22 | 0.4878 | 0.4146 |
| rolling_10d | normal_only | 41 | -0.1756 | -2.96 | 1.22 | 0.4878 | 0.4146 |
| rolling_10d | initial_only | 36 | -0.1547 | -3.2 | 1.24 | 0.4722 | 0.4167 |
| rolling_10d | pyramid_activated | 3 | 0.52 | 0.13 | 0.93 | 1 | 0 |
| rolling_10d | reversal_add_activated | 2 | -1.595 | -2.96 | -0.23 | 0 | 1 |
| rolling_20d | all_completed_valid | 213 | -0.0369 | -3.88 | 2.47 | 0.5493 | 0.3944 |
| rolling_20d | normal_only | 213 | -0.0369 | -3.88 | 2.47 | 0.5493 | 0.3944 |
| rolling_20d | initial_only | 172 | 0.0431 | -3.67 | 2.47 | 0.5523 | 0.3895 |
| rolling_20d | pyramid_activated | 5 | -0.002 | -2.12 | 0.93 | 0.8 | 0.2 |
| rolling_20d | reversal_add_activated | 36 | -0.4236 | -4.6 | 2.55 | 0.5 | 0.4444 |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 295878 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 101 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 18967 | True | report_only_reference |
| cumulative | entry_split_order_plan | submit | 159 | True | report_only_reference |
| cumulative | scale_in_split_order_plan | scale_in | 7 | True | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 3885 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 181344 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 47725 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 23314 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 106 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 621 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 257369 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 108681 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 19390 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 19390 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 1899 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 255 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 118 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2788 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 573 | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 573 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 410 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 330 | False | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 62 | True | report_only_reference |
| rolling_5d | entry_split_order_plan | submit | 159 | True | report_only_reference |
| rolling_5d | scale_in_split_order_plan | scale_in | 7 | True | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 95 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 110 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 3 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 17 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 1 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 0 | False | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 2560 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 1251 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 27 | False | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 27 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 24 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 14 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 20 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 20 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 410 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 907 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 252 | True | report_only_reference |
| rolling_10d | entry_split_order_plan | submit | 159 | True | report_only_reference |
| rolling_10d | scale_in_split_order_plan | scale_in | 7 | True | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 174 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 1135 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 19 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 173 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 15 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 1 | False | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 7691 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 3133 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 199 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 199 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 140 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 68 | True | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 3 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 29 | False | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 41 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 41 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 410 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 5130 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 12 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 1961 | True | report_only_reference |
| rolling_20d | entry_split_order_plan | submit | 159 | True | report_only_reference |
| rolling_20d | scale_in_split_order_plan | scale_in | 7 | True | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 1228 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 8679 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 929 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 1164 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 31 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 63 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 39245 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 15041 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 904 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 904 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 847 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 93 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 27 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 468 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 213 | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 213 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 410 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
