# Cumulative Threshold Cycle Report - 2026-08-04

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-08-04`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 106 | 1905303 | 669 | -0.2648 | 0.4843 | 0.4813 |
| rolling_5d | 5 | 125257 | 32 | 0.2419 | 0.6875 | 0.3125 |
| rolling_10d | 10 | 135788 | 53 | -0.1589 | 0.6226 | 0.3774 |
| rolling_20d | 20 | 172600 | 113 | -0.1612 | 0.5664 | 0.3894 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 669 | -0.2648 | 0.4843 |
| cumulative | sim | 3307 | -1.3204 | 0.235 |
| cumulative | combined | 3976 | -1.1427 | 0.2769 |
| rolling_5d | real | 32 | 0.2419 | 0.6875 |
| rolling_5d | sim | 10 | -0.676 | 0.4 |
| rolling_5d | combined | 42 | 0.0233 | 0.619 |
| rolling_10d | real | 53 | -0.1589 | 0.6226 |
| rolling_10d | sim | 19 | -0.6179 | 0.3158 |
| rolling_10d | combined | 72 | -0.28 | 0.5417 |
| rolling_20d | real | 113 | -0.1612 | 0.5664 |
| rolling_20d | sim | 40 | -0.737 | 0.3 |
| rolling_20d | combined | 153 | -0.3118 | 0.4967 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 669 | -0.2648 | -3.16 | 1.93 | 0.4843 | 0.4813 |
| cumulative | normal_only | 669 | -0.2648 | -3.16 | 1.93 | 0.4843 | 0.4813 |
| cumulative | initial_only | 588 | -0.2813 | -3.14 | 1.93 | 0.4796 | 0.4847 |
| cumulative | pyramid_activated | 31 | 0.3365 | -1.45 | 1.59 | 0.6452 | 0.3548 |
| cumulative | reversal_add_activated | 51 | -0.2973 | -4.32 | 2.18 | 0.451 | 0.5098 |
| rolling_5d | all_completed_valid | 32 | 0.2419 | -3.28 | 2.38 | 0.6875 | 0.3125 |
| rolling_5d | normal_only | 32 | 0.2419 | -3.28 | 2.38 | 0.6875 | 0.3125 |
| rolling_5d | initial_only | 30 | 0.2453 | -3.33 | 2.38 | 0.7 | 0.3 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 2 | 0.19 | -0.32 | 0.7 | 0.5 | 0.5 |
| rolling_10d | all_completed_valid | 53 | -0.1589 | -3.67 | 1.66 | 0.6226 | 0.3774 |
| rolling_10d | normal_only | 53 | -0.1589 | -3.67 | 1.66 | 0.6226 | 0.3774 |
| rolling_10d | initial_only | 51 | -0.1725 | -3.67 | 1.66 | 0.6275 | 0.3725 |
| rolling_10d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_10d | reversal_add_activated | 2 | 0.19 | -0.32 | 0.7 | 0.5 | 0.5 |
| rolling_20d | all_completed_valid | 113 | -0.1612 | -3.56 | 1.48 | 0.5664 | 0.3894 |
| rolling_20d | normal_only | 113 | -0.1612 | -3.56 | 1.48 | 0.5664 | 0.3894 |
| rolling_20d | initial_only | 107 | -0.1369 | -3.56 | 1.51 | 0.5794 | 0.3738 |
| rolling_20d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_20d | reversal_add_activated | 6 | -0.595 | -3.68 | 0.7 | 0.3333 | 0.6667 |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 202314 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 15 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 17190 | True | report_only_reference |
| cumulative | entry_split_order_plan | submit | 1909 | True | report_only_reference |
| cumulative | scale_in_split_order_plan | scale_in | 8 | True | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 3940 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 144495 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 28321 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 21870 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 95 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 906 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 229746 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 97231 | False | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 15220 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 15220 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 2652 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 216 | False | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 110 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2693 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 669 | True | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 669 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 2046 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 1800 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 430 | True | report_only_reference |
| rolling_5d | entry_split_order_plan | submit | 1909 | True | report_only_reference |
| rolling_5d | scale_in_split_order_plan | scale_in | 8 | True | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 74 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 8586 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 4794 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 1294 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 1 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 521 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 4816 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 2284 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 217 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 217 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 435 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 7 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 9 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 32 | True | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 32 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 2046 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 2054 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 489 | True | report_only_reference |
| rolling_10d | entry_split_order_plan | submit | 1909 | True | report_only_reference |
| rolling_10d | scale_in_split_order_plan | scale_in | 8 | True | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 138 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 9090 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 4794 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 1307 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 1 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 635 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 5742 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 2509 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 540 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 540 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 531 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 15 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 9 | False | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 53 | True | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 53 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 2046 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 3382 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 682 | True | report_only_reference |
| rolling_20d | entry_split_order_plan | submit | 1909 | True | report_only_reference |
| rolling_20d | scale_in_split_order_plan | scale_in | 8 | True | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 377 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 9631 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 4799 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 1339 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 4 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 664 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 13114 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 5571 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 714 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 714 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 977 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 20 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 27 | False | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 113 | True | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 113 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 2046 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
