# Statistical Action Weight Report - 2026-06-11

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 41 |
| exit_only | 39 |
| avg_down_wait | 0 |
| pyramid_wait | 2 |
| compact_exit_signal | 330 |
| compact_sell_completed | 2 |
| compact_scale_in_executed | 2 |
| compact_decision_snapshot | 7053 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 41 |
| volume_known | 35 |
| time_known | 41 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 8 |
| insufficient_sample | 2 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.6594 | - | 6 | 1.3383 | 0.3333 | candidate_weight_source |
| price_gte_70k | exit_only | -0.6512 | - | 33 | -0.3782 | 0.5152 | candidate_weight_source |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -0.7953 | - | 18 | -0.5211 | 0.5 | candidate_weight_source |
| volume_500k_2m | exit_only | -0.8891 | - | 10 | -0.313 | 0.5 | candidate_weight_source |
| volume_gte_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_lt_500k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_unknown | exit_only | -1.0024 | - | 5 | -0.154 | 0.6 | candidate_weight_source |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0930_1030 | exit_only | -0.6492 | - | 8 | 0.2213 | 0.375 | candidate_weight_source |
| time_1030_1400 | exit_only | -0.4988 | - | 26 | -0.0458 | 0.5 | candidate_weight_source |
| time_1400_1530 | exit_only | -1.1742 | - | 5 | -1.006 | 0.6 | candidate_weight_source |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `7053`
- sample_candidates: `6942`
- post_sell_joined_candidates: `33`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 4476 | 21 | -0.8177 | 0.8956 | 0.538 | -11.53 |
| exit_only | 594 | 2 | 0.1914 | 1.2333 | 0.538 | -11.53 |
| hold_defer | 3 | 0 | 1.95 | 0.08 | - | - |
| pyramid_wait | 1869 | 10 | 0.5696 | 0.2486 | 0.538 | -11.53 |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| exit_only | 187 | 1 | -2.3803 | 2.2721 | 0.538 | -11.53 |
| hold_defer | 6749 | 32 | -0.3026 | 0.7084 | 0.538 | -11.53 |
| pyramid_wait | 3 | 0 | 1.95 | 0.08 | - | - |

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
