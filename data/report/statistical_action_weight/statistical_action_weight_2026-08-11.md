# Statistical Action Weight Report - 2026-08-11

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
| compact_exit_signal | 3 |
| compact_sell_completed | 0 |
| compact_scale_in_executed | 0 |
| compact_decision_snapshot | 10 |

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
- sample_snapshots: `10`
- sample_candidates: `18`
- post_sell_joined_candidates: `0`

| candidate_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 4 | 0 | -0.7675 | 0.725 | - | - |
| exit_only | 9 | 0 | -0.6111 | 0.52 | - | - |
| hold_defer | 4 | 0 | -0.6125 | 0.445 | - | - |
| pyramid_wait | 1 | 0 | 0.02 | 0 | - | - |

### Chosen Action Proxy

| chosen_action | sample | joined | avg_snapshot_profit | avg_snapshot_dd | avg_post_mfe_10m_proxy | avg_post_mae_10m_proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| avg_down_wait | 3 | 0 | -0.8233 | 0.5933 | - | - |
| hold_defer | 5 | 0 | -0.61 | 0.58 | - | - |
| pyramid_wait | 1 | 0 | 0.02 | 0 | - | - |

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
