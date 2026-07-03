# Statistical Action Weight Report - 2026-07-03

## 판정

- 상태: `candidate_weight_source_review`
- weight_source_ready: `True`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 128 |
| exit_only | 102 |
| avg_down_wait | 25 |
| pyramid_wait | 1 |
| compact_exit_signal | 220 |
| compact_sell_completed | 20 |
| compact_scale_in_executed | 19 |
| compact_decision_snapshot | 2825 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 128 |
| volume_known | 120 |
| time_known | 128 |

## Policy Counts

| policy | count |
| --- | ---: |
| candidate_weight_source | 13 |
| insufficient_sample | 1 |

## Price Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| price_10k_30k | exit_only | -0.4512 | 1.5856 | 26 | -0.0277 | 0.4231 | candidate_weight_source |
| price_30k_70k | exit_only | 0.1563 | 1.5597 | 22 | 0.5968 | 0.2727 | candidate_weight_source |
| price_gte_70k | exit_only | -0.1946 | 0.7392 | 36 | 0.2472 | 0.3889 | candidate_weight_source |
| price_lt_10k | exit_only | -0.161 | - | 18 | 0.3806 | 0.3889 | candidate_weight_source |

## Volume Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| volume_2m_10m | exit_only | -0.5657 | 0.8357 | 16 | 0.0912 | 0.4375 | candidate_weight_source |
| volume_500k_2m | exit_only | 0.0484 | 2.158 | 32 | 0.3928 | 0.3438 | candidate_weight_source |
| volume_gte_10m | exit_only | -0.4832 | - | 7 | 0.3057 | 0.4286 | candidate_weight_source |
| volume_lt_500k | exit_only | 0.1024 | 1.3001 | 42 | 0.4512 | 0.3333 | candidate_weight_source |
| volume_unknown | exit_only | -2.7002 | - | 5 | -1.392 | 0.6 | candidate_weight_source |

## Time Bucket

| bucket | best_action | score | edge | sample | avg_profit | loss_rate | policy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| time_0900_0930 | insufficient_sample | - | - | - | - | - | insufficient_sample |
| time_0930_1030 | exit_only | -0.3448 | - | 12 | 0.3192 | 0.25 | candidate_weight_source |
| time_1030_1400 | exit_only | 0.5706 | 1.3533 | 28 | 1.2132 | 0.1429 | candidate_weight_source |
| time_1400_1530 | exit_only | 0.1272 | - | 14 | 0.5814 | 0.5 | candidate_weight_source |
| time_outside_regular | exit_only | -0.7618 | 1.0181 | 45 | -0.5076 | 0.5333 | candidate_weight_source |

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `2825`
- sample_candidates: `2812`
- post_sell_joined_candidates: `545`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 2283 | 374 | -1.6858 | 1.5706 | 1.5652 | -5.6627 |
| buy_pressure_below_min | 1 | 0 | 1.78 | 0.22 | - | - |
| exit_only | 71 | 36 | -1.9239 | 2.1168 | 2.2248 | -2.2355 |
| hold_defer | 29 | 1 | -0.3983 | 0.3659 | 1.631 | -0.753 |
| large_sell_detected | 4 | 2 | 1.8075 | 0.1125 | 2.4315 | -3.4235 |
| micro_vwap_missing | 1 | 0 | 2.53 | 0 | - | - |
| micro_vwap_overheated | 12 | 10 | 2.6383 | 0.02 | 1.9241 | -4.8455 |
| pyramid_wait | 402 | 114 | 0.5695 | 0.2263 | 1.088 | -6.3391 |
| tick_accel_below_min | 9 | 8 | 3.3278 | 0.0522 | 1.5109 | -3.9583 |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 20 | 0 | -0.772 | 0.4975 | - | - |
| exit_only | 151 | 5 | -11.2759 | 11.1908 | 1.8122 | -2.1278 |
| hold_defer | 2576 | 518 | -0.7927 | 0.8255 | 1.5035 | -5.6169 |
| pyramid_wait | 9 | 1 | 0.4322 | 0.0733 | 1.631 | -0.753 |

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
