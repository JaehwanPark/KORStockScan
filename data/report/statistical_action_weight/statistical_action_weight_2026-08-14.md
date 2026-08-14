# Statistical Action Weight Report - 2026-08-14

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 11 |
| exit_only | 11 |
| avg_down_wait | 0 |
| pyramid_wait | 0 |
| compact_exit_signal | 470 |
| compact_sell_completed | 6 |
| compact_scale_in_executed | 0 |
| compact_decision_snapshot | 828 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 11 |
| volume_known | 11 |
| time_known | 11 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 2 |
| insufficient_sample | 5 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.6974 | - | 11 | -0.14 | 0.2727 | candidate_weight_source |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_500k_2m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_gte_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_1030_1400 | exit_only | -1.3257 | - | 6 | -0.535 | 0.3333 | candidate_weight_source |
| time_1400_1530 | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `828`
- sample_candidates: `1599`
- post_sell_joined_candidates: `188`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 774 | 80 | -0.9799 | 0.9349 | 1.6124 | -24.4973 |
| buy_pressure_severe_below_min | 1 | 1 | 0.08 | 0.04 | 1.443 | -30.6 |
| exit_only | 771 | 90 | -0.8615 | 0.7769 | 1.6025 | -25.1342 |
| fresh_micro_confirmation_missing | 1 | 1 | 1.7 | 0 | 1.443 | -30.6 |
| hold_defer | 16 | 0 | -0.58 | 0.4587 | - | - |
| large_sell_detected | 2 | 2 | 0.04 | 0.08 | 1.443 | -30.6 |
| micro_vwap_overheated | 1 | 1 | 1.16 | 0 | 1.443 | -30.6 |
| micro_vwap_severe_overheated | 1 | 1 | 0.83 | 0 | 1.736 | -31.094 |
| pyramid_wait | 31 | 11 | 0.2929 | 0.0758 | 1.548 | -28.0692 |
| tick_accel_below_min | 1 | 1 | 1.16 | 0 | 1.443 | -30.6 |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 14 | 0 | -0.7543 | 0.5243 | - | - |
| exit_only | 50 | 1 | -1.8892 | 2.687 | 1.793 | -6.474 |
| hold_defer | 755 | 90 | -0.8675 | 0.7836 | 1.6025 | -25.1342 |
| pyramid_wait | 2 | 0 | 0.64 | 0 | - | - |

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
