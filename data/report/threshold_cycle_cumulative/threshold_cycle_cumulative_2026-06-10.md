# Cumulative Threshold Cycle Report - 2026-06-10

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-06-10`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 51 | 1107940 | 277 | -0.3988 | 0.444 | 0.5307 |
| rolling_5d | 5 | 480229 | 38 | 0.0855 | 0.5526 | 0.4474 |
| rolling_10d | 10 | 1065711 | 76 | -0.2571 | 0.5263 | 0.4737 |
| rolling_20d | 20 | 1065711 | 97 | -0.2847 | 0.4948 | 0.4639 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 277 | -0.3988 | 0.444 |
| cumulative | sim | 1976 | -1.2804 | 0.2454 |
| cumulative | combined | 2253 | -1.172 | 0.2699 |
| rolling_5d | real | 38 | 0.0855 | 0.5526 |
| rolling_5d | sim | 1088 | -1.375 | 0.2298 |
| rolling_5d | combined | 1126 | -1.3257 | 0.2407 |
| rolling_10d | real | 76 | -0.2571 | 0.5263 |
| rolling_10d | sim | 1976 | -1.2804 | 0.2454 |
| rolling_10d | combined | 2052 | -1.2425 | 0.2558 |
| rolling_20d | real | 97 | -0.2847 | 0.4948 |
| rolling_20d | sim | 1976 | -1.2804 | 0.2454 |
| rolling_20d | combined | 2073 | -1.2338 | 0.2571 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 277 | -0.3988 | -2.3 | 1.58 | 0.444 | 0.5307 |
| cumulative | normal_only | 277 | -0.3988 | -2.3 | 1.58 | 0.444 | 0.5307 |
| cumulative | initial_only | 254 | -0.472 | -2.33 | 1.52 | 0.4252 | 0.5472 |
| cumulative | pyramid_activated | 22 | 0.4477 | -1.2 | 1.59 | 0.6818 | 0.3182 |
| cumulative | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |
| rolling_5d | all_completed_valid | 38 | 0.0855 | -2.51 | 3.22 | 0.5526 | 0.4474 |
| rolling_5d | normal_only | 38 | 0.0855 | -2.51 | 3.22 | 0.5526 | 0.4474 |
| rolling_5d | initial_only | 37 | 0.0008 | -2.51 | 2.8 | 0.5405 | 0.4595 |
| rolling_5d | pyramid_activated | 1 | 3.22 | 3.22 | 3.22 | 1 | 0 |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 76 | -0.2571 | -2.55 | 1.85 | 0.5263 | 0.4737 |
| rolling_10d | normal_only | 76 | -0.2571 | -2.55 | 1.85 | 0.5263 | 0.4737 |
| rolling_10d | initial_only | 74 | -0.3259 | -2.55 | 1.7 | 0.5135 | 0.4865 |
| rolling_10d | pyramid_activated | 2 | 2.29 | 1.36 | 3.22 | 1 | 0 |
| rolling_10d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_20d | all_completed_valid | 97 | -0.2847 | -2.69 | 2.2 | 0.4948 | 0.4639 |
| rolling_20d | normal_only | 97 | -0.2847 | -2.69 | 2.2 | 0.4948 | 0.4639 |
| rolling_20d | initial_only | 95 | -0.3389 | -2.69 | 2.03 | 0.4842 | 0.4737 |
| rolling_20d | pyramid_activated | 2 | 2.29 | 1.36 | 3.22 | 1 | 0 |
| rolling_20d | reversal_add_activated | 0 | - | - | - | - | - |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 174697 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 86 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 11751 | False | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 580 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 98747 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 36675 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 10367 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 39 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 475 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 103953 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 42576 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 9565 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 9565 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 474 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 39 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 65 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 602 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 277 | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 277 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 25704 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 52955 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 6118 | False | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 352 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 37251 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 9281 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 6095 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 32 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 96 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 55639 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 22731 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 3288 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 3288 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 241 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 36 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 466 | True | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 38 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 38 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 25704 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 135669 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 2 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 11371 | False | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 432 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 98747 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 36675 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 10367 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 39 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 136 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 103953 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 40605 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 9182 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 9182 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 474 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 39 | True | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 65 | True | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 602 | True | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 76 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 76 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 25704 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 135669 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 2 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 11371 | False | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 432 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 98747 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 36675 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 10367 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 39 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 136 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 103953 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 40605 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 9182 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 9182 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 474 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 39 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 65 | True | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 602 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 97 | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 97 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 25704 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
