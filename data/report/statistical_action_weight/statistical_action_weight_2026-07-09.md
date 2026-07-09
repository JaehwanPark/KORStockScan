# Statistical Action Weight Report - 2026-07-09

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `True`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 101 |
| exit_only | 79 |
| avg_down_wait | 21 |
| pyramid_wait | 1 |
| compact_exit_signal | 18 |
| compact_sell_completed | 6 |
| compact_scale_in_executed | 2 |
| compact_decision_snapshot | 628 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 101 |
| volume_known | 89 |
| time_known | 101 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 12 |
| insufficient_sample | 1 |
| no_clear_edge | 1 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -1.3233 | 0.0206 | 29 | -0.7579 | 0.4828 | no_clear_edge |
| price_30k_70k | exit_only | -0.2729 | - | 16 | 0.9012 | 0.1875 | candidate_weight_source |
| price_gte_70k | exit_only | -0.5251 | 1.7017 | 11 | 0.0064 | 0.3636 | candidate_weight_source |
| price_lt_10k | exit_only | -0.4961 | - | 23 | 0.0526 | 0.3478 | candidate_weight_source |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -0.5653 | 1.6323 | 10 | 0.931 | 0.1 | candidate_weight_source |
| volume_500k_2m | exit_only | -0.4805 | - | 15 | 0.32 | 0.3333 | candidate_weight_source |
| volume_gte_10m | exit_only | -1.9345 | - | 8 | -0.6175 | 0.5 | candidate_weight_source |
| volume_lt_500k | exit_only | -0.5622 | 0.6986 | 36 | -0.0858 | 0.3889 | candidate_weight_source |
| volume_unknown | exit_only | -1.9107 | - | 10 | -1.236 | 0.5 | candidate_weight_source |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_0930_1030 | exit_only | -0.3537 | - | 7 | 1.4757 | 0.2857 | candidate_weight_source |
| time_1030_1400 | exit_only | -1.2844 | - | 23 | -0.7448 | 0.3913 | candidate_weight_source |
| time_1400_1530 | exit_only | -0.2056 | - | 11 | 1.1927 | 0.1818 | candidate_weight_source |
| time_outside_regular | exit_only | -0.6913 | 0.8261 | 36 | -0.2147 | 0.4167 | candidate_weight_source |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `628`
- sample_candidates: `713`
- post_sell_joined_candidates: `178`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 543 | 101 | -1.4796 | 1.1268 | 1.513 | -0.806 |
| buy_pressure_severe_below_min | 2 | 2 | 0.25 | 0.08 | 4.89 | -23.553 |
| exit_only | 20 | 0 | -2.0095 | 2.259 | - | - |
| fresh_micro_confirmation_missing | 11 | 9 | 0.6945 | 0.6245 | 1.7802 | -18.3354 |
| hold_defer | 10 | 0 | -0.486 | 0.444 | - | - |
| large_sell_detected | 4 | 3 | 0.315 | 0.3775 | 4.1263 | -19.291 |
| micro_context_stale | 21 | 11 | 1.5143 | 0.3229 | 2.1374 | -18.1217 |
| micro_vwap_missing | 2 | 0 | 1.12 | 0.155 | - | - |
| micro_vwap_overheated | 1 | 1 | 1.18 | 0 | 4.89 | -23.553 |
| pyramid_wait | 57 | 25 | 1.0282 | 0.1965 | 2.2348 | -15.4538 |
| quote_stale | 3 | 2 | 0.34 | 0.8167 | 1.633 | -16.3 |
| tick_accel_below_min | 1 | 1 | 1.18 | 0 | 4.89 | -23.553 |
| tick_accel_stale | 23 | 12 | 1.5043 | 0.2948 | 2.0148 | -18.431 |
| tick_aggressor_pressure_unusable | 15 | 11 | 1.24 | 0.362 | 1.9617 | -19.1277 |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 6 | 0 | -0.895 | 0.74 | - | - |
| exit_only | 9 | 1 | -4.25 | 4.4322 | 0.667 | -21.833 |
| hold_defer | 601 | 125 | -1.2344 | 1.0381 | 1.6641 | -3.5674 |
| pyramid_wait | 4 | 0 | 0.1275 | 0 | - | - |

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
