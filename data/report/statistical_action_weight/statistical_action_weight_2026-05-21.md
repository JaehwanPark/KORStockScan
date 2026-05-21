# Statistical Action Weight Report - 2026-05-21

## 판정

- 상태: `collect_more_samples`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 3 |
| exit_only | 3 |
| avg_down_wait | 0 |
| pyramid_wait | 0 |
| compact_exit_signal | 149 |
| compact_sell_completed | 1 |
| compact_scale_in_executed | 35 |
| compact_decision_snapshot | 14461 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 3 |
| volume_known | 3 |
| time_known | 3 |

## Policy Counts

| policy | count |
| --- | ---: |
| insufficient_sample | 5 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| price_gte_70k | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_lt_500k | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_1030_1400 | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `14461`
- sample_candidates: `14441`
- post_sell_joined_candidates: `232`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 9122 | 38 | -0.2288 | 0.5348 | 2.232 | -1.161 |
| exit_only | 5278 | 164 | 0.4825 | 0.8986 | 2.232 | -1.161 |
| hold_defer | 41 | 30 | 3.2088 | 0.1493 | 2.232 | -1.161 |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 11 | 0 | -0.4591 | 0.3382 | - | - |
| exit_only | 66 | 0 | -11.5095 | 11.1982 | - | - |
| hold_defer | 14293 | 172 | 0.0761 | 0.621 | 2.232 | -1.161 |
| pyramid_wait | 30 | 30 | 4.5537 | 0.08 | 2.232 | -1.161 |

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
