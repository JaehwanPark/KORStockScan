# Bedrock Nova Micro Shadow Report - 2026-05-21

- generated_at: `2026-05-21T11:56:23+09:00`
- decision_authority: `shadow_observation_only`
- runtime_effect: `False`
- rows: `573`
- parse_ok_rate: `0.9983`
- action_match_rate: `0.6871`

## Latency

- latency: `{'openai_latency_ms': {'n': 571, 'avg': 1130.0, 'median': 987.0, 'p75': 1215.0, 'p90': 1572.0, 'p95': 1865.0, 'max': 5875.0}, 'nova_latency_ms': {'n': 572, 'avg': 520.6, 'median': 530.5, 'p75': 590.0, 'p90': 653.9, 'p95': 687.45, 'max': 1135.0}}`

## Cost

- cost: `{'estimated_openai_cost_usd': 0.0713638, 'estimated_nova_cost_usd': 0.04765303, 'estimated_nova_minus_openai_usd': -0.02371077, 'estimated_nova_to_openai_ratio': 0.6677}`

## Prompt Cache

- prompt_cache: `{'enabled_row_count': 309, 'nova_input_tokens': 1250744, 'nova_cache_read_input_tokens': 283341, 'nova_cache_write_input_tokens': 3888, 'nova_total_input_tokens': 1537973, 'cache_read_stats': {'n': 309, 'avg': 916.96, 'median': 732.0, 'p75': 1234.0, 'p90': 1244.2, 'p95': 1249.0, 'max': 1251.0}, 'cache_write_stats': {'n': 309, 'avg': 12.58, 'median': 0.0, 'p75': 0.0, 'p90': 0.0, 'p95': 0.0, 'max': 1218.0}, 'pricing_note': 'When Bedrock prompt caching is enabled, inputTokens can exclude cache read/write tokens; cost uses all three buckets when present.'}`

## Decision Agreement

- decision_agreement: `{'endpoint_counts': {'manual_bedrock_nova_micro_test': 2, 'analyze_target': 571}, 'source_event_stage_counts': {'unknown': 497, 'scalp_sim_holding_review': 43, 'watching_analyze_target': 33}, 'score_delta': {'n': 572, 'avg': 13.22, 'median': 13.0, 'p75': 40.0, 'p90': 43.0, 'p95': 43.0, 'max': 57.0}, 'openai_action_counts': {'WAIT': 204, 'HOLD': 218, 'EXIT': 149, 'TRIM': 1}, 'nova_action_counts': {'BUY': 9, 'HOLD': 366, 'WAIT': 173, 'EXIT': 2, 'DROP': 22}}`

## Outcome-Linked Performance

- outcome_linked_performance: `{'metric_role': 'sim_probe_ev', 'decision_authority': 'shadow_observation_only', 'runtime_effect': False, 'source_path': 'data/post_sell/sim_post_sell_candidates_2026-05-21.jsonl', 'sell_completed_count': 129, 'exact_matched_count': 3, 'unmatched_sell_count': 126, 'join_quality': {'method': 'exact_sim_record_id_only', 'exact_match_rate': 0.0233, 'note': 'Rows before sim_record_id instrumentation remain unmatched instead of being treated as reliable performance evidence.'}, 'overall': {'openai_outcome_score_sum': -3, 'nova_outcome_score_sum': 1, 'nova_minus_openai_outcome_score': 4, 'nova_edge_count': 2, 'openai_edge_count': 0, 'tie_count': 1}, 'by_stage': {'scalp_sim_holding_review': {'matched_count': 3, 'openai_outcome_score_sum': -3, 'nova_outcome_score_sum': 1, 'nova_edge_count': 2, 'openai_edge_count': 0, 'tie_count': 1, 'avg_profit_rate': 2.2467}}, 'sample_rows': [{'sim_record_id': 'SCALPSIM-119830-1779330995344-7ff897', 'symbol': '아이텍', 'stock_name': '아이텍', 'sell_time': '11:53:58', 'profit_rate': -1.51, 'exit_rule': 'scalp_soft_stop_pct', 'source_event_stage': 'scalp_sim_holding_review', 'openai_action': 'HOLD', 'openai_score': 78, 'nova_action': 'HOLD', 'nova_score': 85, 'openai_outcome_score': -1, 'nova_outcome_score': -1, 'model_edge': 'tie', 'join_type': 'exact_sim_record_id', 'post_sell_id': '0a09b7f70e454edc', 'entry_adm_candidate_id': 'ADM-119830-7461-1779330995339-300194'}, {'sim_record_id': 'SCALPSIM-034220-1779329002202-5710c7', 'symbol': 'LG디스플레이', 'stock_name': 'LG디스플레이', 'sell_time': '11:55:45', 'profit_rate': 5.23, 'exit_rule': 'scalp_ai_momentum_decay', 'source_event_stage': 'scalp_sim_holding_review', 'openai_action': 'EXIT', 'openai_score': 42, 'nova_action': 'HOLD', 'nova_score': 85, 'openai_outcome_score': -1, 'nova_outcome_score': 1, 'model_edge': 'nova', 'join_type': 'exact_sim_record_id', 'post_sell_id': '114bfeb2e1644171', 'entry_adm_candidate_id': 'ADM-034220-7465-1779329002186-33ef29'}, {'sim_record_id': 'SCALPSIM-032580-1779331568002-b7f78c', 'symbol': '피델릭스', 'stock_name': '피델릭스', 'sell_time': '11:55:45', 'profit_rate': 3.02, 'exit_rule': 'scalp_trailing_take_profit', 'source_event_stage': 'scalp_sim_holding_review', 'openai_action': 'EXIT', 'openai_score': 42, 'nova_action': 'HOLD', 'nova_score': 85, 'openai_outcome_score': -1, 'nova_outcome_score': 1, 'model_edge': 'nova', 'join_type': 'exact_sim_record_id', 'post_sell_id': '8b9dd047da0d42db', 'entry_adm_candidate_id': 'ADM-032580-7603-1779331246890-d59f7b'}], 'scoring_note': 'defensive action is positive when final sim PnL is negative and negative when final sim PnL is positive; HOLD/BUY is the inverse; WAIT is neutral.', 'forbidden_uses': ['provider route change', 'runtime threshold mutation', 'broker order decision', 'bot restart trigger']}`

## Parse / Schema Quality

- parse_schema_quality: `{'error_counts': {'ValidationException': 1}, 'parse_fail_count': 1}`
- forbidden: threshold/provider/order/bot restart 변경 근거로 사용하지 않는다.
