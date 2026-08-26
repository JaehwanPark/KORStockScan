# Statistical Action Weight Report - 2026-08-26

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 44 |
| exit_only | 42 |
| avg_down_wait | 1 |
| pyramid_wait | 1 |
| compact_exit_signal | 13 |
| compact_sell_completed | 1 |
| compact_scale_in_executed | 0 |
| compact_decision_snapshot | 1394 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 44 |
| volume_known | 40 |
| time_known | 44 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 10 |
| insufficient_sample | 3 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.5889 | - | 27 | -0.2582 | 0.3333 | candidate_weight_source |
| price_30k_70k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| price_gte_70k | exit_only | -0.6657 | - | 7 | -0.0658 | 0.2857 | candidate_weight_source |
| price_lt_10k | exit_only | -0.7509 | - | 7 | -0.0843 | 0.1429 | candidate_weight_source |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -0.6325 | - | 9 | 0.0522 | 0.1111 | candidate_weight_source |
| volume_500k_2m | exit_only | 0.041 | - | 11 | 0.5248 | 0.2727 | candidate_weight_source |
| volume_gte_10m | exit_only | -1.5375 | - | 5 | -1.012 | 0.4 | candidate_weight_source |
| volume_lt_500k | exit_only | -0.6376 | - | 13 | -0.1819 | 0.3077 | candidate_weight_source |
| volume_unknown | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_0930_1030 | exit_only | -0.7185 | - | 9 | -0.1544 | 0.3333 | candidate_weight_source |
| time_1030_1400 | exit_only | 0.0111 | - | 22 | 0.3851 | 0.1818 | candidate_weight_source |
| time_1400_1530 | exit_only | -1.7476 | - | 9 | -1.7462 | 0.5556 | candidate_weight_source |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `1394`
- sample_candidates: `2778`
- post_sell_joined_candidates: `9`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 1331 | 5 | -1.1411 | 0.9757 | 1.541 | -0.193 |
| exit_only | 1385 | 4 | -1.0899 | 0.9404 | 1.541 | -0.193 |
| hold_defer | 26 | 0 | -0.5223 | 0.4119 | - | - |
| large_sell_detected | 1 | 0 | 1.35 | 0 | - | - |
| micro_context_stale | 1 | 0 | 1.76 | 0.14 | - | - |
| pyramid_wait | 32 | 0 | 0.3069 | 0.1697 | - | - |
| tick_accel_stale | 1 | 0 | 1.76 | 0.14 | - | - |
| tick_aggressor_pressure_unusable | 1 | 0 | 1.76 | 0.14 | - | - |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 19 | 0 | -0.7689 | 0.5389 | - | - |
| exit_only | 4 | 1 | -3.245 | 3.075 | 1.541 | -0.193 |
| hold_defer | 1359 | 4 | -1.1008 | 0.9505 | 1.541 | -0.193 |
| pyramid_wait | 7 | 0 | 0.1471 | 0.0671 | - | - |

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
