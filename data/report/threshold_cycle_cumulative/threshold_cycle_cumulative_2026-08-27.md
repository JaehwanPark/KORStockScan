# Cumulative Threshold Cycle Report - 2026-08-27

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-08-27`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 129 | 2235695 | 734 | -0.254 | 0.5027 | 0.4646 |
| rolling_5d | 5 | 88212 | 20 | -0.3132 | 0.7 | 0.3 |
| rolling_10d | 10 | 179578 | 53 | -0.1242 | 0.717 | 0.283 |
| rolling_20d | 20 | 259119 | 65 | -0.1472 | 0.6769 | 0.2923 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 734 | -0.254 | 0.5027 |
| cumulative | sim | 3484 | -1.2962 | 0.244 |
| cumulative | combined | 4218 | -1.1148 | 0.289 |
| rolling_5d | real | 20 | -0.3132 | 0.7 |
| rolling_5d | sim | 67 | -0.6787 | 0.4179 |
| rolling_5d | combined | 87 | -0.5946 | 0.4828 |
| rolling_10d | real | 53 | -0.1242 | 0.717 |
| rolling_10d | sim | 124 | -0.9469 | 0.4113 |
| rolling_10d | combined | 177 | -0.7005 | 0.5028 |
| rolling_20d | real | 65 | -0.1472 | 0.6769 |
| rolling_20d | sim | 168 | -0.8482 | 0.4107 |
| rolling_20d | combined | 233 | -0.6526 | 0.485 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 734 | -0.254 | -3.18 | 1.8 | 0.5027 | 0.4646 |
| cumulative | normal_only | 734 | -0.254 | -3.18 | 1.8 | 0.5027 | 0.4646 |
| cumulative | initial_only | 651 | -0.2691 | -3.16 | 1.76 | 0.5008 | 0.4654 |
| cumulative | pyramid_activated | 32 | 0.3794 | -1.45 | 1.71 | 0.6562 | 0.3438 |
| cumulative | reversal_add_activated | 52 | -0.3152 | -4.32 | 2.18 | 0.4423 | 0.5192 |
| rolling_5d | all_completed_valid | 20 | -0.3132 | -3.89 | 1.04 | 0.7 | 0.3 |
| rolling_5d | normal_only | 20 | -0.3132 | -3.89 | 1.04 | 0.7 | 0.3 |
| rolling_5d | initial_only | 20 | -0.3132 | -3.89 | 1.04 | 0.7 | 0.3 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 53 | -0.1242 | -3.38 | 1.16 | 0.717 | 0.283 |
| rolling_10d | normal_only | 53 | -0.1242 | -3.38 | 1.16 | 0.717 | 0.283 |
| rolling_10d | initial_only | 51 | -0.1385 | -3.38 | 1.14 | 0.7255 | 0.2745 |
| rolling_10d | pyramid_activated | 1 | 1.71 | 1.71 | 1.71 | 1 | 0 |
| rolling_10d | reversal_add_activated | 1 | -1.23 | -1.23 | -1.23 | 0 | 1 |
| rolling_20d | all_completed_valid | 65 | -0.1472 | -3.38 | 1.2105 | 0.6769 | 0.2923 |
| rolling_20d | normal_only | 65 | -0.1472 | -3.38 | 1.2105 | 0.6769 | 0.2923 |
| rolling_20d | initial_only | 63 | -0.1595 | -3.38 | 1.16 | 0.6825 | 0.2857 |
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
| cumulative | entry_mechanical_momentum | entry | 211369 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 15 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 18369 | True | report_only_reference |
| cumulative | entry_split_order_plan | submit | 2295 | True | report_only_reference |
| cumulative | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 4176 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 175638 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 36466 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 25876 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 111 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 2560 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 2 | False | report_only_reference |
| cumulative | reversal_add | holding_exit | 105289 | False | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 17957 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 17957 | False | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 4694 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 216 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 120 | False | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2746 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 734 | True | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 734 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 1646 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 3125 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 313 | True | report_only_reference |
| rolling_5d | entry_split_order_plan | submit | 2295 | True | report_only_reference |
| rolling_5d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 88 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 5240 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 1712 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 773 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 38 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 534 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 2 | False | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 2945 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 708 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 708 | False | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 76 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 4 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 33 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 20 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 20 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 1646 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 5992 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 622 | True | report_only_reference |
| rolling_10d | entry_split_order_plan | submit | 2295 | True | report_only_reference |
| rolling_10d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 200 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 11550 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 3593 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 1638 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 71 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 1277 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 2 | False | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 5284 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 2199 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 2199 | False | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 1556 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 8 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 39 | True | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 53 | True | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 53 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 1646 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 7921 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 1032 | True | report_only_reference |
| rolling_20d | entry_split_order_plan | submit | 2295 | True | report_only_reference |
| rolling_20d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 236 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 21199 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 6727 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 2858 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 53 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 1609 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 2 | False | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 7826 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 2640 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 2640 | False | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 2038 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 10 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 53 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 65 | True | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 65 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 1646 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
