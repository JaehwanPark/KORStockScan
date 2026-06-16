# Statistical Action Weight Report - 2026-06-16

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 19 |
| exit_only | 17 |
| avg_down_wait | 0 |
| pyramid_wait | 2 |
| compact_exit_signal | 169 |
| compact_sell_completed | 0 |
| compact_scale_in_executed | 0 |
| compact_decision_snapshot | 9050 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 19 |
| volume_known | 16 |
| time_known | 19 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 5 |
| defensive_only_high_loss_rate | 1 |
| insufficient_sample | 3 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.6023 | - | 7 | 0.7586 | 0.5714 | candidate_weight_source |
| price_gte_70k | exit_only | -0.8194 | - | 10 | -0.395 | 0.6 | candidate_weight_source |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -0.8408 | - | 6 | 0.57 | 0.5 | candidate_weight_source |
| volume_500k_2m | exit_only | -0.5524 | - | 7 | 0.5557 | 0.4286 | candidate_weight_source |
| volume_gte_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_unknown | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0930_1030 | exit_only | -0.2591 | - | 6 | 1.1883 | 0.3333 | candidate_weight_source |
| time_1030_1400 | exit_only | -0.7998 | - | 10 | -0.246 | 0.7 | defensive_only_high_loss_rate |
| time_1400_1530 | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `9050`
- sample_candidates: `9563`
- post_sell_joined_candidates: `0`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 6255 | 0 | -0.8206 | 0.7613 | - | - |
| exit_only | 1433 | 0 | 0.4295 | 0.9105 | - | - |
| hold_defer | 542 | 0 | 1.8682 | 0.1875 | - | - |
| pyramid_wait | 1333 | 0 | 0.4951 | 0.32 | - | - |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 146 | 0 | -0.8073 | 0.539 | - | - |
| exit_only | 127 | 0 | -2.2757 | 2.1585 | - | - |
| hold_defer | 8352 | 0 | -0.5485 | 0.7324 | - | - |
| pyramid_wait | 396 | 0 | 2.8545 | 0.0579 | - | - |

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
