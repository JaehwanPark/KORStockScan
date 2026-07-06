# Cumulative Threshold Cycle Report - 2026-07-06

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-07-06`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 77 | 2182373 | 461 | -0.2422 | 0.4685 | 0.4967 |
| rolling_5d | 5 | 65553 | 69 | 0.3359 | 0.6232 | 0.3333 |
| rolling_10d | 10 | 167343 | 150 | 0.1847 | 0.56 | 0.38 |
| rolling_20d | 20 | 624297 | 176 | 0.0455 | 0.5227 | 0.4261 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 461 | -0.2422 | 0.4685 |
| cumulative | sim | 3915 | -1.2806 | 0.2404 |
| cumulative | combined | 4376 | -1.1713 | 0.2644 |
| rolling_5d | real | 69 | 0.3359 | 0.6232 |
| rolling_5d | sim | 58 | -1.8798 | 0.3103 |
| rolling_5d | combined | 127 | -0.676 | 0.4803 |
| rolling_10d | real | 150 | 0.1847 | 0.56 |
| rolling_10d | sim | 127 | -1.1288 | 0.4016 |
| rolling_10d | combined | 277 | -0.4175 | 0.4874 |
| rolling_20d | real | 176 | 0.0455 | 0.5227 |
| rolling_20d | sim | 1077 | -1.3621 | 0.2293 |
| rolling_20d | combined | 1253 | -1.1644 | 0.2706 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 461 | -0.2422 | -2.52 | 2.03 | 0.4685 | 0.4967 |
| cumulative | normal_only | 461 | -0.2422 | -2.52 | 2.03 | 0.4685 | 0.4967 |
| cumulative | initial_only | 402 | -0.2692 | -2.51 | 1.93 | 0.4577 | 0.5075 |
| cumulative | pyramid_activated | 27 | 0.3081 | -2.12 | 3.15 | 0.5926 | 0.4074 |
| cumulative | reversal_add_activated | 33 | -0.1442 | -4.57 | 2.55 | 0.5152 | 0.4242 |
| rolling_5d | all_completed_valid | 69 | 0.3359 | -3.32 | 2.98 | 0.6232 | 0.3333 |
| rolling_5d | normal_only | 69 | 0.3359 | -3.32 | 2.98 | 0.6232 | 0.3333 |
| rolling_5d | initial_only | 52 | 0.6229 | -1.17 | 2.98 | 0.6346 | 0.3077 |
| rolling_5d | pyramid_activated | 1 | -2.12 | -2.12 | -2.12 | 0 | 1 |
| rolling_5d | reversal_add_activated | 16 | -0.4431 | -4.65 | 2.55 | 0.625 | 0.375 |
| rolling_10d | all_completed_valid | 150 | 0.1847 | -4.29 | 2.57 | 0.56 | 0.38 |
| rolling_10d | normal_only | 150 | 0.1847 | -4.29 | 2.57 | 0.56 | 0.38 |
| rolling_10d | initial_only | 117 | 0.3015 | -3.32 | 2.59 | 0.5726 | 0.3675 |
| rolling_10d | pyramid_activated | 3 | 0.6767 | -2.87 | 7.02 | 0.3333 | 0.6667 |
| rolling_10d | reversal_add_activated | 31 | -0.0835 | -4.57 | 2.55 | 0.5484 | 0.3871 |
| rolling_20d | all_completed_valid | 176 | 0.0455 | -3.64 | 2.57 | 0.5227 | 0.4261 |
| rolling_20d | normal_only | 176 | 0.0455 | -3.64 | 2.57 | 0.5227 | 0.4261 |
| rolling_20d | initial_only | 141 | 0.1312 | -3.31 | 2.57 | 0.5319 | 0.4184 |
| rolling_20d | pyramid_activated | 4 | 0.215 | -2.87 | 7.02 | 0.25 | 0.75 |
| rolling_20d | reversal_add_activated | 32 | -0.1353 | -4.57 | 2.55 | 0.5312 | 0.4062 |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 293357 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 89 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 31545 | True | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 3360 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 177815 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 47514 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 22715 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 85 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 620 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 239979 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 102434 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 18938 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 18938 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 1223 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 187 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 106 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2712 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 461 | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 461 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 3054 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 1587 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 1477 | True | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 418 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 4155 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 476 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 505 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 11 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 59 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 12404 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 5529 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 297 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 297 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 104 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 25 | True | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 9 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 124 | True | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 69 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 69 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 3054 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 3716 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 3217 | True | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 1075 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 7350 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 1369 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 982 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 27 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 64 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 37804 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 15849 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 772 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 772 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 321 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 30 | True | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 27 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 690 | True | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 150 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 150 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 3054 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 58271 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 10717 | True | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 1996 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 48915 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 5336 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 6722 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 25 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 90 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 87064 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 35543 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 6247 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 6247 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 566 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 53 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 36 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 1379 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 176 | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 176 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 3054 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
