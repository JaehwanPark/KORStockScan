# Statistical Action Weight Report - 2026-07-10

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `True`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 85 |
| exit_only | 72 |
| avg_down_wait | 11 |
| pyramid_wait | 2 |
| compact_exit_signal | 17 |
| compact_sell_completed | 9 |
| compact_scale_in_executed | 3 |
| compact_decision_snapshot | 1206 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 85 |
| volume_known | 75 |
| time_known | 85 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 13 |
| insufficient_sample | 1 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | avg_down_wait | -1.3341 | 0.451 | 5 | -0.388 | 0.4 | candidate_weight_source |
| price_30k_70k | exit_only | -0.4646 | - | 15 | 0.946 | 0.2 | candidate_weight_source |
| price_gte_70k | exit_only | -0.6542 | - | 11 | 0.1191 | 0.3636 | candidate_weight_source |
| price_lt_10k | exit_only | -1.3282 | - | 17 | -0.7606 | 0.4706 | candidate_weight_source |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -1.2379 | - | 10 | -0.455 | 0.3 | candidate_weight_source |
| volume_500k_2m | exit_only | -1.0076 | - | 14 | -0.195 | 0.3571 | candidate_weight_source |
| volume_gte_10m | exit_only | -1.7028 | - | 12 | -0.7208 | 0.5833 | candidate_weight_source |
| volume_lt_500k | exit_only | -0.9639 | - | 27 | -0.2889 | 0.4444 | candidate_weight_source |
| volume_unknown | exit_only | -2.2711 | - | 9 | -1.3478 | 0.4444 | candidate_weight_source |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_0930_1030 | exit_only | -0.348 | - | 8 | 1.5387 | 0.25 | candidate_weight_source |
| time_1030_1400 | exit_only | -1.7661 | - | 25 | -1.3112 | 0.48 | candidate_weight_source |
| time_1400_1530 | exit_only | -0.8513 | - | 8 | -0.1212 | 0.5 | candidate_weight_source |
| time_outside_regular | exit_only | -0.9851 | 1.0028 | 29 | -0.3293 | 0.4138 | candidate_weight_source |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `1206`
- sample_candidates: `1394`
- post_sell_joined_candidates: `346`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 975 | 153 | -0.8146 | 0.6256 | 2.0953 | -9.0497 |
| buy_pressure_below_min | 1 | 1 | 1.51 | 0 | 0.111 | -1.439 |
| buy_pressure_severe_below_min | 1 | 0 | 0.11 | 0.29 | - | - |
| exit_only | 56 | 2 | -0.3391 | 0.3691 | 0.696 | -1.2795 |
| fresh_micro_confirmation_missing | 27 | 22 | 0.4696 | 0.0841 | 0.9911 | -5.2157 |
| hold_defer | 56 | 2 | -0.3391 | 0.3691 | 0.696 | -1.2795 |
| large_sell_detected | 1 | 0 | 5.44 | 0 | - | - |
| micro_context_stale | 32 | 29 | 0.7834 | 0.0775 | 0.8412 | -4.1965 |
| micro_vwap_overheated | 3 | 3 | 2.5233 | 0 | 0.5563 | -1.2607 |
| pyramid_wait | 164 | 65 | 0.5502 | 0.0767 | 0.4551 | -2.9601 |
| quote_stale | 11 | 9 | 0.2491 | 0.0855 | 0.9143 | -4.3207 |
| tick_accel_below_min | 1 | 1 | 2.91 | 0 | 1.447 | -0.904 |
| tick_accel_stale | 34 | 30 | 0.7956 | 0.0729 | 0.8113 | -4.1118 |
| tick_aggressor_pressure_unusable | 32 | 29 | 0.8284 | 0.0653 | 0.8165 | -4.2373 |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 35 | 0 | -0.8437 | 0.5757 | - | - |
| exit_only | 5 | 3 | -3.6 | 3.818 | 6.356 | -11.1277 |
| hold_defer | 1134 | 215 | -0.6049 | 0.5321 | 1.54 | -7.1797 |
| pyramid_wait | 21 | 2 | 0.5019 | 0.0248 | 0.696 | -1.2795 |

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
