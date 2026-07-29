# Statistical Action Weight Report - 2026-07-28

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 47 |
| exit_only | 44 |
| avg_down_wait | 3 |
| pyramid_wait | 0 |
| compact_exit_signal | 163 |
| compact_sell_completed | 12 |
| compact_scale_in_executed | 0 |
| compact_decision_snapshot | 154 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 47 |
| volume_known | 46 |
| time_known | 47 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 7 |
| defensive_only_high_loss_rate | 1 |
| insufficient_sample | 6 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.4183 | - | 20 | -0.0105 | 0.45 | candidate_weight_source |
| price_30k_70k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| price_gte_70k | exit_only | -0.7641 | - | 17 | -0.4453 | 0.3529 | candidate_weight_source |
| price_lt_10k | exit_only | -1.388 | - | 6 | -0.765 | 0.5 | candidate_weight_source |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -0.6365 | - | 5 | 0.26 | 0.4 | candidate_weight_source |
| volume_500k_2m | exit_only | -0.3831 | - | 23 | -0.0261 | 0.3043 | candidate_weight_source |
| volume_gte_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_lt_500k | exit_only | -1.465 | - | 11 | -1.2382 | 0.7273 | defensive_only_high_loss_rate |
| volume_unknown | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_0930_1030 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_1030_1400 | exit_only | -0.3788 | - | 13 | 0.0308 | 0.3077 | candidate_weight_source |
| time_1400_1530 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_outside_regular | exit_only | -0.5543 | - | 24 | -0.1808 | 0.4167 | candidate_weight_source |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `154`
- sample_candidates: `161`
- post_sell_joined_candidates: `102`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 64 | 35 | -1.7722 | 1.672 | 0.2017 | -1.3201 |
| exit_only | 79 | 50 | -1.2161 | 1.2248 | 0.4177 | -1.738 |
| pyramid_wait | 18 | 17 | 0.3917 | 0.0033 | 0.8546 | -2.6166 |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| exit_only | 3 | 2 | -3.4333 | 3.4367 | 0.3525 | -1.8945 |
| hold_defer | 79 | 50 | -1.2161 | 1.2248 | 0.4177 | -1.738 |

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
