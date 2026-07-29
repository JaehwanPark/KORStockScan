# Statistical Action Weight Report - 2026-07-29

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 34 |
| exit_only | 32 |
| avg_down_wait | 2 |
| pyramid_wait | 0 |
| compact_exit_signal | 8 |
| compact_sell_completed | 5 |
| compact_scale_in_executed | 0 |
| compact_decision_snapshot | 147 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 34 |
| volume_known | 33 |
| time_known | 34 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 7 |
| insufficient_sample | 7 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.8327 | - | 12 | -0.355 | 0.5 | candidate_weight_source |
| price_30k_70k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| price_gte_70k | exit_only | -0.3436 | - | 15 | 0.0127 | 0.2 | candidate_weight_source |
| price_lt_10k | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -0.6636 | - | 5 | -0.356 | 0.6 | candidate_weight_source |
| volume_500k_2m | exit_only | -0.4601 | - | 17 | -0.0765 | 0.2941 | candidate_weight_source |
| volume_gte_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_lt_500k | exit_only | -1.2394 | - | 7 | -0.6943 | 0.5714 | candidate_weight_source |
| volume_unknown | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_0930_1030 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_1030_1400 | exit_only | -0.1398 | - | 9 | 0.1556 | 0.3333 | candidate_weight_source |
| time_1400_1530 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_outside_regular | exit_only | -0.7517 | - | 19 | -0.3942 | 0.3684 | candidate_weight_source |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `147`
- sample_candidates: `295`
- post_sell_joined_candidates: `77`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 111 | 22 | -0.4763 | 0.5135 | 1.7559 | -0.9029 |
| buy_pressure_severe_below_min | 3 | 3 | 0.0867 | 0.1533 | 0.472 | -0.708 |
| exit_only | 145 | 36 | -0.2688 | 0.415 | 1.2703 | -0.8214 |
| hold_defer | 4 | 2 | 0.325 | 0.1 | 0.472 | -0.708 |
| large_sell_detected | 1 | 1 | 0.24 | 0 | 0.472 | -0.708 |
| pyramid_wait | 31 | 13 | 0.2977 | 0.1929 | 0.7169 | -0.6626 |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 1 | 0 | -0.63 | 0.4 | - | - |
| exit_only | 1 | 1 | -3.36 | 3.21 | 3.163 | -0.324 |
| hold_defer | 141 | 34 | -0.2857 | 0.4239 | 1.3172 | -0.828 |
| pyramid_wait | 3 | 2 | 0.6433 | 0 | 0.472 | -0.708 |

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
