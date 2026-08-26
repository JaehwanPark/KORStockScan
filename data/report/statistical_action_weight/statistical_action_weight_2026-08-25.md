# Statistical Action Weight Report - 2026-08-25

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 48 |
| exit_only | 46 |
| avg_down_wait | 1 |
| pyramid_wait | 1 |
| compact_exit_signal | 34 |
| compact_sell_completed | 9 |
| compact_scale_in_executed | 0 |
| compact_decision_snapshot | 699 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 48 |
| volume_known | 44 |
| time_known | 48 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 9 |
| insufficient_sample | 4 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.5895 | - | 28 | -0.2621 | 0.3214 | candidate_weight_source |
| price_30k_70k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| price_gte_70k | exit_only | -0.6431 | - | 7 | -0.0658 | 0.2857 | candidate_weight_source |
| price_lt_10k | exit_only | -0.4341 | - | 10 | 0.105 | 0.1 | candidate_weight_source |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -0.6226 | - | 14 | -0.11 | 0.2143 | candidate_weight_source |
| volume_500k_2m | exit_only | 0.0724 | - | 11 | 0.4864 | 0.1818 | candidate_weight_source |
| volume_gte_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_lt_500k | exit_only | -0.3417 | - | 13 | 0.1594 | 0.2308 | candidate_weight_source |
| volume_unknown | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_0930_1030 | exit_only | -0.5979 | - | 10 | -0.063 | 0.3 | candidate_weight_source |
| time_1030_1400 | exit_only | -0.1277 | - | 26 | 0.222 | 0.1923 | candidate_weight_source |
| time_1400_1530 | exit_only | -1.6616 | - | 8 | -1.5626 | 0.5 | candidate_weight_source |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `699`
- sample_candidates: `1366`
- post_sell_joined_candidates: `73`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 651 | 31 | -1.0065 | 0.7831 | 0.9186 | -0.365 |
| exit_only | 679 | 36 | -0.9184 | 0.7284 | 0.9309 | -0.3507 |
| hold_defer | 8 | 3 | 0.085 | 0.2288 | 0.958 | -0.319 |
| pyramid_wait | 28 | 3 | 0.1254 | 0.1229 | 0.958 | -0.319 |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 3 | 0 | -0.69 | 0.46 | - | - |
| exit_only | 8 | 1 | -3.4325 | 2.5675 | 0.714 | -0.604 |
| hold_defer | 671 | 33 | -0.9304 | 0.7343 | 0.9284 | -0.3535 |
| pyramid_wait | 5 | 3 | 0.55 | 0.09 | 0.958 | -0.319 |

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
