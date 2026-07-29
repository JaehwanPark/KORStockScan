# Cumulative Threshold Cycle Report - 2026-07-29

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-07-29`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 100 | 1847443 | 635 | -0.2764 | 0.4756 | 0.4882 |
| rolling_5d | 5 | 6620 | 19 | -0.3595 | 0.5789 | 0.4211 |
| rolling_10d | 10 | 39295 | 77 | -0.213 | 0.5455 | 0.4026 |
| rolling_20d | 20 | 78198 | 114 | -0.256 | 0.5 | 0.4474 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 635 | -0.2764 | 0.4756 |
| cumulative | sim | 3325 | -1.3199 | 0.2337 |
| cumulative | combined | 3960 | -1.1526 | 0.2725 |
| rolling_5d | real | 19 | -0.3595 | 0.5789 |
| rolling_5d | sim | 6 | -0.56 | 0.1667 |
| rolling_5d | combined | 25 | -0.4076 | 0.48 |
| rolling_10d | real | 77 | -0.213 | 0.5455 |
| rolling_10d | sim | 20 | -0.903 | 0.15 |
| rolling_10d | combined | 97 | -0.3553 | 0.4639 |
| rolling_20d | real | 114 | -0.256 | 0.5 |
| rolling_20d | sim | 51 | -1.0349 | 0.2941 |
| rolling_20d | combined | 165 | -0.4967 | 0.4364 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 635 | -0.2764 | -3.14 | 1.89 | 0.4756 | 0.4882 |
| cumulative | normal_only | 635 | -0.2764 | -3.14 | 1.89 | 0.4756 | 0.4882 |
| cumulative | initial_only | 556 | -0.2939 | -2.77 | 1.89 | 0.4694 | 0.4928 |
| cumulative | pyramid_activated | 31 | 0.3365 | -1.45 | 1.59 | 0.6452 | 0.3548 |
| cumulative | reversal_add_activated | 49 | -0.3171 | -4.57 | 2.55 | 0.449 | 0.5102 |
| rolling_5d | all_completed_valid | 19 | -0.3595 | -3.67 | 1.48 | 0.5789 | 0.4211 |
| rolling_5d | normal_only | 19 | -0.3595 | -3.67 | 1.48 | 0.5789 | 0.4211 |
| rolling_5d | initial_only | 19 | -0.3595 | -3.67 | 1.48 | 0.5789 | 0.4211 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 77 | -0.213 | -3.56 | 1.41 | 0.5455 | 0.4026 |
| rolling_10d | normal_only | 77 | -0.213 | -3.56 | 1.41 | 0.5455 | 0.4026 |
| rolling_10d | initial_only | 74 | -0.1714 | -3.29 | 1.41 | 0.5541 | 0.3919 |
| rolling_10d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_10d | reversal_add_activated | 3 | -1.24 | -3.68 | 0.19 | 0.3333 | 0.6667 |
| rolling_20d | all_completed_valid | 114 | -0.256 | -3.56 | 1.37 | 0.5 | 0.4474 |
| rolling_20d | normal_only | 114 | -0.256 | -3.56 | 1.37 | 0.5 | 0.4474 |
| rolling_20d | initial_only | 103 | -0.2617 | -3.56 | 1.37 | 0.4951 | 0.4466 |
| rolling_20d | pyramid_activated | 4 | 0.5275 | 0.13 | 0.93 | 1 | 0 |
| rolling_20d | reversal_add_activated | 7 | -0.62 | -3.68 | 2.8 | 0.2857 | 0.7143 |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 205030 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 15 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 16779 | True | report_only_reference |
| cumulative | entry_split_order_plan | submit | 207 | True | report_only_reference |
| cumulative | scale_in_split_order_plan | scale_in | 1 | True | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 3863 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 137360 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 24351 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 20665 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 95 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 343 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 226825 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 95593 | False | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 15105 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 15105 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 2218 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 216 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 102 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2696 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 635 | True | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 635 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 196 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 243 | False | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 44 | True | report_only_reference |
| rolling_5d | entry_split_order_plan | submit | 207 | True | report_only_reference |
| rolling_5d | scale_in_split_order_plan | scale_in | 1 | True | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 58 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 286 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 0 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 9 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 0 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 72 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 708 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 177 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 191 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 191 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 95 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 6 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 0 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 19 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 19 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 196 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 1515 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 212 | True | report_only_reference |
| rolling_10d | entry_split_order_plan | submit | 207 | True | report_only_reference |
| rolling_10d | scale_in_split_order_plan | scale_in | 1 | True | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 292 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 731 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 4 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 32 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 3 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 101 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 7285 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 2761 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 354 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 354 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 535 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 11 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 16 | False | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 77 | True | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 77 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 196 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 2473 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 557 | True | report_only_reference |
| rolling_20d | entry_split_order_plan | submit | 207 | True | report_only_reference |
| rolling_20d | scale_in_split_order_plan | scale_in | 1 | True | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 440 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 2324 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 52 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 251 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 12 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 102 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 15018 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 6142 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 539 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 539 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 666 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 68 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 14 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 44 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 114 | True | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 114 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 196 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
