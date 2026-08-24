# Statistical Action Weight Report - 2026-08-24

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 38 |
| exit_only | 36 |
| avg_down_wait | 1 |
| pyramid_wait | 1 |
| compact_exit_signal | 595 |
| compact_sell_completed | 8 |
| compact_scale_in_executed | 0 |
| compact_decision_snapshot | 990 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 38 |
| volume_known | 34 |
| time_known | 38 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 9 |
| insufficient_sample | 4 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.6243 | - | 23 | -0.2428 | 0.3478 | candidate_weight_source |
| price_30k_70k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| price_gte_70k | exit_only | -0.9651 | - | 5 | -0.237 | 0.2 | candidate_weight_source |
| price_lt_10k | exit_only | -0.6952 | - | 8 | -0.1021 | 0.25 | candidate_weight_source |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -0.9316 | - | 11 | -0.3815 | 0.2727 | candidate_weight_source |
| volume_500k_2m | exit_only | -0.0319 | - | 10 | 0.4844 | 0.3 | candidate_weight_source |
| volume_gte_10m | exit_only | -1.5646 | - | 5 | -1.0128 | 0.4 | candidate_weight_source |
| volume_lt_500k | exit_only | -0.125 | - | 6 | 0.4587 | 0.1667 | candidate_weight_source |
| volume_unknown | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_0930_1030 | exit_only | -0.6535 | - | 10 | -0.1064 | 0.3 | candidate_weight_source |
| time_1030_1400 | exit_only | -0.2775 | - | 21 | 0.1522 | 0.2381 | candidate_weight_source |
| time_1400_1530 | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `990`
- sample_candidates: `1404`
- post_sell_joined_candidates: `17`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 958 | 8 | -2.4514 | 2.7297 | 1.5364 | -8.3584 |
| exit_only | 426 | 8 | -1.4192 | 1.5451 | 1.109 | -9.215 |
| pyramid_wait | 20 | 1 | 0.338 | 0.0885 | 1.109 | -9.215 |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| exit_only | 552 | 1 | -3.1469 | 3.5482 | 4.528 | -2.362 |
| hold_defer | 426 | 8 | -1.4192 | 1.5451 | 1.109 | -9.215 |

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
