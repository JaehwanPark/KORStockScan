# Statistical Action Weight Report - 2026-07-20

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 37 |
| exit_only | 32 |
| avg_down_wait | 2 |
| pyramid_wait | 3 |
| compact_exit_signal | 25 |
| compact_sell_completed | 15 |
| compact_scale_in_executed | 5 |
| compact_decision_snapshot | 948 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 37 |
| volume_known | 36 |
| time_known | 37 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 8 |
| defensive_only_high_loss_rate | 1 |
| insufficient_sample | 4 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.7138 | - | 13 | -0.2831 | 0.3077 | candidate_weight_source |
| price_30k_70k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| price_gte_70k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| price_lt_10k | exit_only | -0.0222 | - | 15 | 0.3287 | 0.3333 | candidate_weight_source |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -0.7633 | - | 12 | -0.38 | 0.25 | candidate_weight_source |
| volume_500k_2m | exit_only | -1.0356 | - | 6 | -0.3567 | 0.3333 | candidate_weight_source |
| volume_gte_10m | exit_only | -0.2224 | - | 7 | 0.1429 | 0.5714 | candidate_weight_source |
| volume_lt_500k | exit_only | -0.221 | - | 7 | 0.4343 | 0.4286 | candidate_weight_source |
| volume_unknown | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0930_1030 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_1030_1400 | exit_only | -0.2277 | - | 14 | 0.3079 | 0.2143 | candidate_weight_source |
| time_1400_1530 | exit_only | -0.7709 | - | 8 | -0.4825 | 0.5 | candidate_weight_source |
| time_outside_regular | exit_only | -1.1366 | - | 6 | -0.95 | 0.8333 | defensive_only_high_loss_rate |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `948`
- sample_candidates: `1941`
- post_sell_joined_candidates: `346`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 653 | 83 | -1.4884 | 1.328 | 1.905 | -5.9654 |
| buy_pressure_below_min | 1 | 0 | 1.18 | 0 | - | - |
| buy_pressure_severe_below_min | 8 | 7 | 0.255 | 0.0338 | 1.7589 | -5.7761 |
| exit_only | 923 | 139 | -0.9237 | 0.935 | 2.2241 | -5.7589 |
| fresh_micro_confirmation_missing | 18 | 14 | 0.6922 | 0.0683 | 4.4969 | -4.4012 |
| hold_defer | 6 | 5 | 0.7267 | 0.1067 | 1.3078 | -5.3542 |
| micro_context_stale | 19 | 14 | 1.2016 | 0.0284 | 5.2508 | -6.5419 |
| micro_vwap_missing | 1 | 0 | 2.26 | 0 | - | - |
| micro_vwap_overheated | 1 | 0 | 1.18 | 0 | - | - |
| micro_vwap_severe_overheated | 1 | 1 | 0.32 | 0 | 2.027 | -3.243 |
| pyramid_wait | 268 | 53 | 0.399 | 0.0163 | 2.8132 | -5.4277 |
| quote_stale | 3 | 3 | 0.2033 | 0 | 1.695 | -6.0927 |
| tick_accel_stale | 20 | 14 | 1.2545 | 0.027 | 5.2508 | -6.5419 |
| tick_aggressor_pressure_unusable | 19 | 13 | 1.2089 | 0.0284 | 4.129 | -7.0771 |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 1 | 0 | -0.72 | 0.49 | - | - |
| exit_only | 9 | 2 | -2.9311 | 2.9378 | 2.303 | -4.5415 |
| hold_defer | 917 | 134 | -0.9345 | 0.9404 | 2.2583 | -5.774 |
| pyramid_wait | 5 | 5 | 1.016 | 0.03 | 1.3078 | -5.3542 |

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
