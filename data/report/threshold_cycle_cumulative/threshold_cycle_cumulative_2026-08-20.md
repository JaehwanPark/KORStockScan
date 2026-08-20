# Cumulative Threshold Cycle Report - 2026-08-20

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-08-20`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 122 | 2118503 | 697 | -0.2575 | 0.4921 | 0.472 |
| rolling_5d | 5 | 62386 | 16 | 0.0401 | 0.8125 | 0.1875 |
| rolling_10d | 10 | 128235 | 28 | -0.0836 | 0.6786 | 0.25 |
| rolling_20d | 20 | 311758 | 54 | 0.1205 | 0.6667 | 0.2963 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 697 | -0.2575 | 0.4921 |
| cumulative | sim | 3407 | -1.3086 | 0.2395 |
| cumulative | combined | 4104 | -1.1301 | 0.2824 |
| rolling_5d | real | 16 | 0.0401 | 0.8125 |
| rolling_5d | sim | 47 | -1.2766 | 0.3617 |
| rolling_5d | combined | 63 | -0.9422 | 0.4762 |
| rolling_10d | real | 28 | -0.0836 | 0.6786 |
| rolling_10d | sim | 79 | -0.8859 | 0.3797 |
| rolling_10d | combined | 107 | -0.676 | 0.4579 |
| rolling_20d | real | 54 | 0.1205 | 0.6667 |
| rolling_20d | sim | 107 | -0.8729 | 0.4019 |
| rolling_20d | combined | 161 | -0.5397 | 0.4907 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 697 | -0.2575 | -3.16 | 1.86 | 0.4921 | 0.472 |
| cumulative | normal_only | 697 | -0.2575 | -3.16 | 1.86 | 0.4921 | 0.472 |
| cumulative | initial_only | 615 | -0.2755 | -3.14 | 1.86 | 0.4878 | 0.4748 |
| cumulative | pyramid_activated | 32 | 0.3795 | -1.45 | 1.7143 | 0.6562 | 0.3438 |
| cumulative | reversal_add_activated | 51 | -0.2973 | -4.32 | 2.18 | 0.451 | 0.5098 |
| rolling_5d | all_completed_valid | 16 | 0.0401 | -4.4477 | 1.2746 | 0.8125 | 0.1875 |
| rolling_5d | normal_only | 16 | 0.0401 | -4.4477 | 1.2746 | 0.8125 | 0.1875 |
| rolling_5d | initial_only | 15 | -0.0715 | -4.4477 | 1.138 | 0.8 | 0.2 |
| rolling_5d | pyramid_activated | 1 | 1.7143 | 1.7143 | 1.7143 | 1 | 0 |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 28 | -0.0836 | -4.01 | 1.63 | 0.6786 | 0.25 |
| rolling_10d | normal_only | 28 | -0.0836 | -4.01 | 1.63 | 0.6786 | 0.25 |
| rolling_10d | initial_only | 27 | -0.1502 | -4.01 | 1.2746 | 0.6667 | 0.2593 |
| rolling_10d | pyramid_activated | 1 | 1.7143 | 1.7143 | 1.7143 | 1 | 0 |
| rolling_10d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_20d | all_completed_valid | 54 | 0.1205 | -3.28 | 1.86 | 0.6667 | 0.2963 |
| rolling_20d | normal_only | 54 | 0.1205 | -3.28 | 1.86 | 0.6667 | 0.2963 |
| rolling_20d | initial_only | 51 | 0.0866 | -3.28 | 1.86 | 0.6667 | 0.2941 |
| rolling_20d | pyramid_activated | 1 | 1.7143 | 1.7143 | 1.7143 | 1 | 0 |
| rolling_20d | reversal_add_activated | 2 | 0.19 | -0.32 | 0.7 | 0.5 | 0.5 |

## Smoothing Source-Only Rolling Decision

| family | decision | samples_ready | EV_windows_positive | risk_ready | risk_review | next_action |
| --- | --- | --- | ---: | --- | --- | --- |
| soft_stop_whipsaw_confirmation | hold_sample | False | 0 | False | False | keep_collecting_exact_paths |
| holding_flow_ofi_smoothing | hold_sample | False | 0 | False | False | keep_collecting_exact_paths |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 207349 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 15 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 17983 | True | report_only_reference |
| cumulative | entry_split_order_plan | submit | 2355 | True | report_only_reference |
| cumulative | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 4044 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 169018 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 34249 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 24905 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 101 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 1819 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 242487 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 101742 | False | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 16977 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 16977 | False | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 3230 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 216 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 114 | False | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2711 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 697 | True | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 697 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 2666 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 1972 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 236 | True | report_only_reference |
| rolling_5d | entry_split_order_plan | submit | 2355 | True | report_only_reference |
| rolling_5d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 68 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 4930 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 1376 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 667 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 2 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 536 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 5948 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 1737 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 1219 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 1219 | False | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 92 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 2 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 4 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 16 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 16 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 2666 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 3827 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 506 | True | report_only_reference |
| rolling_10d | entry_split_order_plan | submit | 2355 | True | report_only_reference |
| rolling_10d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 104 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 12158 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 3379 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 1527 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 5 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 812 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 11260 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 3773 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 1558 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 1558 | False | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 569 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 4 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 13 | False | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 28 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 28 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 2666 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 6302 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 1111 | True | report_only_reference |
| rolling_20d | entry_split_order_plan | submit | 2355 | True | report_only_reference |
| rolling_20d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 168 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 30761 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 9001 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 4026 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 8 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 1361 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 16223 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 6225 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 1963 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 1963 | False | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 1007 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 11 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 22 | False | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 54 | True | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 54 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 2666 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
