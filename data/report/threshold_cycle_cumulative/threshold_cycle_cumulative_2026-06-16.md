# Cumulative Threshold Cycle Report - 2026-06-16

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-06-16`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 57 | 1558076 | 285 | -0.4199 | 0.4351 | 0.5404 |
| rolling_5d | 5 | 352920 | 6 | -0.8083 | 0.1667 | 0.8333 |
| rolling_10d | 10 | 930365 | 46 | -0.1293 | 0.4783 | 0.5217 |
| rolling_20d | 20 | 1515847 | 92 | -0.3466 | 0.4674 | 0.5 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 285 | -0.4199 | 0.4351 |
| cumulative | sim | 2838 | -1.2497 | 0.2445 |
| cumulative | combined | 3123 | -1.174 | 0.2619 |
| rolling_5d | real | 6 | -0.8083 | 0.1667 |
| rolling_5d | sim | 526 | -1.4688 | 0.1597 |
| rolling_5d | combined | 532 | -1.4614 | 0.1598 |
| rolling_10d | real | 46 | -0.1293 | 0.4783 |
| rolling_10d | sim | 1950 | -1.2886 | 0.2354 |
| rolling_10d | combined | 1996 | -1.2619 | 0.241 |
| rolling_20d | real | 92 | -0.3466 | 0.4674 |
| rolling_20d | sim | 2838 | -1.2497 | 0.2445 |
| rolling_20d | combined | 2930 | -1.2214 | 0.2515 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 285 | -0.4199 | -2.32 | 1.58 | 0.4351 | 0.5404 |
| cumulative | normal_only | 285 | -0.4199 | -2.32 | 1.58 | 0.4351 | 0.5404 |
| cumulative | initial_only | 261 | -0.4855 | -2.33 | 1.52 | 0.4176 | 0.5556 |
| cumulative | pyramid_activated | 23 | 0.3243 | -1.42 | 1.59 | 0.6522 | 0.3478 |
| cumulative | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |
| rolling_5d | all_completed_valid | 6 | -0.8083 | -3.31 | 3.3 | 0.1667 | 0.8333 |
| rolling_5d | normal_only | 6 | -0.8083 | -3.31 | 3.3 | 0.1667 | 0.8333 |
| rolling_5d | initial_only | 6 | -0.8083 | -3.31 | 3.3 | 0.1667 | 0.8333 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 46 | -0.1293 | -2.51 | 3.22 | 0.4783 | 0.5217 |
| rolling_10d | normal_only | 46 | -0.1293 | -2.51 | 3.22 | 0.4783 | 0.5217 |
| rolling_10d | initial_only | 44 | -0.1541 | -2.51 | 2.8 | 0.4773 | 0.5227 |
| rolling_10d | pyramid_activated | 2 | 0.415 | -2.39 | 3.22 | 0.5 | 0.5 |
| rolling_10d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_20d | all_completed_valid | 92 | -0.3466 | -2.62 | 2.03 | 0.4674 | 0.5 |
| rolling_20d | normal_only | 92 | -0.3466 | -2.62 | 2.03 | 0.4674 | 0.5 |
| rolling_20d | initial_only | 89 | -0.3829 | -2.67 | 2.03 | 0.4607 | 0.5056 |
| rolling_20d | pyramid_activated | 3 | 0.73 | -2.39 | 3.22 | 0.6667 | 0.3333 |
| rolling_20d | reversal_add_activated | 0 | - | - | - | - | - |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 235086 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 89 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 20828 | True | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 1364 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 128900 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 42178 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 15993 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 60 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 530 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 152915 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 66891 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 12691 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 12691 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 657 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 134 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 70 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 1333 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 285 | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 285 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 22185 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 50219 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 3 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 6804 | True | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 569 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 25022 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 3976 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 4042 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 21 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 55 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 39134 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 19869 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 2756 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 2756 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 70 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 70 | True | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 3 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 684 | True | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 6 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 6 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 22185 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 113344 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 3 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 15195 | True | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 1136 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 67404 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 14784 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 11721 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 36 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 151 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 104601 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 47046 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 6414 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 6414 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 424 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 95 | True | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 41 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 1197 | True | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 46 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 46 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 22185 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 196058 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 5 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 20448 | True | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 1216 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 128900 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 42178 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 15993 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 60 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 191 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 152915 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 64920 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 12308 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 12308 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 657 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 134 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 70 | True | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 1333 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 92 | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 92 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 22185 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
