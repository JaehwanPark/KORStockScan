# Statistical Action Weight Report - 2026-05-27

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 13 |
| exit_only | 13 |
| avg_down_wait | 0 |
| pyramid_wait | 0 |
| compact_exit_signal | 253 |
| compact_sell_completed | 5 |
| compact_scale_in_executed | 77 |
| compact_decision_snapshot | 12597 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 13 |
| volume_known | 12 |
| time_known | 13 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 4 |
| insufficient_sample | 7 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| price_gte_70k | exit_only | -0.8042 | - | 9 | 0.39 | 0.4444 | candidate_weight_source |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -1.0649 | - | 5 | -0.59 | 0.4 | candidate_weight_source |
| volume_500k_2m | exit_only | -1.2622 | - | 5 | 0.46 | 0.4 | candidate_weight_source |
| volume_gte_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_lt_500k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_unknown | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_0930_1030 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_1030_1400 | exit_only | -1.2091 | - | 6 | 0.4567 | 0.5 | candidate_weight_source |
| time_1400_1530 | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `12597`
- sample_candidates: `12551`
- post_sell_joined_candidates: `492`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 7534 | 372 | -1.0068 | 1.0468 | 0.7071 | -4.3726 |
| exit_only | 3344 | 97 | -0.2097 | 1.2382 | 0.7204 | -6.2131 |
| hold_defer | 7 | 7 | 3.0914 | 0.02 | 1.7476 | -13.4036 |
| pyramid_wait | 1666 | 16 | 0.4709 | 0.2962 | 1.156 | -8.4482 |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| exit_only | 159 | 3 | -16.2625 | 16.1595 | 1.135 | -10.378 |
| hold_defer | 12378 | 475 | -0.3989 | 0.8039 | 0.7069 | -4.7147 |
| pyramid_wait | 7 | 7 | 3.0914 | 0.02 | 1.7476 | -13.4036 |

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
