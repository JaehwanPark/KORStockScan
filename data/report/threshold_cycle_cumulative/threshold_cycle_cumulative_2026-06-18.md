# Cumulative Threshold Cycle Report - 2026-06-18

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-06-18`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 59 | 1870925 | 293 | -0.4545 | 0.43 | 0.5461 |
| rolling_5d | 5 | 569733 | 10 | -1.464 | 0.2 | 0.8 |
| rolling_10d | 10 | 1076468 | 29 | -0.3048 | 0.4138 | 0.5862 |
| rolling_20d | 20 | 1828696 | 92 | -0.4589 | 0.4674 | 0.5326 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 293 | -0.4545 | 0.43 |
| cumulative | sim | 3222 | -1.2353 | 0.2452 |
| cumulative | combined | 3515 | -1.1702 | 0.2606 |
| rolling_5d | real | 10 | -1.464 | 0.2 |
| rolling_5d | sim | 685 | -1.1886 | 0.2263 |
| rolling_5d | combined | 695 | -1.1926 | 0.2259 |
| rolling_10d | real | 29 | -0.3048 | 0.4138 |
| rolling_10d | sim | 1958 | -1.2342 | 0.2344 |
| rolling_10d | combined | 1987 | -1.2206 | 0.237 |
| rolling_20d | real | 92 | -0.4589 | 0.4674 |
| rolling_20d | sim | 3222 | -1.2353 | 0.2452 |
| rolling_20d | combined | 3314 | -1.2138 | 0.2514 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 293 | -0.4545 | -2.36 | 1.52 | 0.43 | 0.5461 |
| cumulative | normal_only | 293 | -0.4545 | -2.36 | 1.52 | 0.43 | 0.5461 |
| cumulative | initial_only | 268 | -0.5187 | -2.38 | 1.52 | 0.4142 | 0.5597 |
| cumulative | pyramid_activated | 24 | 0.2621 | -1.42 | 1.59 | 0.625 | 0.375 |
| cumulative | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |
| rolling_5d | all_completed_valid | 10 | -1.464 | -4.24 | 0.87 | 0.2 | 0.8 |
| rolling_5d | normal_only | 10 | -1.464 | -4.24 | 0.87 | 0.2 | 0.8 |
| rolling_5d | initial_only | 9 | -1.4967 | -4.24 | 1.34 | 0.2222 | 0.7778 |
| rolling_5d | pyramid_activated | 1 | -1.17 | -1.17 | -1.17 | 0 | 1 |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 29 | -0.3048 | -3.31 | 3.22 | 0.4138 | 0.5862 |
| rolling_10d | normal_only | 29 | -0.3048 | -3.31 | 3.22 | 0.4138 | 0.5862 |
| rolling_10d | initial_only | 26 | -0.3269 | -3.31 | 2.8 | 0.4231 | 0.5769 |
| rolling_10d | pyramid_activated | 3 | -0.1133 | -2.39 | 3.22 | 0.3333 | 0.6667 |
| rolling_10d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_20d | all_completed_valid | 92 | -0.4589 | -2.62 | 1.7 | 0.4674 | 0.5326 |
| rolling_20d | normal_only | 92 | -0.4589 | -2.62 | 1.7 | 0.4674 | 0.5326 |
| rolling_20d | initial_only | 88 | -0.4914 | -2.67 | 1.7 | 0.4659 | 0.5341 |
| rolling_20d | pyramid_activated | 4 | 0.255 | -2.39 | 3.22 | 0.5 | 0.5 |
| rolling_20d | reversal_add_activated | 0 | - | - | - | - | - |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 285404 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 89 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 24303 | True | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 1833 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 160297 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 44696 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 19672 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 69 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 535 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 184688 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 80040 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 16735 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 16735 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 772 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 157 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 76 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 1676 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 293 | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 293 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 21287 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 88110 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 3 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 6573 | True | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 693 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 48139 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 4472 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 6188 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 25 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 53 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 60673 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 26808 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 6312 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 6312 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 164 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 34 | True | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 6 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 662 | True | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 10 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 10 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 21287 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 146907 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 3 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 16725 | True | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 1559 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 82748 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 12899 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 13486 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 43 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 145 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 116040 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 51641 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 9750 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 9750 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 437 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 118 | True | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 22 | True | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 1332 | True | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 29 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 29 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 21287 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 246376 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 5 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 23923 | True | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 1685 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 160297 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 44696 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 19672 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 69 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 196 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 184688 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 78069 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 16352 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 16352 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 772 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 157 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 76 | True | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 1676 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 92 | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 92 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 21287 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
