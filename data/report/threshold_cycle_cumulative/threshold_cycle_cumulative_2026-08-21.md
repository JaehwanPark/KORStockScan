# Cumulative Threshold Cycle Report - 2026-08-21

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-08-21`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 123 | 2147483 | 711 | -0.2561 | 0.4937 | 0.4712 |
| rolling_5d | 5 | 91366 | 30 | -0.0656 | 0.7 | 0.3 |
| rolling_10d | 10 | 147667 | 42 | -0.1179 | 0.6429 | 0.3095 |
| rolling_20d | 20 | 340738 | 68 | 0.0573 | 0.6471 | 0.3235 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 711 | -0.2561 | 0.4937 |
| cumulative | sim | 3417 | -1.3083 | 0.2406 |
| cumulative | combined | 4128 | -1.1271 | 0.2842 |
| rolling_5d | real | 30 | -0.0656 | 0.7 |
| rolling_5d | sim | 57 | -1.2621 | 0.4035 |
| rolling_5d | combined | 87 | -0.8495 | 0.5057 |
| rolling_10d | real | 42 | -0.1179 | 0.6429 |
| rolling_10d | sim | 86 | -0.9313 | 0.407 |
| rolling_10d | combined | 128 | -0.6644 | 0.4844 |
| rolling_20d | real | 68 | 0.0573 | 0.6471 |
| rolling_20d | sim | 117 | -0.9003 | 0.4188 |
| rolling_20d | combined | 185 | -0.5483 | 0.5027 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 711 | -0.2561 | -3.16 | 1.85 | 0.4937 | 0.4712 |
| cumulative | normal_only | 711 | -0.2561 | -3.16 | 1.85 | 0.4937 | 0.4712 |
| cumulative | initial_only | 628 | -0.272 | -3.15 | 1.85 | 0.4904 | 0.4729 |
| cumulative | pyramid_activated | 32 | 0.3795 | -1.45 | 1.7143 | 0.6562 | 0.3438 |
| cumulative | reversal_add_activated | 52 | -0.3151 | -4.32 | 2.18 | 0.4423 | 0.5192 |
| rolling_5d | all_completed_valid | 30 | -0.0656 | -3.7132 | 1.2105 | 0.7 | 0.3 |
| rolling_5d | normal_only | 30 | -0.0656 | -3.7132 | 1.2105 | 0.7 | 0.3 |
| rolling_5d | initial_only | 28 | -0.0878 | -3.7132 | 1.2105 | 0.7143 | 0.2857 |
| rolling_5d | pyramid_activated | 1 | 1.7143 | 1.7143 | 1.7143 | 1 | 0 |
| rolling_5d | reversal_add_activated | 1 | -1.226 | -1.226 | -1.226 | 0 | 1 |
| rolling_10d | all_completed_valid | 42 | -0.1179 | -3.3838 | 1.2746 | 0.6429 | 0.3095 |
| rolling_10d | normal_only | 42 | -0.1179 | -3.3838 | 1.2746 | 0.6429 | 0.3095 |
| rolling_10d | initial_only | 40 | -0.136 | -3.7132 | 1.2105 | 0.65 | 0.3 |
| rolling_10d | pyramid_activated | 1 | 1.7143 | 1.7143 | 1.7143 | 1 | 0 |
| rolling_10d | reversal_add_activated | 1 | -1.226 | -1.226 | -1.226 | 0 | 1 |
| rolling_20d | all_completed_valid | 68 | 0.0573 | -3.33 | 1.7143 | 0.6471 | 0.3235 |
| rolling_20d | normal_only | 68 | 0.0573 | -3.33 | 1.7143 | 0.6471 | 0.3235 |
| rolling_20d | initial_only | 64 | 0.0473 | -3.33 | 1.66 | 0.6562 | 0.3125 |
| rolling_20d | pyramid_activated | 1 | 1.7143 | 1.7143 | 1.7143 | 1 | 0 |
| rolling_20d | reversal_add_activated | 3 | -0.282 | -1.226 | 0.7 | 0.3333 | 0.6667 |

## Smoothing Source-Only Rolling Decision

| family | decision | samples_ready | EV_windows_positive | risk_ready | risk_review | next_action |
| --- | --- | --- | ---: | --- | --- | --- |
| soft_stop_whipsaw_confirmation | hold_sample | False | 3 | True | True | keep_collecting_exact_paths |
| holding_flow_ofi_smoothing | hold_sample | False | 0 | False | False | keep_collecting_exact_paths |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 208244 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 15 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 18056 | True | report_only_reference |
| cumulative | entry_split_order_plan | submit | 4069 | True | report_only_reference |
| cumulative | scale_in_split_order_plan | scale_in | 2 | False | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 4088 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 170398 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 34754 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 25103 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 105 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 2026 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 13 | False | report_only_reference |
| cumulative | reversal_add | holding_exit | 102344 | False | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 17249 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 17249 | False | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 4618 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 216 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 116 | False | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2713 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 711 | True | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 711 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 2626 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 2867 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 309 | True | report_only_reference |
| rolling_5d | entry_split_order_plan | submit | 4069 | True | report_only_reference |
| rolling_5d | scale_in_split_order_plan | scale_in | 2 | False | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 112 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 6310 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 1881 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 865 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 112 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 743 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 13 | False | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 2339 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 1491 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 1491 | False | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 1480 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 4 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 6 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 30 | True | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 30 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 2626 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 4575 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 537 | True | report_only_reference |
| rolling_10d | entry_split_order_plan | submit | 4069 | True | report_only_reference |
| rolling_10d | scale_in_split_order_plan | scale_in | 2 | False | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 148 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 11828 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 3298 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 1464 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 63 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 1018 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 13 | False | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 4368 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 1830 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 1830 | False | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 1956 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 6 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 14 | False | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 42 | True | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 42 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 2626 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 7197 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 1184 | True | report_only_reference |
| rolling_20d | entry_split_order_plan | submit | 4069 | True | report_only_reference |
| rolling_20d | scale_in_split_order_plan | scale_in | 2 | False | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 212 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 32141 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 9506 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 4224 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 59 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 1568 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 13 | False | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 6827 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 2235 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 2235 | False | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 2395 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 13 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 24 | False | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 68 | True | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 68 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 2626 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
