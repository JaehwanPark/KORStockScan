# Statistical Action Weight Report - 2026-06-04

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 40 |
| exit_only | 39 |
| avg_down_wait | 0 |
| pyramid_wait | 1 |
| compact_exit_signal | 17 |
| compact_sell_completed | 1 |
| compact_scale_in_executed | 0 |
| compact_decision_snapshot | 1244 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 40 |
| volume_known | 37 |
| time_known | 40 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 7 |
| insufficient_sample | 4 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.937 | - | 9 | -0.1533 | 0.3333 | candidate_weight_source |
| price_30k_70k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| price_gte_70k | exit_only | -1.0716 | - | 29 | -0.7379 | 0.5517 | candidate_weight_source |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -1.3401 | - | 16 | -0.9419 | 0.5625 | candidate_weight_source |
| volume_500k_2m | exit_only | -0.6772 | - | 11 | 0.0973 | 0.3636 | candidate_weight_source |
| volume_gte_10m | exit_only | -1.2236 | - | 7 | -0.4143 | 0.4286 | candidate_weight_source |
| volume_lt_500k | insufficient_sample | - | - | - | - | - | insufficient_sample |
| volume_unknown | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0930_1030 | exit_only | -1.3569 | - | 10 | -0.865 | 0.6 | candidate_weight_source |
| time_1030_1400 | exit_only | -0.9301 | - | 25 | -0.532 | 0.48 | candidate_weight_source |
| time_1400_1530 | insufficient_sample | - | - | - | - | - | insufficient_sample |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `1244`
- sample_candidates: `1242`
- post_sell_joined_candidates: `26`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 791 | 3 | -0.7585 | 0.4827 | 1.852 | -21.252 |
| exit_only | 338 | 23 | -1.1981 | 1.1125 | 1.852 | -21.252 |
| pyramid_wait | 113 | 0 | 0.361 | 0.0934 | - | - |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| exit_only | 12 | 1 | -1.8758 | 1.3942 | 1.852 | -21.252 |
| hold_defer | 1230 | 25 | -0.7656 | 0.6111 | 1.852 | -21.252 |

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
