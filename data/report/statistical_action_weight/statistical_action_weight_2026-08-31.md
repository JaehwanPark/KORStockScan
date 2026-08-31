# Statistical Action Weight Report - 2026-08-31

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 18 |
| exit_only | 18 |
| avg_down_wait | 0 |
| pyramid_wait | 0 |
| compact_exit_signal | 12 |
| compact_sell_completed | 2 |
| compact_scale_in_executed | 0 |
| compact_decision_snapshot | 395 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 18 |
| volume_known | 17 |
| time_known | 18 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 4 |
| insufficient_sample | 8 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.1363 | - | 11 | 0.3114 | 0.1818 | candidate_weight_source |
| price_30k_70k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| price_gte_70k | exit_only | -0.6654 | - | 6 | -0.1817 | 0.3333 | candidate_weight_source |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_500k_2m | exit_only | -0.3782 | - | 12 | 0.0563 | 0.25 | candidate_weight_source |
| volume_lt_500k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_unknown | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_0930_1030 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_1030_1400 | exit_only | -0.6144 | - | 6 | 0.0083 | 0.1667 | candidate_weight_source |
| time_1400_1530 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_outside_regular | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `395`
- sample_candidates: `781`
- post_sell_joined_candidates: `0`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 347 | 0 | -1.0778 | 0.9621 | - | - |
| exit_only | 386 | 0 | -0.8861 | 0.8497 | - | - |
| hold_defer | 8 | 0 | -0.21 | 0.2625 | - | - |
| micro_context_stale | 2 | 0 | 1.895 | 0 | - | - |
| pyramid_wait | 35 | 0 | 0.5629 | 0.1063 | - | - |
| tick_accel_stale | 2 | 0 | 1.895 | 0 | - | - |
| tick_aggressor_pressure_unusable | 1 | 0 | 2.57 | 0 | - | - |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 4 | 0 | -0.7275 | 0.4975 | - | - |
| exit_only | 4 | 0 | -3.49 | 2.92 | - | - |
| hold_defer | 378 | 0 | -0.9004 | 0.8622 | - | - |
| pyramid_wait | 4 | 0 | 0.3075 | 0.0275 | - | - |

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
