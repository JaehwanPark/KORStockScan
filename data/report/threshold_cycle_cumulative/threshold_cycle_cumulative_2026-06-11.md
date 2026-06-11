# Cumulative Threshold Cycle Report - 2026-06-11

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-06-11`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 52 | 1205156 | 279 | -0.4116 | 0.4409 | 0.5341 |
| rolling_5d | 5 | 577445 | 40 | -0.0275 | 0.525 | 0.475 |
| rolling_10d | 10 | 948298 | 66 | -0.2595 | 0.5152 | 0.4848 |
| rolling_20d | 20 | 1162927 | 99 | -0.3229 | 0.4848 | 0.4747 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 279 | -0.4116 | 0.4409 |
| cumulative | sim | 2312 | -1.1999 | 0.2638 |
| cumulative | combined | 2591 | -1.115 | 0.2829 |
| rolling_5d | real | 40 | -0.0275 | 0.525 |
| rolling_5d | sim | 1424 | -1.222 | 0.2633 |
| rolling_5d | combined | 1464 | -1.1894 | 0.2705 |
| rolling_10d | real | 66 | -0.2595 | 0.5152 |
| rolling_10d | sim | 1963 | -1.2196 | 0.2608 |
| rolling_10d | combined | 2029 | -1.1884 | 0.2691 |
| rolling_20d | real | 99 | -0.3229 | 0.4848 |
| rolling_20d | sim | 2312 | -1.1999 | 0.2638 |
| rolling_20d | combined | 2411 | -1.1639 | 0.2729 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 279 | -0.4116 | -2.32 | 1.58 | 0.4409 | 0.5341 |
| cumulative | normal_only | 279 | -0.4116 | -2.32 | 1.58 | 0.4409 | 0.5341 |
| cumulative | initial_only | 255 | -0.4779 | -2.33 | 1.52 | 0.4235 | 0.549 |
| cumulative | pyramid_activated | 23 | 0.3243 | -1.42 | 1.59 | 0.6522 | 0.3478 |
| cumulative | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |
| rolling_5d | all_completed_valid | 40 | -0.0275 | -2.51 | 2.8 | 0.525 | 0.475 |
| rolling_5d | normal_only | 40 | -0.0275 | -2.51 | 2.8 | 0.525 | 0.475 |
| rolling_5d | initial_only | 38 | -0.0508 | -2.51 | 2.8 | 0.5263 | 0.4737 |
| rolling_5d | pyramid_activated | 2 | 0.415 | -2.39 | 3.22 | 0.5 | 0.5 |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 66 | -0.2595 | -2.55 | 2.03 | 0.5152 | 0.4848 |
| rolling_10d | normal_only | 66 | -0.2595 | -2.55 | 2.03 | 0.5152 | 0.4848 |
| rolling_10d | initial_only | 63 | -0.3067 | -2.55 | 1.85 | 0.5079 | 0.4921 |
| rolling_10d | pyramid_activated | 3 | 0.73 | -2.39 | 3.22 | 0.6667 | 0.3333 |
| rolling_10d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_20d | all_completed_valid | 99 | -0.3229 | -2.69 | 2.2 | 0.4848 | 0.4747 |
| rolling_20d | normal_only | 99 | -0.3229 | -2.69 | 2.2 | 0.4848 | 0.4747 |
| rolling_20d | initial_only | 96 | -0.3558 | -2.69 | 2.03 | 0.4792 | 0.4792 |
| rolling_20d | pyramid_activated | 3 | 0.73 | -2.39 | 3.22 | 0.6667 | 0.3333 |
| rolling_20d | reversal_add_activated | 0 | - | - | - | - | - |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 184867 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 86 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 14024 | True | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 795 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 103878 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 38202 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 11951 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 39 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 475 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 113781 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 47022 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 9935 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 9935 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 587 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 64 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 67 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 649 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 279 | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 279 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 16418 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 63125 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 8391 | True | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 567 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 42382 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 10808 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 7679 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 32 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 96 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 65467 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 27177 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 3658 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 3658 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 354 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 25 | True | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 38 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 513 | True | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 40 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 40 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 16418 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 120440 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 11782 | True | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 605 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 80163 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 25531 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 10628 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 33 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 108 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 95170 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 38597 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 7011 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 7011 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 490 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 64 | True | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 56 | True | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 614 | True | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 66 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 66 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 16418 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 145839 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 2 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 13644 | True | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 647 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 103878 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 38202 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 11951 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 39 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 136 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 113781 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 45051 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 9552 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 9552 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 587 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 64 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 67 | True | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 649 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 99 | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 99 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 16418 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
