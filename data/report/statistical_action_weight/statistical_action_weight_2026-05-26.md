# Statistical Action Weight Report - 2026-05-26

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 10 |
| exit_only | 10 |
| avg_down_wait | 0 |
| pyramid_wait | 0 |
| compact_exit_signal | 242 |
| compact_sell_completed | 7 |
| compact_scale_in_executed | 49 |
| compact_decision_snapshot | 16461 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 10 |
| volume_known | 10 |
| time_known | 10 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 3 |
| insufficient_sample | 6 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.7256 | - | 5 | -0.366 | 0.4 | candidate_weight_source |
| price_gte_70k | exit_only | -1.1725 | - | 5 | 0.542 | 0.4 | candidate_weight_source |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_500k_2m | exit_only | -0.562 | - | 5 | 0.472 | 0.2 | candidate_weight_source |
| volume_lt_500k | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_0930_1030 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_1030_1400 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_1400_1530 | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `16461`
- sample_candidates: `16391`
- post_sell_joined_candidates: `553`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 8199 | 62 | -0.8858 | 1.1162 | 0.8238 | -9.8682 |
| exit_only | 5666 | 198 | 0.0939 | 1.2853 | 0.7914 | -17.6234 |
| hold_defer | 8 | 8 | 2.4438 | 0.055 | 1.8619 | -8.211 |
| pyramid_wait | 2518 | 285 | 0.5213 | 0.2392 | -0.0799 | -18.7921 |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| exit_only | 125 | 3 | -13.5315 | 13.5534 | 0.766 | -10.51 |
| hold_defer | 16250 | 534 | -0.2305 | 0.9441 | 0.3142 | -17.5277 |
| pyramid_wait | 8 | 8 | 2.4438 | 0.055 | 1.8619 | -8.211 |

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
