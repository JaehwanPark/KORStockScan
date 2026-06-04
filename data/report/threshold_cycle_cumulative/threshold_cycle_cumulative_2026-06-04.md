# Cumulative Threshold Cycle Report - 2026-06-04

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-06-04`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 45 | 482044 | 238 | -0.4673 | 0.4286 | 0.542 |
| rolling_5d | 5 | 439815 | 37 | -0.5478 | 0.5135 | 0.4865 |
| rolling_10d | 10 | 439815 | 58 | -0.4888 | 0.4655 | 0.4655 |
| rolling_20d | 20 | 439815 | 61 | -0.3975 | 0.4754 | 0.459 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 238 | -0.4673 | 0.4286 |
| cumulative | sim | 737 | -1.1485 | 0.2741 |
| cumulative | combined | 975 | -0.9822 | 0.3118 |
| rolling_5d | real | 37 | -0.5478 | 0.5135 |
| rolling_5d | sim | 737 | -1.1485 | 0.2741 |
| rolling_5d | combined | 774 | -1.1198 | 0.2855 |
| rolling_10d | real | 58 | -0.4888 | 0.4655 |
| rolling_10d | sim | 737 | -1.1485 | 0.2741 |
| rolling_10d | combined | 795 | -1.1004 | 0.2881 |
| rolling_20d | real | 61 | -0.3975 | 0.4754 |
| rolling_20d | sim | 737 | -1.1485 | 0.2741 |
| rolling_20d | combined | 798 | -1.0911 | 0.2895 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 238 | -0.4673 | -2.27 | 1.47 | 0.4286 | 0.542 |
| cumulative | normal_only | 238 | -0.4673 | -2.27 | 1.47 | 0.4286 | 0.542 |
| cumulative | initial_only | 216 | -0.5436 | -2.32 | 1.47 | 0.4074 | 0.5602 |
| cumulative | pyramid_activated | 21 | 0.3157 | -1.2 | 1.36 | 0.6667 | 0.3333 |
| cumulative | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |
| rolling_5d | all_completed_valid | 37 | -0.5478 | -2.7 | 1.52 | 0.5135 | 0.4865 |
| rolling_5d | normal_only | 37 | -0.5478 | -2.7 | 1.52 | 0.5135 | 0.4865 |
| rolling_5d | initial_only | 36 | -0.6008 | -2.7 | 1.52 | 0.5 | 0.5 |
| rolling_5d | pyramid_activated | 1 | 1.36 | 1.36 | 1.36 | 1 | 0 |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 58 | -0.4888 | -2.71 | 1.7 | 0.4655 | 0.4655 |
| rolling_10d | normal_only | 58 | -0.4888 | -2.71 | 1.7 | 0.4655 | 0.4655 |
| rolling_10d | initial_only | 57 | -0.5212 | -2.71 | 1.7 | 0.4561 | 0.4737 |
| rolling_10d | pyramid_activated | 1 | 1.36 | 1.36 | 1.36 | 1 | 0 |
| rolling_10d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_20d | all_completed_valid | 61 | -0.3975 | -2.7 | 1.7 | 0.4754 | 0.459 |
| rolling_20d | normal_only | 61 | -0.3975 | -2.7 | 1.7 | 0.4754 | 0.459 |
| rolling_20d | initial_only | 60 | -0.4268 | -2.71 | 1.7 | 0.4667 | 0.4667 |
| rolling_20d | pyramid_activated | 1 | 1.36 | 1.36 | 1.36 | 1 | 0 |
| rolling_20d | reversal_add_activated | 0 | - | - | - | - | - |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 96616 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 86 | True | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 46370 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 24200 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 2766 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 13 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 379 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 38177 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 15770 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 4857 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 4857 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 200 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 39 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 28 | False | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 108 | True | report_only_reference |
| cumulative | position_sizing_cap_release | position_sizing | 238 | False | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 238 | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 238 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 2558 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 57588 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 2 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 46370 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 24200 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 2766 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 13 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 40 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 38177 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 13799 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 4474 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 4474 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 200 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 39 | True | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 28 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 108 | True | report_only_reference |
| rolling_5d | position_sizing_cap_release | position_sizing | 37 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 37 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 37 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 2558 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 57588 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 2 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 46370 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 24200 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 2766 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 13 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 40 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 38177 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 13799 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 4474 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 4474 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 200 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 39 | True | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 28 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 108 | True | report_only_reference |
| rolling_10d | position_sizing_cap_release | position_sizing | 58 | False | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 58 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 58 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 2558 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 57588 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 2 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 46370 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 24200 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 2766 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 13 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 40 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 38177 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 13799 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 4474 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 4474 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 200 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 39 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 28 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 108 | True | report_only_reference |
| rolling_20d | position_sizing_cap_release | position_sizing | 61 | False | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 61 | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 61 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 2558 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
