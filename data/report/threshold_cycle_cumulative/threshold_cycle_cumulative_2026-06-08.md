# Cumulative Threshold Cycle Report - 2026-06-08

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-06-08`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 49 | 794457 | 264 | -0.4709 | 0.4318 | 0.5417 |
| rolling_5d | 5 | 335962 | 34 | -0.7171 | 0.4118 | 0.5882 |
| rolling_10d | 10 | 752228 | 63 | -0.5298 | 0.4921 | 0.5079 |
| rolling_20d | 20 | 752228 | 87 | -0.4294 | 0.4713 | 0.4828 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 264 | -0.4709 | 0.4318 |
| cumulative | sim | 1264 | -1.2371 | 0.2619 |
| cumulative | combined | 1528 | -1.1048 | 0.2912 |
| rolling_5d | real | 34 | -0.7171 | 0.4118 |
| rolling_5d | sim | 558 | -1.3403 | 0.2401 |
| rolling_5d | combined | 592 | -1.3045 | 0.25 |
| rolling_10d | real | 63 | -0.5298 | 0.4921 |
| rolling_10d | sim | 1264 | -1.2371 | 0.2619 |
| rolling_10d | combined | 1327 | -1.2036 | 0.2728 |
| rolling_20d | real | 87 | -0.4294 | 0.4713 |
| rolling_20d | sim | 1264 | -1.2371 | 0.2619 |
| rolling_20d | combined | 1351 | -1.1851 | 0.2754 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 264 | -0.4709 | -2.32 | 1.47 | 0.4318 | 0.5417 |
| cumulative | normal_only | 264 | -0.4709 | -2.32 | 1.47 | 0.4318 | 0.5417 |
| cumulative | initial_only | 242 | -0.5393 | -2.36 | 1.47 | 0.4132 | 0.5579 |
| cumulative | pyramid_activated | 21 | 0.3157 | -1.2 | 1.36 | 0.6667 | 0.3333 |
| cumulative | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |
| rolling_5d | all_completed_valid | 34 | -0.7171 | -2.55 | 1.39 | 0.4118 | 0.5882 |
| rolling_5d | normal_only | 34 | -0.7171 | -2.55 | 1.39 | 0.4118 | 0.5882 |
| rolling_5d | initial_only | 34 | -0.7171 | -2.55 | 1.39 | 0.4118 | 0.5882 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 63 | -0.5298 | -2.62 | 1.47 | 0.4921 | 0.5079 |
| rolling_10d | normal_only | 63 | -0.5298 | -2.62 | 1.47 | 0.4921 | 0.5079 |
| rolling_10d | initial_only | 62 | -0.5603 | -2.62 | 1.47 | 0.4839 | 0.5161 |
| rolling_10d | pyramid_activated | 1 | 1.36 | 1.36 | 1.36 | 1 | 0 |
| rolling_10d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_20d | all_completed_valid | 87 | -0.4294 | -2.7 | 1.7 | 0.4713 | 0.4828 |
| rolling_20d | normal_only | 87 | -0.4294 | -2.7 | 1.7 | 0.4713 | 0.4828 |
| rolling_20d | initial_only | 86 | -0.4502 | -2.7 | 1.7 | 0.4651 | 0.4884 |
| rolling_20d | pyramid_activated | 1 | 1.36 | 1.36 | 1.36 | 1 | 0 |
| rolling_20d | reversal_add_activated | 0 | - | - | - | - | - |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 138497 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 86 | True | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 77549 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 31797 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 6186 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 26 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 390 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 68648 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 28399 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 6985 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 6985 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 335 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 39 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 54 | False | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 344 | True | report_only_reference |
| cumulative | position_sizing_cap_release | position_sizing | 264 | False | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 264 | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 264 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 25034 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 46408 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 32848 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 8421 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 3513 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 14 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 11 | False | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 32584 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 13323 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 2362 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 2362 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 137 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 27 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 248 | True | report_only_reference |
| rolling_5d | position_sizing_cap_release | position_sizing | 34 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 34 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 34 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 25034 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 99469 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 2 | True | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 77549 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 31797 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 6186 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 26 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 51 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 68648 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 26428 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 6602 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 6602 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 335 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 39 | True | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 54 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 344 | True | report_only_reference |
| rolling_10d | position_sizing_cap_release | position_sizing | 63 | False | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 63 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 63 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 25034 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 99469 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 2 | True | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 77549 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 31797 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 6186 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 26 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 51 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 68648 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 26428 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 6602 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 6602 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 335 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 39 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 54 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 344 | True | report_only_reference |
| rolling_20d | position_sizing_cap_release | position_sizing | 87 | False | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 87 | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 87 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 25034 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
