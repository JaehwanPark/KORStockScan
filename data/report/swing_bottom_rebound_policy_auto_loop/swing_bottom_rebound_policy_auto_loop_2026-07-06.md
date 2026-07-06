# Swing Bottom Rebound Policy Auto Loop - 2026-07-06

- generated_at: `2026-07-06T20:53:06+09:00`
- decision_authority: `swing_bottom_rebound_sim_policy_auto_approval`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- ai_tier2_status: `parsed`
- classification_state: `sim_auto_approved`
- promote_policy: `True`
- baseline_research_ev_pct: `1.292905`
- candidate_sim_bucket_ev_pct: `1.292905`
- relative_improvement: `1.0`
- sample_count: `57773`
- warnings: `[]`

## Contract

- A 1 percent improvement can auto-approve only the next sim candidate-source policy.
- This does not approve live orders, real canaries, runtime env, thresholds, providers, or bot actions.
- If Tier-2 AI is unavailable, the report keeps collecting instead of promoting.
