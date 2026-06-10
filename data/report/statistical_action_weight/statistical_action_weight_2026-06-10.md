# Statistical Action Weight Report - 2026-06-10

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 47 |
| exit_only | 46 |
| avg_down_wait | 0 |
| pyramid_wait | 1 |
| compact_exit_signal | 436 |
| compact_sell_completed | 11 |
| compact_scale_in_executed | 1 |
| compact_decision_snapshot | 12690 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 47 |
| volume_known | 40 |
| time_known | 47 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 6 |
| defensive_only_high_loss_rate | 2 |
| insufficient_sample | 3 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.5531 | - | 7 | 1.2757 | 0.2857 | candidate_weight_source |
| price_30k_70k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| price_gte_70k | exit_only | -0.8003 | - | 38 | -0.5347 | 0.5526 | candidate_weight_source |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -0.4473 | - | 22 | 0.1236 | 0.4091 | candidate_weight_source |
| volume_500k_2m | exit_only | -0.8364 | - | 14 | -0.2643 | 0.5 | candidate_weight_source |
| volume_gte_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_lt_500k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_unknown | exit_only | -1.1783 | - | 6 | -0.49 | 0.6667 | defensive_only_high_loss_rate |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0930_1030 | exit_only | -0.9456 | - | 12 | -0.3917 | 0.5 | candidate_weight_source |
| time_1030_1400 | exit_only | -0.5243 | - | 28 | -0.0529 | 0.5 | candidate_weight_source |
| time_1400_1530 | exit_only | -1.3519 | - | 6 | -1.2633 | 0.6667 | defensive_only_high_loss_rate |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `12690`
- sample_candidates: `13031`
- post_sell_joined_candidates: `133`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 8045 | 4 | -0.9484 | 0.8963 | 0.8698 | -9.0005 |
| exit_only | 2835 | 52 | -0.4862 | 1.1337 | 1.1437 | -11.1825 |
| hold_defer | 411 | 34 | 1.4689 | 0.0944 | 1.1962 | -12.5141 |
| pyramid_wait | 1740 | 43 | 0.5049 | 0.3187 | 0.7045 | -5.3571 |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 124 | 0 | -1.0039 | 0.2281 | - | - |
| exit_only | 322 | 0 | -2.2648 | 1.8819 | - | - |
| hold_defer | 11887 | 65 | -0.6733 | 0.8694 | 0.8088 | -6.498 |
| pyramid_wait | 287 | 34 | 2.5373 | 0.0367 | 1.1962 | -12.5141 |

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
