# Bedrock Nova Micro Cumulative Decision - 2026-05-22

## 판정

- window_policy: `cumulative`
- source_dates: `['2026-05-21', '2026-05-22']`
- winner: `openai`
- winning_profile: `openai_baseline_with_holding_continuation_nova_micro_candidate`
- winner_reason: `split_profile_entry_openai_holding_nova_micro_candidate_no_global_route_change`
- no_defer_policy: `True`

## Profile Decisions

- entry_watch_buy: winner=`openai`, reason=`openai_ev_edge_0.8000_pct`, unique_valid_join_rows=`20`, openai_ev=`0.0`, nova_micro_ev=`-0.8`, diff=`-0.8`
  action_pair_counts: `{'WAIT->BUY': 103}`
  outcome_counts: `{'MISSED_UPSIDE': 9, 'NEUTRAL': 7, 'GOOD_EXIT': 4}`
- holding_continuation: winner=`nova_micro`, reason=`nova_ev_edge_0.0314_pct`, unique_valid_join_rows=`132`, openai_ev=`-0.04`, nova_micro_ev=`-0.0086`, diff=`0.0314`
  action_pair_counts: `{'HOLD->HOLD': 2826, 'EXIT->HOLD': 1097, 'TRIM->HOLD': 11, 'HOLD->EXIT': 11, 'TO_BE_DETERMINED->HOLD': 1, 'EXIT->EXIT': 3}`
  outcome_counts: `{'MISSED_UPSIDE': 45, 'GOOD_EXIT': 47, 'NEUTRAL': 40}`

## 근거

- entry_watch_buy: unique_valid_join_rows=`20`, openai_ev=`0.0`, nova_micro_ev=`-0.8`, diff=`-0.8`
- holding_continuation: unique_valid_join_rows=`132`, openai_ev=`-0.04`, nova_micro_ev=`-0.0086`, diff=`0.0314`
- source_paths: `{'shadow_jsonl': ['/home/ubuntu/KORStockScan/data/report/bedrock_nova_micro_shadow/bedrock_nova_micro_shadow_2026-05-21.jsonl', '/home/ubuntu/KORStockScan/data/report/bedrock_nova_micro_shadow/bedrock_nova_micro_shadow_2026-05-22.jsonl'], 'sim_post_sell_evaluations': ['data/post_sell/sim_post_sell_evaluations_2026-05-21.jsonl', 'data/post_sell/sim_post_sell_evaluations_2026-05-22.jsonl'], 'sim_post_sell_candidates': ['data/post_sell/sim_post_sell_candidates_2026-05-21.jsonl', 'data/post_sell/sim_post_sell_candidates_2026-05-22.jsonl']}`

## 다음 액션

- `keep_micro_shadow_collecting_for_profile_split`
- 기존 threshold/postclose/LDM/runtime approval 자동화체인에는 연결하지 않는다.
- global provider route, broker order, threshold mutation 근거로 사용하지 않는다.
