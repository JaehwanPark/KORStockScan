# Statistical Action Weight Report - 2026-07-21

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 38 |
| exit_only | 33 |
| avg_down_wait | 2 |
| pyramid_wait | 3 |
| compact_exit_signal | 3 |
| compact_sell_completed | 3 |
| compact_scale_in_executed | 0 |
| compact_decision_snapshot | 528 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 38 |
| volume_known | 37 |
| time_known | 38 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 7 |
| defensive_only_high_loss_rate | 2 |
| insufficient_sample | 4 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.8699 | - | 12 | -0.4658 | 0.5 | candidate_weight_source |
| price_30k_70k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| price_gte_70k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| price_lt_10k | exit_only | -0.0554 | - | 17 | 0.2606 | 0.4118 | candidate_weight_source |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -0.4831 | - | 17 | -0.1 | 0.4118 | candidate_weight_source |
| volume_500k_2m | exit_only | -0.7136 | - | 9 | -0.14 | 0.4444 | candidate_weight_source |
| volume_gte_10m | exit_only | -0.1831 | - | 6 | -0.1367 | 0.6667 | defensive_only_high_loss_rate |
| volume_lt_500k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_unknown | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0930_1030 | exit_only | -0.1652 | - | 5 | 0.492 | 0.2 | candidate_weight_source |
| time_1030_1400 | exit_only | -0.514 | - | 15 | -0.0473 | 0.4 | candidate_weight_source |
| time_1400_1530 | exit_only | -0.1865 | - | 8 | -0.0325 | 0.5 | candidate_weight_source |
| time_outside_regular | exit_only | -1.3228 | - | 5 | -1.204 | 1 | defensive_only_high_loss_rate |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `528`
- sample_candidates: `1072`
- post_sell_joined_candidates: `218`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 474 | 104 | -0.876 | 0.7195 | 1.1674 | -0.2938 |
| exit_only | 525 | 104 | -0.7472 | 0.6422 | 1.1153 | -0.414 |
| fresh_micro_confirmation_missing | 2 | 2 | 0.305 | 0.06 | 0.98 | -8.878 |
| micro_context_stale | 6 | 2 | 1.1417 | 0.0867 | 0.98 | -8.878 |
| pyramid_wait | 53 | 2 | 0.3562 | 0.0098 | 0.98 | -8.878 |
| quote_stale | 1 | 1 | 0.54 | 0 | 0.842 | -17.508 |
| tick_accel_stale | 6 | 2 | 1.1417 | 0.0867 | 0.98 | -8.878 |
| tick_aggressor_pressure_unusable | 5 | 1 | 1.262 | 0.104 | 1.118 | -0.248 |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| exit_only | 2 | 2 | -2.03 | 2.215 | 3.6885 | -2.6275 |
| hold_defer | 525 | 104 | -0.7472 | 0.6422 | 1.1153 | -0.414 |

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
