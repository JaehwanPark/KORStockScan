# Cumulative Threshold Cycle Report - 2026-05-26

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-05-26`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 36 | 925351 | 187 | -0.4603 | 0.4225 | 0.5615 |
| rolling_5d | 5 | 367032 | 7 | -0.46 | 0.5714 | 0.4286 |
| rolling_10d | 10 | 825575 | 10 | 0.088 | 0.6 | 0.4 |
| rolling_20d | 20 | 838181 | 22 | -0.5564 | 0.4091 | 0.5909 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 187 | -0.4603 | 0.4225 |
| cumulative | sim | 845 | -0.4202 | 0.3704 |
| cumulative | combined | 1032 | -0.4275 | 0.3798 |
| rolling_5d | real | 7 | -0.46 | 0.5714 |
| rolling_5d | sim | 326 | -0.6129 | 0.3834 |
| rolling_5d | combined | 333 | -0.6097 | 0.3874 |
| rolling_10d | real | 10 | 0.088 | 0.6 |
| rolling_10d | sim | 832 | -0.4702 | 0.3666 |
| rolling_10d | combined | 842 | -0.4636 | 0.3694 |
| rolling_20d | real | 22 | -0.5564 | 0.4091 |
| rolling_20d | sim | 845 | -0.4202 | 0.3704 |
| rolling_20d | combined | 867 | -0.4237 | 0.3714 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 187 | -0.4603 | -2.03 | 1.3 | 0.4225 | 0.5615 |
| cumulative | normal_only | 187 | -0.4603 | -2.03 | 1.3 | 0.4225 | 0.5615 |
| cumulative | initial_only | 166 | -0.5477 | -2.07 | 1.3 | 0.3976 | 0.5843 |
| cumulative | pyramid_activated | 20 | 0.2635 | -1.42 | 1.18 | 0.65 | 0.35 |
| cumulative | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |
| rolling_5d | all_completed_valid | 7 | -0.46 | -2.89 | 2.21 | 0.5714 | 0.4286 |
| rolling_5d | normal_only | 7 | -0.46 | -2.89 | 2.21 | 0.5714 | 0.4286 |
| rolling_5d | initial_only | 7 | -0.46 | -2.89 | 2.21 | 0.5714 | 0.4286 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 10 | 0.088 | -2.89 | 2.21 | 0.6 | 0.4 |
| rolling_10d | normal_only | 10 | 0.088 | -2.89 | 2.21 | 0.6 | 0.4 |
| rolling_10d | initial_only | 10 | 0.088 | -2.89 | 2.21 | 0.6 | 0.4 |
| rolling_10d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_10d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_20d | all_completed_valid | 22 | -0.5564 | -2.52 | 2.08 | 0.4091 | 0.5909 |
| rolling_20d | normal_only | 22 | -0.5564 | -2.52 | 2.08 | 0.4091 | 0.5909 |
| rolling_20d | initial_only | 22 | -0.5564 | -2.52 | 2.08 | 0.4091 | 0.5909 |
| rolling_20d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_20d | reversal_add_activated | 0 | - | - | - | - | - |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 69869 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 84 | True | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 232565 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 112050 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 6525 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 121 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 770 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 76597 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 33153 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 9440 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 9440 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 315 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 846 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 9 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 1001 | True | report_only_reference |
| cumulative | position_sizing_cap_release | position_sizing | 187 | False | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 187 | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 187 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 48781 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 2805 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 93458 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 45733 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 2607 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 1 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 73 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 34753 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 11753 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 3105 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 3105 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 104 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 20 | True | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 6 | True | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 146 | True | report_only_reference |
| rolling_5d | position_sizing_cap_release | position_sizing | 7 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 7 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 7 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 48781 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 4615 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 232565 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 112050 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 6525 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 12 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 195 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 67484 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 26612 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 7939 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 7939 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 254 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 28 | True | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 7 | True | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 685 | True | report_only_reference |
| rolling_10d | position_sizing_cap_release | position_sizing | 10 | False | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 10 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 10 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 48781 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 7881 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 0 | True | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 232565 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 112050 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 6525 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 33 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 204 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 69571 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 27617 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 8392 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 8392 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 264 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 55 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 8 | True | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 969 | True | report_only_reference |
| rolling_20d | position_sizing_cap_release | position_sizing | 22 | False | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 22 | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 22 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 48781 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
