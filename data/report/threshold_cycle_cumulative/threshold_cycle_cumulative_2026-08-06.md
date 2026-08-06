# Cumulative Threshold Cycle Report - 2026-08-06

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-08-06`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 108 | 1961063 | 669 | -0.2648 | 0.4843 | 0.4813 |
| rolling_5d | 5 | 154318 | 26 | 0.3404 | 0.6538 | 0.3462 |
| rolling_10d | 10 | 189767 | 51 | -0.1753 | 0.6275 | 0.3725 |
| rolling_20d | 20 | 224224 | 111 | -0.1621 | 0.5766 | 0.3874 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 669 | -0.2648 | 0.4843 |
| cumulative | sim | 3314 | -1.3201 | 0.2351 |
| cumulative | combined | 3983 | -1.1428 | 0.2769 |
| rolling_5d | real | 26 | 0.3404 | 0.6538 |
| rolling_5d | sim | 14 | -0.6814 | 0.4286 |
| rolling_5d | combined | 40 | -0.0172 | 0.575 |
| rolling_10d | real | 51 | -0.1753 | 0.6275 |
| rolling_10d | sim | 25 | -0.7912 | 0.32 |
| rolling_10d | combined | 76 | -0.3779 | 0.5263 |
| rolling_20d | real | 111 | -0.1621 | 0.5766 |
| rolling_20d | sim | 40 | -0.8678 | 0.25 |
| rolling_20d | combined | 151 | -0.349 | 0.4901 |

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
| rolling_10d | all_completed_valid | 51 | -0.1753 | -3.67 | 1.66 | 0.6275 | 0.3725 |
| rolling_10d | normal_only | 51 | -0.1753 | -3.67 | 1.66 | 0.6275 | 0.3725 |
| rolling_10d | initial_only | 49 | -0.1902 | -3.71 | 2.03 | 0.6327 | 0.3673 |
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
| cumulative | entry_mechanical_momentum | entry | 203234 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 15 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 17304 | True | report_only_reference |
| cumulative | entry_split_order_plan | submit | 454 | True | report_only_reference |
| cumulative | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 3940 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 152184 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 29402 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 22637 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 96 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 917 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 230047 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 97392 | False | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 15316 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 15316 | False | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 2654 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 216 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 110 | False | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2693 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 669 | True | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 669 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 1364 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 2187 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 432 | True | report_only_reference |
| rolling_5d | entry_split_order_plan | submit | 454 | True | report_only_reference |
| rolling_5d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 64 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 13927 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 4154 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 1758 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 19 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 459 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 3783 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 1875 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 302 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 302 | False | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 431 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 7 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 4 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 26 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 26 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 1364 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 2824 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 601 | True | report_only_reference |
| rolling_10d | entry_split_order_plan | submit | 454 | True | report_only_reference |
| rolling_10d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 134 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 16764 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 5875 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 2074 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 19 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 646 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 5948 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 2668 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 630 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 630 | False | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 532 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 14 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 9 | False | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 51 | True | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 51 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 1364 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 4246 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 771 | True | report_only_reference |
| rolling_20d | entry_split_order_plan | submit | 454 | True | report_only_reference |
| rolling_20d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 372 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 17224 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 5879 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 2097 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 9 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 675 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 12620 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 5254 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 799 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 799 | False | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 973 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 20 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 25 | False | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 111 | True | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 111 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 1364 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
