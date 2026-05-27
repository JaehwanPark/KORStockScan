# Cumulative Threshold Cycle Report - 2026-05-27

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-05-27`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 37 | 1144167 | 192 | -0.4572 | 0.4219 | 0.5625 |
| rolling_5d | 5 | 412999 | 12 | -0.4108 | 0.5 | 0.5 |
| rolling_10d | 10 | 1044391 | 15 | -0.0553 | 0.5333 | 0.4667 |
| rolling_20d | 20 | 1054131 | 19 | -0.2589 | 0.4737 | 0.5263 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 192 | -0.4572 | 0.4219 |
| cumulative | sim | 1012 | -0.5778 | 0.3498 |
| cumulative | combined | 1204 | -0.5586 | 0.3613 |
| rolling_5d | real | 12 | -0.4108 | 0.5 |
| rolling_5d | sim | 370 | -0.9686 | 0.3243 |
| rolling_5d | combined | 382 | -0.9511 | 0.3298 |
| rolling_10d | real | 15 | -0.0553 | 0.5333 |
| rolling_10d | sim | 999 | -0.6215 | 0.3463 |
| rolling_10d | combined | 1014 | -0.6131 | 0.3491 |
| rolling_20d | real | 19 | -0.2589 | 0.4737 |
| rolling_20d | sim | 1012 | -0.5778 | 0.3498 |
| rolling_20d | combined | 1031 | -0.5719 | 0.3521 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 192 | -0.4572 | -2.03 | 1.3 | 0.4219 | 0.5625 |
| cumulative | normal_only | 192 | -0.4572 | -2.03 | 1.3 | 0.4219 | 0.5625 |
| cumulative | initial_only | 171 | -0.5417 | -2.08 | 1.3 | 0.3977 | 0.5848 |
| cumulative | pyramid_activated | 20 | 0.2635 | -1.42 | 1.18 | 0.65 | 0.35 |
| cumulative | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |
| rolling_5d | all_completed_valid | 12 | -0.4108 | -2.71 | 2.21 | 0.5 | 0.5 |
| rolling_5d | normal_only | 12 | -0.4108 | -2.71 | 2.21 | 0.5 | 0.5 |
| rolling_5d | initial_only | 12 | -0.4108 | -2.71 | 2.21 | 0.5 | 0.5 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 15 | -0.0553 | -2.71 | 4.41 | 0.5333 | 0.4667 |
| rolling_10d | normal_only | 15 | -0.0553 | -2.71 | 4.41 | 0.5333 | 0.4667 |
| rolling_10d | initial_only | 15 | -0.0553 | -2.71 | 4.41 | 0.5333 | 0.4667 |
| rolling_10d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_10d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_20d | all_completed_valid | 19 | -0.2589 | -2.71 | 4.41 | 0.4737 | 0.5263 |
| rolling_20d | normal_only | 19 | -0.2589 | -2.71 | 4.41 | 0.4737 | 0.5263 |
| rolling_20d | initial_only | 19 | -0.2589 | -2.71 | 4.41 | 0.4737 | 0.5263 |
| rolling_20d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_20d | reversal_add_activated | 0 | - | - | - | - | - |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 106928 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 84 | True | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 250904 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 120863 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 7739 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 121 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 785 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 93593 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 40131 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 10936 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 10936 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 356 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 857 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 14 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 1126 | True | report_only_reference |
| cumulative | position_sizing_cap_release | position_sizing | 192 | False | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 192 | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 192 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 41172 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 39772 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 50877 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 29662 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 2645 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 2 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 33 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 37558 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 14453 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 3427 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 3427 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 111 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 25 | True | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 11 | True | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 226 | True | report_only_reference |
| rolling_5d | position_sizing_cap_release | position_sizing | 12 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 12 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 12 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 41172 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 41674 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 250904 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 120863 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 7739 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 14 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 210 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 84480 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 33590 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 9435 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 9435 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 295 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 39 | True | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 12 | True | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 810 | True | report_only_reference |
| rolling_10d | position_sizing_cap_release | position_sizing | 15 | False | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 15 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 15 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 41172 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 43829 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 0 | True | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 250904 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 120863 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 7739 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 15 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 210 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 86126 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 34417 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 9603 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 9603 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 302 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 66 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 12 | True | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 1090 | True | report_only_reference |
| rolling_20d | position_sizing_cap_release | position_sizing | 19 | False | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 19 | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 19 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 41172 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
