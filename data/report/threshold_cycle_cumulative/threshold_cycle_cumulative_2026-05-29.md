# Cumulative Threshold Cycle Report - 2026-05-29

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-05-29`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 39 | 1386585 | 201 | -0.4524 | 0.4129 | 0.5522 |
| rolling_5d | 5 | 655114 | 21 | -0.3848 | 0.381 | 0.4286 |
| rolling_10d | 10 | 1167819 | 24 | -0.1658 | 0.4167 | 0.4167 |
| rolling_20d | 20 | 1295228 | 25 | -0.2212 | 0.4 | 0.44 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 201 | -0.4524 | 0.4129 |
| cumulative | sim | 1368 | -0.5796 | 0.3677 |
| cumulative | combined | 1569 | -0.5633 | 0.3735 |
| rolling_5d | real | 21 | -0.3848 | 0.381 |
| rolling_5d | sim | 726 | -0.7804 | 0.3705 |
| rolling_5d | combined | 747 | -0.7693 | 0.3708 |
| rolling_10d | real | 24 | -0.1658 | 0.4167 |
| rolling_10d | sim | 1253 | -0.6401 | 0.3551 |
| rolling_10d | combined | 1277 | -0.6312 | 0.3563 |
| rolling_20d | real | 25 | -0.2212 | 0.4 |
| rolling_20d | sim | 1368 | -0.5796 | 0.3677 |
| rolling_20d | combined | 1393 | -0.5732 | 0.3683 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 201 | -0.4524 | -2.08 | 1.41 | 0.4129 | 0.5522 |
| cumulative | normal_only | 201 | -0.4524 | -2.08 | 1.41 | 0.4129 | 0.5522 |
| cumulative | initial_only | 180 | -0.5321 | -2.11 | 1.41 | 0.3889 | 0.5722 |
| cumulative | pyramid_activated | 20 | 0.2635 | -1.42 | 1.18 | 0.65 | 0.35 |
| cumulative | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |
| rolling_5d | all_completed_valid | 21 | -0.3848 | -2.71 | 2.32 | 0.381 | 0.4286 |
| rolling_5d | normal_only | 21 | -0.3848 | -2.71 | 2.32 | 0.381 | 0.4286 |
| rolling_5d | initial_only | 21 | -0.3848 | -2.71 | 2.32 | 0.381 | 0.4286 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 24 | -0.1658 | -2.71 | 2.75 | 0.4167 | 0.4167 |
| rolling_10d | normal_only | 24 | -0.1658 | -2.71 | 2.75 | 0.4167 | 0.4167 |
| rolling_10d | initial_only | 24 | -0.1658 | -2.71 | 2.75 | 0.4167 | 0.4167 |
| rolling_10d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_10d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_20d | all_completed_valid | 25 | -0.2212 | -2.71 | 2.75 | 0.4 | 0.44 |
| rolling_20d | normal_only | 25 | -0.2212 | -2.71 | 2.75 | 0.4 | 0.44 |
| rolling_20d | initial_only | 25 | -0.2212 | -2.71 | 2.75 | 0.4 | 0.44 |
| rolling_20d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_20d | reversal_add_activated | 0 | - | - | - | - | - |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 138584 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 84 | True | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 282683 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 134151 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 9675 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 121 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 793 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 112997 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 46932 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 12385 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 12385 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 495 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 857 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 17 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 1216 | True | report_only_reference |
| cumulative | position_sizing_cap_release | position_sizing | 201 | False | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 201 | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 201 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 22977 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 71421 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 82656 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 42950 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 4581 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 3 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 41 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 56939 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 21254 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 4876 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 4876 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 250 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 18 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 14 | True | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 288 | True | report_only_reference |
| rolling_5d | position_sizing_cap_release | position_sizing | 21 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 21 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 21 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 22977 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 72487 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 232531 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 116044 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 8328 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 11 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 218 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 93758 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 36161 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 9267 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 9267 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 389 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 39 | True | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 15 | True | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 639 | True | report_only_reference |
| rolling_10d | position_sizing_cap_release | position_sizing | 24 | False | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 24 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 24 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 22977 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 74771 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 0 | True | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 282683 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 134151 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 9675 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 15 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 218 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 105442 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 41203 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 11024 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 11024 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 440 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 52 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 15 | True | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 1121 | True | report_only_reference |
| rolling_20d | position_sizing_cap_release | position_sizing | 25 | False | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 25 | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 25 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 22977 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
