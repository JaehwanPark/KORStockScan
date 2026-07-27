# Cumulative Threshold Cycle Report - 2026-07-27

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-07-27`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 98 | 2301098 | 618 | -0.2722 | 0.4725 | 0.4903 |
| rolling_5d | 5 | 10326 | 17 | -0.1976 | 0.5882 | 0.3529 |
| rolling_10d | 10 | 34457 | 60 | -0.1508 | 0.5333 | 0.4 |
| rolling_20d | 20 | 98407 | 123 | -0.4615 | 0.4715 | 0.4797 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 618 | -0.2722 | 0.4725 |
| cumulative | sim | 4026 | -1.2919 | 0.2417 |
| cumulative | combined | 4644 | -1.1562 | 0.2724 |
| rolling_5d | real | 17 | -0.1976 | 0.5882 |
| rolling_5d | sim | 3 | -0.23 | 0 |
| rolling_5d | combined | 20 | -0.2025 | 0.5 |
| rolling_10d | real | 60 | -0.1508 | 0.5333 |
| rolling_10d | sim | 15 | -0.9953 | 0.1333 |
| rolling_10d | combined | 75 | -0.3197 | 0.4533 |
| rolling_20d | real | 123 | -0.4615 | 0.4715 |
| rolling_20d | sim | 89 | -1.6435 | 0.2921 |
| rolling_20d | combined | 212 | -0.9577 | 0.3962 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 618 | -0.2722 | -2.96 | 1.93 | 0.4725 | 0.4903 |
| cumulative | normal_only | 618 | -0.2722 | -2.96 | 1.93 | 0.4725 | 0.4903 |
| cumulative | initial_only | 539 | -0.2895 | -2.71 | 1.93 | 0.4657 | 0.4954 |
| cumulative | pyramid_activated | 31 | 0.3365 | -1.45 | 1.59 | 0.6452 | 0.3548 |
| cumulative | reversal_add_activated | 49 | -0.3171 | -4.57 | 2.55 | 0.449 | 0.5102 |
| rolling_5d | all_completed_valid | 17 | -0.1976 | -1.79 | 0.63 | 0.5882 | 0.3529 |
| rolling_5d | normal_only | 17 | -0.1976 | -1.79 | 0.63 | 0.5882 | 0.3529 |
| rolling_5d | initial_only | 15 | 0.0087 | -1.22 | 0.63 | 0.6 | 0.3333 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 2 | -1.745 | -3.68 | 0.19 | 0.5 | 0.5 |
| rolling_10d | all_completed_valid | 60 | -0.1508 | -3.29 | 1.24 | 0.5333 | 0.4 |
| rolling_10d | normal_only | 60 | -0.1508 | -3.29 | 1.24 | 0.5333 | 0.4 |
| rolling_10d | initial_only | 57 | -0.0935 | -3.26 | 1.41 | 0.5439 | 0.386 |
| rolling_10d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_10d | reversal_add_activated | 3 | -1.24 | -3.68 | 0.19 | 0.3333 | 0.6667 |
| rolling_20d | all_completed_valid | 123 | -0.4615 | -3.83 | 1.43 | 0.4715 | 0.4797 |
| rolling_20d | normal_only | 123 | -0.4615 | -3.83 | 1.43 | 0.4715 | 0.4797 |
| rolling_20d | initial_only | 108 | -0.4865 | -3.86 | 1.43 | 0.463 | 0.4815 |
| rolling_20d | pyramid_activated | 4 | 0.5275 | 0.13 | 0.93 | 1 | 0 |
| rolling_20d | reversal_add_activated | 11 | -0.5764 | -3.68 | 1.48 | 0.3636 | 0.6364 |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 297026 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 101 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 19100 | False | report_only_reference |
| cumulative | entry_split_order_plan | submit | 26 | False | report_only_reference |
| cumulative | scale_in_split_order_plan | scale_in | 1 | True | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 4033 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 181790 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 47727 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 23329 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 107 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 650 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 262276 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 110494 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 19543 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 19543 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 2322 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 255 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 124 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2792 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 618 | True | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 618 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 168 | False | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 589 | False | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 51 | False | report_only_reference |
| rolling_5d | entry_split_order_plan | submit | 26 | False | report_only_reference |
| rolling_5d | scale_in_split_order_plan | scale_in | 1 | True | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 33 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 188 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 0 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 7 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 1 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 14 | False | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 1405 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 372 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 127 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 127 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 202 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 4 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 2 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 17 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 17 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 168 | False | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 1422 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 170 | False | report_only_reference |
| rolling_10d | entry_split_order_plan | submit | 26 | False | report_only_reference |
| rolling_10d | scale_in_split_order_plan | scale_in | 1 | True | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 238 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 460 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 4 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 23 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 3 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 29 | False | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 6672 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 2586 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 169 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 169 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 441 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 6 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 16 | False | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 60 | True | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 60 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 168 | False | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 3294 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 12 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 838 | False | report_only_reference |
| rolling_20d | entry_split_order_plan | submit | 26 | False | report_only_reference |
| rolling_20d | scale_in_split_order_plan | scale_in | 1 | True | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 551 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 3150 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 105 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 474 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 19 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 30 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 18385 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 7143 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 497 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 497 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 807 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 68 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 14 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 73 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 123 | True | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 123 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 168 | False | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
