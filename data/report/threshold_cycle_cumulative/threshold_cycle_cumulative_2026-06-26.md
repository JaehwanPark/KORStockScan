# Cumulative Threshold Cycle Report - 2026-06-26

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-06-26`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 67 | 2015030 | 311 | -0.4481 | 0.4244 | 0.5531 |
| rolling_5d | 5 | 128578 | 15 | -0.4753 | 0.3333 | 0.6667 |
| rolling_10d | 10 | 456954 | 26 | -0.7573 | 0.3077 | 0.6923 |
| rolling_20d | 20 | 1387319 | 72 | -0.3561 | 0.4167 | 0.5833 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 311 | -0.4481 | 0.4244 |
| cumulative | sim | 3788 | -1.2857 | 0.235 |
| cumulative | combined | 4099 | -1.2222 | 0.2493 |
| rolling_5d | real | 15 | -0.4753 | 0.3333 |
| rolling_5d | sim | 480 | -1.5638 | 0.1792 |
| rolling_5d | combined | 495 | -1.5308 | 0.1838 |
| rolling_10d | real | 26 | -0.7573 | 0.3077 |
| rolling_10d | sim | 950 | -1.3933 | 0.2063 |
| rolling_10d | combined | 976 | -1.3764 | 0.209 |
| rolling_20d | real | 72 | -0.3561 | 0.4167 |
| rolling_20d | sim | 2900 | -1.3229 | 0.2259 |
| rolling_20d | combined | 2972 | -1.2995 | 0.2305 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 311 | -0.4481 | -2.37 | 1.58 | 0.4244 | 0.5531 |
| cumulative | normal_only | 311 | -0.4481 | -2.37 | 1.58 | 0.4244 | 0.5531 |
| cumulative | initial_only | 285 | -0.5035 | -2.39 | 1.58 | 0.4105 | 0.5649 |
| cumulative | pyramid_activated | 24 | 0.2621 | -1.42 | 1.59 | 0.625 | 0.375 |
| cumulative | reversal_add_activated | 2 | -1.085 | -1.74 | -0.43 | 0 | 1 |
| rolling_5d | all_completed_valid | 15 | -0.4753 | -2.77 | 2.75 | 0.3333 | 0.6667 |
| rolling_5d | normal_only | 15 | -0.4753 | -2.77 | 2.75 | 0.3333 | 0.6667 |
| rolling_5d | initial_only | 14 | -0.385 | -2.77 | 2.75 | 0.3571 | 0.6429 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 1 | -1.74 | -1.74 | -1.74 | 0 | 1 |
| rolling_10d | all_completed_valid | 26 | -0.7573 | -3.22 | 2.21 | 0.3077 | 0.6923 |
| rolling_10d | normal_only | 26 | -0.7573 | -3.22 | 2.21 | 0.3077 | 0.6923 |
| rolling_10d | initial_only | 24 | -0.6992 | -3.22 | 2.21 | 0.3333 | 0.6667 |
| rolling_10d | pyramid_activated | 1 | -1.17 | -1.17 | -1.17 | 0 | 1 |
| rolling_10d | reversal_add_activated | 1 | -1.74 | -1.74 | -1.74 | 0 | 1 |
| rolling_20d | all_completed_valid | 72 | -0.3561 | -2.55 | 2.75 | 0.4167 | 0.5833 |
| rolling_20d | normal_only | 72 | -0.3561 | -2.55 | 2.75 | 0.4167 | 0.5833 |
| rolling_20d | initial_only | 68 | -0.3465 | -2.67 | 2.75 | 0.4265 | 0.5735 |
| rolling_20d | pyramid_activated | 3 | -0.1133 | -2.39 | 3.22 | 0.3333 | 0.6667 |
| rolling_20d | reversal_add_activated | 1 | -1.74 | -1.74 | -1.74 | 0 | 1 |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 289641 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 89 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 28328 | True | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 2285 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 170465 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 46145 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 21733 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 69 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 556 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 202175 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 86585 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 18166 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 18166 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 902 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 157 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 79 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2022 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 311 | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 311 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 6798 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 3212 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 3304 | True | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 319 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 8083 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 1449 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 2061 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 2 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 21 | False | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 16284 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 6039 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 1366 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 1366 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 64 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 2 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 290 | True | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 15 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 15 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 6798 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 54555 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 7500 | True | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 921 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 41565 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 3967 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 5740 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 11 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 26 | False | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 49260 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 19694 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 5475 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 5475 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 245 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 23 | True | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 9 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 689 | True | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 26 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 26 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 6798 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 167899 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 3 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 22695 | True | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 2057 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 108969 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 18751 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 17461 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 45 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 177 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 153861 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 66740 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 11889 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 11889 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 669 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 118 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 50 | True | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 1886 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 72 | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 72 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 6798 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
