# Cumulative Threshold Cycle Report - 2026-06-29

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-06-29`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 70 | 2039810 | 313 | -0.4427 | 0.4249 | 0.5527 |
| rolling_5d | 5 | 74095 | 12 | -0.2275 | 0.3333 | 0.6667 |
| rolling_10d | 10 | 153358 | 17 | -0.3712 | 0.3529 | 0.6471 |
| rolling_20d | 20 | 1106960 | 47 | -0.3549 | 0.3617 | 0.6383 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 313 | -0.4427 | 0.4249 |
| cumulative | sim | 3819 | -1.2801 | 0.2364 |
| cumulative | combined | 4132 | -1.2166 | 0.2507 |
| rolling_5d | real | 12 | -0.2275 | 0.3333 |
| rolling_5d | sim | 169 | -1.2077 | 0.2189 |
| rolling_5d | combined | 181 | -1.1427 | 0.2265 |
| rolling_10d | real | 17 | -0.3712 | 0.3529 |
| rolling_10d | sim | 511 | -1.5047 | 0.1937 |
| rolling_10d | combined | 528 | -1.4682 | 0.1989 |
| rolling_20d | real | 47 | -0.3549 | 0.3617 |
| rolling_20d | sim | 2274 | -1.3227 | 0.2199 |
| rolling_20d | combined | 2321 | -1.3031 | 0.2227 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 313 | -0.4427 | -2.37 | 1.58 | 0.4249 | 0.5527 |
| cumulative | normal_only | 313 | -0.4427 | -2.37 | 1.58 | 0.4249 | 0.5527 |
| cumulative | initial_only | 287 | -0.4971 | -2.39 | 1.58 | 0.4111 | 0.5645 |
| cumulative | pyramid_activated | 24 | 0.2621 | -1.42 | 1.59 | 0.625 | 0.375 |
| cumulative | reversal_add_activated | 2 | -1.085 | -1.74 | -0.43 | 0 | 1 |
| rolling_5d | all_completed_valid | 12 | -0.2275 | -2.51 | 2.21 | 0.3333 | 0.6667 |
| rolling_5d | normal_only | 12 | -0.2275 | -2.51 | 2.21 | 0.3333 | 0.6667 |
| rolling_5d | initial_only | 11 | -0.09 | -2.51 | 2.21 | 0.3636 | 0.6364 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 1 | -1.74 | -1.74 | -1.74 | 0 | 1 |
| rolling_10d | all_completed_valid | 17 | -0.3712 | -2.77 | 2.75 | 0.3529 | 0.6471 |
| rolling_10d | normal_only | 17 | -0.3712 | -2.77 | 2.75 | 0.3529 | 0.6471 |
| rolling_10d | initial_only | 16 | -0.2856 | -2.77 | 2.75 | 0.375 | 0.625 |
| rolling_10d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_10d | reversal_add_activated | 1 | -1.74 | -1.74 | -1.74 | 0 | 1 |
| rolling_20d | all_completed_valid | 47 | -0.3549 | -2.77 | 2.8 | 0.3617 | 0.6383 |
| rolling_20d | normal_only | 47 | -0.3549 | -2.77 | 2.8 | 0.3617 | 0.6383 |
| rolling_20d | initial_only | 43 | -0.3395 | -2.77 | 2.75 | 0.3721 | 0.6279 |
| rolling_20d | pyramid_activated | 3 | -0.1133 | -2.39 | 3.22 | 0.3333 | 0.6667 |
| rolling_20d | reversal_add_activated | 1 | -1.74 | -1.74 | -1.74 | 0 | 1 |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 289703 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 89 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 28575 | True | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 2359 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 171960 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 46668 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 22073 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 69 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 556 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 206638 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 88594 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 18228 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 18228 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 912 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 157 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 79 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2039 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 313 | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 313 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 7792 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 163 | False | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 1029 | True | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 224 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 4708 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 1077 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 1245 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 1 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 14 | False | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 11343 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 4317 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 556 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 556 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 28 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 1 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 139 | True | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 12 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 12 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 7792 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 3274 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 3551 | True | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 393 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 9578 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 1972 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 2401 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 2 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 21 | False | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 20747 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 8048 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 1428 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 1428 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 74 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 2 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 307 | True | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 17 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 17 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 7792 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 137097 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 3 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 19661 | True | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 2050 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 82411 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 11371 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 14111 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 42 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 104 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 122302 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 54726 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 10137 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 10137 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 508 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 118 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 23 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 1661 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 47 | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 47 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 7792 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
