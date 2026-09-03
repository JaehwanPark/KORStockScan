# Statistical Action Weight Report - 2026-09-03

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 14 |
| exit_only | 14 |
| avg_down_wait | 0 |
| pyramid_wait | 0 |
| compact_exit_signal | 16 |
| compact_sell_completed | 3 |
| compact_scale_in_executed | 0 |
| compact_decision_snapshot | 856 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 14 |
| volume_known | 13 |
| time_known | 14 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 4 |
| insufficient_sample | 7 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.4613 | - | 11 | 0.1109 | 0.2727 | candidate_weight_source |
| price_gte_70k | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_500k_2m | exit_only | -1.3744 | - | 5 | -1.022 | 0.4 | candidate_weight_source |
| volume_gte_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_lt_500k | exit_only | -0.7679 | - | 5 | 0.046 | 0.4 | candidate_weight_source |
| volume_unknown | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_0930_1030 | exit_only | -0.7406 | - | 5 | -0.266 | 0.2 | candidate_weight_source |
| time_1030_1400 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_outside_regular | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `856`
- sample_candidates: `1705`
- post_sell_joined_candidates: `229`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 801 | 115 | -1.0874 | 1.0125 | 0.532 | -0.177 |
| exit_only | 850 | 114 | -0.9885 | 0.9505 | 0.532 | -0.177 |
| hold_defer | 13 | 0 | -0.5992 | 0.3962 | - | - |
| pyramid_wait | 41 | 0 | 0.562 | 0.1559 | - | - |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 10 | 0 | -0.881 | 0.515 | - | - |
| exit_only | 5 | 1 | -3.112 | 2.924 | 0.532 | -0.177 |
| hold_defer | 837 | 114 | -0.9945 | 0.9591 | 0.532 | -0.177 |
| pyramid_wait | 3 | 0 | 0.34 | 0 | - | - |

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
