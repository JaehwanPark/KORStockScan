# Statistical Action Weight Report - 2026-07-07

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `True`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 129 |
| exit_only | 99 |
| avg_down_wait | 29 |
| pyramid_wait | 1 |
| compact_exit_signal | 947 |
| compact_sell_completed | 22 |
| compact_scale_in_executed | 3 |
| compact_decision_snapshot | 2924 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 129 |
| volume_known | 123 |
| time_known | 129 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 13 |
| insufficient_sample | 1 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.2287 | 1.4211 | 30 | 0.3437 | 0.3333 | candidate_weight_source |
| price_30k_70k | exit_only | 0.5715 | - | 25 | 1.236 | 0.2 | candidate_weight_source |
| price_gte_70k | exit_only | 0.1471 | 1.4949 | 16 | 0.425 | 0.3125 | candidate_weight_source |
| price_lt_10k | exit_only | -0.1076 | - | 28 | 0.2039 | 0.3571 | candidate_weight_source |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | 0.0924 | 1.8426 | 21 | 0.8267 | 0.2381 | candidate_weight_source |
| volume_500k_2m | exit_only | 0.2649 | 2.4565 | 19 | 0.7979 | 0.2632 | candidate_weight_source |
| volume_gte_10m | exit_only | -0.9958 | - | 10 | -0.381 | 0.5 | candidate_weight_source |
| volume_lt_500k | exit_only | 0.3315 | 1.3608 | 44 | 0.6673 | 0.2727 | candidate_weight_source |
| volume_unknown | exit_only | -1.8897 | - | 5 | -0.87 | 0.6 | candidate_weight_source |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_0930_1030 | exit_only | 0.0492 | - | 7 | 1.3543 | 0.1429 | candidate_weight_source |
| time_1030_1400 | exit_only | -0.1179 | 1.3273 | 30 | 0.3897 | 0.2333 | candidate_weight_source |
| time_1400_1530 | exit_only | 0.3475 | - | 17 | 1.0365 | 0.3529 | candidate_weight_source |
| time_outside_regular | exit_only | -0.1173 | 1.2759 | 41 | 0.2207 | 0.3902 | candidate_weight_source |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `2924`
- sample_candidates: `2513`
- post_sell_joined_candidates: `418`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 1561 | 211 | -1.4864 | 1.2243 | 2.5533 | -3.9795 |
| buy_pressure_below_min | 1 | 0 | 3.91 | 0 | - | - |
| buy_pressure_severe_below_min | 5 | 0 | 0.152 | 0.77 | - | - |
| exit_only | 122 | 73 | -3.1294 | 2.983 | 1.5555 | -1.807 |
| fresh_micro_confirmation_missing | 71 | 18 | 0.8424 | 0.3844 | 1.6801 | -17.4243 |
| hold_defer | 32 | 1 | -0.1522 | 0.4881 | -0.104 | -4.87 |
| large_sell_detected | 10 | 3 | 1.218 | 0.21 | 1.2793 | -23.7193 |
| micro_context_stale | 97 | 20 | 1.2624 | 0.3332 | 1.8785 | -15.5731 |
| micro_vwap_overheated | 1 | 0 | 5.19 | 0 | - | - |
| micro_vwap_severe_overheated | 4 | 2 | 3.205 | 0 | 1.8855 | -18.341 |
| pyramid_wait | 384 | 40 | 0.7358 | 0.3948 | 1.4258 | -13.7948 |
| quote_stale | 20 | 4 | 0.1985 | 0.6215 | 1.466 | -16.634 |
| tick_accel_below_min | 2 | 0 | 3.66 | 0.075 | - | - |
| tick_accel_stale | 106 | 23 | 1.2356 | 0.3129 | 1.6946 | -13.9723 |
| tick_aggressor_pressure_unusable | 97 | 23 | 1.1084 | 0.3394 | 1.6946 | -13.9723 |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 18 | 0 | -0.7111 | 0.515 | - | - |
| exit_only | 90 | 50 | -5.8849 | 5.4593 | 1.4068 | -3.0117 |
| hold_defer | 1945 | 273 | -0.9692 | 0.987 | 2.341 | -5.0107 |
| pyramid_wait | 14 | 1 | 0.5664 | 0.4536 | -0.104 | -4.87 |

- `post_decision_*_proxy`는 record_id가 post_sell 평가와 맞는 경우의 10분 proxy이며 live 판단 근거가 아니다.
- true 후행 quote join이 추가되기 전까지는 selection-bias 점검과 후보 발굴에만 쓴다.

## Threshold 반영 원칙

- 이 리포트는 AI/주문 runtime을 직접 변경하지 않는다.
- `candidate_weight_source`는 ADM advisory canary/live-readiness 후보로 연결할 수 있다.
- `no_clear_edge`, `insufficient_sample`, `defensive_only_high_loss_rate`는 최소 edge 부재 또는 calibration 보류 상태다.

## 다음 액션

- Markdown 자동생성 상태와 표본 충분성을 확인한다.
- sample-ready bucket은 `holding_exit_decision_matrix` advisory canary 후보로 넘긴다.
- 부족하면 live 금지가 아니라 `hold_sample` calibration과 join 품질 보강으로 남긴다.
