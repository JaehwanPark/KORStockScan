# Cumulative Threshold Cycle Report - 2026-06-23

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-06-23`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 64 | 1940415 | 297 | -0.4415 | 0.431 | 0.5455 |
| rolling_5d | 5 | 69490 | 1 | 1.12 | 1 | 0 |
| rolling_10d | 10 | 639223 | 14 | -0.9 | 0.2857 | 0.7143 |
| rolling_20d | 20 | 1481920 | 67 | -0.4654 | 0.4179 | 0.5821 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 297 | -0.4415 | 0.431 |
| cumulative | sim | 3578 | -1.2771 | 0.2384 |
| cumulative | combined | 3875 | -1.213 | 0.2532 |
| rolling_5d | real | 1 | 1.12 | 1 |
| rolling_5d | sim | 356 | -1.6548 | 0.177 |
| rolling_5d | combined | 357 | -1.6471 | 0.1793 |
| rolling_10d | real | 14 | -0.9 | 0.2857 |
| rolling_10d | sim | 1041 | -1.348 | 0.2094 |
| rolling_10d | combined | 1055 | -1.3421 | 0.2104 |
| rolling_20d | real | 67 | -0.4654 | 0.4179 |
| rolling_20d | sim | 2872 | -1.3069 | 0.2284 |
| rolling_20d | combined | 2939 | -1.2878 | 0.2327 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 297 | -0.4415 | -2.36 | 1.52 | 0.431 | 0.5455 |
| cumulative | normal_only | 297 | -0.4415 | -2.36 | 1.52 | 0.431 | 0.5455 |
| cumulative | initial_only | 272 | -0.5036 | -2.37 | 1.52 | 0.4154 | 0.5588 |
| cumulative | pyramid_activated | 24 | 0.2621 | -1.42 | 1.59 | 0.625 | 0.375 |
| cumulative | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |
| rolling_5d | all_completed_valid | 1 | 1.12 | 1.12 | 1.12 | 1 | 0 |
| rolling_5d | normal_only | 1 | 1.12 | 1.12 | 1.12 | 1 | 0 |
| rolling_5d | initial_only | 1 | 1.12 | 1.12 | 1.12 | 1 | 0 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 14 | -0.9 | -3.44 | 1.34 | 0.2857 | 0.7143 |
| rolling_10d | normal_only | 14 | -0.9 | -3.44 | 1.34 | 0.2857 | 0.7143 |
| rolling_10d | initial_only | 13 | -0.8792 | -3.44 | 1.34 | 0.3077 | 0.6923 |
| rolling_10d | pyramid_activated | 1 | -1.17 | -1.17 | -1.17 | 0 | 1 |
| rolling_10d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_20d | all_completed_valid | 67 | -0.4654 | -2.55 | 2.2 | 0.4179 | 0.5821 |
| rolling_20d | normal_only | 67 | -0.4654 | -2.55 | 2.2 | 0.4179 | 0.5821 |
| rolling_20d | initial_only | 64 | -0.4819 | -2.55 | 2.03 | 0.4219 | 0.5781 |
| rolling_20d | pyramid_activated | 3 | -0.1133 | -2.39 | 3.22 | 0.3333 | 0.6667 |
| rolling_20d | reversal_add_activated | 0 | - | - | - | - | - |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 289434 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 89 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 26987 | True | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 2089 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 164997 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 45013 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 20338 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 69 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 538 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 192013 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 82940 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 17531 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 17531 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 875 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 157 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 77 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 1866 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 297 | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 297 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 7800 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 4030 | False | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 2684 | True | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 256 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 4700 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 317 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 666 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 1 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 3 | False | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 7325 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 2900 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 796 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 796 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 103 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 1 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 190 | True | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 1 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 1 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 7800 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 92140 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 3 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 9257 | True | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 949 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 52839 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 4789 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 6854 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 25 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 56 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 67998 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 29708 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 7108 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 7108 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 267 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 34 | True | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 7 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 852 | True | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 14 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 14 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 7800 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 197345 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 3 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 22703 | True | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 1865 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 120296 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 21637 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 17665 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 57 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 159 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 155949 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 67864 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 12908 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 12908 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 677 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 118 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 50 | True | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 1770 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 67 | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 67 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 7800 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
