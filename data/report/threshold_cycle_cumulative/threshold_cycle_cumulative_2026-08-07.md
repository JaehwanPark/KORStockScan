# Cumulative Threshold Cycle Report - 2026-08-07

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-08-07`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 109 | 1976576 | 669 | -0.2648 | 0.4843 | 0.4813 |
| rolling_5d | 5 | 169831 | 26 | 0.3404 | 0.6538 | 0.3462 |
| rolling_10d | 10 | 202654 | 39 | -0.1167 | 0.641 | 0.359 |
| rolling_20d | 20 | 239737 | 111 | -0.1621 | 0.5766 | 0.3874 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 669 | -0.2648 | 0.4843 |
| cumulative | sim | 3316 | -1.3189 | 0.2355 |
| cumulative | combined | 3985 | -1.1419 | 0.2773 |
| rolling_5d | real | 26 | 0.3404 | 0.6538 |
| rolling_5d | sim | 16 | -0.5194 | 0.5 |
| rolling_5d | combined | 42 | 0.0129 | 0.5952 |
| rolling_10d | real | 39 | -0.1167 | 0.641 |
| rolling_10d | sim | 26 | -0.7046 | 0.3846 |
| rolling_10d | combined | 65 | -0.3518 | 0.5385 |
| rolling_20d | real | 111 | -0.1621 | 0.5766 |
| rolling_20d | sim | 42 | -0.7971 | 0.2857 |
| rolling_20d | combined | 153 | -0.3364 | 0.4967 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 669 | -0.2648 | -3.16 | 1.93 | 0.4843 | 0.4813 |
| cumulative | normal_only | 669 | -0.2648 | -3.16 | 1.93 | 0.4843 | 0.4813 |
| cumulative | initial_only | 588 | -0.2813 | -3.14 | 1.93 | 0.4796 | 0.4847 |
| cumulative | pyramid_activated | 31 | 0.3365 | -1.45 | 1.59 | 0.6452 | 0.3548 |
| cumulative | reversal_add_activated | 51 | -0.2973 | -4.32 | 2.18 | 0.451 | 0.5098 |
| rolling_5d | all_completed_valid | 26 | 0.3404 | -3.28 | 3.14 | 0.6538 | 0.3462 |
| rolling_5d | normal_only | 26 | 0.3404 | -3.28 | 3.14 | 0.6538 | 0.3462 |
| rolling_5d | initial_only | 24 | 0.3529 | -3.28 | 3.14 | 0.6667 | 0.3333 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 2 | 0.19 | -0.32 | 0.7 | 0.5 | 0.5 |
| rolling_10d | all_completed_valid | 39 | -0.1167 | -3.93 | 2.38 | 0.641 | 0.359 |
| rolling_10d | normal_only | 39 | -0.1167 | -3.93 | 2.38 | 0.641 | 0.359 |
| rolling_10d | initial_only | 37 | -0.1332 | -3.93 | 2.38 | 0.6486 | 0.3514 |
| rolling_10d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_10d | reversal_add_activated | 2 | 0.19 | -0.32 | 0.7 | 0.5 | 0.5 |
| rolling_20d | all_completed_valid | 111 | -0.1621 | -3.56 | 1.48 | 0.5766 | 0.3874 |
| rolling_20d | normal_only | 111 | -0.1621 | -3.56 | 1.48 | 0.5766 | 0.3874 |
| rolling_20d | initial_only | 106 | -0.1382 | -3.56 | 1.51 | 0.5849 | 0.3774 |
| rolling_20d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_20d | reversal_add_activated | 5 | -0.668 | -3.68 | 0.7 | 0.4 | 0.6 |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 203448 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 15 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 17337 | True | report_only_reference |
| cumulative | entry_split_order_plan | submit | 359 | True | report_only_reference |
| cumulative | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 3940 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 154439 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 29739 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 23018 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 96 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 951 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 230249 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 97463 | False | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 15317 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 15317 | False | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 2656 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 216 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 110 | False | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2693 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 669 | True | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 669 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 850 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 2401 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 465 | True | report_only_reference |
| rolling_5d | entry_split_order_plan | submit | 359 | True | report_only_reference |
| rolling_5d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 64 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 16182 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 4491 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 2139 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 19 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 493 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 3985 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 1946 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 303 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 303 | False | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 433 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 7 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 4 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 26 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 26 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 850 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 2982 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 622 | True | report_only_reference |
| rolling_10d | entry_split_order_plan | submit | 359 | True | report_only_reference |
| rolling_10d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 108 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 19019 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 6212 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 2455 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 19 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 627 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 5823 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 2676 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 485 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 485 | False | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 445 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 10 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 9 | False | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 39 | True | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 39 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 850 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 4460 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 804 | True | report_only_reference |
| rolling_20d | entry_split_order_plan | submit | 359 | True | report_only_reference |
| rolling_20d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 372 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 19479 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 6216 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 2478 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 9 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 709 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 12822 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 5325 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 800 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 800 | False | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 975 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 20 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 25 | False | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 111 | True | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 111 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 850 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
