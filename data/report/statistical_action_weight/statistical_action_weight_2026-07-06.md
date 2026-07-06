# Statistical Action Weight Report - 2026-07-06

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `True`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 148 |
| exit_only | 115 |
| avg_down_wait | 31 |
| pyramid_wait | 2 |
| compact_exit_signal | 152 |
| compact_sell_completed | 19 |
| compact_scale_in_executed | 6 |
| compact_decision_snapshot | 1994 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 148 |
| volume_known | 139 |
| time_known | 148 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 12 |
| defensive_only_high_loss_rate | 1 |
| insufficient_sample | 1 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.5161 | 1.1794 | 33 | -0.0706 | 0.4242 | candidate_weight_source |
| price_30k_70k | exit_only | 0.2988 | 1.6711 | 25 | 0.7604 | 0.24 | candidate_weight_source |
| price_gte_70k | exit_only | -0.173 | 0.6436 | 36 | 0.2706 | 0.3889 | candidate_weight_source |
| price_lt_10k | exit_only | -0.0767 | - | 21 | 0.3829 | 0.381 | candidate_weight_source |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -0.6579 | - | 15 | -0.0347 | 0.4 | candidate_weight_source |
| volume_500k_2m | exit_only | 0.2055 | 1.7339 | 43 | 0.5379 | 0.3488 | candidate_weight_source |
| volume_gte_10m | exit_only | -0.498 | - | 9 | 0.9678 | 0.3333 | candidate_weight_source |
| volume_lt_500k | exit_only | -0.0872 | 1.2131 | 42 | 0.246 | 0.3333 | candidate_weight_source |
| volume_unknown | exit_only | -2.2584 | - | 6 | -1.1983 | 0.6667 | defensive_only_high_loss_rate |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_0930_1030 | exit_only | -0.4313 | - | 14 | 0.1036 | 0.2857 | candidate_weight_source |
| time_1030_1400 | exit_only | 0.3887 | 0.7403 | 31 | 0.9713 | 0.1613 | candidate_weight_source |
| time_1400_1530 | exit_only | 0.236 | - | 17 | 1.0112 | 0.4706 | candidate_weight_source |
| time_outside_regular | exit_only | -0.6511 | 0.8777 | 50 | -0.387 | 0.5 | candidate_weight_source |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `1994`
- sample_candidates: `2138`
- post_sell_joined_candidates: `473`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ai_score_below_min | 2 | 2 | 0.335 | 0.565 | 1.2135 | -6.0795 |
| ai_score_unavailable | 11 | 9 | 0.2755 | 0.3091 | 0.8717 | -5.9293 |
| avg_down_wait | 1561 | 300 | -1.0931 | 1.0194 | 1.5049 | -3.6185 |
| buy_pressure_below_min | 2 | 1 | 2.05 | 0 | 5.87 | -1.03 |
| buy_pressure_severe_below_min | 1 | 0 | 0.15 | 0.19 | - | - |
| exit_only | 42 | 1 | -1.0831 | 1.2679 | 0 | -0.833 |
| fresh_micro_confirmation_missing | 41 | 19 | 1.0668 | 0.2576 | 0.6232 | -6.183 |
| hold_defer | 30 | 1 | 0.092 | 0.252 | 0 | -0.833 |
| large_sell_detected | 8 | 4 | 1.8263 | 0.0475 | 1.6078 | -8.0055 |
| micro_context_stale | 57 | 25 | 1.1463 | 0.1939 | 0.7999 | -4.0277 |
| micro_vwap_missing | 1 | 0 | 0.14 | 0 | - | - |
| pyramid_wait | 255 | 52 | 0.7083 | 0.2116 | 0.9526 | -3.9309 |
| quote_age_gt_max | 1 | 0 | -3.96 | 3.88 | - | - |
| quote_stale | 27 | 14 | 0.3456 | 0.3619 | 0.4541 | -5.0726 |
| tick_accel_below_min | 1 | 0 | 1.41 | 0 | - | - |
| tick_accel_stale | 57 | 25 | 1.1463 | 0.1939 | 0.7999 | -4.0277 |
| tick_aggressor_pressure_unusable | 41 | 20 | 0.9359 | 0.2271 | 0.3765 | -4.6456 |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 14 | 0 | -0.7543 | 0.49 | - | - |
| exit_only | 11 | 2 | -4.0836 | 3.7345 | 0.872 | -6.692 |
| hold_defer | 1817 | 350 | -0.8415 | 0.908 | 1.4265 | -3.6473 |
| pyramid_wait | 16 | 1 | 0.8325 | 0.0437 | 0 | -0.833 |

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
