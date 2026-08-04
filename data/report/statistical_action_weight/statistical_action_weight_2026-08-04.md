# Statistical Action Weight Report - 2026-08-04

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 39 |
| exit_only | 37 |
| avg_down_wait | 2 |
| pyramid_wait | 0 |
| compact_exit_signal | 403 |
| compact_sell_completed | 14 |
| compact_scale_in_executed | 2 |
| compact_decision_snapshot | 1246 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 39 |
| volume_known | 39 |
| time_known | 39 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 8 |
| defensive_only_high_loss_rate | 1 |
| insufficient_sample | 4 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.7114 | - | 13 | 0.0392 | 0.3846 | candidate_weight_source |
| price_30k_70k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| price_gte_70k | exit_only | -0.3518 | - | 15 | 0.2113 | 0.2 | candidate_weight_source |
| price_lt_10k | exit_only | -0.145 | - | 5 | 0.846 | 0.2 | candidate_weight_source |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -1.3796 | - | 6 | -1.0483 | 0.6667 | defensive_only_high_loss_rate |
| volume_500k_2m | exit_only | -0.9074 | - | 18 | -0.37 | 0.3889 | candidate_weight_source |
| volume_gte_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_lt_500k | exit_only | -0.2335 | - | 11 | 0.51 | 0.1818 | candidate_weight_source |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | exit_only | -1.0528 | - | 6 | 0.0467 | 0.3333 | candidate_weight_source |
| time_0930_1030 | exit_only | 0.0688 | - | 15 | 0.7307 | 0.1333 | candidate_weight_source |
| time_1030_1400 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_1400_1530 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_outside_regular | exit_only | -1.0754 | - | 12 | -0.4667 | 0.4167 | candidate_weight_source |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `1246`
- sample_candidates: `2507`
- post_sell_joined_candidates: `1562`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 1159 | 738 | -1.2035 | 1.1552 | 1.4983 | -1.0113 |
| buy_pressure_severe_below_min | 5 | 5 | 0.28 | 0.216 | 0.6382 | -0.8188 |
| exit_only | 1234 | 763 | -1.0827 | 1.0752 | 1.4739 | -1.2113 |
| fresh_micro_confirmation_missing | 6 | 6 | 0.52 | 0 | 1.4182 | -9.9597 |
| hold_defer | 3 | 2 | 0.8033 | 0.08 | 0.299 | -0.838 |
| large_sell_detected | 1 | 1 | 1.39 | 0 | 2.265 | -13.724 |
| micro_context_stale | 4 | 3 | 0.46 | 0 | 1.6097 | -9.4287 |
| micro_vwap_severe_overheated | 5 | 5 | 0.79 | 0.012 | 0.9522 | -6.3594 |
| pyramid_wait | 80 | 30 | 0.4577 | 0.1268 | 1.046 | -5.8523 |
| tick_accel_below_min | 1 | 1 | 1.39 | 0.27 | 2.265 | -13.724 |
| tick_accel_stale | 5 | 4 | 0.528 | 0 | 1.3133 | -7.7222 |
| tick_aggressor_pressure_unusable | 4 | 4 | 0.37 | 0 | 1.3133 | -7.7222 |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| exit_only | 8 | 7 | -2.4663 | 2.8163 | 1.8777 | 0.1004 |
| hold_defer | 1231 | 761 | -1.0873 | 1.0776 | 1.477 | -1.2123 |
| pyramid_wait | 3 | 2 | 0.8033 | 0.08 | 0.299 | -0.838 |

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
