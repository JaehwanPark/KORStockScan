# Cumulative Threshold Cycle Report - 2026-06-12

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-06-12`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 53 | 1299925 | 283 | -0.4188 | 0.4382 | 0.5371 |
| rolling_5d | 5 | 672214 | 44 | -0.1089 | 0.5 | 0.5 |
| rolling_10d | 10 | 841430 | 53 | -0.3506 | 0.4528 | 0.5472 |
| rolling_20d | 20 | 1257696 | 103 | -0.3462 | 0.4757 | 0.4854 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 283 | -0.4188 | 0.4382 |
| cumulative | sim | 2537 | -1.248 | 0.2503 |
| cumulative | combined | 2820 | -1.1647 | 0.2691 |
| rolling_5d | real | 44 | -0.1089 | 0.5 |
| rolling_5d | sim | 1649 | -1.2929 | 0.2426 |
| rolling_5d | combined | 1693 | -1.2622 | 0.2493 |
| rolling_10d | real | 53 | -0.3506 | 0.4528 |
| rolling_10d | sim | 1831 | -1.2836 | 0.2392 |
| rolling_10d | combined | 1884 | -1.2573 | 0.2452 |
| rolling_20d | real | 103 | -0.3462 | 0.4757 |
| rolling_20d | sim | 2537 | -1.248 | 0.2503 |
| rolling_20d | combined | 2640 | -1.2128 | 0.2591 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 283 | -0.4188 | -2.32 | 1.58 | 0.4382 | 0.5371 |
| cumulative | normal_only | 283 | -0.4188 | -2.32 | 1.58 | 0.4382 | 0.5371 |
| cumulative | initial_only | 259 | -0.4847 | -2.36 | 1.58 | 0.4208 | 0.5521 |
| cumulative | pyramid_activated | 23 | 0.3243 | -1.42 | 1.59 | 0.6522 | 0.3478 |
| cumulative | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |
| rolling_5d | all_completed_valid | 44 | -0.1089 | -2.51 | 3.22 | 0.5 | 0.5 |
| rolling_5d | normal_only | 44 | -0.1089 | -2.51 | 3.22 | 0.5 | 0.5 |
| rolling_5d | initial_only | 42 | -0.1338 | -2.51 | 2.8 | 0.5 | 0.5 |
| rolling_5d | pyramid_activated | 2 | 0.415 | -2.39 | 3.22 | 0.5 | 0.5 |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 53 | -0.3506 | -2.55 | 2.8 | 0.4528 | 0.5472 |
| rolling_10d | normal_only | 53 | -0.3506 | -2.55 | 2.8 | 0.4528 | 0.5472 |
| rolling_10d | initial_only | 51 | -0.3806 | -2.55 | 2.2 | 0.451 | 0.549 |
| rolling_10d | pyramid_activated | 2 | 0.415 | -2.39 | 3.22 | 0.5 | 0.5 |
| rolling_10d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_20d | all_completed_valid | 103 | -0.3462 | -2.69 | 2.2 | 0.4757 | 0.4854 |
| rolling_20d | normal_only | 103 | -0.3462 | -2.69 | 2.2 | 0.4757 | 0.4854 |
| rolling_20d | initial_only | 100 | -0.3785 | -2.7 | 2.03 | 0.47 | 0.49 |
| rolling_20d | pyramid_activated | 3 | 0.73 | -2.39 | 3.22 | 0.6667 | 0.3333 |
| rolling_20d | reversal_add_activated | 0 | - | - | - | - | - |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 197262 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 86 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 17666 | True | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 1076 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 112158 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 40224 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 13484 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 44 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 482 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 123887 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 53232 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 10423 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 10423 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 608 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 91 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 70 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 886 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 283 | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 283 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 19279 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 75520 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 12033 | True | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 848 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 50662 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 12830 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 9212 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 28 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 103 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 75573 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 33387 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 4146 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 4146 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 375 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 52 | True | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 41 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 750 | True | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 44 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 44 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 19279 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 105173 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 13382 | True | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 852 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 67457 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 16848 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 10811 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 32 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 103 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 87823 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 38156 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 5800 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 5800 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 410 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 52 | True | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 43 | True | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 790 | True | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 53 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 53 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 19279 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 158234 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 2 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 17286 | True | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 928 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 112158 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 40224 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 13484 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 44 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 143 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 123887 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 51261 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 10040 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 10040 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 608 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 91 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 70 | True | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 886 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 103 | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 103 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 19279 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
