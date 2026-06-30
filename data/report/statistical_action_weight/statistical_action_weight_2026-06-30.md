# Statistical Action Weight Report - 2026-06-30

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 53 |
| exit_only | 51 |
| avg_down_wait | 1 |
| pyramid_wait | 1 |
| compact_exit_signal | 183 |
| compact_sell_completed | 34 |
| compact_scale_in_executed | 4 |
| compact_decision_snapshot | 7191 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 53 |
| volume_known | 46 |
| time_known | 53 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 9 |
| defensive_only_high_loss_rate | 2 |
| insufficient_sample | 3 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -1.0364 | - | 13 | -0.5869 | 0.6154 | candidate_weight_source |
| price_30k_70k | exit_only | -1.295 | - | 11 | -0.9336 | 0.5455 | candidate_weight_source |
| price_gte_70k | exit_only | -0.4719 | - | 24 | 0.3225 | 0.375 | candidate_weight_source |
| price_lt_10k | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -1.8862 | - | 5 | -2.208 | 1 | defensive_only_high_loss_rate |
| volume_500k_2m | exit_only | -0.4994 | - | 16 | -0.0956 | 0.5625 | candidate_weight_source |
| volume_gte_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_lt_500k | exit_only | -0.4471 | - | 21 | 0.3586 | 0.3333 | candidate_weight_source |
| volume_unknown | exit_only | -2.5499 | - | 6 | -1.1483 | 0.5 | candidate_weight_source |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_0930_1030 | exit_only | -0.7066 | - | 12 | 0.1625 | 0.25 | candidate_weight_source |
| time_1030_1400 | exit_only | -0.925 | - | 9 | 0.56 | 0.3333 | candidate_weight_source |
| time_1400_1530 | exit_only | -1.4822 | - | 5 | -0.754 | 0.8 | defensive_only_high_loss_rate |
| time_outside_regular | exit_only | -1.0839 | - | 24 | -0.5971 | 0.5833 | candidate_weight_source |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `7191`
- sample_candidates: `7340`
- post_sell_joined_candidates: `1330`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 4753 | 713 | -1.1488 | 1.2787 | 10.9739 | -2.9251 |
| exit_only | 606 | 117 | 2.9183 | 1.0251 | 2.5227 | -2.9451 |
| hold_defer | 295 | 73 | 5.0366 | 0.0785 | 1.0853 | -3.446 |
| pyramid_wait | 1686 | 427 | 0.622 | 0.3117 | 3.3785 | -2.4517 |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 24 | 1 | -0.8567 | 0.6125 | 1.695 | -3.178 |
| exit_only | 34 | 14 | -5.3385 | 5.2853 | 13.4548 | -4.4944 |
| hold_defer | 6716 | 1170 | -0.5878 | 1.0455 | 7.9441 | -2.703 |
| pyramid_wait | 271 | 72 | 5.5585 | 0.0312 | 1.0769 | -3.4497 |

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
