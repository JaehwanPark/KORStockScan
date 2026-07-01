# Statistical Action Weight Report - 2026-07-01

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `True`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 85 |
| exit_only | 70 |
| avg_down_wait | 14 |
| pyramid_wait | 1 |
| compact_exit_signal | 472 |
| compact_sell_completed | 27 |
| compact_scale_in_executed | 24 |
| compact_decision_snapshot | 4806 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 85 |
| volume_known | 76 |
| time_known | 85 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 9 |
| defensive_only_high_loss_rate | 2 |
| insufficient_sample | 3 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.9494 | - | 17 | -0.4494 | 0.5294 | candidate_weight_source |
| price_30k_70k | exit_only | -0.312 | - | 18 | 0.2011 | 0.4444 | candidate_weight_source |
| price_gte_70k | avg_down_wait | -0.0218 | 0.1643 | 8 | 1.1612 | 0.375 | candidate_weight_source |
| price_lt_10k | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -1.8788 | - | 9 | -1.5022 | 0.6667 | defensive_only_high_loss_rate |
| volume_500k_2m | exit_only | -0.2599 | 1.3213 | 25 | 0.164 | 0.44 | candidate_weight_source |
| volume_gte_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_lt_500k | exit_only | -0.0285 | - | 29 | 0.5186 | 0.4138 | candidate_weight_source |
| volume_unknown | exit_only | -2.4124 | - | 6 | -1.1483 | 0.5 | candidate_weight_source |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_0930_1030 | exit_only | -0.4064 | - | 15 | 0.24 | 0.2667 | candidate_weight_source |
| time_1030_1400 | exit_only | 0.3264 | 0.3126 | 14 | 1.5164 | 0.1429 | candidate_weight_source |
| time_1400_1530 | exit_only | -0.5957 | - | 8 | -0.1838 | 0.875 | defensive_only_high_loss_rate |
| time_outside_regular | exit_only | -1.2932 | - | 29 | -0.9383 | 0.6207 | candidate_weight_source |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `4806`
- sample_candidates: `4732`
- post_sell_joined_candidates: `1153`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 3063 | 698 | -1.3457 | 1.4361 | 1.9018 | -6.0366 |
| exit_only | 361 | 113 | 2.4699 | 0.613 | 1.9948 | -4.6049 |
| hold_defer | 272 | 77 | 2.7581 | 0.0545 | 1.7875 | -6.069 |
| pyramid_wait | 1036 | 265 | 0.7434 | 0.2658 | 1.6724 | -10.8092 |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 19 | 0 | -0.8505 | 0.6205 | - | - |
| exit_only | 124 | 115 | -5.6704 | 5.7326 | 3.2441 | -0.4847 |
| hold_defer | 4064 | 884 | -0.6169 | 1.026 | 1.6803 | -8.0037 |
| pyramid_wait | 253 | 77 | 3.0291 | 0.012 | 1.7875 | -6.069 |

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
