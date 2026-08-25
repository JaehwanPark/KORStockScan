# Cumulative Threshold Cycle Report - 2026-08-25

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-08-25`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 127 | 2190399 | 727 | -0.2584 | 0.4979 | 0.4677 |
| rolling_5d | 5 | 71896 | 30 | -0.2798 | 0.6333 | 0.3667 |
| rolling_10d | 10 | 134282 | 46 | -0.1685 | 0.6957 | 0.3043 |
| rolling_20d | 20 | 266496 | 58 | -0.1851 | 0.6552 | 0.3103 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 727 | -0.2584 | 0.4979 |
| cumulative | sim | 3459 | -1.3022 | 0.2417 |
| cumulative | combined | 4186 | -1.1209 | 0.2862 |
| rolling_5d | real | 30 | -0.2798 | 0.6333 |
| rolling_5d | sim | 52 | -0.8779 | 0.3846 |
| rolling_5d | combined | 82 | -0.6591 | 0.4756 |
| rolling_10d | real | 46 | -0.1685 | 0.6957 |
| rolling_10d | sim | 99 | -1.0672 | 0.3737 |
| rolling_10d | combined | 145 | -0.7821 | 0.4759 |
| rolling_20d | real | 58 | -0.1851 | 0.6552 |
| rolling_20d | sim | 148 | -0.8971 | 0.3919 |
| rolling_20d | combined | 206 | -0.6966 | 0.466 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 727 | -0.2584 | -3.18 | 1.82 | 0.4979 | 0.4677 |
| cumulative | normal_only | 727 | -0.2584 | -3.18 | 1.82 | 0.4979 | 0.4677 |
| cumulative | initial_only | 644 | -0.2742 | -3.16 | 1.77 | 0.4953 | 0.4689 |
| cumulative | pyramid_activated | 32 | 0.3795 | -1.45 | 1.7143 | 0.6562 | 0.3438 |
| cumulative | reversal_add_activated | 52 | -0.3151 | -4.32 | 2.18 | 0.4423 | 0.5192 |
| rolling_5d | all_completed_valid | 30 | -0.2798 | -3.7132 | 1.0835 | 0.6333 | 0.3667 |
| rolling_5d | normal_only | 30 | -0.2798 | -3.7132 | 1.0835 | 0.6333 | 0.3667 |
| rolling_5d | initial_only | 29 | -0.2471 | -3.7132 | 1.1636 | 0.6552 | 0.3448 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 1 | -1.226 | -1.226 | -1.226 | 0 | 1 |
| rolling_10d | all_completed_valid | 46 | -0.1685 | -3.7132 | 1.1636 | 0.6957 | 0.3043 |
| rolling_10d | normal_only | 46 | -0.1685 | -3.7132 | 1.1636 | 0.6957 | 0.3043 |
| rolling_10d | initial_only | 44 | -0.1872 | -3.7132 | 1.138 | 0.7045 | 0.2955 |
| rolling_10d | pyramid_activated | 1 | 1.7143 | 1.7143 | 1.7143 | 1 | 0 |
| rolling_10d | reversal_add_activated | 1 | -1.226 | -1.226 | -1.226 | 0 | 1 |
| rolling_20d | all_completed_valid | 58 | -0.1851 | -3.7132 | 1.2105 | 0.6552 | 0.3103 |
| rolling_20d | normal_only | 58 | -0.1851 | -3.7132 | 1.2105 | 0.6552 | 0.3103 |
| rolling_20d | initial_only | 56 | -0.2004 | -3.7132 | 1.1636 | 0.6607 | 0.3036 |
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
| cumulative | entry_mechanical_momentum | entry | 209623 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 15 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 18256 | True | report_only_reference |
| cumulative | entry_split_order_plan | submit | 4566 | True | report_only_reference |
| cumulative | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 4160 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 173227 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 35650 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 25511 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 108 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 2359 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 8 | False | report_only_reference |
| cumulative | reversal_add | holding_exit | 103444 | False | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 17778 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 17778 | False | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 4680 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 216 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 119 | False | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2713 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 727 | True | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 727 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 2815 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 2274 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 273 | True | report_only_reference |
| rolling_5d | entry_split_order_plan | submit | 4566 | True | report_only_reference |
| rolling_5d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 116 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 4209 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 1401 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 606 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 105 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 540 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 8 | False | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 1702 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 801 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 801 | False | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 1450 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 5 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 2 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 30 | True | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 30 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 2815 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 4246 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 509 | True | report_only_reference |
| rolling_10d | entry_split_order_plan | submit | 4566 | True | report_only_reference |
| rolling_10d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 184 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 9139 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 2777 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 1273 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 91 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 1076 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 8 | False | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 3439 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 2020 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 2020 | False | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 1542 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 7 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 6 | False | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 46 | True | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 46 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 2815 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 7299 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 999 | True | report_only_reference |
| rolling_20d | entry_split_order_plan | submit | 4566 | True | report_only_reference |
| rolling_20d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 220 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 24772 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 6764 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 3301 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 58 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 1447 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 8 | False | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 6181 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 2506 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 2506 | False | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 2027 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 9 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 20 | False | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 58 | True | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 58 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 2815 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
