# Statistical Action Weight Report - 2026-08-28

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 25 |
| exit_only | 25 |
| avg_down_wait | 0 |
| pyramid_wait | 0 |
| compact_exit_signal | 13 |
| compact_sell_completed | 5 |
| compact_scale_in_executed | 0 |
| compact_decision_snapshot | 513 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 25 |
| volume_known | 21 |
| time_known | 25 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 7 |
| insufficient_sample | 6 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.8125 | - | 15 | -0.3522 | 0.2667 | candidate_weight_source |
| price_30k_70k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| price_gte_70k | exit_only | -1.0448 | - | 8 | -0.4938 | 0.375 | candidate_weight_source |
| price_lt_10k | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_500k_2m | exit_only | -0.794 | - | 7 | -0.0839 | 0.2857 | candidate_weight_source |
| volume_lt_500k | exit_only | -0.7397 | - | 12 | -0.1938 | 0.25 | candidate_weight_source |
| volume_unknown | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_0930_1030 | exit_only | -0.2504 | - | 5 | 0.27 | 0.2 | candidate_weight_source |
| time_1030_1400 | exit_only | -0.4938 | - | 10 | 0.1282 | 0.2 | candidate_weight_source |
| time_1400_1530 | exit_only | -1.8954 | - | 7 | -1.7823 | 0.5714 | candidate_weight_source |
| time_outside_regular | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `513`
- sample_candidates: `1022`
- post_sell_joined_candidates: `143`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 439 | 72 | -0.9766 | 0.8768 | 0.985 | -4.118 |
| buy_pressure_severe_below_min | 2 | 0 | 0.585 | 0.105 | - | - |
| exit_only | 508 | 71 | -0.8167 | 0.7729 | 0.985 | -4.118 |
| hold_defer | 17 | 0 | -0.5318 | 0.3988 | - | - |
| micro_vwap_severe_overheated | 2 | 0 | 0.585 | 0.105 | - | - |
| pyramid_wait | 54 | 0 | 0.2957 | 0.1252 | - | - |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 12 | 0 | -0.7775 | 0.5475 | - | - |
| exit_only | 2 | 1 | -3.45 | 2.915 | 0.985 | -4.118 |
| hold_defer | 491 | 71 | -0.8266 | 0.7858 | 0.985 | -4.118 |
| pyramid_wait | 5 | 0 | 0.058 | 0.042 | - | - |

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
