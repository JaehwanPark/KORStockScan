# Cumulative Threshold Cycle Report - 2026-05-21

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-05-21`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 31 | 558319 | 180 | -0.4603 | 0.4167 | 0.5667 |
| rolling_5d | 5 | 458543 | 3 | 1.3667 | 0.6667 | 0.3333 |
| rolling_10d | 10 | 463154 | 3 | 1.3667 | 0.6667 | 0.3333 |
| rolling_20d | 20 | 501530 | 54 | -0.4541 | 0.3889 | 0.6111 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 180 | -0.4603 | 0.4167 |
| cumulative | sim | 519 | -0.2992 | 0.3622 |
| cumulative | combined | 699 | -0.3407 | 0.3763 |
| rolling_5d | real | 3 | 1.3667 | 0.6667 |
| rolling_5d | sim | 506 | -0.3783 | 0.3557 |
| rolling_5d | combined | 509 | -0.3681 | 0.3576 |
| rolling_10d | real | 3 | 1.3667 | 0.6667 |
| rolling_10d | sim | 509 | -0.3826 | 0.3556 |
| rolling_10d | combined | 512 | -0.3723 | 0.3574 |
| rolling_20d | real | 54 | -0.4541 | 0.3889 |
| rolling_20d | sim | 519 | -0.2992 | 0.3622 |
| rolling_20d | combined | 573 | -0.3138 | 0.3647 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 180 | -0.4603 | -2.02 | 1.29 | 0.4167 | 0.5667 |
| cumulative | normal_only | 180 | -0.4603 | -2.02 | 1.29 | 0.4167 | 0.5667 |
| cumulative | initial_only | 159 | -0.5516 | -2.03 | 1.3 | 0.3899 | 0.5912 |
| cumulative | pyramid_activated | 20 | 0.2635 | -1.42 | 1.18 | 0.65 | 0.35 |
| cumulative | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |
| rolling_5d | all_completed_valid | 3 | 1.3667 | -0.76 | 4.63 | 0.6667 | 0.3333 |
| rolling_5d | normal_only | 3 | 1.3667 | -0.76 | 4.63 | 0.6667 | 0.3333 |
| rolling_5d | initial_only | 3 | 1.3667 | -0.76 | 4.63 | 0.6667 | 0.3333 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 3 | 1.3667 | -0.76 | 4.63 | 0.6667 | 0.3333 |
| rolling_10d | normal_only | 3 | 1.3667 | -0.76 | 4.63 | 0.6667 | 0.3333 |
| rolling_10d | initial_only | 3 | 1.3667 | -0.76 | 4.63 | 0.6667 | 0.3333 |
| rolling_10d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_10d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_20d | all_completed_valid | 54 | -0.4541 | -2.16 | 1.69 | 0.3889 | 0.6111 |
| rolling_20d | normal_only | 54 | -0.4541 | -2.16 | 1.69 | 0.3889 | 0.6111 |
| rolling_20d | initial_only | 47 | -0.4328 | -2.19 | 2.08 | 0.4043 | 0.5957 |
| rolling_20d | pyramid_activated | 6 | -0.625 | -1.2 | 0.6 | 0.3333 | 0.6667 |
| rolling_20d | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 67064 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 84 | True | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 139107 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 66317 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 3918 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 121 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 697 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 41844 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 21400 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 6335 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 6335 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 211 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 826 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 3 | False | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 855 | True | report_only_reference |
| cumulative | position_sizing_cap_release | position_sizing | 180 | False | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 180 | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 180 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 40910 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 1810 | False | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 139107 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 66317 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 3918 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 11 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 122 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 32731 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 14859 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 4834 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 4834 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 150 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 8 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 1 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 539 | True | report_only_reference |
| rolling_5d | position_sizing_cap_release | position_sizing | 3 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 3 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 3 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 40910 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 2534 | False | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 139107 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 66317 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 3918 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 11 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 122 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 33709 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 15350 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 4929 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 4929 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 151 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 9 | False | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 1 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 677 | True | report_only_reference |
| rolling_10d | position_sizing_cap_release | position_sizing | 3 | False | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 3 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 3 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 40910 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 13693 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 0 | True | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 139107 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 66317 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 3918 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 121 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 358 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 41823 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 19429 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 5952 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 5952 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 196 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 826 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 3 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 855 | True | report_only_reference |
| rolling_20d | position_sizing_cap_release | position_sizing | 54 | False | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 54 | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 54 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 40910 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
