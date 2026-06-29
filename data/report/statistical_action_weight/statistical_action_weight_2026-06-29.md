# Statistical Action Weight Report - 2026-06-29

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 17 |
| exit_only | 16 |
| avg_down_wait | 1 |
| pyramid_wait | 0 |
| compact_exit_signal | 28 |
| compact_sell_completed | 1 |
| compact_scale_in_executed | 0 |
| compact_decision_snapshot | 1980 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 17 |
| volume_known | 16 |
| time_known | 17 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 3 |
| defensive_only_high_loss_rate | 1 |
| insufficient_sample | 9 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| price_30k_70k | exit_only | -1.4342 | - | 5 | -1.83 | 1 | defensive_only_high_loss_rate |
| price_gte_70k | exit_only | -0.4644 | - | 5 | 0.704 | 0.4 | candidate_weight_source |
| price_lt_10k | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -1.6253 | - | 5 | -0.674 | 0.6 | candidate_weight_source |
| volume_500k_2m | exit_only | -0.9227 | - | 8 | -0.0938 | 0.625 | candidate_weight_source |
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
- sample_snapshots: `1980`
- sample_candidates: `2003`
- post_sell_joined_candidates: `90`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 1595 | 58 | -1.1429 | 0.5544 | 0.633 | -16.709 |
| exit_only | 158 | 1 | 1.01 | 1.0294 | 0.633 | -16.709 |
| hold_defer | 42 | 1 | 0.2105 | 0.3057 | 0.633 | -16.709 |
| pyramid_wait | 208 | 30 | 0.586 | 0.0906 | 0.633 | -16.709 |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 22 | 0 | -0.7768 | 0.5627 | - | - |
| exit_only | 9 | 0 | -4.3978 | 1.2433 | - | - |
| hold_defer | 1910 | 88 | -0.7909 | 0.5454 | 0.633 | -16.709 |
| pyramid_wait | 20 | 1 | 1.2965 | 0.023 | 0.633 | -16.709 |

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
