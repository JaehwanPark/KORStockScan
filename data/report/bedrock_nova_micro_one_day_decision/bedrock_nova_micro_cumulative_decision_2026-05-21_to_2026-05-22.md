# Bedrock Nova Micro Cumulative Decision - 2026-05-22

## 판정

- window_policy: `cumulative`
- source_dates: `['2026-05-21', '2026-05-22']`
- winner: `openai`
- winning_profile: `openai_baseline`
- winner_reason: `openai_ev_edge_0.8000_pct`
- no_defer_policy: `True`

## 근거

- entry_watch_buy: unique_valid_join_rows=`20`, openai_ev=`0.0`, nova_micro_ev=`-0.8`, diff=`-0.8`
- holding_continuation: unique_valid_join_rows=`132`, openai_ev=`-0.04`, nova_micro_ev=`-0.0086`, diff=`0.0314`
- source_paths: `{'shadow_jsonl': ['/home/ubuntu/KORStockScan/data/report/bedrock_nova_micro_shadow/bedrock_nova_micro_shadow_2026-05-21.jsonl', '/home/ubuntu/KORStockScan/data/report/bedrock_nova_micro_shadow/bedrock_nova_micro_shadow_2026-05-22.jsonl'], 'sim_post_sell_evaluations': ['data/post_sell/sim_post_sell_evaluations_2026-05-21.jsonl', 'data/post_sell/sim_post_sell_evaluations_2026-05-22.jsonl'], 'sim_post_sell_candidates': ['data/post_sell/sim_post_sell_candidates_2026-05-21.jsonl', 'data/post_sell/sim_post_sell_candidates_2026-05-22.jsonl']}`

## 다음 액션

- `turn_micro_shadow_off_keep_openai`
- 기존 threshold/postclose/LDM/runtime approval 자동화체인에는 연결하지 않는다.
- global provider route, broker order, threshold mutation 근거로 사용하지 않는다.
