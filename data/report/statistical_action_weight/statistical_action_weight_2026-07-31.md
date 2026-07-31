# Statistical Action Weight Report - 2026-07-31

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 26 |
| exit_only | 26 |
| avg_down_wait | 0 |
| pyramid_wait | 0 |
| compact_exit_signal | 8 |
| compact_sell_completed | 5 |
| compact_scale_in_executed | 0 |
| compact_decision_snapshot | 610 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 26 |
| volume_known | 26 |
| time_known | 26 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 5 |
| insufficient_sample | 8 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -1.0216 | - | 9 | -0.1889 | 0.4444 | candidate_weight_source |
| price_30k_70k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| price_gte_70k | exit_only | -0.5168 | - | 12 | 0.0675 | 0.1667 | candidate_weight_source |
| price_lt_10k | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_500k_2m | exit_only | -1.0469 | - | 14 | -0.4914 | 0.3571 | candidate_weight_source |
| volume_gte_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_lt_500k | exit_only | -1.1338 | - | 8 | -0.3425 | 0.375 | candidate_weight_source |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_0930_1030 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_1030_1400 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_1400_1530 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_outside_regular | exit_only | -1.3256 | - | 18 | -0.9178 | 0.4444 | candidate_weight_source |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `610`
- sample_candidates: `1218`
- post_sell_joined_candidates: `44`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 554 | 7 | -1.3271 | 1.6462 | 1.2474 | -0.6777 |
| exit_only | 606 | 20 | -1.1778 | 1.5124 | 1.1886 | -0.7116 |
| hold_defer | 13 | 2 | 0.0223 | 0.2892 | 0.365 | -1.186 |
| large_sell_detected | 5 | 4 | 0.374 | 0.036 | 0.365 | -1.186 |
| pyramid_wait | 40 | 11 | 0.4293 | 0.1147 | 1.3009 | -0.6469 |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 5 | 0 | -0.854 | 0.624 | - | - |
| exit_only | 1 | 0 | -4.05 | 3.82 | - | - |
| hold_defer | 593 | 18 | -1.2041 | 1.5392 | 1.2801 | -0.6589 |
| pyramid_wait | 8 | 2 | 0.57 | 0.08 | 0.365 | -1.186 |

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
