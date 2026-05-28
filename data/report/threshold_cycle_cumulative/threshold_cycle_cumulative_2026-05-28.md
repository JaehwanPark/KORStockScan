# Cumulative Threshold Cycle Report - 2026-05-28

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-05-28`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 38 | 1247017 | 197 | -0.4317 | 0.4162 | 0.5482 |
| rolling_5d | 5 | 515771 | 17 | -0.1282 | 0.4118 | 0.3529 |
| rolling_10d | 10 | 1145258 | 20 | 0.096 | 0.45 | 0.35 |
| rolling_20d | 20 | 1155954 | 21 | 0.0176 | 0.4286 | 0.381 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 197 | -0.4317 | 0.4162 |
| cumulative | sim | 1176 | -0.636 | 0.3503 |
| cumulative | combined | 1373 | -0.6067 | 0.3598 |
| rolling_5d | real | 17 | -0.1282 | 0.4118 |
| rolling_5d | sim | 534 | -0.9769 | 0.3333 |
| rolling_5d | combined | 551 | -0.9507 | 0.3358 |
| rolling_10d | real | 20 | 0.096 | 0.45 |
| rolling_10d | sim | 1161 | -0.6716 | 0.348 |
| rolling_10d | combined | 1181 | -0.6586 | 0.3497 |
| rolling_20d | real | 21 | 0.0176 | 0.4286 |
| rolling_20d | sim | 1176 | -0.636 | 0.3503 |
| rolling_20d | combined | 1197 | -0.6246 | 0.3517 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 197 | -0.4317 | -2.03 | 1.41 | 0.4162 | 0.5482 |
| cumulative | normal_only | 197 | -0.4317 | -2.03 | 1.41 | 0.4162 | 0.5482 |
| cumulative | initial_only | 176 | -0.5107 | -2.08 | 1.41 | 0.392 | 0.5682 |
| cumulative | pyramid_activated | 20 | 0.2635 | -1.42 | 1.18 | 0.65 | 0.35 |
| cumulative | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |
| rolling_5d | all_completed_valid | 17 | -0.1282 | -2.71 | 2.75 | 0.4118 | 0.3529 |
| rolling_5d | normal_only | 17 | -0.1282 | -2.71 | 2.75 | 0.4118 | 0.3529 |
| rolling_5d | initial_only | 17 | -0.1282 | -2.71 | 2.75 | 0.4118 | 0.3529 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 20 | 0.096 | -2.71 | 2.75 | 0.45 | 0.35 |
| rolling_10d | normal_only | 20 | 0.096 | -2.71 | 2.75 | 0.45 | 0.35 |
| rolling_10d | initial_only | 20 | 0.096 | -2.71 | 2.75 | 0.45 | 0.35 |
| rolling_10d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_10d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_20d | all_completed_valid | 21 | 0.0176 | -2.69 | 2.75 | 0.4286 | 0.381 |
| rolling_20d | normal_only | 21 | 0.0176 | -2.69 | 2.75 | 0.4286 | 0.381 |
| rolling_20d | initial_only | 21 | 0.0176 | -2.69 | 2.75 | 0.4286 | 0.381 |
| rolling_20d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_20d | reversal_add_activated | 0 | - | - | - | - | - |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 122436 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 84 | True | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 257149 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 122284 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 8785 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 121 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 791 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 103223 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 44013 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 11808 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 11808 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 414 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 857 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 14 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 1162 | True | report_only_reference |
| cumulative | position_sizing_cap_release | position_sizing | 197 | False | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 197 | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 197 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 24465 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 55278 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 57122 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 31083 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 3691 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 2 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 39 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 47180 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 18335 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 4299 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 4299 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 169 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 23 | True | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 11 | True | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 254 | True | report_only_reference |
| rolling_5d | position_sizing_cap_release | position_sizing | 17 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 17 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 17 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 24465 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 57057 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 257149 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 122284 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 8785 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 14 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 216 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 93625 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 37284 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 10131 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 10131 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 353 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 39 | True | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 12 | True | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 808 | True | report_only_reference |
| rolling_10d | position_sizing_cap_release | position_sizing | 20 | False | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 20 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 20 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 24465 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 58634 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 257149 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 122284 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 8785 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 14 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 216 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 95701 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 38284 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 10447 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 10447 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 359 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 63 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 12 | True | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 1111 | True | report_only_reference |
| rolling_20d | position_sizing_cap_release | position_sizing | 21 | False | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 21 | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 21 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 24465 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
