# Holding/Exit Decision Matrix - 2026-07-03

## 판정

- matrix_version: `holding_exit_decision_matrix_v1_2026-07-03`
- application_mode: `advisory_canary_live_readiness_until_owner_approval`
- runtime_change: `False`

## Hard Veto

- `emergency_or_hard_stop`
- `active_sell_order_pending`
- `invalid_feature`
- `post_add_eval_exclusion`

## Counterfactual Coverage

- non_no_clear_edge_count: `8`
- no_clear_edge_count: `6`
- candidate_weight_source_non_clear_edge_count: `8`
- ready_count: `3` / `14`
- ready_rate: `0.2143`
- per_action_edge_buckets: `{'prefer_exit': 8, 'prefer_avg_down_wait': 0, 'prefer_pyramid_wait': 0}`
- per_action_samples: `{'exit_only': 306, 'avg_down_wait': 75, 'pyramid_wait': 3}`
- proxy_sample_snapshots: `2825`
- proxy_joined_candidates: `545`
- proxy_actions_present: `['hold_defer', 'exit_only', 'avg_down_wait', 'pyramid_wait']`
- proxy_missing_actions: `[]`
- proxy_per_action_samples: `{'hold_defer': 2605, 'exit_only': 222, 'avg_down_wait': 2303, 'pyramid_wait': 411}`


## Matrix Entries

| axis | bucket | bias | score | edge | sample | loss_rate | cf_ready | missing_actions | policy |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| price_bucket | price_10k_30k | prefer_exit | -0.4512 | 1.5856 | 26 | 0.4231 | False | pyramid_wait | candidate_weight_source |
| price_bucket | price_30k_70k | prefer_exit | 0.1563 | 1.5597 | 22 | 0.2727 | False | pyramid_wait | candidate_weight_source |
| price_bucket | price_gte_70k | prefer_exit | -0.1946 | 0.7392 | 36 | 0.3889 | True | - | candidate_weight_source |
| price_bucket | price_lt_10k | no_clear_edge | -0.161 | - | 18 | 0.3889 | False | pyramid_wait | candidate_weight_source |
| volume_bucket | volume_2m_10m | prefer_exit | -0.5657 | 0.8357 | 16 | 0.4375 | False | pyramid_wait | candidate_weight_source |
| volume_bucket | volume_500k_2m | prefer_exit | 0.0484 | 2.158 | 32 | 0.3438 | False | pyramid_wait | candidate_weight_source |
| volume_bucket | volume_gte_10m | no_clear_edge | -0.4832 | - | 7 | 0.4286 | False | pyramid_wait | candidate_weight_source |
| volume_bucket | volume_lt_500k | prefer_exit | 0.1024 | 1.3001 | 42 | 0.3333 | False | pyramid_wait | candidate_weight_source |
| volume_bucket | volume_unknown | no_clear_edge | -2.7002 | - | 5 | 0.6 | True | - | candidate_weight_source |
| time_bucket | time_0900_0930 | no_clear_edge | - | - | - | - | False | pyramid_wait | insufficient_sample |
| time_bucket | time_0930_1030 | no_clear_edge | -0.3448 | - | 12 | 0.25 | True | - | candidate_weight_source |
| time_bucket | time_1030_1400 | prefer_exit | 0.5706 | 1.3533 | 28 | 0.1429 | False | pyramid_wait | candidate_weight_source |
| time_bucket | time_1400_1530 | no_clear_edge | 0.1272 | - | 14 | 0.5 | False | pyramid_wait | candidate_weight_source |
| time_bucket | time_outside_regular | prefer_exit | -0.7618 | 1.0181 | 45 | 0.5333 | False | pyramid_wait | candidate_weight_source |

## Prompt Hints

- `price_bucket=price_10k_30k` / `prefer_exit`: price_bucket=price_10k_30k 과거 표본은 보유/추가매수보다 청산 우위가 있다. 단 hard veto와 현재 thesis를 먼저 확인한다.
- `price_bucket=price_30k_70k` / `prefer_exit`: price_bucket=price_30k_70k 과거 표본은 보유/추가매수보다 청산 우위가 있다. 단 hard veto와 현재 thesis를 먼저 확인한다.
- `price_bucket=price_gte_70k` / `prefer_exit`: price_bucket=price_gte_70k 과거 표본은 보유/추가매수보다 청산 우위가 있다. 단 hard veto와 현재 thesis를 먼저 확인한다.
- `price_bucket=price_lt_10k` / `no_clear_edge`: price_bucket=price_lt_10k 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `volume_bucket=volume_2m_10m` / `prefer_exit`: volume_bucket=volume_2m_10m 과거 표본은 보유/추가매수보다 청산 우위가 있다. 단 hard veto와 현재 thesis를 먼저 확인한다.
- `volume_bucket=volume_500k_2m` / `prefer_exit`: volume_bucket=volume_500k_2m 과거 표본은 보유/추가매수보다 청산 우위가 있다. 단 hard veto와 현재 thesis를 먼저 확인한다.
- `volume_bucket=volume_gte_10m` / `no_clear_edge`: volume_bucket=volume_gte_10m 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `volume_bucket=volume_lt_500k` / `prefer_exit`: volume_bucket=volume_lt_500k 과거 표본은 보유/추가매수보다 청산 우위가 있다. 단 hard veto와 현재 thesis를 먼저 확인한다.
- `volume_bucket=volume_unknown` / `no_clear_edge`: volume_bucket=volume_unknown 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `time_bucket=time_0900_0930` / `no_clear_edge`: time_bucket=time_0900_0930 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `time_bucket=time_0930_1030` / `no_clear_edge`: time_bucket=time_0930_1030 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `time_bucket=time_1030_1400` / `prefer_exit`: time_bucket=time_1030_1400 과거 표본은 보유/추가매수보다 청산 우위가 있다. 단 hard veto와 현재 thesis를 먼저 확인한다.
- `time_bucket=time_1400_1530` / `no_clear_edge`: time_bucket=time_1400_1530 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `time_bucket=time_outside_regular` / `prefer_exit`: time_bucket=time_outside_regular 과거 표본은 보유/추가매수보다 청산 우위가 있다. 단 hard veto와 현재 thesis를 먼저 확인한다.

## 다음 액션

- `ADM`은 shadow가 아니라 advisory canary/live-readiness 축으로 관리한다.
- `recommended_bias != no_clear_edge`이고 `policy_hint=candidate_weight_source`인 bucket만 다음 bounded canary 후보로 본다.
- all `no_clear_edge`이면 perfect spot 대기가 아니라 최소 edge 부재로 판정하고 live AI 응답을 바꾸지 않는다.
