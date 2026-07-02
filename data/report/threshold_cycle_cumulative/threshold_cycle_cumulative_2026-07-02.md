# Cumulative Threshold Cycle Report - 2026-07-02

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-07-02`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 73 | 2143591 | 416 | -0.301 | 0.4471 | 0.5168 |
| rolling_5d | 5 | 128561 | 105 | 0.1348 | 0.5143 | 0.4095 |
| rolling_10d | 10 | 238436 | 120 | 0.0585 | 0.4917 | 0.4417 |
| rolling_20d | 20 | 843666 | 133 | -0.0504 | 0.4662 | 0.4737 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 416 | -0.301 | 0.4471 |
| cumulative | sim | 3878 | -1.2787 | 0.2393 |
| cumulative | combined | 4294 | -1.184 | 0.2594 |
| rolling_5d | real | 105 | 0.1348 | 0.5143 |
| rolling_5d | sim | 90 | -0.9833 | 0.4222 |
| rolling_5d | combined | 195 | -0.3813 | 0.4718 |
| rolling_10d | real | 120 | 0.0585 | 0.4917 |
| rolling_10d | sim | 456 | -1.4463 | 0.2237 |
| rolling_10d | combined | 576 | -1.1328 | 0.2795 |
| rolling_20d | real | 133 | -0.0504 | 0.4662 |
| rolling_20d | sim | 1341 | -1.3369 | 0.2185 |
| rolling_20d | combined | 1474 | -1.2208 | 0.2408 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 416 | -0.301 | -2.51 | 1.93 | 0.4471 | 0.5168 |
| cumulative | normal_only | 416 | -0.301 | -2.51 | 1.93 | 0.4471 | 0.5168 |
| cumulative | initial_only | 371 | -0.349 | -2.51 | 1.9 | 0.4367 | 0.5283 |
| cumulative | pyramid_activated | 26 | 0.4015 | -1.45 | 3.15 | 0.6154 | 0.3846 |
| cumulative | reversal_add_activated | 20 | 0.0425 | -4.57 | 2.18 | 0.45 | 0.45 |
| rolling_5d | all_completed_valid | 105 | 0.1348 | -4.32 | 2.57 | 0.5143 | 0.4095 |
| rolling_5d | normal_only | 105 | 0.1348 | -4.32 | 2.57 | 0.5143 | 0.4095 |
| rolling_5d | initial_only | 86 | 0.1628 | -3.75 | 2.57 | 0.5233 | 0.407 |
| rolling_5d | pyramid_activated | 2 | 2.075 | -2.87 | 7.02 | 0.5 | 0.5 |
| rolling_5d | reversal_add_activated | 18 | 0.1678 | -4.57 | 6.26 | 0.5 | 0.3889 |
| rolling_10d | all_completed_valid | 120 | 0.0585 | -4.29 | 2.57 | 0.4917 | 0.4417 |
| rolling_10d | normal_only | 120 | 0.0585 | -4.29 | 2.57 | 0.4917 | 0.4417 |
| rolling_10d | initial_only | 100 | 0.0861 | -3.32 | 2.57 | 0.5 | 0.44 |
| rolling_10d | pyramid_activated | 2 | 2.075 | -2.87 | 7.02 | 0.5 | 0.5 |
| rolling_10d | reversal_add_activated | 19 | 0.0674 | -4.57 | 6.26 | 0.4737 | 0.4211 |
| rolling_20d | all_completed_valid | 133 | -0.0504 | -3.75 | 2.53 | 0.4662 | 0.4737 |
| rolling_20d | normal_only | 133 | -0.0504 | -3.75 | 2.53 | 0.4662 | 0.4737 |
| rolling_20d | initial_only | 112 | -0.0352 | -3.32 | 2.53 | 0.4732 | 0.4732 |
| rolling_20d | pyramid_activated | 3 | 0.9933 | -2.87 | 7.02 | 0.3333 | 0.6667 |
| rolling_20d | reversal_add_activated | 19 | 0.0674 | -4.57 | 6.26 | 0.4737 | 0.4211 |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 292203 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 89 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 30682 | True | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 3096 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 175149 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 47277 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 22423 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 81 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 574 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 232426 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 99070 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 18739 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 18739 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 1136 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 162 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 100 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2658 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 416 | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 416 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 6662 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 2562 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 2354 | True | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 811 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 4684 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 1132 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 690 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 33 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 18 | False | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 30251 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 12485 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 573 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 573 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 234 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 5 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 21 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 636 | True | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 105 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 105 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 6662 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 4923 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 4685 | True | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 1060 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 12125 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 2518 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 2522 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 33 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 38 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 44498 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 17485 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 1829 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 1829 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 286 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 5 | False | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 23 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 842 | True | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 120 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 120 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 6662 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 94941 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 3 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 13016 | True | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 2020 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 62991 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 7053 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 8939 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 37 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 92 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 108539 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 45838 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 8316 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 8316 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 528 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 71 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 30 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 1772 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 133 | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 133 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 6662 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
