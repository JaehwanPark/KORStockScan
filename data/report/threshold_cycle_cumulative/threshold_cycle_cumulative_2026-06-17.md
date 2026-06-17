# Cumulative Threshold Cycle Report - 2026-06-17

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-06-17`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 58 | 1748746 | 285 | -0.4199 | 0.4351 | 0.5404 |
| rolling_5d | 5 | 448821 | 2 | -0.58 | 0 | 1 |
| rolling_10d | 10 | 1121035 | 46 | -0.1293 | 0.4783 | 0.5217 |
| rolling_20d | 20 | 1706517 | 87 | -0.3708 | 0.4828 | 0.5172 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 285 | -0.4199 | 0.4351 |
| cumulative | sim | 3021 | -1.242 | 0.244 |
| cumulative | combined | 3306 | -1.1711 | 0.2604 |
| rolling_5d | real | 2 | -0.58 | 0 |
| rolling_5d | sim | 484 | -1.2108 | 0.2107 |
| rolling_5d | combined | 486 | -1.2082 | 0.2099 |
| rolling_10d | real | 46 | -0.1293 | 0.4783 |
| rolling_10d | sim | 2133 | -1.2743 | 0.2353 |
| rolling_10d | combined | 2179 | -1.2501 | 0.2405 |
| rolling_20d | real | 87 | -0.3708 | 0.4828 |
| rolling_20d | sim | 3021 | -1.242 | 0.244 |
| rolling_20d | combined | 3108 | -1.2176 | 0.2506 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 285 | -0.4199 | -2.32 | 1.58 | 0.4351 | 0.5404 |
| cumulative | normal_only | 285 | -0.4199 | -2.32 | 1.58 | 0.4351 | 0.5404 |
| cumulative | initial_only | 261 | -0.4855 | -2.33 | 1.52 | 0.4176 | 0.5556 |
| cumulative | pyramid_activated | 23 | 0.3243 | -1.42 | 1.59 | 0.6522 | 0.3478 |
| cumulative | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |
| rolling_5d | all_completed_valid | 2 | -0.58 | -0.93 | -0.23 | 0 | 1 |
| rolling_5d | normal_only | 2 | -0.58 | -0.93 | -0.23 | 0 | 1 |
| rolling_5d | initial_only | 2 | -0.58 | -0.93 | -0.23 | 0 | 1 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 46 | -0.1293 | -2.51 | 3.22 | 0.4783 | 0.5217 |
| rolling_10d | normal_only | 46 | -0.1293 | -2.51 | 3.22 | 0.4783 | 0.5217 |
| rolling_10d | initial_only | 44 | -0.1541 | -2.51 | 2.8 | 0.4773 | 0.5227 |
| rolling_10d | pyramid_activated | 2 | 0.415 | -2.39 | 3.22 | 0.5 | 0.5 |
| rolling_10d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_20d | all_completed_valid | 87 | -0.3708 | -2.67 | 2.03 | 0.4828 | 0.5172 |
| rolling_20d | normal_only | 87 | -0.3708 | -2.67 | 2.03 | 0.4828 | 0.5172 |
| rolling_20d | initial_only | 84 | -0.4101 | -2.67 | 1.85 | 0.4762 | 0.5238 |
| rolling_20d | pyramid_activated | 3 | 0.73 | -2.39 | 3.22 | 0.6667 | 0.3333 |
| rolling_20d | reversal_add_activated | 0 | - | - | - | - | - |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 280511 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 89 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 21817 | True | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 1421 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 142364 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 43140 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 17788 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 62 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 532 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 168930 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 73463 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 14885 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 14885 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 696 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 134 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 70 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 1559 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 285 | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 285 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 23836 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 83249 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 3 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 4151 | True | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 345 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 30206 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 2916 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 4304 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 18 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 50 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 45043 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 20231 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 4462 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 4462 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 88 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 43 | True | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 673 | True | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 2 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 2 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 23836 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 158769 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 3 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 16184 | True | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 1193 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 80868 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 15746 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 13516 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 38 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 153 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 120616 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 53618 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 8608 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 8608 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 463 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 95 | True | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 41 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 1423 | True | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 46 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 46 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 23836 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 241483 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 5 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 21437 | True | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 1273 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 142364 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 43140 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 17788 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 62 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 193 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 168930 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 71492 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 14502 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 14502 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 696 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 134 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 70 | True | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 1559 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 87 | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 87 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 23836 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
