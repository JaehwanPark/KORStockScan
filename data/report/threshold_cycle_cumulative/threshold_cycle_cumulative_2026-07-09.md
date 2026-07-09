# Cumulative Threshold Cycle Report - 2026-07-09

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-07-09`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 80 | 2227739 | 518 | -0.2812 | 0.473 | 0.4942 |
| rolling_5d | 5 | 61322 | 73 | -0.4874 | 0.5753 | 0.411 |
| rolling_10d | 10 | 187929 | 205 | -0.0347 | 0.5463 | 0.4049 |
| rolling_20d | 20 | 341287 | 222 | -0.0605 | 0.5315 | 0.4234 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 518 | -0.2812 | 0.473 |
| cumulative | sim | 3980 | -1.2944 | 0.241 |
| cumulative | combined | 4498 | -1.1777 | 0.2677 |
| rolling_5d | real | 73 | -0.4874 | 0.5753 |
| rolling_5d | sim | 84 | -1.9979 | 0.2738 |
| rolling_5d | combined | 157 | -1.2955 | 0.414 |
| rolling_10d | real | 205 | -0.0347 | 0.5463 |
| rolling_10d | sim | 161 | -1.634 | 0.3478 |
| rolling_10d | combined | 366 | -0.7383 | 0.459 |
| rolling_20d | real | 222 | -0.0605 | 0.5315 |
| rolling_20d | sim | 672 | -1.5357 | 0.2307 |
| rolling_20d | combined | 894 | -1.1694 | 0.3054 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 518 | -0.2812 | -2.77 | 2.09 | 0.473 | 0.4942 |
| cumulative | normal_only | 518 | -0.2812 | -2.77 | 2.09 | 0.473 | 0.4942 |
| cumulative | initial_only | 451 | -0.3016 | -2.69 | 2.08 | 0.4656 | 0.5011 |
| cumulative | pyramid_activated | 27 | 0.3081 | -2.12 | 3.15 | 0.5926 | 0.4074 |
| cumulative | reversal_add_activated | 41 | -0.2676 | -4.57 | 2.18 | 0.4878 | 0.4634 |
| rolling_5d | all_completed_valid | 73 | -0.4874 | -5.3 | 3.27 | 0.5753 | 0.411 |
| rolling_5d | normal_only | 73 | -0.4874 | -5.3 | 3.27 | 0.5753 | 0.411 |
| rolling_5d | initial_only | 61 | -0.4705 | -5.32 | 3.31 | 0.5738 | 0.4098 |
| rolling_5d | pyramid_activated | 1 | -2.12 | -2.12 | -2.12 | 0 | 1 |
| rolling_5d | reversal_add_activated | 11 | -0.4327 | -3.88 | 1.48 | 0.6364 | 0.3636 |
| rolling_10d | all_completed_valid | 205 | -0.0347 | -4.56 | 2.93 | 0.5463 | 0.4049 |
| rolling_10d | normal_only | 205 | -0.0347 | -4.56 | 2.93 | 0.5463 | 0.4049 |
| rolling_10d | initial_only | 164 | 0.0407 | -4.52 | 2.94 | 0.561 | 0.3902 |
| rolling_10d | pyramid_activated | 3 | 0.6767 | -2.87 | 7.02 | 0.3333 | 0.6667 |
| rolling_10d | reversal_add_activated | 39 | -0.2256 | -4.6 | 2.55 | 0.5128 | 0.4359 |
| rolling_20d | all_completed_valid | 222 | -0.0605 | -4.48 | 2.75 | 0.5315 | 0.4234 |
| rolling_20d | normal_only | 222 | -0.0605 | -4.48 | 2.75 | 0.5315 | 0.4234 |
| rolling_20d | initial_only | 180 | 0.0117 | -4.48 | 2.93 | 0.5444 | 0.4111 |
| rolling_20d | pyramid_activated | 3 | 0.6767 | -2.87 | 7.02 | 0.3333 | 0.6667 |
| rolling_20d | reversal_add_activated | 40 | -0.2635 | -4.6 | 2.18 | 0.5 | 0.45 |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 294646 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 101 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 18585 | True | report_only_reference |
| cumulative | entry_split_order_plan | submit | 2020 | True | report_only_reference |
| cumulative | scale_in_split_order_plan | scale_in | 4 | True | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 3647 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 179737 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 47675 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 23087 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 99 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 620 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 247871 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 104527 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 19189 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 19189 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 1750 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 187 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 115 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2748 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 518 | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 518 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 1244 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 1947 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 12 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 759 | True | report_only_reference |
| rolling_5d | entry_split_order_plan | submit | 2020 | True | report_only_reference |
| rolling_5d | scale_in_split_order_plan | scale_in | 4 | True | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 373 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 2778 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 295 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 549 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 16 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 1 | False | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 10681 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 3175 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 292 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 292 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 600 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 25 | True | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 10 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 61 | True | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 73 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 73 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 1244 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 4943 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 12 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 1907 | True | report_only_reference |
| rolling_10d | entry_split_order_plan | submit | 2020 | True | report_only_reference |
| rolling_10d | scale_in_split_order_plan | scale_in | 4 | True | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 1288 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 7777 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 1007 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 1014 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 30 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 64 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 41233 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 15933 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 961 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 961 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 838 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 30 | True | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 36 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 709 | True | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 205 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 205 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 1244 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 8217 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 12 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 4220 | True | report_only_reference |
| rolling_20d | entry_split_order_plan | submit | 2020 | True | report_only_reference |
| rolling_20d | scale_in_split_order_plan | scale_in | 4 | True | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 1681 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 17355 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 2979 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 3415 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 30 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 85 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 61980 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 23981 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 2389 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 2389 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 912 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 30 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 38 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 1016 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 222 | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 222 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 1244 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
