# Cumulative Threshold Cycle Report - 2026-08-25

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-08-25`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 127 | 2190399 | 731 | -0.2533 | 0.5021 | 0.4651 |
| rolling_5d | 5 | 71896 | 31 | -0.2428 | 0.6452 | 0.3548 |
| rolling_10d | 10 | 134282 | 50 | -0.105 | 0.72 | 0.28 |
| rolling_20d | 20 | 266496 | 62 | -0.1328 | 0.6774 | 0.2903 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 731 | -0.2533 | 0.5021 |
| cumulative | sim | 3459 | -1.3022 | 0.2417 |
| cumulative | combined | 4190 | -1.1192 | 0.2871 |
| rolling_5d | real | 31 | -0.2428 | 0.6452 |
| rolling_5d | sim | 52 | -0.8779 | 0.3846 |
| rolling_5d | combined | 83 | -0.6407 | 0.4819 |
| rolling_10d | real | 50 | -0.105 | 0.72 |
| rolling_10d | sim | 99 | -1.0672 | 0.3737 |
| rolling_10d | combined | 149 | -0.7443 | 0.4899 |
| rolling_20d | real | 62 | -0.1328 | 0.6774 |
| rolling_20d | sim | 148 | -0.8971 | 0.3919 |
| rolling_20d | combined | 210 | -0.6714 | 0.4762 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 731 | -0.2533 | -3.17 | 1.8 | 0.5021 | 0.4651 |
| cumulative | normal_only | 731 | -0.2533 | -3.17 | 1.8 | 0.5021 | 0.4651 |
| cumulative | initial_only | 648 | -0.2683 | -3.16 | 1.77 | 0.5 | 0.466 |
| cumulative | pyramid_activated | 32 | 0.3794 | -1.45 | 1.71 | 0.6562 | 0.3438 |
| cumulative | reversal_add_activated | 52 | -0.3152 | -4.32 | 2.18 | 0.4423 | 0.5192 |
| rolling_5d | all_completed_valid | 31 | -0.2428 | -3.38 | 1.08 | 0.6452 | 0.3548 |
| rolling_5d | normal_only | 31 | -0.2428 | -3.38 | 1.08 | 0.6452 | 0.3548 |
| rolling_5d | initial_only | 30 | -0.2099 | -3.71 | 1.08 | 0.6667 | 0.3333 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 1 | -1.23 | -1.23 | -1.23 | 0 | 1 |
| rolling_10d | all_completed_valid | 50 | -0.105 | -3.71 | 1.14 | 0.72 | 0.28 |
| rolling_10d | normal_only | 50 | -0.105 | -3.71 | 1.14 | 0.72 | 0.28 |
| rolling_10d | initial_only | 48 | -0.1193 | -3.71 | 1.14 | 0.7292 | 0.2708 |
| rolling_10d | pyramid_activated | 1 | 1.71 | 1.71 | 1.71 | 1 | 0 |
| rolling_10d | reversal_add_activated | 1 | -1.23 | -1.23 | -1.23 | 0 | 1 |
| rolling_20d | all_completed_valid | 62 | -0.1328 | -3.38 | 1.16 | 0.6774 | 0.2903 |
| rolling_20d | normal_only | 62 | -0.1328 | -3.38 | 1.16 | 0.6774 | 0.2903 |
| rolling_20d | initial_only | 60 | -0.1452 | -3.71 | 1.14 | 0.6833 | 0.2833 |
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
| cumulative | position_sizing_dynamic_formula | position_sizing | 731 | True | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 731 | False | report_only_reference |
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
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 31 | True | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 31 | False | report_only_reference |
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
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 50 | True | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 50 | False | report_only_reference |
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
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 62 | True | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 62 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 2815 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
