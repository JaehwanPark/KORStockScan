# Cumulative Threshold Cycle Report - 2026-09-11

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-06-05` ~ `2026-09-11`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 99 | 399949 | 532 | -0.1443 | 0.5508 | 0.4173 |
| rolling_5d | 5 | 7729 | 20 | -0.0115 | 0.75 | 0.25 |
| rolling_10d | 10 | 14862 | 31 | 0.0065 | 0.7097 | 0.2903 |
| rolling_20d | 20 | 36561 | 95 | -0.0997 | 0.7158 | 0.2842 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 532 | -0.1443 | 0.5508 |
| cumulative | sim | 3597 | -1.2902 | 0.2474 |
| cumulative | combined | 4129 | -1.1425 | 0.2865 |
| rolling_5d | real | 20 | -0.0115 | 0.75 |
| rolling_5d | sim | 54 | -0.9567 | 0.4074 |
| rolling_5d | combined | 74 | -0.7012 | 0.5 |
| rolling_10d | real | 31 | 0.0065 | 0.7097 |
| rolling_10d | sim | 104 | -1.0903 | 0.3654 |
| rolling_10d | combined | 135 | -0.8384 | 0.4444 |
| rolling_20d | real | 95 | -0.0997 | 0.7158 |
| rolling_20d | sim | 248 | -0.9563 | 0.3871 |
| rolling_20d | combined | 343 | -0.7191 | 0.4781 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 532 | -0.1443 | -3.56 | 1.93 | 0.5508 | 0.4173 |
| cumulative | normal_only | 532 | -0.1443 | -3.56 | 1.93 | 0.5508 | 0.4173 |
| cumulative | initial_only | 468 | -0.1314 | -3.51 | 1.93 | 0.5577 | 0.4103 |
| cumulative | pyramid_activated | 12 | 0.475 | -2.39 | 3.22 | 0.6667 | 0.3333 |
| cumulative | reversal_add_activated | 53 | -0.2625 | -4.32 | 2.18 | 0.4717 | 0.4906 |
| rolling_5d | all_completed_valid | 20 | -0.0115 | -3.32 | 1.49 | 0.75 | 0.25 |
| rolling_5d | normal_only | 20 | -0.0115 | -3.32 | 1.49 | 0.75 | 0.25 |
| rolling_5d | initial_only | 17 | -0.1453 | -3.32 | 1.53 | 0.7059 | 0.2941 |
| rolling_5d | pyramid_activated | 1 | 0.19 | 0.19 | 0.19 | 1 | 0 |
| rolling_5d | reversal_add_activated | 2 | 1.025 | 0.82 | 1.23 | 1 | 0 |
| rolling_10d | all_completed_valid | 31 | 0.0065 | -3.04 | 1.53 | 0.7097 | 0.2903 |
| rolling_10d | normal_only | 31 | 0.0065 | -3.04 | 1.53 | 0.7097 | 0.2903 |
| rolling_10d | initial_only | 28 | -0.0729 | -3.28 | 1.61 | 0.6786 | 0.3214 |
| rolling_10d | pyramid_activated | 1 | 0.19 | 0.19 | 0.19 | 1 | 0 |
| rolling_10d | reversal_add_activated | 2 | 1.025 | 0.82 | 1.23 | 1 | 0 |
| rolling_20d | all_completed_valid | 95 | -0.0997 | -3.28 | 1.27 | 0.7158 | 0.2842 |
| rolling_20d | normal_only | 95 | -0.0997 | -3.28 | 1.27 | 0.7158 | 0.2842 |
| rolling_20d | initial_only | 90 | -0.1355 | -3.32 | 1.23 | 0.7111 | 0.2889 |
| rolling_20d | pyramid_activated | 2 | 0.95 | 0.19 | 1.71 | 1 | 0 |
| rolling_20d | reversal_add_activated | 3 | 0.2733 | -1.23 | 1.23 | 0.6667 | 0.3333 |

## Smoothing Source-Only Rolling Decision

| family | decision | samples_ready | EV_windows_positive | risk_ready | risk_review | next_action |
| --- | --- | --- | ---: | --- | --- | --- |
| soft_stop_whipsaw_confirmation | hold_sample | False | 3 | True | True | keep_collecting_exact_paths |
| holding_flow_ofi_smoothing | hold_sample | False | 0 | False | False | keep_collecting_exact_paths |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 218696 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 17162 | True | report_only_reference |
| cumulative | entry_split_order_plan | submit | 180 | True | report_only_reference |
| cumulative | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 3078 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 0 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 0 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 0 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 105 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 0 | False | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 0 | False | report_only_reference |
| cumulative | reversal_add | holding_exit | 0 | False | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 19172 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 19172 | False | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 4765 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 216 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 126 | False | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2765 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 532 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 3137 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 242 | True | report_only_reference |
| rolling_5d | entry_split_order_plan | submit | 180 | True | report_only_reference |
| rolling_5d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 50 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 0 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 0 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 0 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 2 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 0 | False | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 0 | False | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 0 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 728 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 728 | False | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 38 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 4 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 12 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 20 | False | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 6666 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 460 | True | report_only_reference |
| rolling_10d | entry_split_order_plan | submit | 180 | True | report_only_reference |
| rolling_10d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 163 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 0 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 0 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 0 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 21 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 0 | False | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 0 | False | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 0 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 1166 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 1166 | False | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 65 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 5 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 16 | False | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 31 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 13982 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 1221 | True | report_only_reference |
| rolling_20d | entry_split_order_plan | submit | 180 | True | report_only_reference |
| rolling_20d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 389 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 0 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 0 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 0 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 50 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 0 | False | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 0 | False | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 0 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 3510 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 3510 | False | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 2092 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 15 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 61 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 95 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
