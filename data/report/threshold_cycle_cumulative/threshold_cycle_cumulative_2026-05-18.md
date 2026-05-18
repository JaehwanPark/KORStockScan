# Cumulative Threshold Cycle Report - 2026-05-18

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-05-18`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 28 | 87312 | 177 | -0.4913 | 0.4124 | 0.5706 |
| rolling_5d | 5 | 4709 | 0 | - | - | - |
| rolling_10d | 10 | 10696 | 1 | -1.55 | 0 | 1 |
| rolling_20d | 20 | 71070 | 144 | -0.5281 | 0.4028 | 0.5833 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 177 | -0.4913 | 0.4124 |
| cumulative | sim | 15 | 2.114 | 0.5333 |
| cumulative | combined | 192 | -0.2878 | 0.4219 |
| rolling_5d | real | 0 | - | - |
| rolling_5d | sim | 5 | -1.546 | 0.2 |
| rolling_5d | combined | 5 | -1.546 | 0.2 |
| rolling_10d | real | 1 | -1.55 | 0 |
| rolling_10d | sim | 15 | 2.114 | 0.5333 |
| rolling_10d | combined | 16 | 1.885 | 0.5 |
| rolling_20d | real | 144 | -0.5281 | 0.4028 |
| rolling_20d | sim | 15 | 2.114 | 0.5333 |
| rolling_20d | combined | 159 | -0.2789 | 0.4151 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 177 | -0.4913 | -2.02 | 1.29 | 0.4124 | 0.5706 |
| cumulative | normal_only | 177 | -0.4913 | -2.02 | 1.29 | 0.4124 | 0.5706 |
| cumulative | initial_only | 156 | -0.5885 | -2.03 | 1.29 | 0.3846 | 0.5962 |
| cumulative | pyramid_activated | 20 | 0.2635 | -1.42 | 1.18 | 0.65 | 0.35 |
| cumulative | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |
| rolling_5d | all_completed_valid | 0 | - | - | - | - | - |
| rolling_5d | normal_only | 0 | - | - | - | - | - |
| rolling_5d | initial_only | 0 | - | - | - | - | - |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_10d | all_completed_valid | 1 | -1.55 | -1.55 | -1.55 | 0 | 1 |
| rolling_10d | normal_only | 1 | -1.55 | -1.55 | -1.55 | 0 | 1 |
| rolling_10d | initial_only | 1 | -1.55 | -1.55 | -1.55 | 0 | 1 |
| rolling_10d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_10d | reversal_add_activated | 0 | - | - | - | - | - |
| rolling_20d | all_completed_valid | 144 | -0.5281 | -2.03 | 1.18 | 0.4028 | 0.5833 |
| rolling_20d | normal_only | 144 | -0.5281 | -2.03 | 1.18 | 0.4028 | 0.5833 |
| rolling_20d | initial_only | 125 | -0.6538 | -2.08 | 1.02 | 0.368 | 0.616 |
| rolling_20d | pyramid_activated | 18 | 0.3389 | -1.2 | 1.59 | 0.6667 | 0.3333 |
| rolling_20d | reversal_add_activated | 1 | -0.43 | -0.43 | -0.43 | 0 | 1 |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 51043 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 84 | True | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 0 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 0 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 0 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 121 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 575 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 9598 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 6729 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 1677 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 1677 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 46 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 818 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 2 | False | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 354 | True | report_only_reference |
| cumulative | position_sizing_cap_release | position_sizing | 177 | False | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 177 | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 177 | False | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 207 | False | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 0 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 0 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 0 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 0 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 0 | False | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 1231 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 614 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 271 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 271 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 1 | False | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 1 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 100 | True | report_only_reference |
| rolling_5d | position_sizing_cap_release | position_sizing | 0 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 0 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 0 | False | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 1577 | False | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 0 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 0 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 0 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 0 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 0 | False | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 2076 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 1000 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 316 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 316 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 6 | False | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 24 | True | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 303 | True | report_only_reference |
| rolling_10d | position_sizing_cap_release | position_sizing | 1 | False | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 1 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 1 | False | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 34874 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 84 | True | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 0 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 0 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 0 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 121 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 575 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 9598 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 6729 | True | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 1656 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 1656 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 46 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 818 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 2 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 354 | True | report_only_reference |
| rolling_20d | position_sizing_cap_release | position_sizing | 144 | False | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 144 | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 144 | False | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
