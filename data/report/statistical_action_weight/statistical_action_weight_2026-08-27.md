# Statistical Action Weight Report - 2026-08-27

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 34 |
| exit_only | 33 |
| avg_down_wait | 1 |
| pyramid_wait | 0 |
| compact_exit_signal | 12 |
| compact_sell_completed | 2 |
| compact_scale_in_executed | 0 |
| compact_decision_snapshot | 548 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 34 |
| volume_known | 30 |
| time_known | 34 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 8 |
| insufficient_sample | 5 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.556 | - | 23 | -0.1814 | 0.3478 | candidate_weight_source |
| price_30k_70k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| price_gte_70k | exit_only | -0.8409 | - | 6 | -0.1951 | 0.3333 | candidate_weight_source |
| price_lt_10k | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -0.1369 | - | 6 | 0.5917 | 0.1667 | candidate_weight_source |
| volume_500k_2m | exit_only | -0.3125 | - | 12 | 0.2029 | 0.25 | candidate_weight_source |
| volume_gte_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_lt_500k | exit_only | -0.9569 | - | 7 | -0.3296 | 0.4286 | candidate_weight_source |
| volume_unknown | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_0930_1030 | exit_only | -0.1248 | - | 7 | 0.3371 | 0.2857 | candidate_weight_source |
| time_1030_1400 | exit_only | -0.2231 | - | 15 | 0.2795 | 0.2667 | candidate_weight_source |
| time_1400_1530 | exit_only | -1.7768 | - | 9 | -1.7462 | 0.5556 | candidate_weight_source |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `548`
- sample_candidates: `1097`
- post_sell_joined_candidates: `212`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 380 | 69 | -0.8714 | 0.8329 | 7.027 | -0.5368 |
| buy_pressure_below_min | 2 | 0 | 2.325 | 0.125 | - | - |
| buy_pressure_severe_below_min | 7 | 7 | 0.2014 | 0.29 | 1.8861 | -0.5189 |
| exit_only | 537 | 98 | -0.5017 | 0.6509 | 5.8488 | -0.5327 |
| fresh_micro_confirmation_missing | 2 | 1 | 1.365 | 0 | 11.973 | -0.554 |
| hold_defer | 41 | 1 | 0.4624 | 0.2024 | 11.973 | -0.554 |
| large_sell_detected | 5 | 5 | 0.176 | 0.292 | 2.5586 | -0.5212 |
| micro_context_stale | 1 | 1 | 0.11 | 0 | 11.973 | -0.554 |
| micro_vwap_overheated | 2 | 0 | 1.48 | 0.065 | - | - |
| pyramid_wait | 118 | 28 | 0.3081 | 0.2603 | 2.7267 | -0.5218 |
| tick_accel_stale | 1 | 1 | 0.11 | 0 | 11.973 | -0.554 |
| tick_aggressor_pressure_unusable | 1 | 1 | 0.11 | 0 | 11.973 | -0.554 |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 16 | 0 | -0.6338 | 0.4231 | - | - |
| exit_only | 2 | 0 | -3.22 | 2.99 | - | - |
| hold_defer | 496 | 97 | -0.5814 | 0.688 | 5.7857 | -0.5324 |
| pyramid_wait | 25 | 1 | 1.164 | 0.0612 | 11.973 | -0.554 |

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
