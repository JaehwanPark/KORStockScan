# Cumulative Threshold Cycle Report - 2026-07-28

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-07-28`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 99 | 1845230 | 630 | -0.2739 | 0.4746 | 0.4889 |
| rolling_5d | 5 | 7193 | 16 | -0.1944 | 0.625 | 0.375 |
| rolling_10d | 10 | 37083 | 72 | -0.1867 | 0.5417 | 0.4028 |
| rolling_20d | 20 | 83236 | 115 | -0.2315 | 0.4957 | 0.4522 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 630 | -0.2739 | 0.4746 |
| cumulative | sim | 3321 | -1.3206 | 0.2337 |
| cumulative | combined | 3951 | -1.1537 | 0.2721 |
| rolling_5d | real | 16 | -0.1944 | 0.625 |
| rolling_5d | sim | 3 | -0.23 | 0 |
| rolling_5d | combined | 19 | -0.2 | 0.5263 |
| rolling_10d | real | 72 | -0.1867 | 0.5417 |
| rolling_10d | sim | 16 | -0.9475 | 0.125 |
| rolling_10d | combined | 88 | -0.325 | 0.4659 |
| rolling_20d | real | 115 | -0.2315 | 0.4957 |
| rolling_20d | sim | 60 | -1.2345 | 0.3 |
| rolling_20d | combined | 175 | -0.5754 | 0.4286 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 630 | -0.2739 | -3.14 | 1.89 | 0.4746 | 0.4889 |
| cumulative | normal_only | 630 | -0.2739 | -3.14 | 1.89 | 0.4746 | 0.4889 |
| cumulative | initial_only | 551 | -0.2912 | -2.73 | 1.89 | 0.4682 | 0.4936 |
| cumulative | pyramid_activated | 31 | 0.3365 | -1.45 | 1.59 | 0.6452 | 0.3548 |
| cumulative | reversal_add_activated | 49 | -0.3171 | -4.57 | 2.55 | 0.449 | 0.5102 |
| rolling_5d | all_completed_valid | 16 | -0.1944 | -3.56 | 1.48 | 0.625 | 0.375 |
| rolling_5d | normal_only | 16 | -0.1944 | -3.56 | 1.48 | 0.625 | 0.375 |
| rolling_5d | initial_only | 16 | -0.1944 | -3.56 | 1.48 | 0.625 | 0.375 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 72 | -0.1867 | -3.29 | 1.41 | 0.5417 | 0.4028 |
| rolling_10d | normal_only | 72 | -0.1867 | -3.29 | 1.41 | 0.5417 | 0.4028 |
| rolling_10d | initial_only | 69 | -0.1409 | -3.29 | 1.44 | 0.5507 | 0.3913 |
| rolling_10d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_10d | reversal_add_activated | 3 | -1.24 | -3.68 | 0.19 | 0.3333 | 0.6667 |
| rolling_20d | all_completed_valid | 115 | -0.2315 | -3.56 | 1.43 | 0.4957 | 0.4522 |
| rolling_20d | normal_only | 115 | -0.2315 | -3.56 | 1.43 | 0.4957 | 0.4522 |
| rolling_20d | initial_only | 103 | -0.2346 | -3.56 | 1.43 | 0.4951 | 0.4466 |
| rolling_20d | pyramid_activated | 4 | 0.5275 | 0.13 | 0.93 | 1 | 0 |
| rolling_20d | reversal_add_activated | 8 | -0.5713 | -3.68 | 2.8 | 0.25 | 0.75 |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 204993 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 15 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 16749 | False | report_only_reference |
| cumulative | entry_split_order_plan | submit | 103 | True | report_only_reference |
| cumulative | scale_in_split_order_plan | scale_in | 1 | True | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 3835 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 137089 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 24351 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 20656 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 95 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 324 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 226539 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 95481 | False | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 15066 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 15066 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 2213 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 216 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 101 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2696 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 630 | True | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 630 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 83 | False | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 443 | False | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 15 | False | report_only_reference |
| rolling_5d | entry_split_order_plan | submit | 103 | True | report_only_reference |
| rolling_5d | scale_in_split_order_plan | scale_in | 1 | True | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 33 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 20 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 0 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 1 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 0 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 53 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 646 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 124 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 263 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 263 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 93 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 5 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 0 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 16 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 16 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 83 | False | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 1478 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 182 | False | report_only_reference |
| rolling_10d | entry_split_order_plan | submit | 103 | True | report_only_reference |
| rolling_10d | scale_in_split_order_plan | scale_in | 1 | True | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 264 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 460 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 4 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 23 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 3 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 82 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 6999 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 2649 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 315 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 315 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 530 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 10 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 16 | False | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 72 | True | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 72 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 83 | False | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 2856 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 605 | False | report_only_reference |
| rolling_20d | entry_split_order_plan | submit | 103 | True | report_only_reference |
| rolling_20d | scale_in_split_order_plan | scale_in | 1 | True | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 481 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 2178 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 61 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 268 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 15 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 83 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 15733 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 6593 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 523 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 523 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 667 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 68 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 13 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 48 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 115 | True | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 115 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 83 | False | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
