# Statistical Action Weight Report - 2026-07-16

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 33 |
| exit_only | 26 |
| avg_down_wait | 3 |
| pyramid_wait | 4 |
| compact_exit_signal | 8 |
| compact_sell_completed | 1 |
| compact_scale_in_executed | 2 |
| compact_decision_snapshot | 490 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 33 |
| volume_known | 32 |
| time_known | 33 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 4 |
| defensive_only_high_loss_rate | 5 |
| insufficient_sample | 4 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -1.3233 | - | 8 | -0.8562 | 0.625 | candidate_weight_source |
| price_30k_70k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| price_gte_70k | exit_only | -1.1185 | - | 9 | -0.4789 | 0.5556 | candidate_weight_source |
| price_lt_10k | exit_only | -1.1376 | - | 8 | -0.6075 | 0.75 | defensive_only_high_loss_rate |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -1.7925 | - | 6 | -1.3983 | 0.8333 | defensive_only_high_loss_rate |
| volume_500k_2m | exit_only | -0.91 | - | 10 | -0.14 | 0.3 | candidate_weight_source |
| volume_gte_10m | exit_only | -1.0082 | - | 8 | -0.5787 | 0.875 | defensive_only_high_loss_rate |
| volume_lt_500k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_unknown | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0930_1030 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_1030_1400 | exit_only | -1.4619 | - | 11 | -0.9618 | 0.4545 | candidate_weight_source |
| time_1400_1530 | exit_only | -1.1266 | - | 7 | -0.6243 | 0.8571 | defensive_only_high_loss_rate |
| time_outside_regular | exit_only | -0.5737 | - | 6 | -0.275 | 0.8333 | defensive_only_high_loss_rate |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `490`
- sample_candidates: `1017`
- post_sell_joined_candidates: `0`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 422 | 0 | -0.9903 | 0.7546 | - | - |
| buy_pressure_below_min | 8 | 0 | 1.56 | 0.0088 | - | - |
| exit_only | 482 | 0 | -0.7441 | 0.6436 | - | - |
| hold_defer | 3 | 0 | -1.2967 | 0.7133 | - | - |
| micro_context_stale | 17 | 0 | 1.6853 | 0.0212 | - | - |
| pyramid_wait | 61 | 0 | 0.91 | 0.0446 | - | - |
| tick_accel_below_min | 2 | 0 | 1.61 | 0 | - | - |
| tick_accel_stale | 17 | 0 | 1.6853 | 0.0212 | - | - |
| tick_aggressor_pressure_unusable | 5 | 0 | 1.82 | 0 | - | - |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 3 | 0 | -1.2967 | 0.7133 | - | - |
| exit_only | 4 | 0 | -1.905 | 3.265 | - | - |
| hold_defer | 479 | 0 | -0.7406 | 0.6432 | - | - |

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
