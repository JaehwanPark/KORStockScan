# Statistical Action Weight Report - 2026-05-19

## 판정

- 상태: `collect_more_samples`
- weight_source_ready: `False`
- runtime_change: `False`

## 표본 충분성

| metric | value |
| --- | ---: |
| completed_valid | 0 |
| exit_only | 0 |
| avg_down_wait | 0 |
| pyramid_wait | 0 |
| compact_exit_signal | 101 |
| compact_sell_completed | 0 |
| compact_scale_in_executed | 0 |
| compact_decision_snapshot | 8834 |

## 데이터 완성도

| field | known |
| --- | ---: |
| price_known | 0 |
| volume_known | 0 |
| time_known | 0 |

## Policy Counts

| policy | count |
| --- | ---: |

## Price Bucket

- 표본 없음

## Volume Bucket

- 표본 없음

## Time Bucket

- 표본 없음

## Eligible But Not Chosen

- status: `report_only`
- join_status: `post_sell_10m_proxy_when_record_id_matches`
- sample_snapshots: `8834`
- sample_candidates: `9227`
- post_sell_joined_candidates: `0`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 4826 | 0 | -0.3152 | 0.674 | - | - |
| exit_only | 3963 | 0 | 0.473 | 0.9454 | - | - |
| hold_defer | 438 | 0 | 1.4084 | 0.1727 | - | - |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 150 | 0 | -0.4652 | 0.3565 | - | - |
| exit_only | 42 | 0 | -2.0679 | 2.1133 | - | - |
| hold_defer | 8309 | 0 | -0.0212 | 0.8226 | - | - |
| pyramid_wait | 288 | 0 | 2.3842 | 0.0769 | - | - |

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
