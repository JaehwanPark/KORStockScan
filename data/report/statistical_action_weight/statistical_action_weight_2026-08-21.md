# Statistical Action Weight Report - 2026-08-21

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 30 |
| exit_only | 28 |
| avg_down_wait | 1 |
| pyramid_wait | 1 |
| compact_exit_signal | 1395 |
| compact_sell_completed | 14 |
| compact_scale_in_executed | 0 |
| compact_decision_snapshot | 1797 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 30 |
| volume_known | 29 |
| time_known | 30 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 7 |
| insufficient_sample | 6 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.5907 | - | 18 | -0.1645 | 0.3333 | candidate_weight_source |
| price_30k_70k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| price_gte_70k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| price_lt_10k | exit_only | -0.7427 | - | 7 | -0.1681 | 0.2857 | candidate_weight_source |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -0.9971 | - | 9 | -0.3051 | 0.2222 | candidate_weight_source |
| volume_500k_2m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_gte_10m | exit_only | -1.5022 | - | 5 | -1.2031 | 0.6 | candidate_weight_source |
| volume_lt_500k | exit_only | 0.0977 | - | 9 | 0.5883 | 0.1111 | candidate_weight_source |
| volume_unknown | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_0930_1030 | exit_only | -0.7829 | - | 8 | -0.2241 | 0.375 | candidate_weight_source |
| time_1030_1400 | exit_only | -0.3567 | - | 17 | 0.1162 | 0.2353 | candidate_weight_source |
| time_1400_1530 | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `1797`
- sample_candidates: `1462`
- post_sell_joined_candidates: `160`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 610 | 54 | -1.1402 | 1.2985 | 1.6487 | -3.5742 |
| buy_pressure_severe_below_min | 10 | 0 | 0.187 | 0.273 | - | - |
| exit_only | 712 | 75 | -0.9031 | 1.1056 | 1.2151 | -3.5619 |
| fresh_micro_confirmation_missing | 3 | 2 | 1.0433 | 0.1167 | 0.6905 | -12.7915 |
| hold_defer | 7 | 1 | -0.2314 | 0.3743 | 2.424 | -3.543 |
| large_sell_detected | 12 | 2 | 0.32 | 0.2208 | -0.409 | -13.3555 |
| micro_context_stale | 1 | 0 | 0.36 | 0.1 | - | - |
| micro_vwap_severe_overheated | 2 | 2 | 0.63 | 0.04 | -0.409 | -13.3555 |
| pyramid_wait | 103 | 24 | 0.3071 | 0.1396 | 0.5435 | -3.3254 |
| tick_accel_stale | 1 | 0 | 0.36 | 0.1 | - | - |
| tick_aggressor_pressure_unusable | 1 | 0 | 0.36 | 0.1 | - | - |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 4 | 1 | -0.8025 | 0.61 | 2.424 | -3.543 |
| exit_only | 8 | 4 | -2.81 | 2.7363 | 3.3413 | -2.3053 |
| hold_defer | 705 | 74 | -0.9098 | 1.1129 | 1.1988 | -3.5621 |
| pyramid_wait | 3 | 0 | 0.53 | 0.06 | - | - |

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
