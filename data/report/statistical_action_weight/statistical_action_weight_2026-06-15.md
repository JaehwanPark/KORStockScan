# Statistical Action Weight Report - 2026-06-15

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 21 |
| exit_only | 19 |
| avg_down_wait | 0 |
| pyramid_wait | 2 |
| compact_exit_signal | 125 |
| compact_sell_completed | 1 |
| compact_scale_in_executed | 14 |
| compact_decision_snapshot | 7849 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 21 |
| volume_known | 18 |
| time_known | 21 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 6 |
| insufficient_sample | 3 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.3751 | - | 8 | 0.78 | 0.5 | candidate_weight_source |
| price_gte_70k | exit_only | -0.6441 | - | 11 | -0.2209 | 0.5455 | candidate_weight_source |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -0.3693 | - | 8 | 0.7338 | 0.375 | candidate_weight_source |
| volume_500k_2m | exit_only | -0.4881 | - | 7 | 0.5557 | 0.4286 | candidate_weight_source |
| volume_gte_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_unknown | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0930_1030 | exit_only | -0.1903 | - | 6 | 1.1883 | 0.3333 | candidate_weight_source |
| time_1030_1400 | exit_only | -0.5215 | - | 12 | -0.0008 | 0.5833 | candidate_weight_source |
| time_1400_1530 | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `7849`
- sample_candidates: `7901`
- post_sell_joined_candidates: `0`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 6209 | 0 | -0.9128 | 0.6676 | - | - |
| exit_only | 819 | 0 | -0.1712 | 1.0221 | - | - |
| hold_defer | 74 | 0 | 0.7784 | 0.2973 | - | - |
| pyramid_wait | 799 | 0 | 0.5399 | 0.2515 | - | - |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 31 | 0 | -0.9374 | 0.6823 | - | - |
| exit_only | 85 | 0 | -6.8592 | 6.3544 | - | - |
| hold_defer | 7668 | 0 | -0.6326 | 0.6027 | - | - |
| pyramid_wait | 43 | 0 | 2.0153 | 0.0198 | - | - |

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
