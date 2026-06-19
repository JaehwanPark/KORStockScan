# Cumulative Threshold Cycle Report - 2026-06-19

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-06-19`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 60 | 1886452 | 296 | -0.4468 | 0.4291 | 0.5473 |
| rolling_5d | 5 | 584882 | 13 | -1.0554 | 0.2308 | 0.7692 |
| rolling_10d | 10 | 953602 | 30 | -0.3457 | 0.3667 | 0.6333 |
| rolling_20d | 20 | 1844223 | 95 | -0.4347 | 0.4632 | 0.5368 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 296 | -0.4468 | 0.4291 |
| cumulative | sim | 3308 | -1.2454 | 0.243 |
| cumulative | combined | 3604 | -1.1798 | 0.2583 |
| rolling_5d | real | 13 | -1.0554 | 0.2308 |
| rolling_5d | sim | 771 | -1.237 | 0.2192 |
| rolling_5d | combined | 784 | -1.2339 | 0.2194 |
| rolling_10d | real | 30 | -0.3457 | 0.3667 |
| rolling_10d | sim | 1763 | -1.27 | 0.2275 |
| rolling_10d | combined | 1793 | -1.2545 | 0.2298 |
| rolling_20d | real | 95 | -0.4347 | 0.4632 |
| rolling_20d | sim | 3308 | -1.2454 | 0.243 |
| rolling_20d | combined | 3403 | -1.2228 | 0.2492 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 296 | -0.4468 | -2.36 | 1.52 | 0.4291 | 0.5473 |
| cumulative | normal_only | 296 | -0.4468 | -2.36 | 1.52 | 0.4291 | 0.5473 |
| cumulative | initial_only | 271 | -0.5096 | -2.37 | 1.52 | 0.4133 | 0.5609 |
| cumulative | pyramid_activated | 24 | 0.2621 | -1.42 | 1.59 | 0.625 | 0.375 |
| cumulative | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |
| rolling_5d | all_completed_valid | 13 | -1.0554 | -3.44 | 1.34 | 0.2308 | 0.7692 |
| rolling_5d | normal_only | 13 | -1.0554 | -3.44 | 1.34 | 0.2308 | 0.7692 |
| rolling_5d | initial_only | 12 | -1.0458 | -3.44 | 1.34 | 0.25 | 0.75 |
| rolling_5d | pyramid_activated | 1 | -1.17 | -1.17 | -1.17 | 0 | 1 |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 30 | -0.3457 | -3.31 | 2.8 | 0.3667 | 0.6333 |
| rolling_10d | normal_only | 30 | -0.3457 | -3.31 | 2.8 | 0.3667 | 0.6333 |
| rolling_10d | initial_only | 27 | -0.3715 | -3.31 | 2.8 | 0.3704 | 0.6296 |
| rolling_10d | pyramid_activated | 3 | -0.1133 | -2.39 | 3.22 | 0.3333 | 0.6667 |
| rolling_10d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_20d | all_completed_valid | 95 | -0.4347 | -2.62 | 1.7 | 0.4632 | 0.5368 |
| rolling_20d | normal_only | 95 | -0.4347 | -2.62 | 1.7 | 0.4632 | 0.5368 |
| rolling_20d | initial_only | 91 | -0.4651 | -2.62 | 1.58 | 0.4615 | 0.5385 |
| rolling_20d | pyramid_activated | 4 | 0.255 | -2.39 | 3.22 | 0.5 | 0.5 |
| rolling_20d | reversal_add_activated | 0 | - | - | - | - | - |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 286429 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 89 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 25024 | True | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 1966 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 162382 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 44696 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 19672 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 69 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 535 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 185891 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 80546 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 16800 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 16800 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 838 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 157 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 77 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 1732 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 296 | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 296 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 3115 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 89126 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 3 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 7276 | True | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 808 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 50224 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 4472 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 6188 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 25 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 53 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 61840 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 27314 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 6377 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 6377 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 230 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 25 | True | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 7 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 682 | True | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 13 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 13 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 3115 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 133823 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 3 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 16110 | True | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 1657 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 72833 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 9399 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 11710 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 42 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 83 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 101555 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 46678 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 8709 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 8709 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 434 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 118 | True | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 21 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 1354 | True | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 30 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 30 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 3115 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 247401 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 5 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 24644 | True | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 1818 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 162382 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 44696 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 19672 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 69 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 196 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 185891 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 78575 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 16417 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 16417 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 838 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 157 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 77 | True | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 1732 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 95 | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 95 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 3115 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
