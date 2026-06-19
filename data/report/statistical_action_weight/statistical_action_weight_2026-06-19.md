# Statistical Action Weight Report - 2026-06-19

## 판정

- 상태: `collect_more_samples`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 13 |
| exit_only | 12 |
| avg_down_wait | 0 |
| pyramid_wait | 1 |
| compact_exit_signal | 140 |
| compact_sell_completed | 1 |
| compact_scale_in_executed | 0 |
| compact_decision_snapshot | 1068 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 13 |
| volume_known | 12 |
| time_known | 13 |

## Policy Counts

| policy | count |
| --- | ---: |
| defensive_only_high_loss_rate | 3 |
| insufficient_sample | 9 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| price_30k_70k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| price_gte_70k | exit_only | -2.0467 | - | 5 | -1.39 | 0.8 | defensive_only_high_loss_rate |
| price_lt_10k | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_500k_2m | exit_only | -1.899 | - | 5 | -0.85 | 0.8 | defensive_only_high_loss_rate |
| volume_gte_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_lt_500k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_unknown | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0930_1030 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_1030_1400 | exit_only | -1.1163 | - | 9 | -0.2989 | 0.6667 | defensive_only_high_loss_rate |
| time_1400_1530 | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `1068`
- sample_candidates: `1033`
- post_sell_joined_candidates: `77`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 567 | 0 | -1.1241 | 0.4028 | - | - |
| exit_only | 155 | 61 | 1.1537 | 0.9195 | 0.53 | -3.814 |
| hold_defer | 31 | 1 | 1.7374 | 0.0523 | 0.53 | -3.814 |
| pyramid_wait | 280 | 15 | 0.5726 | 0.1184 | 0.53 | -3.814 |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 11 | 0 | -0.6318 | 0 | - | - |
| exit_only | 60 | 0 | -2.9402 | 1.2957 | - | - |
| hold_defer | 911 | 75 | -0.1929 | 0.3564 | 0.53 | -3.814 |
| pyramid_wait | 20 | 1 | 3.0405 | 0.081 | 0.53 | -3.814 |

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
