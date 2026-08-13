# Statistical Action Weight Report - 2026-08-13

## 판정

- 상태: `collect_more_samples`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 3 |
| exit_only | 3 |
| avg_down_wait | 0 |
| pyramid_wait | 0 |
| compact_exit_signal | 15 |
| compact_sell_completed | 3 |
| compact_scale_in_executed | 0 |
| compact_decision_snapshot | 982 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 3 |
| volume_known | 3 |
| time_known | 3 |

## Policy Counts

| policy | count |
| --- | ---: |
| insufficient_sample | 5 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_500k_2m | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_1030_1400 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_1400_1530 | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `982`
- sample_candidates: `1946`
- post_sell_joined_candidates: `231`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 883 | 113 | -1.3977 | 1.5253 | 0.315 | -6.619 |
| exit_only | 971 | 115 | -1.2524 | 1.3873 | 0.315 | -6.619 |
| hold_defer | 20 | 0 | -0.4895 | 0.326 | - | - |
| pyramid_wait | 72 | 3 | 0.2257 | 0.1014 | 0.315 | -6.619 |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 15 | 0 | -0.7007 | 0.416 | - | - |
| exit_only | 4 | 1 | -2.92 | 3.395 | 0.315 | -6.619 |
| hold_defer | 951 | 115 | -1.2684 | 1.4096 | 0.315 | -6.619 |
| pyramid_wait | 5 | 0 | 0.144 | 0.056 | - | - |

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
