# Cumulative Threshold Cycle Report - 2026-07-31

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-07-31`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 102 | 1854504 | 642 | -0.2836 | 0.4782 | 0.486 |
| rolling_5d | 5 | 37230 | 26 | -0.5131 | 0.6154 | 0.3846 |
| rolling_10d | 10 | 55347 | 59 | -0.4268 | 0.5593 | 0.4068 |
| rolling_20d | 20 | 98325 | 109 | -0.2946 | 0.5046 | 0.4404 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 642 | -0.2836 | 0.4782 |
| cumulative | sim | 3300 | -1.3228 | 0.2342 |
| cumulative | combined | 3942 | -1.1535 | 0.274 |
| rolling_5d | real | 26 | -0.5131 | 0.6154 |
| rolling_5d | sim | 12 | -0.8725 | 0.1667 |
| rolling_5d | combined | 38 | -0.6266 | 0.4737 |
| rolling_10d | real | 59 | -0.4268 | 0.5593 |
| rolling_10d | sim | 21 | -1.0457 | 0.0952 |
| rolling_10d | combined | 80 | -0.5893 | 0.4375 |
| rolling_20d | real | 109 | -0.2946 | 0.5046 |
| rolling_20d | sim | 49 | -1.1816 | 0.2245 |
| rolling_20d | combined | 158 | -0.5697 | 0.4177 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 642 | -0.2836 | -3.15 | 1.86 | 0.4782 | 0.486 |
| cumulative | normal_only | 642 | -0.2836 | -3.15 | 1.86 | 0.4782 | 0.486 |
| cumulative | initial_only | 563 | -0.3018 | -2.78 | 1.85 | 0.4725 | 0.4902 |
| cumulative | pyramid_activated | 31 | 0.3365 | -1.45 | 1.59 | 0.6452 | 0.3548 |
| cumulative | reversal_add_activated | 49 | -0.3171 | -4.57 | 2.55 | 0.449 | 0.5102 |
| rolling_5d | all_completed_valid | 26 | -0.5131 | -3.71 | 1.37 | 0.6154 | 0.3846 |
| rolling_5d | normal_only | 26 | -0.5131 | -3.71 | 1.37 | 0.6154 | 0.3846 |
| rolling_5d | initial_only | 26 | -0.5131 | -3.71 | 1.37 | 0.6154 | 0.3846 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 59 | -0.4268 | -3.68 | 1.1 | 0.5593 | 0.4068 |
| rolling_10d | normal_only | 59 | -0.4268 | -3.68 | 1.1 | 0.5593 | 0.4068 |
| rolling_10d | initial_only | 56 | -0.3832 | -3.67 | 1.1 | 0.5714 | 0.3929 |
| rolling_10d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_10d | reversal_add_activated | 3 | -1.24 | -3.68 | 0.19 | 0.3333 | 0.6667 |
| rolling_20d | all_completed_valid | 109 | -0.2946 | -3.56 | 1.22 | 0.5046 | 0.4404 |
| rolling_20d | normal_only | 109 | -0.2946 | -3.56 | 1.22 | 0.5046 | 0.4404 |
| rolling_20d | initial_only | 100 | -0.2653 | -3.56 | 1.22 | 0.51 | 0.43 |
| rolling_20d | pyramid_activated | 3 | 0.52 | 0.13 | 0.93 | 1 | 0 |
| rolling_20d | reversal_add_activated | 6 | -1.19 | -3.68 | 0.19 | 0.1667 | 0.8333 |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 201047 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 15 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 16872 | True | report_only_reference |
| cumulative | entry_split_order_plan | submit | 748 | True | report_only_reference |
| cumulative | scale_in_split_order_plan | scale_in | 1 | True | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 3876 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 138257 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 25248 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 20879 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 95 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 458 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 226264 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 95517 | False | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 15014 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 15014 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 2223 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 216 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 103 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2689 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 642 | True | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 642 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 1169 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 787 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 171 | True | report_only_reference |
| rolling_5d | entry_split_order_plan | submit | 748 | True | report_only_reference |
| rolling_5d | scale_in_split_order_plan | scale_in | 1 | True | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 74 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 2852 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 1721 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 316 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 0 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 187 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 2260 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 795 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 334 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 334 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 102 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 8 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 5 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 26 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 26 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 1169 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 1503 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 291 | True | report_only_reference |
| rolling_10d | entry_split_order_plan | submit | 748 | True | report_only_reference |
| rolling_10d | scale_in_split_order_plan | scale_in | 1 | True | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 178 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 3252 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 1721 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 328 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 2 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 213 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 5471 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 2084 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 476 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 476 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 522 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 13 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 9 | False | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 59 | True | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 59 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 1169 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 2692 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 554 | True | report_only_reference |
| rolling_20d | entry_split_order_plan | submit | 748 | True | report_only_reference |
| rolling_20d | scale_in_split_order_plan | scale_in | 1 | True | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 392 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 4418 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 1742 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 504 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 10 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 217 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 14763 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 5739 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 680 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 680 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 664 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 68 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 16 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 38 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 109 | True | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 109 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 1169 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
