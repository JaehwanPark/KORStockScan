# Swing Bottom Rebound Policy Auto Loop - 2026-07-27

- generated_at: `2026-07-27T20:58:05+09:00`
- decision_authority: `swing_bottom_rebound_sim_policy_auto_approval`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- ai_tier2_status: `parsed`
- classification_state: `source_only_keep_collecting`
- promote_policy: `False`
- baseline_research_ev_pct: `1.295732`
- candidate_sim_bucket_ev_pct: `1.295732`
- relative_improvement: `1.0`
- sample_count: `58888`
- warnings: `['explicit_gap:swing_strategy_discovery_ev_contract_failed']`

## Contract

- A 1 percent improvement can auto-approve only the next sim candidate-source policy.
- This does not approve live orders, real canaries, runtime env, thresholds, providers, or bot actions.
- If Tier-2 AI is unavailable, the report keeps collecting instead of promoting.
