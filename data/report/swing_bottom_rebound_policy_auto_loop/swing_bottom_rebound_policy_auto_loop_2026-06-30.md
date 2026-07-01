# Swing Bottom Rebound Policy Auto Loop - 2026-06-30

- generated_at: `2026-06-30T23:30:32+09:00`
- decision_authority: `swing_bottom_rebound_sim_policy_auto_approval`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- ai_tier2_status: `unavailable_deterministic_review`
- classification_state: `source_only_keep_collecting`
- promote_policy: `False`
- baseline_research_ev_pct: `1.27492`
- candidate_sim_bucket_ev_pct: `1.27492`
- relative_improvement: `1.0`
- sample_count: `57748`
- warnings: `['ai_review_response_missing', 'explicit_gap:tier2_ai_review_unavailable']`

## Contract

- A 1 percent improvement can auto-approve only the next sim candidate-source policy.
- This does not approve live orders, real canaries, runtime env, thresholds, providers, or bot actions.
- If Tier-2 AI is unavailable, the report keeps collecting instead of promoting.
