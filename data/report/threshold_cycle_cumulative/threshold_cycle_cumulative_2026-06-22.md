# Cumulative Threshold Cycle Report - 2026-06-22

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-06-22`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 63 | 1905155 | 296 | -0.4468 | 0.4291 | 0.5473 |
| rolling_5d | 5 | 156409 | 11 | -1.1418 | 0.2727 | 0.7273 |
| rolling_10d | 10 | 605230 | 13 | -1.0554 | 0.2308 | 0.7692 |
| rolling_20d | 20 | 1446660 | 66 | -0.4894 | 0.4091 | 0.5909 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 296 | -0.4468 | 0.4291 |
| cumulative | sim | 3422 | -1.2564 | 0.2414 |
| cumulative | combined | 3718 | -1.1919 | 0.2563 |
| rolling_5d | real | 11 | -1.1418 | 0.2727 |
| rolling_5d | sim | 401 | -1.3648 | 0.2219 |
| rolling_5d | combined | 412 | -1.3589 | 0.2233 |
| rolling_10d | real | 13 | -1.0554 | 0.2308 |
| rolling_10d | sim | 885 | -1.2806 | 0.2158 |
| rolling_10d | combined | 898 | -1.2773 | 0.216 |
| rolling_20d | real | 66 | -0.4894 | 0.4091 |
| rolling_20d | sim | 2716 | -1.2826 | 0.2316 |
| rolling_20d | combined | 2782 | -1.2638 | 0.2358 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 296 | -0.4468 | -2.36 | 1.52 | 0.4291 | 0.5473 |
| cumulative | normal_only | 296 | -0.4468 | -2.36 | 1.52 | 0.4291 | 0.5473 |
| cumulative | initial_only | 271 | -0.5096 | -2.37 | 1.52 | 0.4133 | 0.5609 |
| cumulative | pyramid_activated | 24 | 0.2621 | -1.42 | 1.59 | 0.625 | 0.375 |
| cumulative | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |
| rolling_5d | all_completed_valid | 11 | -1.1418 | -3.44 | 1.34 | 0.2727 | 0.7273 |
| rolling_5d | normal_only | 11 | -1.1418 | -3.44 | 1.34 | 0.2727 | 0.7273 |
| rolling_5d | initial_only | 10 | -1.139 | -4.24 | 1.34 | 0.3 | 0.7 |
| rolling_5d | pyramid_activated | 1 | -1.17 | -1.17 | -1.17 | 0 | 1 |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 13 | -1.0554 | -3.44 | 1.34 | 0.2308 | 0.7692 |
| rolling_10d | normal_only | 13 | -1.0554 | -3.44 | 1.34 | 0.2308 | 0.7692 |
| rolling_10d | initial_only | 12 | -1.0458 | -3.44 | 1.34 | 0.25 | 0.75 |
| rolling_10d | pyramid_activated | 1 | -1.17 | -1.17 | -1.17 | 0 | 1 |
| rolling_10d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_20d | all_completed_valid | 66 | -0.4894 | -2.55 | 2.2 | 0.4091 | 0.5909 |
| rolling_20d | normal_only | 66 | -0.4894 | -2.55 | 2.2 | 0.4091 | 0.5909 |
| rolling_20d | initial_only | 63 | -0.5073 | -2.55 | 2.03 | 0.4127 | 0.5873 |
| rolling_20d | pyramid_activated | 3 | -0.1133 | -2.39 | 3.22 | 0.3333 | 0.6667 |
| rolling_20d | reversal_add_activated | 0 | - | - | - | - | - |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 287280 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 89 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 25997 | True | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 2036 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 163024 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 44759 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 19901 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 69 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 536 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 187928 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 81585 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 16910 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 16910 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 850 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 157 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 77 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 1816 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 296 | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 296 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 4940 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 6769 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 4180 | True | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 615 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 20660 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 1619 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 2113 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 9 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 4 | False | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 18998 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 8122 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 2025 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 2025 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 154 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 23 | True | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 7 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 257 | True | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 11 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 11 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 4940 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 90018 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 3 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 8331 | True | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 960 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 50866 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 4535 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 6417 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 25 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 54 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 64041 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 28353 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 6487 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 6487 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 242 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 66 | True | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 7 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 930 | True | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 13 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 13 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 4940 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 195191 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 3 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 21713 | True | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 1812 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 118323 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 21383 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 17228 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 57 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 157 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 151864 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 66509 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 12287 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 12287 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 652 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 118 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 50 | True | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 1720 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 66 | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 66 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 4940 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
