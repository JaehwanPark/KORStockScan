# Statistical Action Weight Report - 2026-06-24

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 16 |
| exit_only | 15 |
| avg_down_wait | 0 |
| pyramid_wait | 1 |
| compact_exit_signal | 72 |
| compact_sell_completed | 4 |
| compact_scale_in_executed | 0 |
| compact_decision_snapshot | 1792 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 16 |
| volume_known | 15 |
| time_known | 16 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 1 |
| defensive_only_high_loss_rate | 2 |
| insufficient_sample | 9 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| price_30k_70k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| price_gte_70k | exit_only | -2.0173 | - | 5 | -1.39 | 0.8 | defensive_only_high_loss_rate |
| price_lt_10k | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_500k_2m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_gte_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_lt_500k | exit_only | -2.5419 | - | 6 | -2.07 | 0.8333 | defensive_only_high_loss_rate |
| volume_unknown | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0930_1030 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_1030_1400 | exit_only | -1.2492 | - | 10 | -0.503 | 0.6 | candidate_weight_source |
| time_1400_1530 | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `1792`
- sample_candidates: `1880`
- post_sell_joined_candidates: `110`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 1263 | 74 | -0.8912 | 0.4808 | 1.903 | -2.1869 |
| exit_only | 222 | 16 | 1.2017 | 0.6184 | 6.54 | -4.747 |
| hold_defer | 103 | 3 | 1.6898 | 0.1484 | 6.54 | -4.747 |
| pyramid_wait | 292 | 17 | 0.4493 | 0.1168 | 3.5834 | -3.8427 |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 27 | 0 | -0.7504 | 0.5122 | - | - |
| exit_only | 57 | 3 | -2.6805 | 1.5718 | 2.7733 | -2.1517 |
| hold_defer | 1617 | 101 | -0.4631 | 0.4167 | 2.7568 | -2.7962 |
| pyramid_wait | 76 | 3 | 2.5567 | 0.0192 | 6.54 | -4.747 |

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
