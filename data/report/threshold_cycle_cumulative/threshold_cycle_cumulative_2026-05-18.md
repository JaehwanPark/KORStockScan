# Cumulative Threshold Cycle Report - 2026-05-18

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-05-18`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 28 | 85453 | 0 | - | - | - |
| rolling_5d | 5 | 2850 | 0 | - | - | - |
| rolling_10d | 10 | 8837 | 0 | - | - | - |
| rolling_20d | 20 | 69211 | 0 | - | - | - |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 0 | - | - |
| cumulative | sim | 14 | 2.4014 | 0.5714 |
| cumulative | combined | 14 | 2.4014 | 0.5714 |
| rolling_5d | real | 0 | - | - |
| rolling_5d | sim | 4 | -1.455 | 0.25 |
| rolling_5d | combined | 4 | -1.455 | 0.25 |
| rolling_10d | real | 0 | - | - |
| rolling_10d | sim | 14 | 2.4014 | 0.5714 |
| rolling_10d | combined | 14 | 2.4014 | 0.5714 |
| rolling_20d | real | 0 | - | - |
| rolling_20d | sim | 14 | 2.4014 | 0.5714 |
| rolling_20d | combined | 14 | 2.4014 | 0.5714 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 0 | - | - | - | - | - |
| cumulative | normal_only | 0 | - | - | - | - | - |
| cumulative | initial_only | 0 | - | - | - | - | - |
| cumulative | pyramid_activated | 0 | - | - | - | - | - |
| cumulative | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_5d | all_completed_valid | 0 | - | - | - | - | - |
| rolling_5d | normal_only | 0 | - | - | - | - | - |
| rolling_5d | initial_only | 0 | - | - | - | - | - |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 0 | - | - | - | - | - |
| rolling_10d | normal_only | 0 | - | - | - | - | - |
| rolling_10d | initial_only | 0 | - | - | - | - | - |
| rolling_10d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_10d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_20d | all_completed_valid | 0 | - | - | - | - | - |
| rolling_20d | normal_only | 0 | - | - | - | - | - |
| rolling_20d | initial_only | 0 | - | - | - | - | - |
| rolling_20d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_20d | reversal_add_activated | 0 | - | - | - | - | - |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 50929 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 84 | True | report_only_reference |
| cumulative | liquidity_gate_refined_candidate | entry | 0 | False | report_only_reference |
| cumulative | overbought_gate_refined_candidate | entry | 0 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 121 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 575 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 9121 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 6544 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 1505 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 1505 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 46 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 818 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 2 | False | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 340 | True | report_only_reference |
| cumulative | position_sizing_cap_release | position_sizing | 0 | False | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 0 | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 0 | False | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 93 | False | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | liquidity_gate_refined_candidate | entry | 0 | False | report_only_reference |
| rolling_5d | overbought_gate_refined_candidate | entry | 0 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 0 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 0 | False | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 754 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 429 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 99 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 99 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 1 | False | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 1 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 86 | True | report_only_reference |
| rolling_5d | position_sizing_cap_release | position_sizing | 0 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 0 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 0 | False | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 1463 | False | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | liquidity_gate_refined_candidate | entry | 0 | False | report_only_reference |
| rolling_10d | overbought_gate_refined_candidate | entry | 0 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 0 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 0 | False | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 1599 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 815 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 144 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 144 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 6 | False | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 24 | True | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 289 | True | report_only_reference |
| rolling_10d | position_sizing_cap_release | position_sizing | 0 | False | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 0 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 0 | False | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 34760 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 84 | True | report_only_reference |
| rolling_20d | liquidity_gate_refined_candidate | entry | 0 | False | report_only_reference |
| rolling_20d | overbought_gate_refined_candidate | entry | 0 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 121 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 575 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 9121 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 6544 | True | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 1484 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 1484 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 46 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 818 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 2 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 340 | True | report_only_reference |
| rolling_20d | position_sizing_cap_release | position_sizing | 0 | False | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 0 | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 0 | False | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
