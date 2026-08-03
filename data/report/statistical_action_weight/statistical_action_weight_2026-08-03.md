# Statistical Action Weight Report - 2026-08-03

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 37 |
| exit_only | 37 |
| avg_down_wait | 0 |
| pyramid_wait | 0 |
| compact_exit_signal | 35 |
| compact_sell_completed | 13 |
| compact_scale_in_executed | 0 |
| compact_decision_snapshot | 647 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 37 |
| volume_known | 37 |
| time_known | 37 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 7 |
| insufficient_sample | 6 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.714 | - | 13 | 0.1031 | 0.3846 | candidate_weight_source |
| price_30k_70k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| price_gte_70k | exit_only | -0.4095 | - | 17 | 0.1006 | 0.2353 | candidate_weight_source |
| price_lt_10k | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -1.4414 | - | 7 | -1.0786 | 0.5714 | candidate_weight_source |
| volume_500k_2m | exit_only | -0.4247 | - | 19 | 0.2437 | 0.3684 | candidate_weight_source |
| volume_gte_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_lt_500k | exit_only | -1.0911 | - | 10 | -0.61 | 0.3 | candidate_weight_source |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_0930_1030 | exit_only | 0.0633 | - | 9 | 0.96 | 0.1111 | candidate_weight_source |
| time_1030_1400 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_1400_1530 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_outside_regular | exit_only | -0.954 | - | 22 | -0.5605 | 0.4091 | candidate_weight_source |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `647`
- sample_candidates: `1259`
- post_sell_joined_candidates: `0`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 567 | 0 | -1.1401 | 1.2477 | - | - |
| buy_pressure_below_min | 2 | 0 | 1.36 | 0 | - | - |
| buy_pressure_severe_below_min | 2 | 0 | 0.175 | 0 | - | - |
| exit_only | 613 | 0 | -0.9688 | 1.1433 | - | - |
| fresh_micro_confirmation_missing | 5 | 0 | 2.18 | 0.034 | - | - |
| hold_defer | 5 | 0 | 1.31 | 0.026 | - | - |
| large_sell_detected | 11 | 0 | 0.8718 | 0.0955 | - | - |
| micro_context_stale | 2 | 0 | 0.935 | 0 | - | - |
| micro_vwap_severe_overheated | 4 | 0 | 1.35 | 0.1525 | - | - |
| pyramid_wait | 45 | 0 | 0.8291 | 0.0802 | - | - |
| tick_accel_stale | 2 | 0 | 0.935 | 0 | - | - |
| tick_aggressor_pressure_unusable | 1 | 0 | 1.11 | 0 | - | - |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| exit_only | 4 | 0 | -2.165 | 2.5975 | - | - |
| hold_defer | 608 | 0 | -0.9876 | 1.1525 | - | - |
| pyramid_wait | 5 | 0 | 1.31 | 0.026 | - | - |

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
