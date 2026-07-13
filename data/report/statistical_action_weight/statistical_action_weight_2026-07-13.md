# Statistical Action Weight Report - 2026-07-13

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 65 |
| exit_only | 58 |
| avg_down_wait | 6 |
| pyramid_wait | 1 |
| compact_exit_signal | 170 |
| compact_sell_completed | 5 |
| compact_scale_in_executed | 0 |
| compact_decision_snapshot | 532 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 65 |
| volume_known | 55 |
| time_known | 65 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 13 |
| insufficient_sample | 1 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -2.0313 | - | 22 | -1.4 | 0.5909 | candidate_weight_source |
| price_30k_70k | exit_only | -1.2382 | - | 11 | -0.1145 | 0.2727 | candidate_weight_source |
| price_gte_70k | exit_only | -1.1551 | - | 10 | -0.274 | 0.3 | candidate_weight_source |
| price_lt_10k | exit_only | -1.6441 | - | 15 | -0.9567 | 0.5333 | candidate_weight_source |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -1.3264 | - | 7 | -0.3714 | 0.4286 | candidate_weight_source |
| volume_500k_2m | exit_only | -1.4957 | - | 13 | -0.8031 | 0.3846 | candidate_weight_source |
| volume_gte_10m | exit_only | -1.9375 | - | 10 | -0.526 | 0.5 | candidate_weight_source |
| volume_lt_500k | exit_only | -1.6002 | - | 19 | -0.9853 | 0.5263 | candidate_weight_source |
| volume_unknown | exit_only | -2.4355 | - | 9 | -1.3478 | 0.4444 | candidate_weight_source |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_0930_1030 | exit_only | -0.0812 | - | 7 | 2.1814 | 0.1429 | candidate_weight_source |
| time_1030_1400 | exit_only | -1.9644 | - | 23 | -1.4448 | 0.5652 | candidate_weight_source |
| time_1400_1530 | exit_only | -1.3118 | - | 6 | -0.255 | 0.5 | candidate_weight_source |
| time_outside_regular | exit_only | -1.7526 | - | 20 | -1.2395 | 0.45 | candidate_weight_source |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `532`
- sample_candidates: `418`
- post_sell_joined_candidates: `120`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 348 | 72 | -1.3755 | 1.3054 | 0.2656 | -2.6701 |
| exit_only | 2 | 0 | 0.48 | 0.265 | - | - |
| fresh_micro_confirmation_missing | 10 | 7 | 0.253 | 0.069 | 1.3786 | -9.2443 |
| hold_defer | 2 | 0 | 0.48 | 0.265 | - | - |
| micro_context_stale | 10 | 7 | 0.253 | 0.069 | 1.3786 | -9.2443 |
| micro_vwap_missing | 2 | 0 | 0.345 | 0 | - | - |
| pyramid_wait | 21 | 16 | 0.5538 | 0.0471 | 1.2268 | -7.6949 |
| quote_stale | 4 | 4 | 0.0725 | 0.1025 | 1.445 | -9.646 |
| tick_accel_stale | 10 | 7 | 0.253 | 0.069 | 1.3786 | -9.2443 |
| tick_aggressor_pressure_unusable | 9 | 7 | 0.1789 | 0.0767 | 1.3786 | -9.2443 |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 1 | 0 | -0.76 | 0.53 | - | - |
| exit_only | 7 | 2 | -2.8729 | 2.7171 | 1.1135 | -7.552 |
| hold_defer | 362 | 86 | -1.2347 | 1.2051 | 0.4247 | -3.4914 |
| pyramid_wait | 1 | 0 | 1.72 | 0 | - | - |

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
