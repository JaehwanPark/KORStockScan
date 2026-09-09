# Cumulative Threshold Cycle Report - 2026-09-09

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-06-05` ~ `2026-09-09`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 97 | 93899 | 514 | -0.1461 | 0.5447 | 0.4222 |
| rolling_5d | 5 | 1557 | 7 | 0.1143 | 0.7143 | 0.2857 |
| rolling_10d | 10 | 2634 | 20 | 0.102 | 0.75 | 0.25 |
| rolling_20d | 20 | 11776 | 83 | -0.1133 | 0.6867 | 0.2892 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 514 | -0.1461 | 0.5447 |
| cumulative | sim | 3577 | -1.293 | 0.2466 |
| cumulative | combined | 4091 | -1.1489 | 0.284 |
| rolling_5d | real | 7 | 0.1143 | 0.7143 |
| rolling_5d | sim | 50 | -1.2822 | 0.3 |
| rolling_5d | combined | 57 | -1.1107 | 0.3509 |
| rolling_10d | real | 20 | 0.102 | 0.75 |
| rolling_10d | sim | 103 | -1.046 | 0.3883 |
| rolling_10d | combined | 123 | -0.8593 | 0.4472 |
| rolling_20d | real | 83 | -0.1133 | 0.6867 |
| rolling_20d | sim | 246 | -0.9543 | 0.3862 |
| rolling_20d | combined | 329 | -0.7421 | 0.462 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 514 | -0.1461 | -3.61 | 2.03 | 0.5447 | 0.4222 |
| cumulative | normal_only | 514 | -0.1461 | -3.61 | 2.03 | 0.5447 | 0.4222 |
| cumulative | initial_only | 451 | -0.1309 | -3.51 | 1.98 | 0.5521 | 0.4146 |
| cumulative | pyramid_activated | 12 | 0.475 | -2.39 | 3.22 | 0.6667 | 0.3333 |
| cumulative | reversal_add_activated | 52 | -0.2833 | -4.32 | 2.18 | 0.4615 | 0.5 |
| rolling_5d | all_completed_valid | 7 | 0.1143 | -3.04 | 2.12 | 0.7143 | 0.2857 |
| rolling_5d | normal_only | 7 | 0.1143 | -3.04 | 2.12 | 0.7143 | 0.2857 |
| rolling_5d | initial_only | 5 | -0.124 | -3.04 | 2.12 | 0.6 | 0.4 |
| rolling_5d | pyramid_activated | 1 | 0.19 | 0.19 | 0.19 | 1 | 0 |
| rolling_5d | reversal_add_activated | 1 | 1.23 | 1.23 | 1.23 | 1 | 0 |
| rolling_10d | all_completed_valid | 20 | 0.102 | -3.04 | 1.29 | 0.75 | 0.25 |
| rolling_10d | normal_only | 20 | 0.102 | -3.04 | 1.29 | 0.75 | 0.25 |
| rolling_10d | initial_only | 18 | 0.0344 | -3.04 | 1.88 | 0.7222 | 0.2778 |
| rolling_10d | pyramid_activated | 1 | 0.19 | 0.19 | 0.19 | 1 | 0 |
| rolling_10d | reversal_add_activated | 1 | 1.23 | 1.23 | 1.23 | 1 | 0 |
| rolling_20d | all_completed_valid | 83 | -0.1133 | -3.22 | 1.23 | 0.6867 | 0.2892 |
| rolling_20d | normal_only | 83 | -0.1133 | -3.22 | 1.23 | 0.6867 | 0.2892 |
| rolling_20d | initial_only | 79 | -0.1431 | -3.38 | 1.23 | 0.6835 | 0.2911 |
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
| cumulative | soft_stop_micro_grace | holding_exit | 18952 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 18952 | False | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 4743 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 216 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 123 | False | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 0 | False | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 514 | False | report_only_reference |
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
| rolling_5d | soft_stop_micro_grace | holding_exit | 627 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 627 | False | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 20 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 2 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 0 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 7 | False | report_only_reference |
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
| rolling_10d | soft_stop_micro_grace | holding_exit | 1012 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 1012 | False | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 58 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 4 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 0 | False | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 20 | False | report_only_reference |
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
| rolling_20d | soft_stop_micro_grace | holding_exit | 3533 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 3533 | False | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 2081 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 13 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 0 | False | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 83 | False | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
