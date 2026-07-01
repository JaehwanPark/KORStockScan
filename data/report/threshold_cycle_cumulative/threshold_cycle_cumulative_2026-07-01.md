# Cumulative Threshold Cycle Report - 2026-07-01

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-07-01`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 72 | 2116820 | 386 | -0.3405 | 0.4456 | 0.5285 |
| rolling_5d | 5 | 101790 | 75 | 0.1059 | 0.5333 | 0.4267 |
| rolling_10d | 10 | 230368 | 90 | 0.009 | 0.5 | 0.4667 |
| rolling_20d | 20 | 911664 | 107 | -0.1551 | 0.4579 | 0.514 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 386 | -0.3405 | 0.4456 |
| cumulative | sim | 3857 | -1.2716 | 0.2393 |
| cumulative | combined | 4243 | -1.1869 | 0.2581 |
| rolling_5d | real | 75 | 0.1059 | 0.5333 |
| rolling_5d | sim | 69 | -0.4975 | 0.4783 |
| rolling_5d | combined | 144 | -0.1833 | 0.5069 |
| rolling_10d | real | 90 | 0.009 | 0.5 |
| rolling_10d | sim | 549 | -1.4298 | 0.2168 |
| rolling_10d | combined | 639 | -1.2272 | 0.2567 |
| rolling_20d | real | 107 | -0.1551 | 0.4579 |
| rolling_20d | sim | 1545 | -1.379 | 0.2026 |
| rolling_20d | combined | 1652 | -1.2997 | 0.2191 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 386 | -0.3405 | -2.51 | 1.85 | 0.4456 | 0.5285 |
| cumulative | normal_only | 386 | -0.3405 | -2.51 | 1.85 | 0.4456 | 0.5285 |
| cumulative | initial_only | 346 | -0.409 | -2.51 | 1.8 | 0.4335 | 0.5405 |
| cumulative | pyramid_activated | 26 | 0.4015 | -1.45 | 3.15 | 0.6154 | 0.3846 |
| cumulative | reversal_add_activated | 15 | 0.4433 | -4.29 | 6.26 | 0.4667 | 0.4667 |
| rolling_5d | all_completed_valid | 75 | 0.1059 | -4.52 | 2.57 | 0.5333 | 0.4267 |
| rolling_5d | normal_only | 75 | 0.1059 | -4.52 | 2.57 | 0.5333 | 0.4267 |
| rolling_5d | initial_only | 61 | 0.0326 | -4.52 | 2.53 | 0.541 | 0.4262 |
| rolling_5d | pyramid_activated | 2 | 2.075 | -2.87 | 7.02 | 0.5 | 0.5 |
| rolling_5d | reversal_add_activated | 13 | 0.6785 | -4.29 | 6.26 | 0.5385 | 0.3846 |
| rolling_10d | all_completed_valid | 90 | 0.009 | -4.48 | 2.57 | 0.5 | 0.4667 |
| rolling_10d | normal_only | 90 | 0.009 | -4.48 | 2.57 | 0.5 | 0.4667 |
| rolling_10d | initial_only | 75 | -0.0453 | -4.48 | 2.57 | 0.5067 | 0.4667 |
| rolling_10d | pyramid_activated | 2 | 2.075 | -2.87 | 7.02 | 0.5 | 0.5 |
| rolling_10d | reversal_add_activated | 14 | 0.5057 | -4.29 | 6.26 | 0.5 | 0.4286 |
| rolling_20d | all_completed_valid | 107 | -0.1551 | -4.24 | 2.57 | 0.4579 | 0.514 |
| rolling_20d | normal_only | 107 | -0.1551 | -4.24 | 2.57 | 0.4579 | 0.514 |
| rolling_20d | initial_only | 91 | -0.2158 | -3.75 | 2.53 | 0.4615 | 0.5165 |
| rolling_20d | pyramid_activated | 3 | 0.9933 | -2.87 | 7.02 | 0.3333 | 0.6667 |
| rolling_20d | reversal_add_activated | 14 | 0.5057 | -4.29 | 6.26 | 0.5 | 0.4286 |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 291770 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 89 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 30068 | True | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 2942 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 173660 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 47038 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 22210 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 81 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 561 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 227575 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 96905 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 18641 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 18641 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 1119 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 162 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 97 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2588 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 386 | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 386 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 7312 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 2129 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 1740 | True | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 657 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 3195 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 893 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 477 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 33 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 5 | False | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 25400 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 10320 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 475 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 475 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 217 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 5 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 18 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 566 | True | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 75 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 75 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 7312 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 5341 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 5044 | True | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 976 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 11278 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 2342 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 2538 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 33 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 26 | False | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 41684 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 16359 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 1841 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 1841 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 281 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 5 | False | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 20 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 856 | True | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 90 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 90 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 7312 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 106903 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 3 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 16044 | True | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 2147 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 69782 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 8836 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 10259 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 42 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 86 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 113794 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 49883 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 8706 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 8706 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 532 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 98 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 30 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 1939 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 107 | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 107 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 7312 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
