# Statistical Action Weight Report - 2026-06-12

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 44 |
| exit_only | 42 |
| avg_down_wait | 0 |
| pyramid_wait | 2 |
| compact_exit_signal | 358 |
| compact_sell_completed | 4 |
| compact_scale_in_executed | 189 |
| compact_decision_snapshot | 7966 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 44 |
| volume_known | 38 |
| time_known | 44 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 7 |
| defensive_only_high_loss_rate | 1 |
| insufficient_sample | 1 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.547 | - | 9 | 0.85 | 0.4444 | candidate_weight_source |
| price_gte_70k | exit_only | -0.68 | - | 33 | -0.4021 | 0.5152 | candidate_weight_source |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -0.4506 | - | 22 | 0.0777 | 0.4091 | candidate_weight_source |
| volume_500k_2m | exit_only | -0.7941 | - | 12 | -0.0958 | 0.5 | candidate_weight_source |
| volume_gte_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_unknown | exit_only | -1.0145 | - | 5 | -0.154 | 0.6 | candidate_weight_source |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0930_1030 | exit_only | -0.5628 | - | 10 | 0.317 | 0.4 | candidate_weight_source |
| time_1030_1400 | exit_only | -0.4761 | - | 26 | -0.0173 | 0.5 | candidate_weight_source |
| time_1400_1530 | exit_only | -1.3724 | - | 6 | -1.39 | 0.6667 | defensive_only_high_loss_rate |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `7966`
- sample_candidates: `8403`
- post_sell_joined_candidates: `27`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 5898 | 13 | -1.8024 | 1.7617 | 0.772 | -1.235 |
| exit_only | 903 | 9 | 0.7644 | 0.8031 | 0.4826 | -0.8839 |
| hold_defer | 485 | 4 | 2.1501 | 0.1085 | 0.251 | -0.603 |
| pyramid_wait | 1117 | 1 | 0.5597 | 0.2931 | 0.772 | -1.235 |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 150 | 0 | -0.7092 | 0.2781 | - | - |
| exit_only | 249 | 1 | -24.2531 | 24.1258 | 0.772 | -1.235 |
| hold_defer | 7184 | 18 | -0.6012 | 0.7493 | 0.7431 | -1.1999 |
| pyramid_wait | 335 | 4 | 3.4304 | 0.0325 | 0.251 | -0.603 |

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
