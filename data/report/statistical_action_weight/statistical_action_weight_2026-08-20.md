# Statistical Action Weight Report - 2026-08-20

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 22 |
| exit_only | 21 |
| avg_down_wait | 0 |
| pyramid_wait | 1 |
| compact_exit_signal | 25 |
| compact_sell_completed | 12 |
| compact_scale_in_executed | 1 |
| compact_decision_snapshot | 1086 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 22 |
| volume_known | 20 |
| time_known | 22 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 4 |
| insufficient_sample | 8 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.9613 | - | 13 | -0.5043 | 0.3077 | candidate_weight_source |
| price_30k_70k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| price_gte_70k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| price_lt_10k | exit_only | -0.1379 | - | 5 | 0.4801 | 0.2 | candidate_weight_source |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -0.9961 | - | 12 | -0.5109 | 0.3333 | candidate_weight_source |
| volume_500k_2m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_gte_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_lt_500k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_unknown | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0930_1030 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_1030_1400 | exit_only | -0.4001 | - | 15 | 0.117 | 0.1333 | candidate_weight_source |
| time_1400_1530 | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `1086`
- sample_candidates: `2174`
- post_sell_joined_candidates: `559`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 887 | 237 | -0.9011 | 0.7738 | 1.9705 | -12.6802 |
| buy_pressure_severe_below_min | 7 | 6 | 0.3343 | 0.2129 | 1.34 | -11.4233 |
| exit_only | 1074 | 269 | -0.6889 | 0.6488 | 1.8505 | -11.9769 |
| fresh_micro_confirmation_missing | 2 | 2 | 1.375 | 0 | 0.314 | -7.202 |
| hold_defer | 23 | 3 | -0.2274 | 0.323 | 0.318 | -1.115 |
| large_sell_detected | 4 | 3 | 0.435 | 0.145 | 2.606 | -10.0573 |
| micro_context_stale | 1 | 1 | 0.55 | 0 | 0.31 | -13.289 |
| micro_vwap_overheated | 1 | 1 | 1.71 | 0 | 0.318 | -1.115 |
| pyramid_already_used | 6 | 5 | 0.3367 | 0.135 | 0.318 | -1.115 |
| pyramid_wait | 167 | 30 | 0.3235 | 0.0805 | 1.0533 | -7.2673 |
| tick_accel_stale | 1 | 1 | 0.55 | 0 | 0.31 | -13.289 |
| tick_aggressor_pressure_unusable | 1 | 1 | 0.55 | 0 | 0.31 | -13.289 |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 14 | 0 | -0.7393 | 0.5093 | - | - |
| exit_only | 3 | 1 | -3.55 | 3.5033 | 1.8 | -4.8 |
| hold_defer | 1051 | 266 | -0.699 | 0.6559 | 1.8677 | -12.0994 |
| pyramid_wait | 9 | 3 | 0.5689 | 0.0333 | 0.318 | -1.115 |

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
