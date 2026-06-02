# Microstructure Reaction Context - 2026-06-02

- runtime_effect: `False`
- decision_authority: `entry_confidence_modifier_source_only`
- forbidden_uses: `['standalone_buy', 'broker_guard_bypass', 'threshold_mutation', 'provider_route_change', 'bot_restart', 'cap_release']`

## Summary
- available: `True`
- row_count: `24203`
- ok/missing_or_unusable: `8607` / `15596`
- real_submitted_count: `22`
- status_counts: `{'not_evaluated': 13369, 'ok': 8607, 'stale': 2227}`
- entry_reaction_quality_counts: `{'favorable_reaction': 385, 'mixed_reaction': 2441, 'neutral_unusable': 15596, 'risk_context_only': 2275, 'weak_reaction': 3506}`
- source_quality_counts: `{'ai_score_50_buy_hold_override_no_tick_audit': 448, 'fresh_short_window': 8607, 'pre_ai_liquidity_gate': 1350, 'pre_ai_overbought_gate': 10705, 'stale_tick_or_quote': 2227, 'watching_ai_cooldown_active': 866}`
- stage_counts: `{'ai_confirmed': 1559, 'ai_cooldown_blocked': 866, 'ai_holding_review': 4447, 'blocked_ai_score': 2236, 'blocked_liquidity': 1350, 'blocked_overbought': 10705, 'order_bundle_failed': 16, 'order_bundle_submitted': 22, 'pre_submit_liquidity_guard_block': 65, 'scalp_entry_action_decision_snapshot': 2937}`
- avg_ask_sweep_score: `46.381`
- avg_post_sweep_hold_score: `50.02`
- avg_bid_replenishment_score: `56.18`
- max_vi_proximity_risk: `80`
- warnings: `[]`
