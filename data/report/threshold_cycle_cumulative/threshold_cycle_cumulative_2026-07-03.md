# Cumulative Threshold Cycle Report - 2026-07-03

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-04-21` ~ `2026-07-03`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 74 | 2166417 | 439 | -0.2675 | 0.4601 | 0.5034 |
| rolling_5d | 5 | 151387 | 128 | 0.1714 | 0.5469 | 0.3828 |
| rolling_10d | 10 | 226002 | 142 | 0.0964 | 0.5211 | 0.4155 |
| rolling_20d | 20 | 865225 | 156 | 0.007 | 0.5 | 0.4423 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 439 | -0.2675 | 0.4601 |
| cumulative | sim | 3896 | -1.2792 | 0.2402 |
| cumulative | combined | 4335 | -1.1768 | 0.2625 |
| rolling_5d | real | 128 | 0.1714 | 0.5469 |
| rolling_5d | sim | 108 | -1.0511 | 0.4259 |
| rolling_5d | combined | 236 | -0.3881 | 0.4915 |
| rolling_10d | real | 142 | 0.0964 | 0.5211 |
| rolling_10d | sim | 318 | -1.3035 | 0.261 |
| rolling_10d | combined | 460 | -0.8714 | 0.3413 |
| rolling_20d | real | 156 | 0.007 | 0.5 |
| rolling_20d | sim | 1359 | -1.3376 | 0.2215 |
| rolling_20d | combined | 1515 | -1.1992 | 0.2502 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 439 | -0.2675 | -2.51 | 2.03 | 0.4601 | 0.5034 |
| cumulative | normal_only | 439 | -0.2675 | -2.51 | 2.03 | 0.4601 | 0.5034 |
| cumulative | initial_only | 387 | -0.298 | -2.46 | 1.93 | 0.4496 | 0.5142 |
| cumulative | pyramid_activated | 26 | 0.4015 | -1.45 | 3.15 | 0.6154 | 0.3846 |
| cumulative | reversal_add_activated | 27 | -0.2044 | -4.64 | 4.13 | 0.4815 | 0.4444 |
| rolling_5d | all_completed_valid | 128 | 0.1714 | -4.32 | 2.59 | 0.5469 | 0.3828 |
| rolling_5d | normal_only | 128 | 0.1714 | -4.32 | 2.59 | 0.5469 | 0.3828 |
| rolling_5d | initial_only | 102 | 0.2761 | -3.31 | 2.57 | 0.5588 | 0.3725 |
| rolling_5d | pyramid_activated | 2 | 2.075 | -2.87 | 7.02 | 0.5 | 0.5 |
| rolling_5d | reversal_add_activated | 25 | -0.134 | -4.64 | 4.13 | 0.52 | 0.4 |
| rolling_10d | all_completed_valid | 142 | 0.0964 | -3.75 | 2.59 | 0.5211 | 0.4155 |
| rolling_10d | normal_only | 142 | 0.0964 | -3.75 | 2.59 | 0.5211 | 0.4155 |
| rolling_10d | initial_only | 115 | 0.1883 | -3.25 | 2.59 | 0.5304 | 0.4087 |
| rolling_10d | pyramid_activated | 2 | 2.075 | -2.87 | 7.02 | 0.5 | 0.5 |
| rolling_10d | reversal_add_activated | 26 | -0.1958 | -4.64 | 4.13 | 0.5 | 0.4231 |
| rolling_20d | all_completed_valid | 156 | 0.007 | -3.75 | 2.57 | 0.5 | 0.4423 |
| rolling_20d | normal_only | 156 | 0.007 | -3.75 | 2.57 | 0.5 | 0.4423 |
| rolling_20d | initial_only | 128 | 0.0798 | -3.31 | 2.57 | 0.5078 | 0.4375 |
| rolling_20d | pyramid_activated | 3 | 0.9933 | -2.87 | 7.02 | 0.3333 | 0.6667 |
| rolling_20d | reversal_add_activated | 26 | -0.1958 | -4.64 | 4.13 | 0.5 | 0.4231 |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 292699 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 89 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 31116 | True | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 3274 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 176959 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 47380 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 22538 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 83 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 619 | True | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 237190 | True | report_only_reference |
| cumulative | reversal_add | holding_exit | 101352 | True | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 18897 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 18897 | True | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 1150 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 162 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 105 | True | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2687 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 439 | False | report_only_reference |
| cumulative | statistical_action_weight | decision_support | 439 | False | report_only_reference |
| cumulative | lifecycle_decision_matrix_runtime | lifecycle | 5088 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 3058 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 2788 | True | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 989 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 6494 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 1235 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 805 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 28 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 63 | True | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 35015 | True | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 14767 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 731 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 731 | True | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 248 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 5 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 26 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 665 | True | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 128 | False | report_only_reference |
| rolling_5d | statistical_action_weight | decision_support | 128 | False | report_only_reference |
| rolling_5d | lifecycle_decision_matrix_runtime | lifecycle | 5088 | True | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 3265 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 4129 | True | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 1185 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 11962 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 2367 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 2200 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 28 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 81 | True | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 45177 | True | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 18412 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 1366 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 1366 | True | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 275 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 5 | False | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 28 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 821 | True | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 142 | False | report_only_reference |
| rolling_10d | statistical_action_weight | decision_support | 142 | False | report_only_reference |
| rolling_10d | lifecycle_decision_matrix_runtime | lifecycle | 5088 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 95405 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 3 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 13386 | True | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 2134 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 64801 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 7156 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 9054 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 39 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 137 | True | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 113175 | True | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 48120 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 8474 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 8474 | True | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 542 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 39 | True | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 35 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 1673 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 156 | False | report_only_reference |
| rolling_20d | statistical_action_weight | decision_support | 156 | False | report_only_reference |
| rolling_20d | lifecycle_decision_matrix_runtime | lifecycle | 5088 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
