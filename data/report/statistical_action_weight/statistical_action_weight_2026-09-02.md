# Statistical Action Weight Report - 2026-09-02

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 13 |
| exit_only | 13 |
| avg_down_wait | 0 |
| pyramid_wait | 0 |
| compact_exit_signal | 11 |
| compact_sell_completed | 0 |
| compact_scale_in_executed | 0 |
| compact_decision_snapshot | 638 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 13 |
| volume_known | 11 |
| time_known | 13 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 2 |
| insufficient_sample | 9 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.149 | - | 10 | 0.337 | 0.2 | candidate_weight_source |
| price_gte_70k | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_500k_2m | exit_only | -0.7086 | - | 6 | -0.0333 | 0.3333 | candidate_weight_source |
| volume_gte_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_lt_500k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_unknown | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_0930_1030 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_1030_1400 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_outside_regular | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `638`
- sample_candidates: `1266`
- post_sell_joined_candidates: `0`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 617 | 0 | -1.4924 | 1.3734 | - | - |
| buy_pressure_below_min | 1 | 0 | 1.57 | 0 | - | - |
| exit_only | 628 | 0 | -1.4204 | 1.3225 | - | - |
| hold_defer | 1 | 0 | -0.83 | 0.6 | - | - |
| micro_context_stale | 2 | 0 | 1.57 | 0.06 | - | - |
| pyramid_wait | 15 | 0 | 0.656 | 0.1047 | - | - |
| tick_accel_stale | 2 | 0 | 1.57 | 0.06 | - | - |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 1 | 0 | -0.83 | 0.6 | - | - |
| exit_only | 5 | 0 | -3.956 | 3.802 | - | - |
| hold_defer | 627 | 0 | -1.4214 | 1.3237 | - | - |

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
