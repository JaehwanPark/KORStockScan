# Cumulative Threshold Cycle Report - 2026-06-15

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-06-15`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 56 | 1423863 | 285 | -0.4199 | 0.4351 | 0.5404 |
| rolling_5d | 5 | 315923 | 8 | -1.15 | 0.125 | 0.875 |
| rolling_10d | 10 | 796152 | 46 | -0.1293 | 0.4783 | 0.5217 |
| rolling_20d | 20 | 1381634 | 98 | -0.3429 | 0.4592 | 0.5 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 285 | -0.4199 | 0.4351 |
| cumulative | sim | 2659 | -1.2423 | 0.2475 |
| cumulative | combined | 2944 | -1.1627 | 0.2656 |
| rolling_5d | real | 8 | -1.15 | 0.125 |
| rolling_5d | sim | 683 | -1.1323 | 0.2533 |
| rolling_5d | combined | 691 | -1.1325 | 0.2518 |
| rolling_10d | real | 46 | -0.1293 | 0.4783 |
| rolling_10d | sim | 1771 | -1.2814 | 0.2388 |
| rolling_10d | combined | 1817 | -1.2522 | 0.2449 |
| rolling_20d | real | 98 | -0.3429 | 0.4592 |
| rolling_20d | sim | 2659 | -1.2423 | 0.2475 |
| rolling_20d | combined | 2757 | -1.2104 | 0.255 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 285 | -0.4199 | -2.32 | 1.58 | 0.4351 | 0.5404 |
| cumulative | normal_only | 285 | -0.4199 | -2.32 | 1.58 | 0.4351 | 0.5404 |
| cumulative | initial_only | 261 | -0.4855 | -2.33 | 1.52 | 0.4176 | 0.5556 |
| cumulative | pyramid_activated | 23 | 0.3243 | -1.42 | 1.59 | 0.6522 | 0.3478 |
| cumulative | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |
| rolling_5d | all_completed_valid | 8 | -1.15 | -3.31 | 3.3 | 0.125 | 0.875 |
| rolling_5d | normal_only | 8 | -1.15 | -3.31 | 3.3 | 0.125 | 0.875 |
| rolling_5d | initial_only | 7 | -0.9729 | -3.31 | 3.3 | 0.1429 | 0.8571 |
| rolling_5d | pyramid_activated | 1 | -2.39 | -2.39 | -2.39 | 0 | 1 |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 46 | -0.1293 | -2.51 | 3.22 | 0.4783 | 0.5217 |
| rolling_10d | normal_only | 46 | -0.1293 | -2.51 | 3.22 | 0.4783 | 0.5217 |
| rolling_10d | initial_only | 44 | -0.1541 | -2.51 | 2.8 | 0.4773 | 0.5227 |
| rolling_10d | pyramid_activated | 2 | 0.415 | -2.39 | 3.22 | 0.5 | 0.5 |
| rolling_10d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_20d | all_completed_valid | 98 | -0.3429 | -2.67 | 2.2 | 0.4592 | 0.5 |
| rolling_20d | normal_only | 98 | -0.3429 | -2.67 | 2.2 | 0.4592 | 0.5 |
| rolling_20d | initial_only | 95 | -0.3767 | -2.67 | 2.03 | 0.4526 | 0.5053 |
| rolling_20d | pyramid_activated | 3 | 0.73 | -2.39 | 3.22 | 0.6667 | 0.3333 |
| rolling_20d | reversal_add_activated | 0 | - | - | - | - | - |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 213871 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 89 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 19264 | True | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 1273 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 121113 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 41592 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 14596 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 54 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 515 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 137704 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 60002 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 11514 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 11514 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 628 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 134 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 70 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 1107 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 285 | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 285 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 19534 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 39174 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 3 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 7513 | True | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 693 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 22366 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 4917 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 4229 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 15 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 40 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 33751 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 17426 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 1949 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 1949 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 154 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 95 | True | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 5 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 505 | True | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 8 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 8 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 19534 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 92129 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 3 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 13631 | True | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 1045 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 59617 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 14198 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 10324 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 30 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 136 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 89390 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 40157 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 5237 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 5237 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 395 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 95 | True | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 41 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 971 | True | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 46 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 46 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 19534 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 174843 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 5 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 18884 | True | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 1125 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 121113 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 41592 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 14596 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 54 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 176 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 137704 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 58031 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 11131 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 11131 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 628 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 134 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 70 | True | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 1107 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 98 | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 98 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 19534 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
