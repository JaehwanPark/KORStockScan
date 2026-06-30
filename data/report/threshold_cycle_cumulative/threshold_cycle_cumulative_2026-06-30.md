# Cumulative Threshold Cycle Report - 2026-06-30

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-06-30`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 71 | 2079038 | 350 | -0.4225 | 0.4343 | 0.54 |
| rolling_5d | 5 | 88865 | 46 | -0.197 | 0.4783 | 0.4783 |
| rolling_10d | 10 | 192586 | 54 | -0.2894 | 0.463 | 0.5 |
| rolling_20d | 20 | 971098 | 73 | -0.5122 | 0.3973 | 0.5753 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 350 | -0.4225 | 0.4343 |
| cumulative | sim | 3840 | -1.2786 | 0.2375 |
| cumulative | combined | 4190 | -1.2071 | 0.2539 |
| rolling_5d | real | 46 | -0.197 | 0.4783 |
| rolling_5d | sim | 121 | -1.0712 | 0.2893 |
| rolling_5d | combined | 167 | -0.8304 | 0.3413 |
| rolling_10d | real | 54 | -0.2894 | 0.463 |
| rolling_10d | sim | 532 | -1.4853 | 0.203 |
| rolling_10d | combined | 586 | -1.3751 | 0.227 |
| rolling_20d | real | 73 | -0.5122 | 0.3973 |
| rolling_20d | sim | 1864 | -1.2768 | 0.2291 |
| rolling_20d | combined | 1937 | -1.248 | 0.2354 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 350 | -0.4225 | -2.51 | 1.69 | 0.4343 | 0.54 |
| cumulative | normal_only | 350 | -0.4225 | -2.51 | 1.69 | 0.4343 | 0.54 |
| cumulative | initial_only | 323 | -0.4617 | -2.51 | 1.7 | 0.4241 | 0.548 |
| cumulative | pyramid_activated | 25 | 0.1368 | -1.45 | 1.59 | 0.6 | 0.4 |
| cumulative | reversal_add_activated | 2 | -1.085 | -1.74 | -0.43 | 0 | 1 |
| rolling_5d | all_completed_valid | 46 | -0.197 | -4.52 | 2.57 | 0.4783 | 0.4783 |
| rolling_5d | normal_only | 46 | -0.197 | -4.52 | 2.57 | 0.4783 | 0.4783 |
| rolling_5d | initial_only | 44 | -0.1011 | -4.52 | 2.57 | 0.5 | 0.4545 |
| rolling_5d | pyramid_activated | 1 | -2.87 | -2.87 | -2.87 | 0 | 1 |
| rolling_5d | reversal_add_activated | 1 | -1.74 | -1.74 | -1.74 | 0 | 1 |
| rolling_10d | all_completed_valid | 54 | -0.2894 | -4.48 | 2.57 | 0.463 | 0.5 |
| rolling_10d | normal_only | 54 | -0.2894 | -4.48 | 2.57 | 0.463 | 0.5 |
| rolling_10d | initial_only | 52 | -0.2119 | -4.48 | 2.57 | 0.4808 | 0.4808 |
| rolling_10d | pyramid_activated | 1 | -2.87 | -2.87 | -2.87 | 0 | 1 |
| rolling_10d | reversal_add_activated | 1 | -1.74 | -1.74 | -1.74 | 0 | 1 |
| rolling_20d | all_completed_valid | 73 | -0.5122 | -3.75 | 2.53 | 0.3973 | 0.5753 |
| rolling_20d | normal_only | 73 | -0.5122 | -3.75 | 2.53 | 0.3973 | 0.5753 |
| rolling_20d | initial_only | 69 | -0.4235 | -4.24 | 2.57 | 0.4203 | 0.5507 |
| rolling_20d | pyramid_activated | 3 | -2.1433 | -2.87 | -1.17 | 0 | 1 |
| rolling_20d | reversal_add_activated | 1 | -1.74 | -1.74 | -1.74 | 0 | 1 |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 290748 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 89 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 29355 | True | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 2657 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 172665 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 46796 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 22150 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 75 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 558 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 218124 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 93640 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 18486 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 18486 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 1052 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 162 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 91 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2320 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 350 | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 350 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 5831 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 1160 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 1417 | True | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 403 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 3427 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 920 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 928 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 9 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 13 | False | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 19758 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 8131 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 530 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 530 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 159 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 5 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 13 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 381 | True | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 46 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 46 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 5831 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 4319 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 4331 | True | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 691 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 10283 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 2100 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 2478 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 9 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 23 | False | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 32233 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 13094 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 1686 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 1686 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 214 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 5 | False | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 14 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 588 | True | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 54 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 54 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 5831 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 116051 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 3 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 17604 | True | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 2077 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 73918 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 10121 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 11783 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 36 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 83 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 114171 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 51064 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 8921 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 8921 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 578 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 123 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 26 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 1718 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 73 | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 73 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 5831 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
