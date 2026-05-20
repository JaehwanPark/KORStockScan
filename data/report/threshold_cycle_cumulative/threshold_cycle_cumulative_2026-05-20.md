# Cumulative Threshold Cycle Report - 2026-05-20

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-05-20`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 30 | 370898 | 179 | -0.4888 | 0.4134 | 0.5698 |
| rolling_5d | 5 | 271122 | 2 | -0.265 | 0.5 | 0.5 |
| rolling_10d | 10 | 279409 | 3 | -0.6933 | 0.3333 | 0.6667 |
| rolling_20d | 20 | 314222 | 53 | -0.55 | 0.3774 | 0.6226 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 179 | -0.4888 | 0.4134 |
| cumulative | sim | 353 | -0.3192 | 0.3428 |
| cumulative | combined | 532 | -0.3762 | 0.3665 |
| rolling_5d | real | 2 | -0.265 | 0.5 |
| rolling_5d | sim | 340 | -0.4377 | 0.3324 |
| rolling_5d | combined | 342 | -0.4367 | 0.3333 |
| rolling_10d | real | 3 | -0.6933 | 0.3333 |
| rolling_10d | sim | 353 | -0.3192 | 0.3428 |
| rolling_10d | combined | 356 | -0.3223 | 0.3427 |
| rolling_20d | real | 53 | -0.55 | 0.3774 |
| rolling_20d | sim | 353 | -0.3192 | 0.3428 |
| rolling_20d | combined | 406 | -0.3493 | 0.3473 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 179 | -0.4888 | -2.02 | 1.29 | 0.4134 | 0.5698 |
| cumulative | normal_only | 179 | -0.4888 | -2.02 | 1.29 | 0.4134 | 0.5698 |
| cumulative | initial_only | 158 | -0.5844 | -2.03 | 1.29 | 0.3861 | 0.5949 |
| cumulative | pyramid_activated | 20 | 0.2635 | -1.42 | 1.18 | 0.65 | 0.35 |
| cumulative | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |
| rolling_5d | all_completed_valid | 2 | -0.265 | -0.76 | 0.23 | 0.5 | 0.5 |
| rolling_5d | normal_only | 2 | -0.265 | -0.76 | 0.23 | 0.5 | 0.5 |
| rolling_5d | initial_only | 2 | -0.265 | -0.76 | 0.23 | 0.5 | 0.5 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 3 | -0.6933 | -1.55 | 0.23 | 0.3333 | 0.6667 |
| rolling_10d | normal_only | 3 | -0.6933 | -1.55 | 0.23 | 0.3333 | 0.6667 |
| rolling_10d | initial_only | 3 | -0.6933 | -1.55 | 0.23 | 0.3333 | 0.6667 |
| rolling_10d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_10d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_20d | all_completed_valid | 53 | -0.55 | -2.16 | 1.3 | 0.3774 | 0.6226 |
| rolling_20d | normal_only | 53 | -0.55 | -2.16 | 1.3 | 0.3774 | 0.6226 |
| rolling_20d | initial_only | 46 | -0.5428 | -2.19 | 1.69 | 0.3913 | 0.6087 |
| rolling_20d | pyramid_activated | 6 | -0.625 | -1.2 | 0.6 | 0.3333 | 0.6667 |
| rolling_20d | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 66721 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 84 | True | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 91122 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 36510 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 2762 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 121 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 575 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 25575 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 13249 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 4437 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 4437 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 159 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 821 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 2 | False | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 794 | True | report_only_reference |
| cumulative | position_sizing_cap_release | position_sizing | 179 | False | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 179 | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 179 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 7155 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 1467 | False | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 91122 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 36510 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 2762 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 10 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 0 | False | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 16462 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 6708 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 2936 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 2936 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 98 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 3 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 478 | True | report_only_reference |
| rolling_5d | position_sizing_cap_release | position_sizing | 2 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 2 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 2 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 7155 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 2903 | False | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 91122 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 36510 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 2762 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 10 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 0 | False | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 18005 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 7520 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 3076 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 3076 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 104 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 11 | False | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 679 | True | report_only_reference |
| rolling_10d | position_sizing_cap_release | position_sizing | 3 | False | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 3 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 3 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 7155 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 13357 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 0 | True | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 91122 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 36510 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 2762 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 121 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 236 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 25575 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 11278 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 4054 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 4054 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 144 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 821 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 2 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 794 | True | report_only_reference |
| rolling_20d | position_sizing_cap_release | position_sizing | 53 | False | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 53 | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 53 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 7155 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
