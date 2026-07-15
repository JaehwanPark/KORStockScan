# Statistical Action Weight Report - 2026-07-15

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 35 |
| exit_only | 28 |
| avg_down_wait | 3 |
| pyramid_wait | 4 |
| compact_exit_signal | 62 |
| compact_sell_completed | 10 |
| compact_scale_in_executed | 13 |
| compact_decision_snapshot | 1809 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 35 |
| volume_known | 34 |
| time_known | 35 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 5 |
| defensive_only_high_loss_rate | 4 |
| insufficient_sample | 4 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -1.4588 | - | 10 | -0.708 | 0.5 | candidate_weight_source |
| price_30k_70k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| price_gte_70k | exit_only | -0.9797 | - | 10 | -0.379 | 0.5 | candidate_weight_source |
| price_lt_10k | exit_only | -1.2143 | - | 7 | -0.6614 | 0.7143 | defensive_only_high_loss_rate |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -1.7293 | - | 10 | -1.572 | 0.8 | defensive_only_high_loss_rate |
| volume_500k_2m | exit_only | -0.549 | - | 9 | 0.3233 | 0.2222 | candidate_weight_source |
| volume_gte_10m | exit_only | -1.2887 | - | 7 | -0.04 | 0.5714 | candidate_weight_source |
| volume_lt_500k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_unknown | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0930_1030 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_1030_1400 | exit_only | -1.429 | - | 14 | -0.8586 | 0.4286 | candidate_weight_source |
| time_1400_1530 | exit_only | -1.3771 | - | 5 | -0.782 | 0.8 | defensive_only_high_loss_rate |
| time_outside_regular | exit_only | -0.5864 | - | 5 | -0.284 | 0.8 | defensive_only_high_loss_rate |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `1809`
- sample_candidates: `3485`
- post_sell_joined_candidates: `740`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 1396 | 307 | -1.0455 | 0.6927 | 2.5365 | -2.2674 |
| buy_pressure_below_min | 1 | 1 | 1.13 | 0.14 | 0.838 | -15.573 |
| exit_only | 1747 | 392 | -0.904 | 0.6484 | 2.403 | -2.0425 |
| fresh_micro_confirmation_missing | 7 | 2 | 0.1843 | 0.0443 | 5.198 | -1.977 |
| hold_defer | 4 | 4 | 1.055 | 0.115 | 3.0415 | -4.4615 |
| micro_context_stale | 9 | 1 | 0.6089 | 0.04 | 0.088 | -4.569 |
| micro_vwap_severe_overheated | 2 | 2 | 0.805 | 0.155 | 10.308 | 0.615 |
| pyramid_wait | 300 | 28 | 0.1845 | 0.0186 | 3.6349 | -3.3714 |
| quote_stale | 1 | 1 | 0.14 | 0 | 0.088 | -4.569 |
| tick_accel_stale | 9 | 1 | 0.6089 | 0.04 | 0.088 | -4.569 |
| tick_aggressor_pressure_unusable | 9 | 1 | 0.6089 | 0.04 | 0.088 | -4.569 |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| exit_only | 56 | 48 | -3.0825 | 2.9489 | 0.8387 | -0.3807 |
| hold_defer | 1743 | 388 | -0.9085 | 0.6496 | 2.3964 | -2.0175 |
| pyramid_wait | 4 | 4 | 1.055 | 0.115 | 3.0415 | -4.4615 |

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
