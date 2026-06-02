# Statistical Action Weight Report - 2026-06-02

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 43 |
| exit_only | 42 |
| avg_down_wait | 0 |
| pyramid_wait | 1 |
| compact_exit_signal | 379 |
| compact_sell_completed | 17 |
| compact_scale_in_executed | 8 |
| compact_decision_snapshot | 13411 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 43 |
| volume_known | 36 |
| time_known | 43 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 9 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.8614 | - | 14 | -0.5121 | 0.3571 | candidate_weight_source |
| price_gte_70k | exit_only | -0.7065 | - | 28 | -0.2875 | 0.4643 | candidate_weight_source |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -0.9805 | - | 14 | -0.5221 | 0.4286 | candidate_weight_source |
| volume_500k_2m | exit_only | -0.5376 | - | 9 | 0.7567 | 0.3333 | candidate_weight_source |
| volume_gte_10m | exit_only | -1.2624 | - | 12 | -1.0033 | 0.5833 | candidate_weight_source |
| volume_unknown | exit_only | -0.8583 | - | 7 | -0.3829 | 0.2857 | candidate_weight_source |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0930_1030 | exit_only | -1.2305 | - | 7 | -0.67 | 0.5714 | candidate_weight_source |
| time_1030_1400 | exit_only | -0.6946 | - | 30 | -0.3417 | 0.4 | candidate_weight_source |
| time_1400_1530 | exit_only | -1.3313 | - | 5 | -0.056 | 0.4 | candidate_weight_source |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `13411`
- sample_candidates: `13403`
- post_sell_joined_candidates: `1014`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 6851 | 246 | -0.7972 | 0.8212 | 1.2696 | -2.3686 |
| exit_only | 4691 | 436 | -0.1342 | 1.2509 | 1.2137 | -2.8545 |
| hold_defer | 97 | 96 | 2.0742 | 0.0997 | 1.4162 | -4.3218 |
| pyramid_wait | 1764 | 236 | 0.5376 | 0.2748 | 0.9846 | -5.9142 |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 1 | 0 | -0.52 | 0.29 | - | - |
| exit_only | 250 | 6 | -3.1634 | 3.2155 | 1.067 | -1.3577 |
| hold_defer | 12959 | 816 | -0.3514 | 0.8616 | 1.1416 | -3.4313 |
| pyramid_wait | 96 | 96 | 2.1012 | 0.0977 | 1.4162 | -4.3218 |

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
