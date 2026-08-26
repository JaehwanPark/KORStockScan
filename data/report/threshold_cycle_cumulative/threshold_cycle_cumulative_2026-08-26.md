# Cumulative Threshold Cycle Report - 2026-08-26

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-08-26`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 128 | 2215617 | 732 | -0.2573 | 0.5014 | 0.4658 |
| rolling_5d | 5 | 68134 | 18 | -0.4524 | 0.6667 | 0.3333 |
| rolling_10d | 10 | 159500 | 51 | -0.1659 | 0.7059 | 0.2941 |
| rolling_20d | 20 | 254554 | 63 | -0.1817 | 0.6667 | 0.3016 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 732 | -0.2573 | 0.5014 |
| cumulative | sim | 3474 | -1.3003 | 0.2424 |
| cumulative | combined | 4206 | -1.1188 | 0.2874 |
| rolling_5d | real | 18 | -0.4524 | 0.6667 |
| rolling_5d | sim | 57 | -0.8233 | 0.3509 |
| rolling_5d | combined | 75 | -0.7343 | 0.4267 |
| rolling_10d | real | 51 | -0.1659 | 0.7059 |
| rolling_10d | sim | 114 | -1.0427 | 0.3772 |
| rolling_10d | combined | 165 | -0.7717 | 0.4788 |
| rolling_20d | real | 63 | -0.1817 | 0.6667 |
| rolling_20d | sim | 160 | -0.8921 | 0.3937 |
| rolling_20d | combined | 223 | -0.6914 | 0.4709 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 732 | -0.2573 | -3.18 | 1.8 | 0.5014 | 0.4658 |
| cumulative | normal_only | 732 | -0.2573 | -3.18 | 1.8 | 0.5014 | 0.4658 |
| cumulative | initial_only | 649 | -0.2728 | -3.16 | 1.77 | 0.4992 | 0.4669 |
| cumulative | pyramid_activated | 32 | 0.3794 | -1.45 | 1.71 | 0.6562 | 0.3438 |
| cumulative | reversal_add_activated | 52 | -0.3152 | -4.32 | 2.18 | 0.4423 | 0.5192 |
| rolling_5d | all_completed_valid | 18 | -0.4524 | -3.89 | 1.04 | 0.6667 | 0.3333 |
| rolling_5d | normal_only | 18 | -0.4524 | -3.89 | 1.04 | 0.6667 | 0.3333 |
| rolling_5d | initial_only | 18 | -0.4524 | -3.89 | 1.04 | 0.6667 | 0.3333 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 51 | -0.1659 | -3.38 | 1.14 | 0.7059 | 0.2941 |
| rolling_10d | normal_only | 51 | -0.1659 | -3.38 | 1.14 | 0.7059 | 0.2941 |
| rolling_10d | initial_only | 49 | -0.1825 | -3.71 | 1.14 | 0.7143 | 0.2857 |
| rolling_10d | pyramid_activated | 1 | 1.71 | 1.71 | 1.71 | 1 | 0 |
| rolling_10d | reversal_add_activated | 1 | -1.23 | -1.23 | -1.23 | 0 | 1 |
| rolling_20d | all_completed_valid | 63 | -0.1817 | -3.38 | 1.16 | 0.6667 | 0.3016 |
| rolling_20d | normal_only | 63 | -0.1817 | -3.38 | 1.16 | 0.6667 | 0.3016 |
| rolling_20d | initial_only | 61 | -0.1955 | -3.38 | 1.14 | 0.6721 | 0.2951 |
| rolling_20d | pyramid_activated | 1 | 1.71 | 1.71 | 1.71 | 1 | 0 |
| rolling_20d | reversal_add_activated | 1 | -1.23 | -1.23 | -1.23 | 0 | 1 |

## Smoothing Source-Only Rolling Decision

| family | decision | samples_ready | EV_windows_positive | risk_ready | risk_review | next_action |
| --- | --- | --- | ---: | --- | --- | --- |
| soft_stop_whipsaw_confirmation | hold_sample | False | 3 | True | True | keep_collecting_exact_paths |
| holding_flow_ofi_smoothing | hold_sample | False | 0 | False | False | keep_collecting_exact_paths |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 210473 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 15 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 18313 | True | report_only_reference |
| cumulative | entry_split_order_plan | submit | 5840 | True | report_only_reference |
| cumulative | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 4160 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 174355 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 35979 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 25694 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 111 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 2535 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 1 | False | report_only_reference |
| cumulative | reversal_add | holding_exit | 104874 | False | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 17940 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 17940 | False | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 4685 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 216 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 119 | False | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2713 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 732 | True | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 732 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 4778 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 2229 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 257 | True | report_only_reference |
| rolling_5d | entry_split_order_plan | submit | 5840 | True | report_only_reference |
| rolling_5d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 72 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 3957 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 1225 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 591 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 38 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 509 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 1 | False | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 2530 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 691 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 691 | False | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 67 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 3 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 0 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 18 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 18 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 4778 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 5096 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 566 | True | report_only_reference |
| rolling_10d | entry_split_order_plan | submit | 5840 | True | report_only_reference |
| rolling_10d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 184 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 10267 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 3106 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 1456 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 71 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 1252 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 1 | False | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 4869 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 2182 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 2182 | False | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 1547 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 7 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 6 | False | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 51 | True | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 51 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 4778 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 7239 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 1009 | True | report_only_reference |
| rolling_20d | entry_split_order_plan | submit | 5840 | True | report_only_reference |
| rolling_20d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 220 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 22171 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 6577 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 3057 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 53 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 1618 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 1 | False | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 7482 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 2624 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 2624 | False | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 2031 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 9 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 20 | False | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 63 | True | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 63 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 4778 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
