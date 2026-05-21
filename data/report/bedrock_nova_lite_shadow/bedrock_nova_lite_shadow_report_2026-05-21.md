# Bedrock Nova Lite Shadow Report - 2026-05-21

- generated_at: `2026-05-21T12:30:18+09:00`
- decision_authority: `shadow_observation_only`
- runtime_effect: `False`
- rows: `8`
- parse_ok_rate: `0.875`
- action_match_rate: `0.8571`

## Latency

- latency: `{'openai_latency_ms': {'n': 7, 'avg': 2113.29, 'median': 2206.0, 'p75': 2486.5, 'p90': 2856.6, 'p95': 3132.3, 'max': 3408.0}, 'nova_latency_ms': {'n': 8, 'avg': 1261.25, 'median': 1267.5, 'p75': 1547.75, 'p90': 1774.7, 'p95': 1823.35, 'max': 1872.0}}`

## Cost

- cost: `{'estimated_openai_cost_usd': 0.01898175, 'estimated_nova_cost_usd': 0.00181451, 'estimated_nova_minus_openai_usd': -0.01716724, 'estimated_nova_to_openai_ratio': 0.0956}`

## Prompt Cache

- prompt_cache: `{'enabled_row_count': 7, 'nova_input_tokens': 20044, 'nova_cache_read_input_tokens': 5129, 'nova_cache_write_input_tokens': 1965, 'nova_total_input_tokens': 27138, 'cache_read_stats': {'n': 7, 'avg': 732.71, 'median': 1033.0, 'p75': 1051.0, 'p90': 1063.6, 'p95': 1067.8, 'max': 1072.0}, 'cache_write_stats': {'n': 7, 'avg': 280.71, 'median': 0.0, 'p75': 467.5, 'p90': 973.0, 'p95': 1001.5, 'max': 1030.0}, 'pricing_note': 'When Bedrock prompt caching is enabled, inputTokens can exclude cache read/write tokens; cost uses all three buckets when present.'}`

## Decision Agreement

- decision_agreement: `{'endpoint_counts': {'manual_bedrock_nova_lite_test': 1, 'holding_flow': 5, 'entry_price': 2}, 'source_event_stage_counts': {'unknown': 8}, 'score_delta': {'n': 7, 'avg': -7.43, 'median': -6.0, 'p75': 2.5, 'p90': 8.4, 'p95': 10.2, 'max': 12.0}, 'openai_action_counts': {'WAIT': 1, 'TRIM': 1, 'HOLD': 3, 'USE_DEFENSIVE': 2}, 'nova_action_counts': {'CLASSIFY': 1, 'TRIM': 1, 'HOLD': 3, 'USE_DEFENSIVE': 2}}`

## Outcome-Linked Performance

- outcome_linked_performance: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'shadow_observation_only', 'runtime_effect': False, 'source_path': 'data/post_sell/sim_post_sell_candidates_2026-05-21.jsonl', 'sell_completed_count': 137, 'exact_matched_count': 0, 'unmatched_sell_count': 137, 'join_quality': {'method': 'exact_sim_record_id_only', 'exact_match_rate': 0.0, 'note': 'Rows before sim_record_id instrumentation remain unmatched instead of being treated as reliable performance evidence.'}, 'overall': {'openai_outcome_score_sum': 0, 'nova_outcome_score_sum': 0, 'nova_minus_openai_outcome_score': 0, 'nova_edge_count': 0, 'openai_edge_count': 0, 'tie_count': 0}, 'by_stage': {}, 'sample_rows': [], 'scoring_note': 'defensive action is positive when final sim PnL is negative and negative when final sim PnL is positive; HOLD/BUY is the inverse; WAIT is neutral.', 'forbidden_uses': ['provider route change', 'runtime threshold mutation', 'broker order decision', 'bot restart trigger']}`

## Parse / Schema Quality

- parse_schema_quality: `{'error_counts': {'JSONDecodeError': 1}, 'parse_fail_count': 1}`
- forbidden: threshold/provider/order/bot restart 변경 근거로 사용하지 않는다.
