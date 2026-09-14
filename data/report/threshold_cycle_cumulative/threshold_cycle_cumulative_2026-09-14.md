# Cumulative Threshold Cycle Report - 2026-09-14

## 판정

- 상태: `report_only_review`
- runtime_change: `False`
- 기준 구간: `2026-06-05` ~ `2026-09-14`
- 손익 기준: `COMPLETED + valid profit_rate only`

## Window Summary

| window | dates | events | completed | avg_profit | win_rate | loss_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | 102 | 400338 | 534 | -0.1468 | 0.5506 | 0.4176 |
| rolling_5d | 5 | 7002 | 20 | -0.164 | 0.7 | 0.3 |
| rolling_10d | 10 | 13038 | 31 | -0.1045 | 0.7097 | 0.2903 |
| rolling_20d | 20 | 35002 | 91 | -0.1066 | 0.7143 | 0.2857 |

## Real / Sim Source Summary

| window | source | sample | avg_profit | win_rate |
| --- | --- | ---: | ---: | ---: |
| cumulative | real | 534 | -0.1468 | 0.5506 |
| cumulative | sim | 3600 | -1.2894 | 0.2475 |
| cumulative | combined | 4134 | -1.1418 | 0.2866 |
| rolling_5d | real | 20 | -0.164 | 0.7 |
| rolling_5d | sim | 48 | -0.8417 | 0.4167 |
| rolling_5d | combined | 68 | -0.6424 | 0.5 |
| rolling_10d | real | 31 | -0.1045 | 0.7097 |
| rolling_10d | sim | 96 | -1.0673 | 0.3542 |
| rolling_10d | combined | 127 | -0.8323 | 0.4409 |
| rolling_20d | real | 91 | -0.1066 | 0.7143 |
| rolling_20d | sim | 240 | -1.0132 | 0.3833 |
| rolling_20d | combined | 331 | -0.764 | 0.4743 |

## Cohort Summary

| window | cohort | sample | avg_profit | p10 | p90 | win_rate | loss_rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| cumulative | all_completed_valid | 534 | -0.1468 | -3.56 | 1.93 | 0.5506 | 0.4176 |
| cumulative | normal_only | 534 | -0.1468 | -3.56 | 1.93 | 0.5506 | 0.4176 |
| cumulative | initial_only | 469 | -0.1311 | -3.51 | 1.93 | 0.5586 | 0.4094 |
| cumulative | pyramid_activated | 12 | 0.475 | -2.39 | 3.22 | 0.6667 | 0.3333 |
| cumulative | reversal_add_activated | 54 | -0.2887 | -4.32 | 2.18 | 0.463 | 0.5 |
| rolling_5d | all_completed_valid | 20 | -0.164 | -3.32 | 1.49 | 0.7 | 0.3 |
| rolling_5d | normal_only | 20 | -0.164 | -3.32 | 1.49 | 0.7 | 0.3 |
| rolling_5d | initial_only | 18 | -0.1344 | -3.32 | 1.53 | 0.7222 | 0.2778 |
| rolling_5d | pyramid_activated | 0 | - | - | - | - | - |
| rolling_5d | reversal_add_activated | 2 | -0.43 | -1.68 | 0.82 | 0.5 | 0.5 |
| rolling_10d | all_completed_valid | 31 | -0.1045 | -3.04 | 1.49 | 0.7097 | 0.2903 |
| rolling_10d | normal_only | 31 | -0.1045 | -3.04 | 1.49 | 0.7097 | 0.2903 |
| rolling_10d | initial_only | 27 | -0.1407 | -3.28 | 1.53 | 0.7037 | 0.2963 |
| rolling_10d | pyramid_activated | 1 | 0.19 | 0.19 | 0.19 | 1 | 0 |
| rolling_10d | reversal_add_activated | 3 | 0.1233 | -1.68 | 1.23 | 0.6667 | 0.3333 |
| rolling_20d | all_completed_valid | 91 | -0.1066 | -3.28 | 1.23 | 0.7143 | 0.2857 |
| rolling_20d | normal_only | 91 | -0.1066 | -3.28 | 1.23 | 0.7143 | 0.2857 |
| rolling_20d | initial_only | 85 | -0.1264 | -3.32 | 1.23 | 0.7176 | 0.2824 |
| rolling_20d | pyramid_activated | 2 | 0.95 | 0.19 | 1.71 | 1 | 0 |
| rolling_20d | reversal_add_activated | 4 | -0.215 | -1.68 | 1.23 | 0.5 | 0.5 |

## Smoothing Source-Only Rolling Decision

| family | decision | samples_ready | EV_windows_positive | risk_ready | risk_review | next_action |
| --- | --- | --- | ---: | --- | --- | --- |
| soft_stop_whipsaw_confirmation | hold_sample | False | 3 | True | True | keep_collecting_exact_paths |
| holding_flow_ofi_smoothing | hold_sample | False | 0 | False | False | keep_collecting_exact_paths |

## Family Readiness

| window | family | stage | sample | sample_ready | apply_mode |
| --- | --- | --- | ---: | --- | --- |
| cumulative | entry_mechanical_momentum | entry | 218920 | True | report_only_reference |
| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| cumulative | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| cumulative | dynamic_entry_price_resolver | entry | 17173 | True | report_only_reference |
| cumulative | entry_split_order_plan | submit | 182 | True | report_only_reference |
| cumulative | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| cumulative | entry_price_execution_quality | entry | 3082 | False | report_only_reference |
| cumulative | strength_momentum_soft_gate_p1 | entry | 0 | False | report_only_reference |
| cumulative | overbought_pullback_guard_p1 | entry | 0 | False | report_only_reference |
| cumulative | liquidity_pre_submit_guard_p1 | entry | 0 | False | report_only_reference |
| cumulative | entry_ofi_ai_smoothing | entry | 105 | False | report_only_reference |
| cumulative | bad_entry_block | holding_exit | 0 | False | report_only_reference |
| cumulative | bad_entry_refined_canary | holding_exit | 0 | False | report_only_reference |
| cumulative | reversal_add | holding_exit | 0 | False | report_only_reference |
| cumulative | soft_stop_micro_grace | holding_exit | 19206 | True | report_only_reference |
| cumulative | soft_stop_whipsaw_confirmation | holding_exit | 19206 | False | report_only_reference |
| cumulative | scalp_trailing_take_profit | holding_exit | 4768 | True | report_only_reference |
| cumulative | protect_trailing_smoothing | holding_exit | 216 | True | report_only_reference |
| cumulative | holding_flow_ofi_smoothing | holding_exit | 127 | False | report_only_reference |
| cumulative | scale_in_price_guard | holding_exit | 2767 | True | report_only_reference |
| cumulative | position_sizing_dynamic_formula | position_sizing | 534 | True | report_only_reference |
| rolling_5d | entry_mechanical_momentum | entry | 2808 | True | report_only_reference |
| rolling_5d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_5d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_5d | dynamic_entry_price_resolver | entry | 206 | True | report_only_reference |
| rolling_5d | entry_split_order_plan | submit | 182 | True | report_only_reference |
| rolling_5d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_5d | entry_price_execution_quality | entry | 48 | False | report_only_reference |
| rolling_5d | strength_momentum_soft_gate_p1 | entry | 0 | False | report_only_reference |
| rolling_5d | overbought_pullback_guard_p1 | entry | 0 | False | report_only_reference |
| rolling_5d | liquidity_pre_submit_guard_p1 | entry | 0 | False | report_only_reference |
| rolling_5d | entry_ofi_ai_smoothing | entry | 2 | False | report_only_reference |
| rolling_5d | bad_entry_block | holding_exit | 0 | False | report_only_reference |
| rolling_5d | bad_entry_refined_canary | holding_exit | 0 | False | report_only_reference |
| rolling_5d | reversal_add | holding_exit | 0 | False | report_only_reference |
| rolling_5d | soft_stop_micro_grace | holding_exit | 702 | True | report_only_reference |
| rolling_5d | soft_stop_whipsaw_confirmation | holding_exit | 702 | False | report_only_reference |
| rolling_5d | scalp_trailing_take_profit | holding_exit | 37 | True | report_only_reference |
| rolling_5d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_5d | holding_flow_ofi_smoothing | holding_exit | 4 | False | report_only_reference |
| rolling_5d | scale_in_price_guard | holding_exit | 10 | False | report_only_reference |
| rolling_5d | position_sizing_dynamic_formula | position_sizing | 20 | False | report_only_reference |
| rolling_10d | entry_mechanical_momentum | entry | 5745 | True | report_only_reference |
| rolling_10d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_10d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_10d | dynamic_entry_price_resolver | entry | 414 | True | report_only_reference |
| rolling_10d | entry_split_order_plan | submit | 182 | True | report_only_reference |
| rolling_10d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_10d | entry_price_execution_quality | entry | 136 | False | report_only_reference |
| rolling_10d | strength_momentum_soft_gate_p1 | entry | 0 | False | report_only_reference |
| rolling_10d | overbought_pullback_guard_p1 | entry | 0 | False | report_only_reference |
| rolling_10d | liquidity_pre_submit_guard_p1 | entry | 0 | False | report_only_reference |
| rolling_10d | entry_ofi_ai_smoothing | entry | 20 | False | report_only_reference |
| rolling_10d | bad_entry_block | holding_exit | 0 | False | report_only_reference |
| rolling_10d | bad_entry_refined_canary | holding_exit | 0 | False | report_only_reference |
| rolling_10d | reversal_add | holding_exit | 0 | False | report_only_reference |
| rolling_10d | soft_stop_micro_grace | holding_exit | 1084 | True | report_only_reference |
| rolling_10d | soft_stop_whipsaw_confirmation | holding_exit | 1084 | False | report_only_reference |
| rolling_10d | scalp_trailing_take_profit | holding_exit | 61 | True | report_only_reference |
| rolling_10d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_10d | holding_flow_ofi_smoothing | holding_exit | 6 | False | report_only_reference |
| rolling_10d | scale_in_price_guard | holding_exit | 15 | False | report_only_reference |
| rolling_10d | position_sizing_dynamic_formula | position_sizing | 31 | True | report_only_reference |
| rolling_20d | entry_mechanical_momentum | entry | 13543 | True | report_only_reference |
| rolling_20d | score65_74_recovery_probe | entry | 0 | False | report_only_reference |
| rolling_20d | pre_submit_price_guard | entry | 0 | False | report_only_reference |
| rolling_20d | dynamic_entry_price_resolver | entry | 1154 | True | report_only_reference |
| rolling_20d | entry_split_order_plan | submit | 182 | True | report_only_reference |
| rolling_20d | scale_in_split_order_plan | scale_in | 0 | False | report_only_reference |
| rolling_20d | entry_price_execution_quality | entry | 373 | False | report_only_reference |
| rolling_20d | strength_momentum_soft_gate_p1 | entry | 0 | False | report_only_reference |
| rolling_20d | overbought_pullback_guard_p1 | entry | 0 | False | report_only_reference |
| rolling_20d | liquidity_pre_submit_guard_p1 | entry | 0 | False | report_only_reference |
| rolling_20d | entry_ofi_ai_smoothing | entry | 50 | False | report_only_reference |
| rolling_20d | bad_entry_block | holding_exit | 0 | False | report_only_reference |
| rolling_20d | bad_entry_refined_canary | holding_exit | 0 | False | report_only_reference |
| rolling_20d | reversal_add | holding_exit | 0 | False | report_only_reference |
| rolling_20d | soft_stop_micro_grace | holding_exit | 3448 | True | report_only_reference |
| rolling_20d | soft_stop_whipsaw_confirmation | holding_exit | 3448 | False | report_only_reference |
| rolling_20d | scalp_trailing_take_profit | holding_exit | 1630 | True | report_only_reference |
| rolling_20d | protect_trailing_smoothing | holding_exit | 0 | False | report_only_reference |
| rolling_20d | holding_flow_ofi_smoothing | holding_exit | 15 | False | report_only_reference |
| rolling_20d | scale_in_price_guard | holding_exit | 60 | True | report_only_reference |
| rolling_20d | position_sizing_dynamic_formula | position_sizing | 91 | True | report_only_reference |

## 사용 금지선

- 이 리포트는 장후 누적/rolling 판정 입력이며 live runtime을 변경하지 않는다.
- 누적 평균 단독으로 threshold를 자동 적용하지 않는다.
- full/partial fill과 runtime flag cohort가 분리되지 않은 손익 결론은 hard 승인 근거로 쓰지 않는다.

## 다음 액션

- daily, rolling, cumulative가 같은 방향인지 먼저 비교한다.
- 불일치하면 당일 장세/데이터 품질/이전 runtime cohort 혼입을 먼저 점검한다.
- 후보가 유지되면 별도 checklist에서 단일 owner, rollback guard, manifest-only 추천값으로 넘긴다.
