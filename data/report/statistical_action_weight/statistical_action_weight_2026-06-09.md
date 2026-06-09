# Statistical Action Weight Report - 2026-06-09

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 36 |
| exit_only | 36 |
| avg_down_wait | 0 |
| pyramid_wait | 0 |
| compact_exit_signal | 285 |
| compact_sell_completed | 2 |
| compact_scale_in_executed | 0 |
| compact_decision_snapshot | 10401 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 36 |
| volume_known | 33 |
| time_known | 36 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 6 |
| defensive_only_high_loss_rate | 1 |
| insufficient_sample | 4 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -1.3159 | - | 5 | 0.416 | 0.4 | candidate_weight_source |
| price_30k_70k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| price_gte_70k | exit_only | -1.044 | - | 30 | -0.7213 | 0.5667 | candidate_weight_source |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -1.0023 | - | 19 | -0.6147 | 0.5263 | candidate_weight_source |
| volume_500k_2m | exit_only | -1.2889 | - | 11 | -0.5836 | 0.5455 | candidate_weight_source |
| volume_gte_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_lt_500k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_unknown | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0930_1030 | exit_only | -1.5613 | - | 8 | -1.3037 | 0.625 | candidate_weight_source |
| time_1030_1400 | exit_only | -0.7443 | - | 22 | -0.1782 | 0.5 | candidate_weight_source |
| time_1400_1530 | exit_only | -1.5291 | - | 6 | -1.2633 | 0.6667 | defensive_only_high_loss_rate |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `10401`
- sample_candidates: `10353`
- post_sell_joined_candidates: `124`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 5309 | 18 | -0.8268 | 0.8518 | 19.274 | 0 |
| exit_only | 2628 | 69 | -0.0174 | 1.1429 | 19.274 | 0 |
| hold_defer | 22 | 11 | 1.7236 | 0.0595 | 19.274 | 0 |
| pyramid_wait | 2394 | 26 | 0.597 | 0.2604 | 19.274 | 0 |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| exit_only | 162 | 0 | -2.3215 | 2.3841 | - | - |
| hold_defer | 10147 | 102 | -0.2629 | 0.7649 | 19.274 | 0 |
| pyramid_wait | 22 | 11 | 1.7236 | 0.0595 | 19.274 | 0 |

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
