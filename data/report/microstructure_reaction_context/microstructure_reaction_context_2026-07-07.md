# Microstructure Reaction Context - 2026-07-07

- runtime_effect: `False`
- decision_authority: `entry_confidence_modifier_source_only`
- forbidden_uses: `['standalone_buy', 'broker_guard_bypass', 'threshold_mutation', 'provider_route_change', 'bot_restart', 'cap_release']`

## Summary
- available: `True`
- row_count: `3035`
- ok/missing_or_unusable: `601` / `2434`
- real_submitted_count: `27`
- status_counts: `{'not_evaluated': 554, 'ok': 601, 'source_quality_partial': 34, 'stale': 1846}`
- entry_reaction_quality_counts: `{'favorable_reaction': 23, 'mixed_reaction': 197, 'neutral_unusable': 2434, 'risk_context_only': 165, 'weak_reaction': 216}`
- source_quality_counts: `{'ai_confirmed_terminal_no_budget_source_quality_missing': 32, 'ai_score_50_buy_hold_override_no_tick_audit': 75, 'blocked_ai_score_no_tick_audit': 32, 'fresh_short_window': 601, 'pre_ai_liquidity_gate': 140, 'pre_ai_overbought_gate': 108, 'snapshot_pre_contract_backfill': 128, 'stale_tick_or_quote': 1846, 'tick_aggressor_pressure_unusable': 34, 'watching_ai_cooldown_active': 39}`
- stage_counts: `{'ai_confirmed': 250, 'ai_confirmed_terminal_no_budget': 299, 'ai_cooldown_blocked': 39, 'ai_holding_review': 1414, 'blocked_ai_score': 233, 'blocked_liquidity': 140, 'blocked_overbought': 108, 'order_bundle_submitted': 1, 'real_weak_pullback_entry_block': 1, 'scalp_entry_action_decision_snapshot': 550}`
- avg_ask_sweep_score: `48.44`
- avg_post_sweep_hold_score: `49.997`
- avg_bid_replenishment_score: `53.516`
- max_vi_proximity_risk: `20`
- warnings: `[]`
