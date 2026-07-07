# Cumulative Threshold Cycle Report - 2026-07-07

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-07-07`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 78 | 2202691 | 0 | - | - | - |
| rolling_5d | 5 | 59100 | 0 | - | - | - |
| rolling_10d | 10 | 187661 | 0 | - | - | - |
| rolling_20d | 20 | 453945 | 0 | - | - | - |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 0 | - | - |
| cumulative | sim | 3937 | -1.284 | 0.2405 |
| cumulative | combined | 3937 | -1.284 | 0.2405 |
| rolling_5d | real | 0 | - | - |
| rolling_5d | sim | 59 | -1.6308 | 0.322 |
| rolling_5d | combined | 59 | -1.6308 | 0.322 |
| rolling_10d | real | 0 | - | - |
| rolling_10d | sim | 149 | -1.2397 | 0.3826 |
| rolling_10d | combined | 149 | -1.2397 | 0.3826 |
| rolling_20d | real | 0 | - | - |
| rolling_20d | sim | 916 | -1.4225 | 0.2293 |
| rolling_20d | combined | 916 | -1.4225 | 0.2293 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 0 | - | - | - | - | - |
| cumulative | normal_only | 0 | - | - | - | - | - |
| cumulative | initial_only | 0 | - | - | - | - | - |
| cumulative | pyramid_activated | 0 | - | - | - | - | - |
| cumulative | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_5d | all_completed_valid | 0 | - | - | - | - | - |
| rolling_5d | normal_only | 0 | - | - | - | - | - |
| rolling_5d | initial_only | 0 | - | - | - | - | - |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 0 | - | - | - | - | - |
| rolling_10d | normal_only | 0 | - | - | - | - | - |
| rolling_10d | initial_only | 0 | - | - | - | - | - |
| rolling_10d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_10d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_20d | all_completed_valid | 0 | - | - | - | - | - |
| rolling_20d | normal_only | 0 | - | - | - | - | - |
| rolling_20d | initial_only | 0 | - | - | - | - | - |
| rolling_20d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_20d | reversal_add_activated | 0 | - | - | - | - | - |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 293732 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 89 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 18262 | True | report_only_reference |
| cumulative | entry_split_order_plan | submit | 6036 | True | report_only_reference |
| cumulative | scale_in_split_order_plan | scale_in | 5 | True | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 3482 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 178640 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 47622 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 22855 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 89 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 620 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 243891 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 103351 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 19046 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 19046 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 1515 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 187 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 110 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2719 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 0 | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 0 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 4063 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 1529 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 636 | True | report_only_reference |
| rolling_5d | entry_split_order_plan | submit | 6036 | True | report_only_reference |
| rolling_5d | scale_in_split_order_plan | scale_in | 5 | True | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 386 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 3491 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 345 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 432 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 8 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 46 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 11465 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 4281 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 307 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 307 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 379 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 25 | True | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 10 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 61 | True | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 0 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 0 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 4063 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 4091 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 1723 | True | report_only_reference |
| rolling_10d | entry_split_order_plan | submit | 6036 | True | report_only_reference |
| rolling_10d | scale_in_split_order_plan | scale_in | 5 | True | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 1197 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 8175 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 1477 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 1122 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 22 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 64 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 41716 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 16766 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 880 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 880 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 613 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 30 | True | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 31 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 697 | True | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 0 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 0 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 4063 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 13221 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 5208 | True | report_only_reference |
| rolling_20d | entry_split_order_plan | submit | 6036 | True | report_only_reference |
| rolling_20d | scale_in_split_order_plan | scale_in | 5 | True | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 2061 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 36276 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 4482 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 5067 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 27 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 88 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 74961 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 29888 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 4161 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 4161 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 819 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 53 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 40 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 1160 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 0 | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 0 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 4063 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
