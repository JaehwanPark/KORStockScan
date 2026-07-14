# Statistical Action Weight Report - 2026-07-14

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 43 |
| exit_only | 37 |
| avg_down_wait | 5 |
| pyramid_wait | 1 |
| compact_exit_signal | 2 |
| compact_sell_completed | 2 |
| compact_scale_in_executed | 0 |
| compact_decision_snapshot | 748 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 43 |
| volume_known | 37 |
| time_known | 43 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 8 |
| defensive_only_high_loss_rate | 3 |
| insufficient_sample | 3 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -2.24 | - | 16 | -1.7012 | 0.625 | candidate_weight_source |
| price_30k_70k | exit_only | -2.1224 | - | 5 | -0.446 | 0.4 | candidate_weight_source |
| price_gte_70k | exit_only | -1.4231 | - | 9 | -0.3956 | 0.3333 | candidate_weight_source |
| price_lt_10k | exit_only | -2.4484 | - | 7 | -1.2014 | 0.7143 | defensive_only_high_loss_rate |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_500k_2m | exit_only | -1.4843 | - | 11 | -0.6209 | 0.3636 | candidate_weight_source |
| volume_gte_10m | exit_only | -2.2642 | - | 7 | -0.56 | 0.5714 | candidate_weight_source |
| volume_lt_500k | exit_only | -2.3809 | - | 10 | -1.863 | 0.7 | defensive_only_high_loss_rate |
| volume_unknown | exit_only | -2.9553 | - | 5 | -1.602 | 0.4 | candidate_weight_source |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_0930_1030 | exit_only | -0.8552 | - | 5 | 1.686 | 0.2 | candidate_weight_source |
| time_1030_1400 | exit_only | -1.7614 | - | 19 | -1.1611 | 0.4737 | candidate_weight_source |
| time_1400_1530 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_outside_regular | exit_only | -2.5343 | - | 10 | -2.164 | 0.7 | defensive_only_high_loss_rate |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `748`
- sample_candidates: `1498`
- post_sell_joined_candidates: `16`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 739 | 2 | -1.3181 | 1.1317 | 1.5425 | -1.035 |
| exit_only | 746 | 5 | -1.2992 | 1.1211 | 1.6422 | -1.1898 |
| fresh_micro_confirmation_missing | 1 | 1 | 1.01 | 0 | 1.044 | -0.261 |
| micro_context_stale | 1 | 1 | 3.13 | 0 | 2.041 | -1.809 |
| pyramid_wait | 7 | 3 | 0.6986 | 0 | 1.7087 | -1.293 |
| tick_accel_stale | 2 | 2 | 2.07 | 0 | 1.5425 | -1.035 |
| tick_aggressor_pressure_unusable | 2 | 2 | 2.07 | 0 | 1.5425 | -1.035 |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| hold_defer | 746 | 5 | -1.2992 | 1.1211 | 1.6422 | -1.1898 |

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
