# Statistical Action Weight Report - 2026-06-26

## 판정

- 상태: `collect_more_samples`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 15 |
| exit_only | 14 |
| avg_down_wait | 1 |
| pyramid_wait | 0 |
| compact_exit_signal | 89 |
| compact_sell_completed | 7 |
| compact_scale_in_executed | 1 |
| compact_decision_snapshot | 2073 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 15 |
| volume_known | 14 |
| time_known | 15 |

## Policy Counts

| policy | count |
| --- | ---: |
| defensive_only_high_loss_rate | 2 |
| insufficient_sample | 12 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| price_30k_70k | exit_only | -1.4954 | - | 5 | -1.83 | 1 | defensive_only_high_loss_rate |
| price_gte_70k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| price_lt_10k | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_500k_2m | exit_only | -1.2007 | - | 6 | -0.64 | 0.8333 | defensive_only_high_loss_rate |
| volume_gte_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_lt_500k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_unknown | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_0930_1030 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_1030_1400 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_1400_1530 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_outside_regular | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `2073`
- sample_candidates: `2264`
- post_sell_joined_candidates: `74`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 1055 | 46 | -0.9914 | 0.8955 | 2.365 | -2.8119 |
| exit_only | 453 | 5 | 1.8436 | 0.5534 | 0.8064 | -3.6306 |
| hold_defer | 205 | 3 | 2.1262 | 0.1552 | 1.296 | -2.653 |
| pyramid_wait | 551 | 20 | 0.7326 | 0.5617 | 2.0509 | -2.1539 |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 17 | 0 | -0.72 | 0.7712 | - | - |
| exit_only | 74 | 20 | -3.2209 | 2.7627 | 3.9371 | -2.0495 |
| hold_defer | 1780 | 48 | -0.0026 | 0.7128 | 1.4835 | -2.9506 |
| pyramid_wait | 188 | 3 | 2.3836 | 0.0995 | 1.296 | -2.653 |

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
