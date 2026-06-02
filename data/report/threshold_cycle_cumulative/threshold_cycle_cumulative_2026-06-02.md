# Cumulative Threshold Cycle Report - 2026-06-02

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-06-02`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 43 | 1803310 | 230 | -0.4345 | 0.4348 | 0.5348 |
| rolling_5d | 5 | 556293 | 32 | -0.3913 | 0.5625 | 0.4375 |
| rolling_10d | 10 | 1072064 | 50 | -0.3416 | 0.5 | 0.42 |
| rolling_20d | 20 | 1706260 | 53 | -0.2449 | 0.5094 | 0.4151 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 230 | -0.4345 | 0.4348 |
| cumulative | sim | 2074 | -0.7757 | 0.3375 |
| cumulative | combined | 2304 | -0.7416 | 0.3472 |
| rolling_5d | real | 32 | -0.3913 | 0.5625 |
| rolling_5d | sim | 898 | -0.9586 | 0.3207 |
| rolling_5d | combined | 930 | -0.9391 | 0.329 |
| rolling_10d | real | 50 | -0.3416 | 0.5 |
| rolling_10d | sim | 1432 | -0.9654 | 0.3254 |
| rolling_10d | combined | 1482 | -0.9443 | 0.3313 |
| rolling_20d | real | 53 | -0.2449 | 0.5094 |
| rolling_20d | sim | 2064 | -0.7986 | 0.3358 |
| rolling_20d | combined | 2117 | -0.7847 | 0.3401 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 230 | -0.4345 | -2.22 | 1.47 | 0.4348 | 0.5348 |
| cumulative | normal_only | 230 | -0.4345 | -2.22 | 1.47 | 0.4348 | 0.5348 |
| cumulative | initial_only | 208 | -0.5103 | -2.25 | 1.47 | 0.4135 | 0.5529 |
| cumulative | pyramid_activated | 21 | 0.3157 | -1.2 | 1.36 | 0.6667 | 0.3333 |
| cumulative | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |
| rolling_5d | all_completed_valid | 32 | -0.3913 | -2.7 | 1.52 | 0.5625 | 0.4375 |
| rolling_5d | normal_only | 32 | -0.3913 | -2.7 | 1.52 | 0.5625 | 0.4375 |
| rolling_5d | initial_only | 31 | -0.4477 | -2.7 | 1.52 | 0.5484 | 0.4516 |
| rolling_5d | pyramid_activated | 1 | 1.36 | 1.36 | 1.36 | 1 | 0 |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 50 | -0.3416 | -2.71 | 1.58 | 0.5 | 0.42 |
| rolling_10d | normal_only | 50 | -0.3416 | -2.71 | 1.58 | 0.5 | 0.42 |
| rolling_10d | initial_only | 49 | -0.3763 | -2.71 | 1.85 | 0.4898 | 0.4286 |
| rolling_10d | pyramid_activated | 1 | 1.36 | 1.36 | 1.36 | 1 | 0 |
| rolling_10d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_20d | all_completed_valid | 53 | -0.2449 | -2.7 | 1.85 | 0.5094 | 0.4151 |
| rolling_20d | normal_only | 53 | -0.2449 | -2.7 | 1.85 | 0.5094 | 0.4151 |
| rolling_20d | initial_only | 52 | -0.2758 | -2.7 | 1.85 | 0.5 | 0.4231 |
| rolling_20d | pyramid_activated | 1 | 1.36 | 1.36 | 1.36 | 1 | 0 |
| rolling_20d | reversal_add_activated | 0 | - | - | - | - | - |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 191657 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 86 | True | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 327384 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 157527 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 12348 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 53 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 833 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 149097 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 60037 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 16625 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 16625 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 693 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 908 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 44 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 1360 | True | report_only_reference |
| cumulative | position_sizing_cap_release | position_sizing | 230 | False | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 230 | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 230 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 22915 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 69221 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 2 | True | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 70235 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 35243 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 3563 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 13 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 42 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 45874 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 16024 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 4817 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 4817 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 279 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 51 | True | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 30 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 198 | True | report_only_reference |
| rolling_5d | position_sizing_cap_release | position_sizing | 32 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 32 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 32 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 22915 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 124499 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 2 | True | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 127357 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 66326 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 7254 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 13 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 81 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 93054 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 34359 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 9116 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 9116 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 448 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 74 | True | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 41 | True | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 452 | True | report_only_reference |
| rolling_10d | position_sizing_cap_release | position_sizing | 50 | False | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 50 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 50 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 22915 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 126485 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 2 | True | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 327384 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 157527 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 12348 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 23 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 258 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 140730 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 53922 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 15219 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 15219 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 633 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 91 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 42 | True | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 1106 | True | report_only_reference |
| rolling_20d | position_sizing_cap_release | position_sizing | 53 | False | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 53 | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 53 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 22915 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
