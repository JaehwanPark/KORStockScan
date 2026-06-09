# Cumulative Threshold Cycle Report - 2026-06-09

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-06-09`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 50 | 932850 | 266 | -0.4582 | 0.4361 | 0.5376 |
| rolling_5d | 5 | 450806 | 28 | -0.3807 | 0.5 | 0.5 |
| rolling_10d | 10 | 890621 | 65 | -0.4758 | 0.5077 | 0.4923 |
| rolling_20d | 20 | 890621 | 87 | -0.3952 | 0.4828 | 0.4713 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 266 | -0.4582 | 0.4361 |
| cumulative | sim | 1545 | -1.2173 | 0.2608 |
| cumulative | combined | 1811 | -1.1058 | 0.2866 |
| rolling_5d | real | 28 | -0.3807 | 0.5 |
| rolling_5d | sim | 808 | -1.2801 | 0.2488 |
| rolling_5d | combined | 836 | -1.25 | 0.2572 |
| rolling_10d | real | 65 | -0.4758 | 0.5077 |
| rolling_10d | sim | 1545 | -1.2173 | 0.2608 |
| rolling_10d | combined | 1610 | -1.1874 | 0.2708 |
| rolling_20d | real | 87 | -0.3952 | 0.4828 |
| rolling_20d | sim | 1545 | -1.2173 | 0.2608 |
| rolling_20d | combined | 1632 | -1.1735 | 0.2727 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 266 | -0.4582 | -2.32 | 1.47 | 0.4361 | 0.5376 |
| cumulative | normal_only | 266 | -0.4582 | -2.32 | 1.47 | 0.4361 | 0.5376 |
| cumulative | initial_only | 244 | -0.5249 | -2.36 | 1.47 | 0.418 | 0.5533 |
| cumulative | pyramid_activated | 21 | 0.3157 | -1.2 | 1.36 | 0.6667 | 0.3333 |
| cumulative | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |
| rolling_5d | all_completed_valid | 28 | -0.3807 | -2.55 | 1.52 | 0.5 | 0.5 |
| rolling_5d | normal_only | 28 | -0.3807 | -2.55 | 1.52 | 0.5 | 0.5 |
| rolling_5d | initial_only | 28 | -0.3807 | -2.55 | 1.52 | 0.5 | 0.5 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 65 | -0.4758 | -2.62 | 1.52 | 0.5077 | 0.4923 |
| rolling_10d | normal_only | 65 | -0.4758 | -2.62 | 1.52 | 0.5077 | 0.4923 |
| rolling_10d | initial_only | 64 | -0.5045 | -2.62 | 1.52 | 0.5 | 0.5 |
| rolling_10d | pyramid_activated | 1 | 1.36 | 1.36 | 1.36 | 1 | 0 |
| rolling_10d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_20d | all_completed_valid | 87 | -0.3952 | -2.7 | 1.7 | 0.4828 | 0.4713 |
| rolling_20d | normal_only | 87 | -0.3952 | -2.7 | 1.7 | 0.4828 | 0.4713 |
| rolling_20d | initial_only | 86 | -0.4156 | -2.7 | 1.7 | 0.4767 | 0.4767 |
| rolling_20d | pyramid_activated | 1 | 1.36 | 1.36 | 1.36 | 1 | 0 |
| rolling_20d | reversal_add_activated | 0 | - | - | - | - | - |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 152606 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 86 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 8914 | False | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 309 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 89549 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 35297 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 7962 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 27 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 452 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 84336 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 33868 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 8091 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 8091 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 404 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 39 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 56 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 378 | True | report_only_reference |
| cumulative | position_sizing_cap_release | position_sizing | 266 | False | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 266 | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 266 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 20862 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 55990 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 4554 | False | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 82 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 43179 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 11097 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 5196 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 15 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 73 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 46159 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 18098 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 3234 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 3234 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 204 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 28 | True | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 270 | True | report_only_reference |
| rolling_5d | position_sizing_cap_release | position_sizing | 28 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 28 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 28 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 20862 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 113578 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 2 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 8534 | False | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 161 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 89549 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 35297 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 7962 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 27 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 113 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 84336 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 31897 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 7708 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 7708 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 404 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 39 | True | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 56 | True | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 378 | True | report_only_reference |
| rolling_10d | position_sizing_cap_release | position_sizing | 65 | False | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 65 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 65 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 20862 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 113578 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 2 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 8534 | False | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 161 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 89549 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 35297 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 7962 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 27 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 113 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 84336 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 31897 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 7708 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 7708 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 404 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 39 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 56 | True | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 378 | True | report_only_reference |
| rolling_20d | position_sizing_cap_release | position_sizing | 87 | False | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 87 | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 87 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 20862 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
