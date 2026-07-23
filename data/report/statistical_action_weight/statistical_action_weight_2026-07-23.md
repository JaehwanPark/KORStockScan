# Statistical Action Weight Report - 2026-07-23

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 54 |
| exit_only | 51 |
| avg_down_wait | 3 |
| pyramid_wait | 0 |
| compact_exit_signal | 203 |
| compact_sell_completed | 12 |
| compact_scale_in_executed | 3 |
| compact_decision_snapshot | 708 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 54 |
| volume_known | 53 |
| time_known | 54 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 9 |
| insufficient_sample | 5 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.563 | - | 21 | -0.1267 | 0.4286 | candidate_weight_source |
| price_30k_70k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| price_gte_70k | exit_only | -1.0332 | - | 11 | -0.7718 | 0.4545 | candidate_weight_source |
| price_lt_10k | exit_only | -0.1981 | - | 17 | 0.2359 | 0.3529 | candidate_weight_source |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -0.3652 | - | 17 | 0.2206 | 0.2941 | candidate_weight_source |
| volume_500k_2m | exit_only | -0.5019 | - | 21 | -0.1862 | 0.3333 | candidate_weight_source |
| volume_gte_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_lt_500k | exit_only | -1.2207 | - | 8 | -0.7925 | 0.625 | candidate_weight_source |
| volume_unknown | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_0930_1030 | exit_only | -0.5707 | - | 8 | -0.0375 | 0.25 | candidate_weight_source |
| time_1030_1400 | exit_only | -0.275 | - | 25 | 0.1328 | 0.36 | candidate_weight_source |
| time_1400_1530 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_outside_regular | exit_only | -0.6565 | - | 15 | -0.2507 | 0.4667 | candidate_weight_source |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `708`
- sample_candidates: `1031`
- post_sell_joined_candidates: `208`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 385 | 50 | -0.9347 | 1.1999 | 3.1349 | -1.7829 |
| exit_only | 508 | 94 | -0.6037 | 0.898 | 2.0571 | -1.1236 |
| fresh_micro_confirmation_missing | 6 | 6 | 0.3917 | 0.1067 | 1.6925 | -1.3973 |
| hold_defer | 1 | 1 | 0.75 | 0 | -0.054 | -0.812 |
| micro_context_stale | 4 | 4 | 0.4475 | 0.095 | 1.3137 | -0.7353 |
| micro_vwap_severe_overheated | 2 | 2 | 0.28 | 0.13 | 2.45 | -2.7215 |
| pyramid_wait | 118 | 44 | 0.2903 | 0.0748 | 1.1265 | -0.8718 |
| quote_stale | 2 | 2 | 0.275 | 0.19 | 0 | -0.596 |
| tick_accel_stale | 4 | 4 | 0.4475 | 0.095 | 1.3137 | -0.7353 |
| tick_aggressor_pressure_unusable | 1 | 1 | 0.52 | 0 | 5.309 | -0.937 |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| exit_only | 6 | 6 | -2.01 | 2.555 | 2.2375 | -4.2242 |
| hold_defer | 507 | 93 | -0.6064 | 0.8998 | 2.0798 | -1.1269 |
| pyramid_wait | 1 | 1 | 0.75 | 0 | -0.054 | -0.812 |

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
