# Cumulative Threshold Cycle Report - 2026-07-13

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-07-13`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 84 | 2242814 | 534 | -0.2849 | 0.4738 | 0.4944 |
| rolling_5d | 5 | 22326 | 21 | -0.3171 | 0.5238 | 0.4762 |
| rolling_10d | 10 | 76397 | 89 | -0.4727 | 0.5618 | 0.427 |
| rolling_20d | 20 | 302399 | 237 | -0.0888 | 0.5274 | 0.4304 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 534 | -0.2849 | 0.4738 |
| cumulative | sim | 3998 | -1.2946 | 0.2416 |
| cumulative | combined | 4532 | -1.1756 | 0.269 |
| rolling_5d | real | 21 | -0.3171 | 0.5238 |
| rolling_5d | sim | 31 | -1.5552 | 0.3548 |
| rolling_5d | combined | 52 | -1.0552 | 0.4231 |
| rolling_10d | real | 89 | -0.4727 | 0.5618 |
| rolling_10d | sim | 102 | -1.8808 | 0.2941 |
| rolling_10d | combined | 191 | -1.2247 | 0.4188 |
| rolling_20d | real | 237 | -0.0888 | 0.5274 |
| rolling_20d | sim | 420 | -1.4437 | 0.269 |
| rolling_20d | combined | 657 | -0.9549 | 0.3623 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 534 | -0.2849 | -2.87 | 2.08 | 0.4738 | 0.4944 |
| cumulative | normal_only | 534 | -0.2849 | -2.87 | 2.08 | 0.4738 | 0.4944 |
| cumulative | initial_only | 465 | -0.3136 | -2.71 | 2.07 | 0.4645 | 0.5032 |
| cumulative | pyramid_activated | 28 | 0.3168 | -2.12 | 3.15 | 0.6071 | 0.3929 |
| cumulative | reversal_add_activated | 42 | -0.1945 | -4.57 | 2.55 | 0.5 | 0.4524 |
| rolling_5d | all_completed_valid | 21 | -0.3171 | -3.67 | 1.98 | 0.5238 | 0.4762 |
| rolling_5d | normal_only | 21 | -0.3171 | -3.67 | 1.98 | 0.5238 | 0.4762 |
| rolling_5d | initial_only | 18 | -0.5433 | -4.44 | 1.98 | 0.5 | 0.5 |
| rolling_5d | pyramid_activated | 1 | 0.55 | 0.55 | 0.55 | 1 | 0 |
| rolling_5d | reversal_add_activated | 2 | 1.285 | -0.23 | 2.8 | 0.5 | 0.5 |
| rolling_10d | all_completed_valid | 89 | -0.4727 | -5.16 | 2.8 | 0.5618 | 0.427 |
| rolling_10d | normal_only | 89 | -0.4727 | -5.16 | 2.8 | 0.5618 | 0.427 |
| rolling_10d | initial_only | 75 | -0.5139 | -5.3 | 3.27 | 0.5467 | 0.44 |
| rolling_10d | pyramid_activated | 2 | -0.785 | -2.12 | 0.55 | 0.5 | 0.5 |
| rolling_10d | reversal_add_activated | 12 | -0.1633 | -3.88 | 2.55 | 0.6667 | 0.3333 |
| rolling_20d | all_completed_valid | 237 | -0.0888 | -4.44 | 2.75 | 0.5274 | 0.4304 |
| rolling_20d | normal_only | 237 | -0.0888 | -4.44 | 2.75 | 0.5274 | 0.4304 |
| rolling_20d | initial_only | 193 | -0.0459 | -4.32 | 2.75 | 0.5337 | 0.4249 |
| rolling_20d | pyramid_activated | 4 | 0.645 | -2.87 | 7.02 | 0.5 | 0.5 |
| rolling_20d | reversal_add_activated | 41 | -0.1888 | -4.57 | 2.55 | 0.5122 | 0.439 |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 295241 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 101 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 18762 | True | report_only_reference |
| cumulative | entry_split_order_plan | submit | 1117 | False | report_only_reference |
| cumulative | scale_in_split_order_plan | scale_in | 1 | True | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 3719 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 180491 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 47706 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 23176 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 104 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 620 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 250363 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 105548 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 19244 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 19244 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 1863 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 187 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 115 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2760 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 534 | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 534 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 603 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 1015 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 255 | True | report_only_reference |
| rolling_5d | entry_split_order_plan | submit | 1117 | False | report_only_reference |
| rolling_5d | scale_in_split_order_plan | scale_in | 1 | True | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 141 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 879 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 40 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 115 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 11 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 0 | False | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 3493 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 1584 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 78 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 78 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 119 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 16 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 21 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 21 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 603 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 2542 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 12 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 936 | True | report_only_reference |
| rolling_10d | entry_split_order_plan | submit | 1117 | False | report_only_reference |
| rolling_10d | scale_in_split_order_plan | scale_in | 1 | True | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 445 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 3532 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 326 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 638 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 21 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 1 | False | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 13173 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 4196 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 347 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 347 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 713 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 25 | True | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 10 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 73 | True | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 89 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 89 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 603 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 5807 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 12 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 3118 | True | report_only_reference |
| rolling_20d | entry_split_order_plan | submit | 1117 | False | report_only_reference |
| rolling_20d | scale_in_split_order_plan | scale_in | 1 | True | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 1630 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 15494 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 2693 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 2838 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 35 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 82 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 58350 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 22608 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 1713 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 1713 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 988 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 30 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 38 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 894 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 237 | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 237 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 603 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
