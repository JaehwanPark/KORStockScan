# Microstructure Reaction Context - 2026-06-24

- runtime_effect: `False`
- decision_authority: `entry_confidence_modifier_source_only`
- forbidden_uses: `['standalone_buy', 'broker_guard_bypass', 'threshold_mutation', 'provider_route_change', 'bot_restart', 'cap_release']`

## Summary
- available: `True`
- row_count: `5579`
- ok/missing_or_unusable: `1681` / `3898`
- real_submitted_count: `18`
- status_counts: `{'not_evaluated': 1391, 'ok': 1681, 'stale': 2507}`
- entry_reaction_quality_counts: `{'favorable_reaction': 40, 'mixed_reaction': 421, 'neutral_unusable': 3898, 'risk_context_only': 628, 'weak_reaction': 592}`
- source_quality_counts: `{'ai_score_50_buy_hold_override_no_tick_audit': 293, 'fresh_short_window': 1681, 'pre_ai_liquidity_gate': 490, 'pre_ai_overbought_gate': 578, 'snapshot_pre_contract_backfill': 1, 'stale_tick_or_quote': 2507, 'watching_ai_cooldown_active': 29}`
- stage_counts: `{'ai_confirmed': 691, 'ai_confirmed_terminal_no_budget': 797, 'ai_cooldown_blocked': 29, 'ai_holding_review': 809, 'blocked_ai_score': 728, 'blocked_liquidity': 490, 'blocked_overbought': 578, 'order_bundle_failed': 1, 'order_bundle_submitted': 9, 'pre_submit_liquidity_guard_block': 8, 'pre_submit_overbought_pullback_guard_block': 1, 'pre_submit_weak_context_late_entry_guard_block': 1, 'real_weak_pullback_entry_block': 2, 'scalp_entry_action_decision_snapshot': 1435}`
- avg_ask_sweep_score: `47.051`
- avg_post_sweep_hold_score: `50.135`
- avg_bid_replenishment_score: `54.308`
- max_vi_proximity_risk: `80`
- warnings: `[]`
