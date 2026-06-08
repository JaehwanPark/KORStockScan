# Statistical Action Weight Report - 2026-06-08

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 51 |
| exit_only | 50 |
| avg_down_wait | 0 |
| pyramid_wait | 1 |
| compact_exit_signal | 411 |
| compact_sell_completed | 25 |
| compact_scale_in_executed | 0 |
| compact_decision_snapshot | 12849 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 51 |
| volume_known | 47 |
| time_known | 51 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 7 |
| insufficient_sample | 4 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -1.346 | - | 7 | -0.35 | 0.5714 | candidate_weight_source |
| price_30k_70k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| price_gte_70k | exit_only | -0.8423 | - | 42 | -0.5514 | 0.5 | candidate_weight_source |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -0.8944 | - | 26 | -0.5115 | 0.5 | candidate_weight_source |
| volume_500k_2m | exit_only | -0.6787 | - | 14 | 0.1086 | 0.3571 | candidate_weight_source |
| volume_gte_10m | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_lt_500k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_unknown | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0930_1030 | exit_only | -1.2751 | - | 10 | -0.766 | 0.5 | candidate_weight_source |
| time_1030_1400 | exit_only | -0.7307 | - | 32 | -0.3303 | 0.5 | candidate_weight_source |
| time_1400_1530 | exit_only | -1.4572 | - | 8 | -1.2188 | 0.625 | candidate_weight_source |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `12849`
- sample_candidates: `12937`
- post_sell_joined_candidates: `1518`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 7773 | 669 | -0.9132 | 1.1855 | 3.5222 | -1.3731 |
| exit_only | 1649 | 364 | 0.1421 | 1.3006 | 2.7519 | -11.1188 |
| hold_defer | 190 | 190 | 3.8389 | 0.009 | 0.901 | -19.9514 |
| pyramid_wait | 3325 | 295 | 0.6262 | 0.5461 | 4.933 | -1.4954 |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| exit_only | 286 | 13 | -2.545 | 2.5964 | 2.8449 | -1.4829 |
| hold_defer | 12271 | 1125 | -0.3898 | 1.013 | 4.0934 | -1.4195 |
| pyramid_wait | 190 | 190 | 3.8389 | 0.009 | 0.901 | -19.9514 |

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
