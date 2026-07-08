# Statistical Action Weight Report - 2026-07-08

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `True`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 119 |
| exit_only | 95 |
| avg_down_wait | 23 |
| pyramid_wait | 1 |
| compact_exit_signal | 304 |
| compact_sell_completed | 20 |
| compact_scale_in_executed | 3 |
| compact_decision_snapshot | 2071 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 119 |
| volume_known | 108 |
| time_known | 119 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 13 |
| insufficient_sample | 1 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.879 | 0.645 | 36 | -0.3717 | 0.4444 | candidate_weight_source |
| price_30k_70k | exit_only | -0.0252 | - | 19 | 0.9626 | 0.1579 | candidate_weight_source |
| price_gte_70k | exit_only | -0.7704 | 1.4598 | 11 | -0.3818 | 0.4545 | candidate_weight_source |
| price_lt_10k | exit_only | -0.3174 | - | 29 | 0.1228 | 0.4138 | candidate_weight_source |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -0.632 | - | 8 | 0.6425 | 0.25 | candidate_weight_source |
| volume_500k_2m | exit_only | -0.0539 | 1.6999 | 29 | 0.4566 | 0.2759 | candidate_weight_source |
| volume_gte_10m | exit_only | -0.6601 | - | 13 | 0.6108 | 0.3077 | candidate_weight_source |
| volume_lt_500k | exit_only | -0.6521 | 0.7667 | 36 | -0.2294 | 0.4722 | candidate_weight_source |
| volume_unknown | exit_only | -2.0771 | - | 9 | -1.5322 | 0.5556 | candidate_weight_source |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_0930_1030 | exit_only | -0.6674 | - | 5 | 1.812 | 0.2 | candidate_weight_source |
| time_1030_1400 | exit_only | -0.9109 | 0.609 | 28 | -0.4029 | 0.3571 | candidate_weight_source |
| time_1400_1530 | exit_only | -0.0279 | - | 14 | 1.05 | 0.2857 | candidate_weight_source |
| time_outside_regular | exit_only | -0.4541 | 1.0652 | 46 | -0.0726 | 0.4348 | candidate_weight_source |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `2071`
- sample_candidates: `2104`
- post_sell_joined_candidates: `495`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 1446 | 298 | -1.5928 | 1.3163 | 3.0992 | -7.2743 |
| buy_pressure_below_min | 3 | 1 | 1.39 | 0.0733 | 3.18 | -25 |
| buy_pressure_severe_below_min | 3 | 3 | 0.4467 | 0.1033 | 0.782 | -5.8357 |
| exit_only | 101 | 43 | -2.1746 | 2.0529 | 0.4263 | -4.0534 |
| fresh_micro_confirmation_missing | 43 | 17 | 1.0993 | 0.1349 | 1.4299 | -16.7297 |
| hold_defer | 51 | 0 | -0.4625 | 0.5927 | - | - |
| large_sell_detected | 8 | 3 | 0.8225 | 0.02 | 0.0437 | -13.689 |
| micro_context_stale | 49 | 13 | 1.2504 | 0.0747 | 1.3355 | -13.0056 |
| micro_vwap_missing | 1 | 0 | 2.27 | 0 | - | - |
| micro_vwap_severe_overheated | 4 | 4 | 2.3875 | 0 | 1.546 | -12.8385 |
| pyramid_wait | 288 | 84 | 0.6699 | 0.1777 | 4.9185 | -9.4354 |
| quote_stale | 9 | 4 | 0.1167 | 0.18 | 1.2047 | -13.1795 |
| tick_accel_below_min | 2 | 2 | 3.32 | 0.11 | 3.1285 | -15.5 |
| tick_accel_stale | 55 | 13 | 1.2356 | 0.1156 | 1.3355 | -13.0056 |
| tick_aggressor_pressure_unusable | 41 | 10 | 1.009 | 0.1446 | 1.0777 | -12.8367 |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 34 | 0 | -0.9674 | 0.8538 | - | - |
| exit_only | 68 | 46 | -5.2512 | 4.7719 | 3.817 | -4.1767 |
| hold_defer | 1716 | 379 | -1.1359 | 1.0531 | 3.112 | -7.7638 |
| pyramid_wait | 17 | 0 | 0.5471 | 0.0706 | - | - |

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
