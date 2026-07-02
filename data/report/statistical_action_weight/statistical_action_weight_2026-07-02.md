# Statistical Action Weight Report - 2026-07-02

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `True`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 112 |
| exit_only | 92 |
| avg_down_wait | 19 |
| pyramid_wait | 1 |
| compact_exit_signal | 766 |
| compact_sell_completed | 19 |
| compact_scale_in_executed | 5 |
| compact_decision_snapshot | 3083 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 112 |
| volume_known | 104 |
| time_known | 112 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 11 |
| defensive_only_high_loss_rate | 2 |
| insufficient_sample | 1 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.4396 | 1.4355 | 26 | 0.0304 | 0.4231 | candidate_weight_source |
| price_30k_70k | exit_only | -0.0914 | - | 23 | 0.3157 | 0.3913 | candidate_weight_source |
| price_gte_70k | exit_only | -0.2052 | 0.4402 | 34 | 0.2991 | 0.4118 | candidate_weight_source |
| price_lt_10k | exit_only | -0.9534 | - | 9 | -0.3378 | 0.5556 | candidate_weight_source |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -1.5839 | - | 9 | -1.2433 | 0.6667 | defensive_only_high_loss_rate |
| volume_500k_2m | exit_only | 0.2475 | 1.6865 | 40 | 0.6152 | 0.375 | candidate_weight_source |
| volume_gte_10m | exit_only | -0.6641 | - | 5 | 0.582 | 0.2 | candidate_weight_source |
| volume_lt_500k | exit_only | -0.2296 | - | 33 | 0.1761 | 0.4242 | candidate_weight_source |
| volume_unknown | exit_only | -2.7685 | - | 5 | -1.392 | 0.6 | candidate_weight_source |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_0930_1030 | exit_only | -0.3851 | - | 14 | 0.2521 | 0.2857 | candidate_weight_source |
| time_1030_1400 | exit_only | 0.395 | 1.0703 | 23 | 1.1639 | 0.1739 | candidate_weight_source |
| time_1400_1530 | exit_only | -0.1777 | - | 10 | 0.311 | 0.7 | defensive_only_high_loss_rate |
| time_outside_regular | exit_only | -0.8392 | 1.5981 | 41 | -0.5429 | 0.561 | candidate_weight_source |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `3083`
- sample_candidates: `2833`
- post_sell_joined_candidates: `557`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 2298 | 437 | -1.6768 | 1.5584 | 0.7795 | -4.3175 |
| exit_only | 91 | 32 | -0.5665 | 1.3423 | 2.2009 | -13.6119 |
| hold_defer | 61 | 21 | 1.0856 | 0.1884 | 3.3034 | -20.2572 |
| large_sell_detected | 9 | 0 | 2.0556 | 0 | - | - |
| micro_vwap_missing | 4 | 0 | 1.9125 | 0 | - | - |
| micro_vwap_overheated | 33 | 6 | 2.2536 | 0 | 2.7617 | -31.7033 |
| pyramid_wait | 320 | 59 | 0.6515 | 0.1635 | 2.2427 | -19.1912 |
| tick_accel_below_min | 17 | 2 | 2.1382 | 0 | 2.91 | -39.0165 |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 21 | 0 | -0.6795 | 0.4481 | - | - |
| exit_only | 392 | 25 | -4.1171 | 3.9117 | 0.1707 | -1.1746 |
| hold_defer | 2256 | 482 | -0.9524 | 0.9799 | 0.9746 | -6.2238 |
| pyramid_wait | 40 | 21 | 2.0122 | 0.052 | 3.3034 | -20.2572 |

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
