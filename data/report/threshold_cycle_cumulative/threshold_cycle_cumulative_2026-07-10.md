# Cumulative Threshold Cycle Report - 2026-07-10

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-07-10`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 81 | 2238222 | 530 | -0.2873 | 0.4736 | 0.4943 |
| rolling_5d | 5 | 71805 | 85 | -0.4964 | 0.5647 | 0.4235 |
| rolling_10d | 10 | 159184 | 170 | -0.0189 | 0.5647 | 0.3882 |
| rolling_20d | 20 | 351770 | 234 | -0.0856 | 0.5299 | 0.4274 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 530 | -0.2873 | 0.4736 |
| cumulative | sim | 3988 | -1.2923 | 0.2417 |
| cumulative | combined | 4518 | -1.1744 | 0.2689 |
| rolling_5d | real | 85 | -0.4964 | 0.5647 |
| rolling_5d | sim | 92 | -1.8458 | 0.3043 |
| rolling_5d | combined | 177 | -1.1977 | 0.4294 |
| rolling_10d | real | 170 | -0.0189 | 0.5647 |
| rolling_10d | sim | 148 | -1.6471 | 0.3514 |
| rolling_10d | combined | 318 | -0.7767 | 0.4654 |
| rolling_20d | real | 234 | -0.0856 | 0.5299 |
| rolling_20d | sim | 680 | -1.5205 | 0.2353 |
| rolling_20d | combined | 914 | -1.1532 | 0.3107 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 530 | -0.2873 | -2.87 | 2.07 | 0.4736 | 0.4943 |
| cumulative | normal_only | 530 | -0.2873 | -2.87 | 2.07 | 0.4736 | 0.4943 |
| cumulative | initial_only | 462 | -0.3099 | -2.7 | 2.07 | 0.4654 | 0.5022 |
| cumulative | pyramid_activated | 28 | 0.3168 | -2.12 | 3.15 | 0.6071 | 0.3929 |
| cumulative | reversal_add_activated | 41 | -0.2676 | -4.57 | 2.18 | 0.4878 | 0.4634 |
| rolling_5d | all_completed_valid | 85 | -0.4964 | -5.16 | 2.64 | 0.5647 | 0.4235 |
| rolling_5d | normal_only | 85 | -0.4964 | -5.16 | 2.64 | 0.5647 | 0.4235 |
| rolling_5d | initial_only | 72 | -0.4981 | -5.3 | 3.27 | 0.5556 | 0.4306 |
| rolling_5d | pyramid_activated | 2 | -0.785 | -2.12 | 0.55 | 0.5 | 0.5 |
| rolling_5d | reversal_add_activated | 11 | -0.4327 | -3.88 | 1.48 | 0.6364 | 0.3636 |
| rolling_10d | all_completed_valid | 170 | -0.0189 | -4.44 | 2.64 | 0.5647 | 0.3882 |
| rolling_10d | normal_only | 170 | -0.0189 | -4.44 | 2.64 | 0.5647 | 0.3882 |
| rolling_10d | initial_only | 135 | 0.0979 | -3.86 | 2.94 | 0.5778 | 0.3778 |
| rolling_10d | pyramid_activated | 2 | -0.785 | -2.12 | 0.55 | 0.5 | 0.5 |
| rolling_10d | reversal_add_activated | 33 | -0.4503 | -4.6 | 1.86 | 0.5152 | 0.4242 |
| rolling_20d | all_completed_valid | 234 | -0.0856 | -4.44 | 2.64 | 0.5299 | 0.4274 |
| rolling_20d | normal_only | 234 | -0.0856 | -4.44 | 2.64 | 0.5299 | 0.4274 |
| rolling_20d | initial_only | 191 | -0.0265 | -4.32 | 2.75 | 0.5393 | 0.4188 |
| rolling_20d | pyramid_activated | 4 | 0.645 | -2.87 | 7.02 | 0.5 | 0.5 |
| rolling_20d | reversal_add_activated | 40 | -0.2635 | -4.6 | 2.18 | 0.5 | 0.45 |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 294971 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 101 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 18715 | True | report_only_reference |
| cumulative | entry_split_order_plan | submit | 1901 | True | report_only_reference |
| cumulative | scale_in_split_order_plan | scale_in | 3 | True | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 3711 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 180209 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 47706 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 23141 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 104 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 620 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 249678 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 105548 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 19191 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 19191 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 1759 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 187 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 115 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2759 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 530 | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 530 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 1623 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 2272 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 12 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 889 | True | report_only_reference |
| rolling_5d | entry_split_order_plan | submit | 1901 | True | report_only_reference |
| rolling_5d | scale_in_split_order_plan | scale_in | 3 | True | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 437 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 3250 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 326 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 603 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 21 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 1 | False | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 12488 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 4196 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 294 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 294 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 609 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 25 | True | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 10 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 72 | True | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 85 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 85 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 1623 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 4223 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 12 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 1709 | True | report_only_reference |
| rolling_10d | entry_split_order_plan | submit | 1901 | True | report_only_reference |
| rolling_10d | scale_in_split_order_plan | scale_in | 3 | True | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 1054 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 7544 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 910 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 991 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 29 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 62 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 31554 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 11908 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 705 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 705 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 707 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 25 | True | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 24 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 439 | True | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 170 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 170 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 1623 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 8542 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 12 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 4350 | True | report_only_reference |
| rolling_20d | entry_split_order_plan | submit | 1901 | True | report_only_reference |
| rolling_20d | scale_in_split_order_plan | scale_in | 3 | True | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 1745 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 17827 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 3010 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 3469 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 35 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 85 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 63787 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 25002 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 2391 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 2391 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 921 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 30 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 38 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 1027 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 234 | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 234 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 1623 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
