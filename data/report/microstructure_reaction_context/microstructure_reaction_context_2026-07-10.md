# Microstructure Reaction Context - 2026-07-10

- runtime_effect: `False`
- decision_authority: `entry_confidence_modifier_source_only`
- forbidden_uses: `['standalone_buy', 'broker_guard_bypass', 'threshold_mutation', 'provider_route_change', 'bot_restart', 'cap_release']`

## Summary
- available: `True`
- row_count: `2180`
- ok/missing_or_unusable: `286` / `1894`
- real_submitted_count: `38`
- status_counts: `{'not_evaluated': 117, 'ok': 286, 'source_quality_partial': 160, 'stale': 1617}`
- entry_reaction_quality_counts: `{'favorable_reaction': 8, 'mixed_reaction': 93, 'neutral_unusable': 1894, 'risk_context_only': 107, 'weak_reaction': 78}`
- source_quality_counts: `{'ai_score_50_buy_hold_override_no_tick_audit': 19, 'fresh_short_window': 286, 'pre_ai_liquidity_gate': 54, 'pre_ai_overbought_gate': 31, 'stale_tick_or_quote': 1617, 'tick_aggressor_pressure_unusable': 160, 'watching_ai_cooldown_active': 13}`
- stage_counts: `{'ai_confirmed': 269, 'ai_confirmed_terminal_no_budget': 185, 'ai_cooldown_blocked': 13, 'ai_holding_review': 905, 'blocked_ai_score': 89, 'blocked_liquidity': 54, 'blocked_overbought': 31, 'order_bundle_submitted': 19, 'pre_submit_entry_ai_authority_guard_block': 8, 'pre_submit_micro_unavailable_block': 2, 'real_weak_ai_micro_entry_block': 4, 'rising_missed_tick_speed_entry_block': 67, 'scalp_entry_action_decision_snapshot': 534}`
- tick_aggressor_source_counts: `{'missing_aggressor_side': 1323, 'orderbook_touch': 915, 'price_change_heuristic': 917}`
- tick_trade_value_source_counts: `{}`
- tick_trade_value_1313_missing_rate_pct: `0.0`
- trade_volume_source_counts: `{}`
- trade_volume_1030_1031_vs_15_mismatch: `0` / `0` (`0.0`%)
- kiwoom_0b_latest_stock_count: `133`
- kiwoom_0b_trade_value_source_counts: `{}`
- kiwoom_0b_1313_missing_rate_pct: `0.0`
- kiwoom_0b_trade_volume_source_counts: `{}`
- kiwoom_0b_1030_1031_vs_15_mismatch: `0` / `0` (`0.0`%)
- avg_ask_sweep_score: `50.015`
- avg_post_sweep_hold_score: `49.985`
- avg_bid_replenishment_score: `51.767`
- max_vi_proximity_risk: `38`
- warnings: `[]`
