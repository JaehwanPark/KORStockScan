# Bedrock Nova Lite One-Day Tier2 Decision - 2026-05-22

## 판정

- status: `pass`
- winner: `lite`
- route_candidate: `tier2_nova_lite_v1`
- route_candidate_scope: `gpt-5.4-mini_tier2_all`
- winner_reason: `lite_within_1pct_or_better diff=0.0209`

## 근거

- overall: unique_valid_join_rows=`185`, openai_ev=`-0.4002`, lite_ev=`-0.3793`, diff=`0.0209`
- holding_flow: unique_valid_join_rows=`82`, openai_ev=`-0.0276`, lite_ev=`0.0196`, diff=`0.0472`, underperformance_blocker=`False`
- entry_price: unique_valid_join_rows=`103`, openai_ev=`-0.6968`, lite_ev=`-0.6968`, diff=`0.0`, underperformance_blocker=`False`
- other_tier2: unique_valid_join_rows=`0`, openai_ev=`0.0`, lite_ev=`0.0`, diff=`0.0`, underperformance_blocker=`False`
- source_paths: `{'shadow_jsonl': '/home/ubuntu/KORStockScan/data/report/bedrock_nova_lite_shadow/bedrock_nova_lite_shadow_2026-05-22.jsonl', 'sim_post_sell_evaluations': 'data/post_sell/sim_post_sell_evaluations_2026-05-22.jsonl', 'sim_post_sell_candidates': 'data/post_sell/sim_post_sell_candidates_2026-05-22.jsonl'}`
- interpretation_guard: `Do not decide from action exact match count, parse_ok, latency, cost, token/cache savings, one-dimensional nova_minus_openai score, or all-row action aggregation.`

## 다음 액션

- `winner_lite_record_tier2_route_candidate_turn_shadow_off`
- 기존 threshold/postclose/LDM/runtime approval 자동화체인에는 연결하지 않는다.
- 실제 provider route 변경은 별도 approval/workorder 또는 명시 실행 지시 없이는 적용하지 않는다.
