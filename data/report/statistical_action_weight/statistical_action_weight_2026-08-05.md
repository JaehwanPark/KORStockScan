# Statistical Action Weight Report - 2026-08-05

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 33 |
| exit_only | 31 |
| avg_down_wait | 2 |
| pyramid_wait | 0 |
| compact_exit_signal | 4 |
| compact_sell_completed | 0 |
| compact_scale_in_executed | 0 |
| compact_decision_snapshot | 40 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 33 |
| volume_known | 33 |
| time_known | 33 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 7 |
| insufficient_sample | 6 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.4274 | - | 12 | 0.3483 | 0.3333 | candidate_weight_source |
| price_30k_70k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| price_gte_70k | exit_only | -0.3682 | - | 13 | 0.1923 | 0.2308 | candidate_weight_source |
| price_lt_10k | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_500k_2m | exit_only | -0.7717 | - | 15 | -0.1727 | 0.4667 | candidate_weight_source |
| volume_gte_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_lt_500k | exit_only | -0.0249 | - | 12 | 0.5708 | 0.0833 | candidate_weight_source |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | exit_only | -0.9366 | - | 6 | 0.0467 | 0.3333 | candidate_weight_source |
| time_0930_1030 | exit_only | 0.1395 | - | 15 | 0.7307 | 0.1333 | candidate_weight_source |
| time_1030_1400 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_1400_1530 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_outside_regular | exit_only | -0.9034 | - | 7 | 0.1814 | 0.4286 | candidate_weight_source |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `40`
- sample_candidates: `79`
- post_sell_joined_candidates: `0`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 33 | 0 | -1.5033 | 1.2797 | - | - |
| exit_only | 38 | 0 | -1.0918 | 1.0421 | - | - |
| fresh_micro_confirmation_missing | 1 | 0 | 1.56 | 0.11 | - | - |
| large_sell_detected | 1 | 0 | 1.56 | 0.11 | - | - |
| pyramid_wait | 6 | 0 | 0.79 | 0.0867 | - | - |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| exit_only | 1 | 0 | -3.38 | 3.15 | - | - |
| hold_defer | 38 | 0 | -1.0918 | 1.0421 | - | - |

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
