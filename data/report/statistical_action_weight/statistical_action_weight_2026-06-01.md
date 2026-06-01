# Statistical Action Weight Report - 2026-06-01

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 33 |
| exit_only | 33 |
| avg_down_wait | 0 |
| pyramid_wait | 0 |
| compact_exit_signal | 365 |
| compact_sell_completed | 12 |
| compact_scale_in_executed | 0 |
| compact_decision_snapshot | 15758 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 33 |
| volume_known | 27 |
| time_known | 33 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 9 |
| insufficient_sample | 1 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.7936 | - | 14 | -0.3479 | 0.2857 | candidate_weight_source |
| price_gte_70k | exit_only | -1.0464 | - | 19 | -0.5247 | 0.5789 | candidate_weight_source |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -1.2935 | - | 10 | -0.906 | 0.5 | candidate_weight_source |
| volume_500k_2m | exit_only | -0.8296 | - | 9 | 0.5111 | 0.4444 | candidate_weight_source |
| volume_gte_10m | exit_only | -1.2968 | - | 8 | -0.7787 | 0.5 | candidate_weight_source |
| volume_unknown | exit_only | -0.9979 | - | 6 | -0.6917 | 0.3333 | candidate_weight_source |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_0930_1030 | exit_only | -1.279 | - | 7 | -0.5671 | 0.5714 | candidate_weight_source |
| time_1030_1400 | exit_only | -0.9279 | - | 19 | -0.46 | 0.4211 | candidate_weight_source |
| time_1400_1530 | exit_only | -0.8716 | - | 5 | 0.656 | 0.2 | candidate_weight_source |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `15758`
- sample_candidates: `15680`
- post_sell_joined_candidates: `785`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 6709 | 170 | -0.849 | 1.0068 | 0.7752 | -4.3543 |
| exit_only | 6535 | 403 | -0.1931 | 1.3635 | 1.2256 | -1.9212 |
| hold_defer | 21 | 19 | 1.7048 | 0.0743 | 2.6603 | -1.2023 |
| pyramid_wait | 2415 | 193 | 0.5627 | 0.2468 | 1.2194 | -1.7837 |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 1 | 0 | -0.35 | 0.12 | - | - |
| exit_only | 237 | 5 | -2.3124 | 2.4704 | 0.7018 | -4.7276 |
| hold_defer | 15401 | 742 | -0.3303 | 1.0177 | 1.0876 | -2.4424 |
| pyramid_wait | 20 | 19 | 1.8075 | 0.072 | 2.6603 | -1.2023 |

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
