# Statistical Action Weight Report - 2026-07-22

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 44 |
| exit_only | 42 |
| avg_down_wait | 2 |
| pyramid_wait | 0 |
| compact_exit_signal | 229 |
| compact_sell_completed | 18 |
| compact_scale_in_executed | 2 |
| compact_decision_snapshot | 1133 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 44 |
| volume_known | 44 |
| time_known | 44 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 9 |
| defensive_only_high_loss_rate | 1 |
| insufficient_sample | 3 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.5038 | - | 19 | 0.0184 | 0.3684 | candidate_weight_source |
| price_30k_70k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| price_gte_70k | exit_only | -1.6234 | - | 6 | -1.7683 | 0.8333 | defensive_only_high_loss_rate |
| price_lt_10k | exit_only | -0.2447 | - | 16 | 0.2094 | 0.3125 | candidate_weight_source |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -0.4719 | - | 12 | -0.005 | 0.25 | candidate_weight_source |
| volume_500k_2m | exit_only | -1.3279 | - | 10 | -1.007 | 0.5 | candidate_weight_source |
| volume_gte_10m | exit_only | -0.2956 | - | 7 | 0.8743 | 0.4286 | candidate_weight_source |
| volume_lt_500k | exit_only | -0.698 | - | 13 | -0.1938 | 0.4615 | candidate_weight_source |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_0930_1030 | exit_only | -0.6832 | - | 7 | -0.08 | 0.2857 | candidate_weight_source |
| time_1030_1400 | exit_only | -0.3705 | - | 21 | 0.1148 | 0.381 | candidate_weight_source |
| time_1400_1530 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_outside_regular | exit_only | -0.895 | - | 11 | -0.4118 | 0.5455 | candidate_weight_source |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `1133`
- sample_candidates: `1843`
- post_sell_joined_candidates: `258`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 844 | 99 | -1.1844 | 1.0399 | 2.4726 | -9.6674 |
| exit_only | 909 | 125 | -1.0488 | 0.9505 | 1.9883 | -8.6059 |
| fresh_micro_confirmation_missing | 3 | 1 | 0.8367 | 0 | 11.523 | -3.807 |
| micro_context_stale | 2 | 1 | 1.77 | 0.105 | 11.523 | -3.807 |
| micro_vwap_overheated | 1 | 1 | 1.65 | 0.21 | 11.523 | -3.807 |
| micro_vwap_severe_overheated | 3 | 0 | 0.3033 | 0.0533 | - | - |
| pyramid_wait | 73 | 27 | 0.3804 | 0.1585 | 2.6917 | -4.7554 |
| tick_accel_below_min | 2 | 2 | 1.39 | 0.105 | 5.8915 | -10.5055 |
| tick_accel_stale | 3 | 1 | 1.4233 | 0.07 | 11.523 | -3.807 |
| tick_aggressor_pressure_unusable | 3 | 1 | 1.4233 | 0.07 | 11.523 | -3.807 |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| exit_only | 22 | 15 | -0.8532 | 1.8355 | 4.7913 | -1.8753 |
| hold_defer | 909 | 125 | -1.0488 | 0.9505 | 1.9883 | -8.6059 |

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
