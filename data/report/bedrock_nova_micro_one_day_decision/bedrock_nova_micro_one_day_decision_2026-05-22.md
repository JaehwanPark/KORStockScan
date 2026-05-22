# Bedrock Nova Micro One-Day Decision - 2026-05-22

## 판정

- window_policy: `one_day`
- source_dates: `['2026-05-22']`
- winner: `openai`
- winning_profile: `openai_baseline`
- winner_reason: `openai_ev_edge_1.4036_pct`
- no_defer_policy: `True`

## 근거

- entry_watch_buy: unique_valid_join_rows=`11`, openai_ev=`0.0`, nova_micro_ev=`-1.4036`, diff=`-1.4036`
- holding_continuation: unique_valid_join_rows=`79`, openai_ev=`-0.0353`, nova_micro_ev=`-0.0063`, diff=`0.029`
- source_paths: `{'shadow_jsonl': ['/home/ubuntu/KORStockScan/data/report/bedrock_nova_micro_shadow/bedrock_nova_micro_shadow_2026-05-22.jsonl'], 'sim_post_sell_evaluations': ['data/post_sell/sim_post_sell_evaluations_2026-05-22.jsonl'], 'sim_post_sell_candidates': ['data/post_sell/sim_post_sell_candidates_2026-05-22.jsonl']}`

## 다음 액션

- `turn_micro_shadow_off_keep_openai`
- 기존 threshold/postclose/LDM/runtime approval 자동화체인에는 연결하지 않는다.
- global provider route, broker order, threshold mutation 근거로 사용하지 않는다.
