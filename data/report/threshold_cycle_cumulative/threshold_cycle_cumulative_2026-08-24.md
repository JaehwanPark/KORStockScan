# Cumulative Threshold Cycle Report - 2026-08-24

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-08-24`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 126 | 2169044 | 719 | -0.2604 | 0.4951 | 0.4701 |
| rolling_5d | 5 | 71541 | 34 | -0.1063 | 0.7059 | 0.2941 |
| rolling_10d | 10 | 112927 | 38 | -0.1868 | 0.6842 | 0.3158 |
| rolling_20d | 20 | 263741 | 50 | -0.2016 | 0.64 | 0.32 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 719 | -0.2604 | 0.4951 |
| cumulative | sim | 3436 | -1.304 | 0.241 |
| cumulative | combined | 4155 | -1.1234 | 0.285 |
| rolling_5d | real | 34 | -0.1063 | 0.7059 |
| rolling_5d | sim | 42 | -0.8205 | 0.4048 |
| rolling_5d | combined | 76 | -0.501 | 0.5395 |
| rolling_10d | real | 38 | -0.1868 | 0.6842 |
| rolling_10d | sim | 76 | -1.0803 | 0.3816 |
| rolling_10d | combined | 114 | -0.7824 | 0.4825 |
| rolling_20d | real | 50 | -0.2016 | 0.64 |
| rolling_20d | sim | 129 | -0.8855 | 0.3953 |
| rolling_20d | combined | 179 | -0.6945 | 0.4637 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 719 | -0.2604 | -3.18 | 1.85 | 0.4951 | 0.4701 |
| cumulative | normal_only | 719 | -0.2604 | -3.18 | 1.85 | 0.4951 | 0.4701 |
| cumulative | initial_only | 636 | -0.2766 | -3.16 | 1.8 | 0.4921 | 0.4717 |
| cumulative | pyramid_activated | 32 | 0.3795 | -1.45 | 1.7143 | 0.6562 | 0.3438 |
| cumulative | reversal_add_activated | 52 | -0.3151 | -4.32 | 2.18 | 0.4423 | 0.5192 |
| rolling_5d | all_completed_valid | 34 | -0.1063 | -3.3838 | 1.2105 | 0.7059 | 0.2941 |
| rolling_5d | normal_only | 34 | -0.1063 | -3.3838 | 1.2105 | 0.7059 | 0.2941 |
| rolling_5d | initial_only | 32 | -0.1282 | -3.3838 | 1.1636 | 0.7188 | 0.2812 |
| rolling_5d | pyramid_activated | 1 | 1.7143 | 1.7143 | 1.7143 | 1 | 0 |
| rolling_5d | reversal_add_activated | 1 | -1.226 | -1.226 | -1.226 | 0 | 1 |
| rolling_10d | all_completed_valid | 38 | -0.1868 | -3.7132 | 1.2105 | 0.6842 | 0.3158 |
| rolling_10d | normal_only | 38 | -0.1868 | -3.7132 | 1.2105 | 0.6842 | 0.3158 |
| rolling_10d | initial_only | 36 | -0.2107 | -3.7132 | 1.1636 | 0.6944 | 0.3056 |
| rolling_10d | pyramid_activated | 1 | 1.7143 | 1.7143 | 1.7143 | 1 | 0 |
| rolling_10d | reversal_add_activated | 1 | -1.226 | -1.226 | -1.226 | 0 | 1 |
| rolling_20d | all_completed_valid | 50 | -0.2016 | -3.7132 | 1.2105 | 0.64 | 0.32 |
| rolling_20d | normal_only | 50 | -0.2016 | -3.7132 | 1.2105 | 0.64 | 0.32 |
| rolling_20d | initial_only | 48 | -0.2202 | -3.7132 | 1.2105 | 0.6458 | 0.3125 |
| rolling_20d | pyramid_activated | 1 | 1.7143 | 1.7143 | 1.7143 | 1 | 0 |
| rolling_20d | reversal_add_activated | 1 | -1.226 | -1.226 | -1.226 | 0 | 1 |

## Smoothing Source-Only Rolling Decision

| family | decision | samples_ready | EV_windows_positive | risk_ready | risk_review | next_action |
| --- | --- | --- | ---: | --- | --- | --- |
| soft_stop_whipsaw_confirmation | hold_sample | False | 3 | True | True | keep_collecting_exact_paths |
| holding_flow_ofi_smoothing | hold_sample | False | 0 | False | False | keep_collecting_exact_paths |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 208852 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 15 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 18157 | True | report_only_reference |
| cumulative | entry_split_order_plan | submit | 233 | False | report_only_reference |
| cumulative | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 4118 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 172076 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 35240 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 25330 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 106 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 2151 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 6 | False | report_only_reference |
| cumulative | reversal_add | holding_exit | 102774 | False | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 17633 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 17633 | False | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 4659 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 216 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 119 | False | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2713 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 719 | True | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 719 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 1116 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 2153 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 261 | True | report_only_reference |
| rolling_5d | entry_split_order_plan | submit | 233 | False | report_only_reference |
| rolling_5d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 106 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 4836 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 1359 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 613 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 112 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 483 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 6 | False | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 1976 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 1020 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 1020 | False | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 1445 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 6 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 6 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 34 | True | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 34 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 1116 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 3475 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 410 | True | report_only_reference |
| rolling_10d | entry_split_order_plan | submit | 233 | False | report_only_reference |
| rolling_10d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 142 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 7988 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 2367 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 1092 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 93 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 868 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 6 | False | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 2769 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 1875 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 1875 | False | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 1521 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 7 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 6 | False | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 38 | True | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 38 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 1116 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 6538 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 967 | True | report_only_reference |
| rolling_20d | entry_split_order_plan | submit | 233 | False | report_only_reference |
| rolling_20d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 178 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 27581 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 6919 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 3460 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 53 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 1245 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 6 | False | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 5543 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 2413 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 2413 | False | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 2007 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 9 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 20 | False | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 50 | True | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 50 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 1116 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
