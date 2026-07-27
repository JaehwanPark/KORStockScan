# Statistical Action Weight Report - 2026-07-27

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 40 |
| exit_only | 37 |
| avg_down_wait | 3 |
| pyramid_wait | 0 |
| compact_exit_signal | 2 |
| compact_sell_completed | 2 |
| compact_scale_in_executed | 0 |
| compact_decision_snapshot | 19 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 40 |
| volume_known | 39 |
| time_known | 40 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 9 |
| insufficient_sample | 5 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.4417 | - | 14 | 0.1471 | 0.5 | candidate_weight_source |
| price_30k_70k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| price_gte_70k | exit_only | -0.8403 | - | 14 | -0.5393 | 0.3571 | candidate_weight_source |
| price_lt_10k | exit_only | -0.7411 | - | 8 | -0.1625 | 0.5 | candidate_weight_source |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -0.5541 | - | 6 | 0.0533 | 0.5 | candidate_weight_source |
| volume_500k_2m | exit_only | -0.7313 | - | 14 | -0.3836 | 0.3571 | candidate_weight_source |
| volume_gte_10m | exit_only | -0.4637 | - | 6 | 0.8133 | 0.3333 | candidate_weight_source |
| volume_lt_500k | exit_only | -1.0424 | - | 10 | -0.651 | 0.6 | candidate_weight_source |
| volume_unknown | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_0930_1030 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_1030_1400 | exit_only | -0.4652 | - | 15 | 0.0753 | 0.3333 | candidate_weight_source |
| time_1400_1530 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_outside_regular | exit_only | -0.4044 | - | 14 | 0.0457 | 0.4286 | candidate_weight_source |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `19`
- sample_candidates: `37`
- post_sell_joined_candidates: `36`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 3 | 2 | -1.3333 | 1.6567 | 0.5 | -0.5 |
| exit_only | 18 | 18 | 0.1361 | 0.2011 | 0.5 | -0.5 |
| pyramid_wait | 16 | 16 | 0.1631 | 0.1762 | 0.5 | -0.5 |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| exit_only | 1 | 0 | -3.84 | 4.17 | - | - |
| hold_defer | 18 | 18 | 0.1361 | 0.2011 | 0.5 | -0.5 |

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
