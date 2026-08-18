# Statistical Action Weight Report - 2026-08-18

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 14 |
| exit_only | 14 |
| avg_down_wait | 0 |
| pyramid_wait | 0 |
| compact_exit_signal | 79 |
| compact_sell_completed | 3 |
| compact_scale_in_executed | 0 |
| compact_decision_snapshot | 788 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 14 |
| volume_known | 13 |
| time_known | 14 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 4 |
| insufficient_sample | 7 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.7519 | - | 12 | -0.2486 | 0.3333 | candidate_weight_source |
| price_gte_70k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| price_lt_10k | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -1.0728 | - | 8 | -0.4472 | 0.5 | candidate_weight_source |
| volume_500k_2m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_lt_500k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_unknown | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_0930_1030 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_1030_1400 | exit_only | -1.3634 | - | 6 | -0.535 | 0.3333 | candidate_weight_source |
| time_1400_1530 | exit_only | -0.5426 | - | 5 | 0.0454 | 0.4 | candidate_weight_source |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `788`
- sample_candidates: `1566`
- post_sell_joined_candidates: `98`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 729 | 42 | -1.4846 | 1.4308 | 6.7831 | -3.9085 |
| exit_only | 773 | 48 | -1.3496 | 1.3321 | 6.3843 | -4.1937 |
| fresh_micro_confirmation_missing | 1 | 0 | 1.31 | 0.1 | - | - |
| hold_defer | 21 | 0 | -0.3629 | 0.3462 | - | - |
| large_sell_detected | 1 | 0 | 1.76 | 0.11 | - | - |
| micro_context_stale | 3 | 0 | 1.3567 | 0.1533 | - | - |
| micro_vwap_severe_overheated | 3 | 2 | 0.6333 | 0.0567 | 8.601 | -2.722 |
| pyramid_wait | 31 | 6 | 0.7319 | 0.1019 | 3.5923 | -6.1907 |
| tick_accel_stale | 3 | 0 | 1.3567 | 0.1533 | - | - |
| tick_aggressor_pressure_unusable | 1 | 0 | 1.25 | 0.25 | - | - |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 13 | 0 | -0.7685 | 0.5523 | - | - |
| exit_only | 8 | 0 | -2.995 | 2.975 | - | - |
| hold_defer | 752 | 48 | -1.3772 | 1.3596 | 6.3843 | -4.1937 |
| pyramid_wait | 8 | 0 | 0.2963 | 0.0112 | - | - |

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
