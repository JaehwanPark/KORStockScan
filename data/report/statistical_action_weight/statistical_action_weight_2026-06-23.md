# Statistical Action Weight Report - 2026-06-23

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 12 |
| exit_only | 11 |
| avg_down_wait | 0 |
| pyramid_wait | 1 |
| compact_exit_signal | 161 |
| compact_sell_completed | 1 |
| compact_scale_in_executed | 0 |
| compact_decision_snapshot | 2666 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 12 |
| volume_known | 11 |
| time_known | 12 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 1 |
| defensive_only_high_loss_rate | 1 |
| insufficient_sample | 10 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| price_30k_70k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| price_gte_70k | exit_only | -1.9776 | - | 5 | -1.39 | 0.8 | defensive_only_high_loss_rate |
| price_lt_10k | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_500k_2m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_gte_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_lt_500k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_unknown | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0930_1030 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_1030_1400 | exit_only | -1.0393 | - | 8 | -0.0512 | 0.5 | candidate_weight_source |
| time_1400_1530 | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `2666`
- sample_candidates: `2707`
- post_sell_joined_candidates: `16`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 1423 | 11 | -0.965 | 0.7819 | -0.178 | -7.315 |
| exit_only | 868 | 1 | 0.6707 | 1.2962 | -0.178 | -7.315 |
| hold_defer | 67 | 1 | 1.4985 | 0.3046 | -0.178 | -7.315 |
| pyramid_wait | 349 | 3 | 0.5789 | 0.3738 | -0.178 | -7.315 |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 21 | 0 | -0.8719 | 0.8214 | - | - |
| exit_only | 123 | 0 | -2.6038 | 1.5285 | - | - |
| hold_defer | 2450 | 14 | -0.1506 | 0.8816 | -0.178 | -7.315 |
| pyramid_wait | 46 | 1 | 2.5807 | 0.0687 | -0.178 | -7.315 |

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
