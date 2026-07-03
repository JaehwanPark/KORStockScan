# Microstructure Reaction Context - 2026-07-03

- runtime_effect: `False`
- decision_authority: `entry_confidence_modifier_source_only`
- forbidden_uses: `['standalone_buy', 'broker_guard_bypass', 'threshold_mutation', 'provider_route_change', 'bot_restart', 'cap_release']`

## Summary
- available: `True`
- row_count: `2943`
- ok/missing_or_unusable: `493` / `2450`
- real_submitted_count: `24`
- status_counts: `{'not_evaluated': 696, 'ok': 493, 'source_quality_missing': 2, 'stale': 1752}`
- entry_reaction_quality_counts: `{'favorable_reaction': 10, 'mixed_reaction': 126, 'neutral_unusable': 2450, 'risk_context_only': 128, 'weak_reaction': 229}`
- source_quality_counts: `{'ai_confirmed_terminal_no_budget_source_quality_missing': 17, 'ai_score_50_buy_hold_override_no_tick_audit': 31, 'blocked_ai_score_no_tick_audit': 17, 'fresh_short_window': 493, 'missing_orderbook': 2, 'pre_ai_liquidity_gate': 115, 'pre_ai_overbought_gate': 103, 'snapshot_pre_contract_backfill': 384, 'stale_tick_or_quote': 1752, 'watching_ai_cooldown_active': 29}`
- stage_counts: `{'ai_confirmed': 157, 'ai_confirmed_terminal_no_budget': 227, 'ai_cooldown_blocked': 29, 'ai_holding_review': 1387, 'blocked_ai_score': 177, 'blocked_liquidity': 115, 'blocked_overbought': 103, 'order_bundle_submitted': 1, 'real_weak_pullback_entry_block': 2, 'scalp_entry_action_decision_snapshot': 745}`
- avg_ask_sweep_score: `47.891`
- avg_post_sweep_hold_score: `49.957`
- avg_bid_replenishment_score: `52.66`
- max_vi_proximity_risk: `41`
- warnings: `[]`
