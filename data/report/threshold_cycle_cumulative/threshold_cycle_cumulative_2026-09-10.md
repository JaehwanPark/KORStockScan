# Cumulative Threshold Cycle Report - 2026-09-10

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-06-05` ~ `2026-09-10`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 98 | 95011 | 519 | -0.1412 | 0.5453 | 0.422 |
| rolling_5d | 5 | 2368 | 9 | 0.3622 | 0.6667 | 0.3333 |
| rolling_10d | 10 | 3562 | 23 | 0.0865 | 0.6957 | 0.3043 |
| rolling_20d | 20 | 12621 | 88 | -0.0861 | 0.6818 | 0.2955 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 519 | -0.1412 | 0.5453 |
| cumulative | sim | 3587 | -1.2912 | 0.2473 |
| cumulative | combined | 4106 | -1.1459 | 0.2849 |
| rolling_5d | real | 9 | 0.3622 | 0.6667 |
| rolling_5d | sim | 47 | -0.9791 | 0.4043 |
| rolling_5d | combined | 56 | -0.7636 | 0.4464 |
| rolling_10d | real | 23 | 0.0865 | 0.6957 |
| rolling_10d | sim | 103 | -1.1239 | 0.3592 |
| rolling_10d | combined | 126 | -0.9029 | 0.4206 |
| rolling_20d | real | 88 | -0.0861 | 0.6818 |
| rolling_20d | sim | 252 | -0.941 | 0.3929 |
| rolling_20d | combined | 340 | -0.7197 | 0.4676 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 519 | -0.1412 | -3.61 | 2.03 | 0.5453 | 0.422 |
| cumulative | normal_only | 519 | -0.1412 | -3.61 | 2.03 | 0.5453 | 0.422 |
| cumulative | initial_only | 456 | -0.1255 | -3.51 | 1.98 | 0.5526 | 0.4145 |
| cumulative | pyramid_activated | 12 | 0.475 | -2.39 | 3.22 | 0.6667 | 0.3333 |
| cumulative | reversal_add_activated | 52 | -0.2833 | -4.32 | 2.18 | 0.4615 | 0.5 |
| rolling_5d | all_completed_valid | 9 | 0.3622 | -1.09 | 1.61 | 0.6667 | 0.3333 |
| rolling_5d | normal_only | 9 | 0.3622 | -1.09 | 1.61 | 0.6667 | 0.3333 |
| rolling_5d | initial_only | 7 | 0.2629 | -1.09 | 1.61 | 0.5714 | 0.4286 |
| rolling_5d | pyramid_activated | 1 | 0.19 | 0.19 | 0.19 | 1 | 0 |
| rolling_5d | reversal_add_activated | 1 | 1.23 | 1.23 | 1.23 | 1 | 0 |
| rolling_10d | all_completed_valid | 23 | 0.0865 | -2.55 | 1.61 | 0.6957 | 0.3043 |
| rolling_10d | normal_only | 23 | 0.0865 | -2.55 | 1.61 | 0.6957 | 0.3043 |
| rolling_10d | initial_only | 21 | 0.0271 | -2.55 | 1.61 | 0.6667 | 0.3333 |
| rolling_10d | pyramid_activated | 1 | 0.19 | 0.19 | 0.19 | 1 | 0 |
| rolling_10d | reversal_add_activated | 1 | 1.23 | 1.23 | 1.23 | 1 | 0 |
| rolling_20d | all_completed_valid | 88 | -0.0861 | -3.22 | 1.27 | 0.6818 | 0.2955 |
| rolling_20d | normal_only | 88 | -0.0861 | -3.22 | 1.27 | 0.6818 | 0.2955 |
| rolling_20d | initial_only | 84 | -0.1128 | -3.22 | 1.23 | 0.6786 | 0.2976 |
| rolling_20d | pyramid_activated | 2 | 0.95 | 0.19 | 1.71 | 1 | 0 |
| rolling_20d | reversal_add_activated | 2 | 0 | -1.23 | 1.23 | 0.5 | 0.5 |

## Smoothing Source-Only Rolling Decision

| family | decision | samples_ready | EV_windows_positive | risk_ready | risk_review | next_action |
| --- | --- | --- | ---: | --- | --- | --- |
| soft_stop_whipsaw_confirmation | hold_sample | False | 3 | True | True | keep_collecting_exact_paths |
| holding_flow_ofi_smoothing | hold_sample | False | 0 | False | False | keep_collecting_exact_paths |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 0 | False | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 0 | False | report_only_reference |
| cumulative | entry_split_order_plan | submit | 179 | False | report_only_reference |
| cumulative | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 0 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 0 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 0 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 0 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 0 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 0 | False | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 0 | False | report_only_reference |
| cumulative | reversal_add | holding_exit | 0 | False | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 19118 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 19118 | False | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 4751 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 216 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 123 | False | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 0 | False | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 519 | False | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 0 | False | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 0 | False | report_only_reference |
| rolling_5d | entry_split_order_plan | submit | 179 | False | report_only_reference |
| rolling_5d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 0 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 0 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 0 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 0 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 0 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 0 | False | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 0 | False | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 0 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 674 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 674 | False | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 25 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 1 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 0 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 9 | False | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 0 | False | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 0 | False | report_only_reference |
| rolling_10d | entry_split_order_plan | submit | 179 | False | report_only_reference |
| rolling_10d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 0 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 0 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 0 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 0 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 0 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 0 | False | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 0 | False | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 0 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 1161 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 1161 | False | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 57 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 3 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 0 | False | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 23 | False | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 0 | False | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 0 | False | report_only_reference |
| rolling_20d | entry_split_order_plan | submit | 179 | False | report_only_reference |
| rolling_20d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 0 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 0 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 0 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 0 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 0 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 0 | False | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 0 | False | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 0 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 3652 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 3652 | False | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 2088 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 13 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 0 | False | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 88 | False | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
