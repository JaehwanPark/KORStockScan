# Holding/Exit Decision Matrix - 2026-07-10

## 판정

- matrix_version: `holding_exit_decision_matrix_v1_2026-07-10`
- application_mode: `advisory_canary_live_readiness_until_owner_approval`
- runtime_change: `False`

## Hard Veto

- `emergency_or_hard_stop`
- `active_sell_order_pending`
- `invalid_feature`
- `post_add_eval_exclusion`

## Counterfactual Coverage

- non_no_clear_edge_count: `2`
- no_clear_edge_count: `12`
- candidate_weight_source_non_clear_edge_count: `2`
- ready_count: `4` / `14`
- ready_rate: `0.2857`
- per_action_edge_buckets: `{'prefer_exit': 1, 'prefer_avg_down_wait': 1, 'prefer_pyramid_wait': 0}`
- per_action_samples: `{'exit_only': 216, 'avg_down_wait': 33, 'pyramid_wait': 6}`
- proxy_sample_snapshots: `1206`
- proxy_joined_candidates: `346`
- proxy_actions_present: `['hold_defer', 'exit_only', 'avg_down_wait', 'pyramid_wait']`
- proxy_missing_actions: `[]`
- proxy_per_action_samples: `{'hold_defer': 1190, 'exit_only': 61, 'avg_down_wait': 1010, 'pyramid_wait': 185}`


## Matrix Entries

| axis | bucket | bias | score | edge | sample | loss_rate | cf_ready | missing_actions | policy |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| price_bucket | price_10k_30k | prefer_avg_down_wait | -1.3341 | 0.451 | 5 | 0.4 | False | pyramid_wait | candidate_weight_source |
| price_bucket | price_30k_70k | no_clear_edge | -0.4646 | - | 15 | 0.2 | True | - | candidate_weight_source |
| price_bucket | price_gte_70k | no_clear_edge | -0.6542 | - | 11 | 0.3636 | True | - | candidate_weight_source |
| price_bucket | price_lt_10k | no_clear_edge | -1.3282 | - | 17 | 0.4706 | False | pyramid_wait | candidate_weight_source |
| volume_bucket | volume_2m_10m | no_clear_edge | -1.2379 | - | 10 | 0.3 | False | pyramid_wait | candidate_weight_source |
| volume_bucket | volume_500k_2m | no_clear_edge | -1.0076 | - | 14 | 0.3571 | True | - | candidate_weight_source |
| volume_bucket | volume_gte_10m | no_clear_edge | -1.7028 | - | 12 | 0.5833 | False | pyramid_wait | candidate_weight_source |
| volume_bucket | volume_lt_500k | no_clear_edge | -0.9639 | - | 27 | 0.4444 | False | pyramid_wait | candidate_weight_source |
| volume_bucket | volume_unknown | no_clear_edge | -2.2711 | - | 9 | 0.4444 | False | pyramid_wait | candidate_weight_source |
| time_bucket | time_0900_0930 | no_clear_edge | - | - | - | - | False | pyramid_wait | insufficient_sample |
| time_bucket | time_0930_1030 | no_clear_edge | -0.348 | - | 8 | 0.25 | False | avg_down_wait,pyramid_wait | candidate_weight_source |
| time_bucket | time_1030_1400 | no_clear_edge | -1.7661 | - | 25 | 0.48 | True | - | candidate_weight_source |
| time_bucket | time_1400_1530 | no_clear_edge | -0.8513 | - | 8 | 0.5 | False | avg_down_wait,pyramid_wait | candidate_weight_source |
| time_bucket | time_outside_regular | prefer_exit | -0.9851 | 1.0028 | 29 | 0.4138 | False | pyramid_wait | candidate_weight_source |

## Prompt Hints

- `price_bucket=price_10k_30k` / `prefer_avg_down_wait`: price_bucket=price_10k_30k 과거 표본은 회복형 물타기 대기 후보가 상대적으로 우위다. 저점 미갱신과 수급 회복이 없으면 무시한다.
- `price_bucket=price_30k_70k` / `no_clear_edge`: price_bucket=price_30k_70k 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `price_bucket=price_gte_70k` / `no_clear_edge`: price_bucket=price_gte_70k 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `price_bucket=price_lt_10k` / `no_clear_edge`: price_bucket=price_lt_10k 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `volume_bucket=volume_2m_10m` / `no_clear_edge`: volume_bucket=volume_2m_10m 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `volume_bucket=volume_500k_2m` / `no_clear_edge`: volume_bucket=volume_500k_2m 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `volume_bucket=volume_gte_10m` / `no_clear_edge`: volume_bucket=volume_gte_10m 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `volume_bucket=volume_lt_500k` / `no_clear_edge`: volume_bucket=volume_lt_500k 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `volume_bucket=volume_unknown` / `no_clear_edge`: volume_bucket=volume_unknown 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `time_bucket=time_0900_0930` / `no_clear_edge`: time_bucket=time_0900_0930 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `time_bucket=time_0930_1030` / `no_clear_edge`: time_bucket=time_0930_1030 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `time_bucket=time_1030_1400` / `no_clear_edge`: time_bucket=time_1030_1400 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `time_bucket=time_1400_1530` / `no_clear_edge`: time_bucket=time_1400_1530 과거 표본은 행동 우위가 불명확하다. 기존 보유/청산 원칙을 우선한다.
- `time_bucket=time_outside_regular` / `prefer_exit`: time_bucket=time_outside_regular 과거 표본은 보유/추가매수보다 청산 우위가 있다. 단 hard veto와 현재 thesis를 먼저 확인한다.

## 다음 액션

- `ADM`은 shadow가 아니라 advisory canary/live-readiness 축으로 관리한다.
- `recommended_bias != no_clear_edge`이고 `policy_hint=candidate_weight_source`인 bucket만 다음 bounded canary 후보로 본다.
- all `no_clear_edge`이면 perfect spot 대기가 아니라 최소 edge 부재로 판정하고 live AI 응답을 바꾸지 않는다.
