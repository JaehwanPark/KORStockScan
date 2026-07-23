# Cumulative Threshold Cycle Report - 2026-07-23

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-07-23`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 94 | 2296531 | 612 | -0.2765 | 0.4722 | 0.4918 |
| rolling_5d | 5 | 29890 | 54 | -0.187 | 0.537 | 0.4074 |
| rolling_10d | 10 | 53717 | 75 | -0.2185 | 0.48 | 0.4533 |
| rolling_20d | 20 | 130114 | 165 | -0.3557 | 0.5212 | 0.4424 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 612 | -0.2765 | 0.4722 |
| cumulative | sim | 4024 | -1.2925 | 0.2418 |
| cumulative | combined | 4636 | -1.1584 | 0.2722 |
| rolling_5d | real | 54 | -0.187 | 0.537 |
| rolling_5d | sim | 13 | -1.1131 | 0.1538 |
| rolling_5d | combined | 67 | -0.3667 | 0.4627 |
| rolling_10d | real | 75 | -0.2185 | 0.48 |
| rolling_10d | sim | 26 | -0.9681 | 0.2692 |
| rolling_10d | combined | 101 | -0.4115 | 0.4257 |
| rolling_20d | real | 165 | -0.3557 | 0.5212 |
| rolling_20d | sim | 128 | -1.6954 | 0.2891 |
| rolling_20d | combined | 293 | -0.941 | 0.4198 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 612 | -0.2765 | -2.96 | 1.93 | 0.4722 | 0.4918 |
| cumulative | normal_only | 612 | -0.2765 | -2.96 | 1.93 | 0.4722 | 0.4918 |
| cumulative | initial_only | 533 | -0.2948 | -2.71 | 1.93 | 0.4653 | 0.4972 |
| cumulative | pyramid_activated | 31 | 0.3365 | -1.45 | 1.59 | 0.6452 | 0.3548 |
| cumulative | reversal_add_activated | 49 | -0.3171 | -4.57 | 2.55 | 0.449 | 0.5102 |
| rolling_5d | all_completed_valid | 54 | -0.187 | -3.29 | 1.41 | 0.537 | 0.4074 |
| rolling_5d | normal_only | 54 | -0.187 | -3.29 | 1.41 | 0.537 | 0.4074 |
| rolling_5d | initial_only | 51 | -0.1251 | -3.26 | 1.41 | 0.549 | 0.3922 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 3 | -1.24 | -3.68 | 0.19 | 0.3333 | 0.6667 |
| rolling_10d | all_completed_valid | 75 | -0.2185 | -3.26 | 1.22 | 0.48 | 0.4533 |
| rolling_10d | normal_only | 75 | -0.2185 | -3.26 | 1.22 | 0.48 | 0.4533 |
| rolling_10d | initial_only | 66 | -0.1638 | -3.26 | 1.24 | 0.4848 | 0.4394 |
| rolling_10d | pyramid_activated | 3 | 0.52 | 0.13 | 0.93 | 1 | 0 |
| rolling_10d | reversal_add_activated | 6 | -1.19 | -3.68 | 0.19 | 0.1667 | 0.8333 |
| rolling_20d | all_completed_valid | 165 | -0.3557 | -3.88 | 1.89 | 0.5212 | 0.4424 |
| rolling_20d | normal_only | 165 | -0.3557 | -3.88 | 1.89 | 0.5212 | 0.4424 |
| rolling_20d | initial_only | 142 | -0.3492 | -3.9 | 1.89 | 0.5141 | 0.4437 |
| rolling_20d | pyramid_activated | 5 | -0.002 | -2.12 | 0.93 | 0.8 | 0.2 |
| rolling_20d | reversal_add_activated | 18 | -0.5056 | -3.88 | 2.55 | 0.5 | 0.5 |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 296639 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 101 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 19097 | False | report_only_reference |
| cumulative | entry_split_order_plan | submit | 410 | True | report_only_reference |
| cumulative | scale_in_split_order_plan | scale_in | 7 | True | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 4026 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 181770 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 47727 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 23328 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 107 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 650 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 261957 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 110433 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 19426 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 19426 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 2318 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 255 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 123 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2792 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 612 | True | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 612 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 353 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 1035 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 167 | False | report_only_reference |
| rolling_5d | entry_split_order_plan | submit | 410 | True | report_only_reference |
| rolling_5d | scale_in_split_order_plan | scale_in | 7 | True | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 231 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 440 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 4 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 22 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 3 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 29 | False | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 6353 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 2525 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 52 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 52 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 437 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 5 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 16 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 54 | True | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 54 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 353 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 1398 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 335 | False | report_only_reference |
| rolling_10d | entry_split_order_plan | submit | 410 | True | report_only_reference |
| rolling_10d | scale_in_split_order_plan | scale_in | 7 | True | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 307 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 1279 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 21 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 152 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 10 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 30 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 11594 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 4885 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 182 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 182 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 455 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 68 | True | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 8 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 32 | False | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 75 | True | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 75 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 353 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 3940 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 12 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 1271 | False | report_only_reference |
| rolling_20d | entry_split_order_plan | submit | 410 | True | report_only_reference |
| rolling_20d | scale_in_split_order_plan | scale_in | 7 | True | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 752 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 4811 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 347 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 790 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 24 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 31 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 24767 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 9081 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 529 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 529 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 1168 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 93 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 18 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 105 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 165 | True | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 165 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 353 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
