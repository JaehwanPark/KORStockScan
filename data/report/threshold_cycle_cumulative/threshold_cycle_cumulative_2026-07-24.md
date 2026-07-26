# Cumulative Threshold Cycle Report - 2026-07-24

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-07-24`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 95 | 2299317 | 616 | -0.2739 | 0.4724 | 0.4903 |
| rolling_5d | 5 | 32675 | 58 | -0.165 | 0.5345 | 0.3966 |
| rolling_10d | 10 | 50632 | 73 | -0.1784 | 0.4795 | 0.4384 |
| rolling_20d | 20 | 132900 | 169 | -0.3441 | 0.5207 | 0.4379 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 616 | -0.2739 | 0.4724 |
| cumulative | sim | 4025 | -1.2922 | 0.2417 |
| cumulative | combined | 4641 | -1.157 | 0.2724 |
| rolling_5d | real | 58 | -0.165 | 0.5345 |
| rolling_5d | sim | 14 | -1.05 | 0.1429 |
| rolling_5d | combined | 72 | -0.3371 | 0.4583 |
| rolling_10d | real | 73 | -0.1784 | 0.4795 |
| rolling_10d | sim | 26 | -0.9281 | 0.2692 |
| rolling_10d | combined | 99 | -0.3753 | 0.4242 |
| rolling_20d | real | 169 | -0.3441 | 0.5207 |
| rolling_20d | sim | 129 | -1.684 | 0.2868 |
| rolling_20d | combined | 298 | -0.9242 | 0.4195 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 616 | -0.2739 | -2.96 | 1.93 | 0.4724 | 0.4903 |
| cumulative | normal_only | 616 | -0.2739 | -2.96 | 1.93 | 0.4724 | 0.4903 |
| cumulative | initial_only | 537 | -0.2916 | -2.71 | 1.93 | 0.4655 | 0.4953 |
| cumulative | pyramid_activated | 31 | 0.3365 | -1.45 | 1.59 | 0.6452 | 0.3548 |
| cumulative | reversal_add_activated | 49 | -0.3171 | -4.57 | 2.55 | 0.449 | 0.5102 |
| rolling_5d | all_completed_valid | 58 | -0.165 | -3.29 | 1.41 | 0.5345 | 0.3966 |
| rolling_5d | normal_only | 58 | -0.165 | -3.29 | 1.41 | 0.5345 | 0.3966 |
| rolling_5d | initial_only | 55 | -0.1064 | -3.26 | 1.41 | 0.5455 | 0.3818 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 3 | -1.24 | -3.68 | 0.19 | 0.3333 | 0.6667 |
| rolling_10d | all_completed_valid | 73 | -0.1784 | -3.18 | 1.22 | 0.4795 | 0.4384 |
| rolling_10d | normal_only | 73 | -0.1784 | -3.18 | 1.22 | 0.4795 | 0.4384 |
| rolling_10d | initial_only | 65 | -0.118 | -3.18 | 1.24 | 0.4769 | 0.4308 |
| rolling_10d | pyramid_activated | 3 | 0.52 | 0.13 | 0.93 | 1 | 0 |
| rolling_10d | reversal_add_activated | 5 | -1.382 | -3.68 | 0.19 | 0.2 | 0.8 |
| rolling_20d | all_completed_valid | 169 | -0.3441 | -3.88 | 1.89 | 0.5207 | 0.4379 |
| rolling_20d | normal_only | 169 | -0.3441 | -3.88 | 1.89 | 0.5207 | 0.4379 |
| rolling_20d | initial_only | 146 | -0.336 | -3.9 | 1.89 | 0.5137 | 0.4384 |
| rolling_20d | pyramid_activated | 5 | -0.002 | -2.12 | 0.93 | 0.8 | 0.2 |
| rolling_20d | reversal_add_activated | 18 | -0.5056 | -3.88 | 2.55 | 0.5 | 0.5 |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 296876 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 101 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 19098 | False | report_only_reference |
| cumulative | entry_split_order_plan | submit | 25 | False | report_only_reference |
| cumulative | scale_in_split_order_plan | scale_in | 1 | True | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 4029 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 181775 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 47727 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 23329 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 107 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 650 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 262181 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 110492 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 19537 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 19537 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 2321 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 255 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 123 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2792 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 616 | True | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 616 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 183 | False | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 1272 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 168 | False | report_only_reference |
| rolling_5d | entry_split_order_plan | submit | 25 | False | report_only_reference |
| rolling_5d | scale_in_split_order_plan | scale_in | 1 | True | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 234 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 445 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 4 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 23 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 3 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 29 | False | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 6577 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 2584 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 163 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 163 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 440 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 5 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 16 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 58 | True | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 58 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 183 | False | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 1479 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 264 | False | report_only_reference |
| rolling_10d | entry_split_order_plan | submit | 25 | False | report_only_reference |
| rolling_10d | scale_in_split_order_plan | scale_in | 1 | True | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 286 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 1135 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 20 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 122 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 10 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 29 | False | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 10325 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 4501 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 292 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 292 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 456 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 68 | True | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 8 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 32 | False | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 73 | True | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 73 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 183 | False | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 4177 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 12 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 1272 | False | report_only_reference |
| rolling_20d | entry_split_order_plan | submit | 25 | False | report_only_reference |
| rolling_20d | scale_in_split_order_plan | scale_in | 1 | True | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 755 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 4816 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 347 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 791 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 24 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 31 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 24991 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 9140 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 640 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 640 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 1171 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 93 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 18 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 105 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 169 | True | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 169 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 183 | False | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
