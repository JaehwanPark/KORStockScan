# Statistical Action Weight Report - 2026-05-29

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 21 |
| exit_only | 21 |
| avg_down_wait | 0 |
| pyramid_wait | 0 |
| compact_exit_signal | 203 |
| compact_sell_completed | 4 |
| compact_scale_in_executed | 0 |
| compact_decision_snapshot | 8126 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 21 |
| volume_known | 15 |
| time_known | 21 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 6 |
| insufficient_sample | 4 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -1.0153 | - | 9 | -0.6878 | 0.3333 | candidate_weight_source |
| price_gte_70k | exit_only | -1.0352 | - | 12 | -0.1575 | 0.5 | candidate_weight_source |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -1.5054 | - | 7 | -1.2557 | 0.5714 | candidate_weight_source |
| volume_500k_2m | exit_only | -0.7701 | - | 7 | 1.0529 | 0.2857 | candidate_weight_source |
| volume_gte_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_unknown | exit_only | -0.9608 | - | 6 | -0.6917 | 0.3333 | candidate_weight_source |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_0930_1030 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_1030_1400 | exit_only | -0.9955 | - | 11 | -0.2464 | 0.3636 | candidate_weight_source |
| time_1400_1530 | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `8126`
- sample_candidates: `8053`
- post_sell_joined_candidates: `118`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 2938 | 21 | -0.7655 | 0.7506 | 0.7959 | -0.8394 |
| exit_only | 3439 | 91 | 0.7247 | 1.0697 | 1.1804 | -1.2783 |
| hold_defer | 10 | 4 | 1.101 | 0.071 | 0.069 | -1.179 |
| pyramid_wait | 1666 | 2 | 0.7191 | 0.233 | 0.411 | -0.795 |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 3 | 0 | -0.37 | 0.14 | - | - |
| exit_only | 96 | 3 | -2.3836 | 2.159 | 1.3043 | -1.1763 |
| hold_defer | 7937 | 107 | 0.209 | 0.764 | 1.1286 | -1.1897 |
| pyramid_wait | 7 | 4 | 1.7314 | 0.0414 | 0.069 | -1.179 |

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
