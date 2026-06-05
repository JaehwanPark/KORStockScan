# Cumulative Threshold Cycle Report - 2026-06-05

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-06-05`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 46 | 627711 | 239 | -0.4759 | 0.4268 | 0.5439 |
| rolling_5d | 5 | 585482 | 38 | -0.5997 | 0.5 | 0.5 |
| rolling_10d | 10 | 585482 | 52 | -0.5317 | 0.4423 | 0.4808 |
| rolling_20d | 20 | 585482 | 62 | -0.4318 | 0.4677 | 0.4677 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 239 | -0.4759 | 0.4268 |
| cumulative | sim | 888 | -1.1644 | 0.2646 |
| cumulative | combined | 1127 | -1.0184 | 0.299 |
| rolling_5d | real | 38 | -0.5997 | 0.5 |
| rolling_5d | sim | 888 | -1.1644 | 0.2646 |
| rolling_5d | combined | 926 | -1.1413 | 0.2743 |
| rolling_10d | real | 52 | -0.5317 | 0.4423 |
| rolling_10d | sim | 888 | -1.1644 | 0.2646 |
| rolling_10d | combined | 940 | -1.1294 | 0.2745 |
| rolling_20d | real | 62 | -0.4318 | 0.4677 |
| rolling_20d | sim | 888 | -1.1644 | 0.2646 |
| rolling_20d | combined | 950 | -1.1166 | 0.2779 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 239 | -0.4759 | -2.3 | 1.47 | 0.4268 | 0.5439 |
| cumulative | normal_only | 239 | -0.4759 | -2.3 | 1.47 | 0.4268 | 0.5439 |
| cumulative | initial_only | 217 | -0.5527 | -2.33 | 1.47 | 0.4055 | 0.5622 |
| cumulative | pyramid_activated | 21 | 0.3157 | -1.2 | 1.36 | 0.6667 | 0.3333 |
| cumulative | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |
| rolling_5d | all_completed_valid | 38 | -0.5997 | -2.7 | 1.52 | 0.5 | 0.5 |
| rolling_5d | normal_only | 38 | -0.5997 | -2.7 | 1.52 | 0.5 | 0.5 |
| rolling_5d | initial_only | 37 | -0.6527 | -2.7 | 1.52 | 0.4865 | 0.5135 |
| rolling_5d | pyramid_activated | 1 | 1.36 | 1.36 | 1.36 | 1 | 0 |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 52 | -0.5317 | -2.7 | 1.58 | 0.4423 | 0.4808 |
| rolling_10d | normal_only | 52 | -0.5317 | -2.7 | 1.58 | 0.4423 | 0.4808 |
| rolling_10d | initial_only | 51 | -0.5688 | -2.7 | 1.58 | 0.4314 | 0.4902 |
| rolling_10d | pyramid_activated | 1 | 1.36 | 1.36 | 1.36 | 1 | 0 |
| rolling_10d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_20d | all_completed_valid | 62 | -0.4318 | -2.7 | 1.7 | 0.4677 | 0.4677 |
| rolling_20d | normal_only | 62 | -0.4318 | -2.7 | 1.7 | 0.4677 | 0.4677 |
| rolling_20d | initial_only | 61 | -0.4611 | -2.7 | 1.7 | 0.459 | 0.4754 |
| rolling_20d | pyramid_activated | 1 | 1.36 | 1.36 | 1.36 | 1 | 0 |
| rolling_20d | reversal_add_activated | 0 | - | - | - | - | - |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 121742 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 86 | True | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 61496 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 27394 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 4272 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 24 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 379 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 48314 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 19845 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 6277 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 6277 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 233 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 39 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 29 | False | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 136 | True | report_only_reference |
| cumulative | position_sizing_cap_release | position_sizing | 239 | False | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 239 | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 239 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 13164 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 82714 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 2 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 61496 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 27394 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 4272 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 24 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 40 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 48314 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 17874 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 5894 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 5894 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 233 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 39 | True | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 29 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 136 | True | report_only_reference |
| rolling_5d | position_sizing_cap_release | position_sizing | 38 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 38 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 38 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 13164 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 82714 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 2 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 61496 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 27394 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 4272 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 24 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 40 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 48314 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 17874 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 5894 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 5894 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 233 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 39 | True | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 29 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 136 | True | report_only_reference |
| rolling_10d | position_sizing_cap_release | position_sizing | 52 | False | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 52 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 52 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 13164 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 82714 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 2 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 61496 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 27394 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 4272 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 24 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 40 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 48314 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 17874 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 5894 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 5894 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 233 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 39 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 29 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 136 | True | report_only_reference |
| rolling_20d | position_sizing_cap_release | position_sizing | 62 | False | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 62 | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 62 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 13164 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
